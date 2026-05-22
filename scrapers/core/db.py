"""Supabase persistence layer."""

from __future__ import annotations

import os
import traceback as tb
from datetime import date
from typing import Any, Optional

from supabase import Client, create_client

from .schema import BenchmarkRecord, ModelRecord, PriceRecord, ScrapeResult


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


class Database:
    def __init__(self, client: Optional[Client] = None, dry_run: bool = False):
        self.dry_run = dry_run
        self._client = client if client is not None else (None if dry_run else get_client())

    @property
    def client(self) -> Client:
        if self._client is None:
            raise RuntimeError("No Supabase client in dry-run mode")
        return self._client

    # ──────────────────────────────────────────────────────────────────────
    # Model upserts
    # ──────────────────────────────────────────────────────────────────────
    def upsert_model(self, m: ModelRecord) -> None:
        row: dict[str, Any] = {
            "id": m.id,
            "vendor_id": m.vendor_id,
            "slug": m.slug,
            "name": m.name,
            "family": m.family,
            "release_date": m.release_date.isoformat() if m.release_date else None,
            "context_window": m.context_window,
            "max_output_tokens": m.max_output_tokens,
            "modalities": list(m.modalities),
            "is_open_weight": m.is_open_weight,
            "license": m.license,
            "parameters_b": m.parameters_b,
            "status": m.status,
            "announcement_url": m.announcement_url,
            "description": m.description,
            "last_seen": "now()",
        }
        # last_seen needs to be a real timestamp — remove if it sneaks through
        row["last_seen"] = None  # let trigger or default refresh; we update via separate query
        row = {k: v for k, v in row.items() if v is not None or k in {"family", "release_date", "context_window", "max_output_tokens", "parameters_b", "announcement_url", "description"}}

        if self.dry_run:
            print(f"  [dry-run] upsert model {m.id}: {m.name}")
            return
        self.client.table("models").upsert(row, on_conflict="id").execute()
        self.client.table("models").update({"last_seen": "now()"}).eq("id", m.id).execute()

    def append_price(self, p: PriceRecord) -> None:
        row = {
            "model_id":               p.model_id,
            "input_per_mtok":         p.input_per_mtok,
            "output_per_mtok":        p.output_per_mtok,
            "cached_input_per_mtok":  p.cached_input_per_mtok,
            "cache_write_per_mtok":   p.cache_write_per_mtok,
            "batch_input_per_mtok":   p.batch_input_per_mtok,
            "batch_output_per_mtok":  p.batch_output_per_mtok,
            "currency":               p.currency,
            "effective_date":         p.effective_date.isoformat(),
            "source_url":             p.source_url,
        }
        if self.dry_run:
            print(f"  [dry-run] price {p.model_id}: in=${p.input_per_mtok} out=${p.output_per_mtok}/Mtok")
            return
        if self._price_already_current(p):
            return
        self.client.table("prices").insert(row).execute()

    def _price_already_current(self, p: PriceRecord) -> bool:
        """Skip insert if latest price row matches exactly — avoids cluttering history with duplicates."""
        res = (
            self.client.table("prices")
            .select("input_per_mtok,output_per_mtok,cached_input_per_mtok,currency")
            .eq("model_id", p.model_id)
            .order("effective_date", desc=True)
            .order("scraped_at", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return False
        last = res.data[0]
        return (
            _eq_num(last.get("input_per_mtok"),        p.input_per_mtok)
            and _eq_num(last.get("output_per_mtok"),   p.output_per_mtok)
            and _eq_num(last.get("cached_input_per_mtok"), p.cached_input_per_mtok)
            and last.get("currency", "USD") == p.currency
        )

    def append_benchmark(self, b: BenchmarkRecord) -> None:
        row = {
            "model_id":       b.model_id,
            "benchmark_name": b.benchmark_name,
            "score":          b.score,
            "score_unit":     b.score_unit,
            "score_max":      b.score_max,
            "source":         b.source,
            "source_url":     b.source_url,
            "measured_at":    b.measured_at.isoformat() if b.measured_at else None,
        }
        if self.dry_run:
            print(f"  [dry-run] {b.benchmark_name} {b.model_id}: {b.score} {b.score_unit}")
            return
        if self._benchmark_already_recorded(b):
            return
        self.client.table("benchmark_scores").insert(row).execute()

    def _benchmark_already_recorded(self, b: BenchmarkRecord) -> bool:
        """De-dupe by (model_id, benchmark_name, source, measured_at).

        Rationale: when measured_at advances we want to record the new
        measurement even if the score happens to equal the previous one
        (the data point is still meaningful — "still 91.5% on the new
        cycle"). But repeated reads of the same measurement should not
        clutter history. When measured_at is null we fall back to
        de-duping on the scraped date itself.
        """
        q = (
            self.client.table("benchmark_scores")
            .select("id, measured_at, scraped_at")
            .eq("model_id", b.model_id)
            .eq("benchmark_name", b.benchmark_name)
            .eq("source", b.source)
        )
        if b.measured_at is not None:
            q = q.eq("measured_at", b.measured_at.isoformat())
        else:
            # No reported measurement date — avoid re-recording within the same UTC day.
            q = q.is_("measured_at", "null").gte("scraped_at", date.today().isoformat())
        res = q.limit(1).execute()
        return bool(res.data)

    # ──────────────────────────────────────────────────────────────────────
    # High-level: persist a ScrapeResult atomically (best-effort)
    # ──────────────────────────────────────────────────────────────────────
    def persist(self, result: ScrapeResult) -> None:
        for m in result.models:
            self.upsert_model(m)
        for p in result.prices:
            self.append_price(p)
        for b in result.benchmarks:
            self.append_benchmark(b)

    # ──────────────────────────────────────────────────────────────────────
    # Errors
    # ──────────────────────────────────────────────────────────────────────
    def record_error(
        self,
        *,
        stage: str,
        message: str,
        vendor_id: Optional[str] = None,
        benchmark: Optional[str] = None,
        url: Optional[str] = None,
        exc: Optional[BaseException] = None,
    ) -> None:
        row = {
            "vendor_id":   vendor_id,
            "benchmark":   benchmark,
            "stage":       stage,
            "error_class": type(exc).__name__ if exc else None,
            "message":     message[:1000],
            "traceback":   "".join(tb.format_exception(exc))[-4000:] if exc else None,
            "url":         url,
        }
        if self.dry_run:
            print(f"  [dry-run] error {stage} {vendor_id or benchmark}: {message}")
            return
        try:
            self.client.table("scrape_errors").insert(row).execute()
        except Exception as e:
            print(f"  [warn] failed to record error: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # Daily snapshot
    # ──────────────────────────────────────────────────────────────────────
    def write_snapshot(self, snapshot_date: date, payload: dict[str, Any]) -> None:
        row = {"snapshot_date": snapshot_date.isoformat(), **payload}
        if self.dry_run:
            print(f"  [dry-run] snapshot {snapshot_date}: {payload}")
            return
        self.client.table("daily_snapshots").upsert(row, on_conflict="snapshot_date").execute()

    def latest_snapshot_before(self, d: date) -> Optional[dict[str, Any]]:
        if self.dry_run or self._client is None:
            return None
        res = (
            self.client.table("daily_snapshots")
            .select("*")
            .lt("snapshot_date", d.isoformat())
            .order("snapshot_date", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def all_current_models(self) -> list[dict[str, Any]]:
        if self.dry_run or self._client is None:
            return []
        res = self.client.table("models").select("id,status,name").execute()
        return res.data or []

    def all_current_prices(self) -> list[dict[str, Any]]:
        if self.dry_run or self._client is None:
            return []
        res = self.client.table("current_prices").select("*").execute()
        return res.data or []


def _eq_num(a: Optional[float], b: Optional[float], eps: float = 1e-9) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) < eps
