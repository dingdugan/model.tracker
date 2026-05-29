"""Supabase persistence layer."""

from __future__ import annotations

import os
import traceback as tb
from datetime import date
from typing import Any, Optional

from supabase import Client, create_client

from .schema import BenchmarkRecord, DiscoveryCandidate, ModelRecord, PriceRecord, ScrapeResult
from .validation import CONFIRM_THRESHOLD, elo_anomaly, price_anomaly


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
        prev = self._latest_price(p.model_id)
        if prev and self._price_matches(prev, p):
            return  # unchanged
        if prev:
            # Anomaly gate: an egregious jump in any field is quarantined rather
            # than allowed to overwrite the known-good price. Auto-applies once
            # the same value persists CONFIRM_THRESHOLD runs.
            reasons = [
                r for r in (
                    price_anomaly(prev.get("input_per_mtok"),        p.input_per_mtok),
                    price_anomaly(prev.get("output_per_mtok"),       p.output_per_mtok),
                    price_anomaly(prev.get("cached_input_per_mtok"), p.cached_input_per_mtok),
                ) if r
            ]
            if reasons:
                confirmed = self._quarantine_or_confirm(
                    kind="price",
                    model_id=p.model_id,
                    field="price",
                    prior=prev.get("input_per_mtok"),
                    proposed=p.input_per_mtok,
                    reason="; ".join(reasons),
                    source_url=p.source_url,
                )
                if not confirmed:
                    return  # held back — last-good price stays live
        if prev:  # real change — record it
            event: dict[str, Any] = {
                "model_id":          p.model_id,
                "changed_at":        date.today().isoformat(),
                "input_old":         prev.get("input_per_mtok"),
                "input_new":         p.input_per_mtok,
                "output_old":        prev.get("output_per_mtok"),
                "output_new":        p.output_per_mtok,
                "cached_input_old":  prev.get("cached_input_per_mtok"),
                "cached_input_new":  p.cached_input_per_mtok,
                "currency":          p.currency,
            }
            self.client.table("price_change_events").insert(event).execute()
        self.client.table("prices").insert(row).execute()

    def _latest_price(self, model_id: str) -> Optional[dict[str, Any]]:
        res = (
            self.client.table("prices")
            .select("input_per_mtok,output_per_mtok,cached_input_per_mtok,currency")
            .eq("model_id", model_id)
            .order("effective_date", desc=True)
            .order("scraped_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def _price_matches(self, prev: dict[str, Any], p: PriceRecord) -> bool:
        return (
            _eq_num(prev.get("input_per_mtok"),        p.input_per_mtok)
            and _eq_num(prev.get("output_per_mtok"),   p.output_per_mtok)
            and _eq_num(prev.get("cached_input_per_mtok"), p.cached_input_per_mtok)
            and prev.get("currency", "USD") == p.currency
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
        # Anomaly gate for ELO: a slow-moving rating that leaps is suspect →
        # quarantine instead of polluting the score history.
        if b.score_unit == "elo":
            prev = self._latest_benchmark_score(b.model_id, b.benchmark_name)
            reason = elo_anomaly(prev, b.score)
            if reason:
                confirmed = self._quarantine_or_confirm(
                    kind="benchmark",
                    model_id=b.model_id,
                    field=b.benchmark_name,
                    prior=prev,
                    proposed=b.score,
                    reason=reason,
                    source_url=b.source_url,
                )
                if not confirmed:
                    return  # held back — history keeps the last-good score
        self.client.table("benchmark_scores").insert(row).execute()

    def _latest_benchmark_score(self, model_id: str, benchmark_name: str) -> Optional[float]:
        res = (
            self.client.table("benchmark_scores")
            .select("score, measured_at, scraped_at")
            .eq("model_id", model_id)
            .eq("benchmark_name", benchmark_name)
            .order("measured_at", desc=True)
            .order("scraped_at", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        try:
            return float(res.data[0]["score"])
        except (TypeError, ValueError, KeyError):
            return None

    def _quarantine_or_confirm(
        self,
        *,
        kind: str,
        model_id: str,
        field: str,
        prior: Optional[float],
        proposed: Optional[float],
        reason: str,
        source_url: Optional[str],
    ) -> bool:
        """Hold a suspicious value in pending_changes. Return True iff it should
        be applied now (same value confirmed across CONFIRM_THRESHOLD runs).

        A transient flip-flop keeps changing the proposed value, so its counter
        resets and it never confirms — the known-good value stays live. A genuine
        sustained change accumulates and auto-applies.
        """
        existing = (
            self.client.table("pending_changes")
            .select("id, proposed_value, occurrences, status")
            .eq("kind", kind)
            .eq("model_id", model_id)
            .eq("field", field)
            .limit(1)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            same = _eq_num(row.get("proposed_value"), proposed)
            if row.get("status") == "rejected" and same:
                return False  # human said no to exactly this value — keep ignoring
            if row.get("status") == "pending" and same:
                occ = (row.get("occurrences") or 1) + 1
                if occ >= CONFIRM_THRESHOLD:
                    self.client.table("pending_changes").update(
                        {"occurrences": occ, "status": "applied", "last_seen": "now()"}
                    ).eq("id", row["id"]).execute()
                    print(f"  [gate] {kind} {model_id}/{field}: confirmed after {occ} runs → applying")
                    return True
                self.client.table("pending_changes").update(
                    {"occurrences": occ, "last_seen": "now()"}
                ).eq("id", row["id"]).execute()
                print(f"  [gate] {kind} {model_id}/{field}: held ({occ}/{CONFIRM_THRESHOLD}) — {reason}")
                return False
            # new/different proposed value → (re)open as pending
            self.client.table("pending_changes").update(
                {
                    "prior_value": prior,
                    "proposed_value": proposed,
                    "reason": reason,
                    "occurrences": 1,
                    "status": "pending",
                    "last_seen": "now()",
                    "source_url": source_url,
                }
            ).eq("id", row["id"]).execute()
            print(f"  [gate] {kind} {model_id}/{field}: quarantined — {reason}")
            return False

        self.client.table("pending_changes").insert(
            {
                "kind": kind,
                "model_id": model_id,
                "field": field,
                "prior_value": prior,
                "proposed_value": proposed,
                "reason": reason,
                "source_url": source_url,
                "status": "pending",
            }
        ).execute()
        print(f"  [gate] {kind} {model_id}/{field}: quarantined — {reason}")
        return False

    def open_pending(self) -> list[dict[str, Any]]:
        """Quarantined changes still awaiting confirmation (status='pending')."""
        if self.dry_run or self._client is None:
            return []
        res = (
            self.client.table("pending_changes")
            .select("kind, model_id, field, prior_value, proposed_value, reason, occurrences")
            .eq("status", "pending")
            .order("last_seen", desc=True)
            .execute()
        )
        return res.data or []

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
    # Discovery candidates (Phase B) — proposed only, NEVER written to `models`
    # ──────────────────────────────────────────────────────────────────────
    def upsert_candidate(self, c: "DiscoveryCandidate") -> bool:
        """Record a discovery candidate. Returns True if it's newly created.

        Keyed on (source, normalized): a repeat sighting bumps occurrences and
        last_seen rather than duplicating. Never touches the `models` table.
        """
        from .model_registry import canon

        normalized = canon(c.reported_name)
        if not normalized:
            return False
        if self.dry_run:
            print(f"  [dry-run] candidate {c.source}: {c.reported_name}")
            return True

        existing = (
            self.client.table("discovery_candidates")
            .select("id, occurrences, status")
            .eq("source", c.source)
            .eq("normalized", normalized)
            .limit(1)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            self.client.table("discovery_candidates").update(
                {
                    "last_seen": "now()",
                    "occurrences": (row.get("occurrences") or 1) + 1,
                    "reported_name": c.reported_name,
                    "vendor_guess": c.vendor_guess,
                    "raw_context": c.raw_context or {},
                }
            ).eq("id", row["id"]).execute()
            return False

        self.client.table("discovery_candidates").insert(
            {
                "source":        c.source,
                "reported_name": c.reported_name,
                "normalized":    normalized,
                "vendor_guess":  c.vendor_guess,
                "raw_context":   c.raw_context or {},
                "status":        "new",
            }
        ).execute()
        return True

    def open_candidates(self) -> list[dict[str, Any]]:
        """Candidates still awaiting review (status='new')."""
        if self.dry_run or self._client is None:
            return []
        res = (
            self.client.table("discovery_candidates")
            .select("source, reported_name, vendor_guess, first_seen, occurrences")
            .eq("status", "new")
            .order("last_seen", desc=True)
            .execute()
        )
        return res.data or []

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

    def latest_benchmark_counts(self) -> dict[str, int]:
        """Per benchmark_name, how many models had a score at its most recent
        measured_at. Used as the baseline for structural-drift detection."""
        if self.dry_run or self._client is None:
            return {}
        res = self.client.table("benchmark_scores").select(
            "benchmark_name, model_id, measured_at"
        ).execute()
        rows = res.data or []
        latest: dict[str, str] = {}
        for r in rows:
            name, m = r.get("benchmark_name"), r.get("measured_at") or ""
            if name and (name not in latest or m > latest[name]):
                latest[name] = m
        counts: dict[str, set] = {}
        for r in rows:
            name = r.get("benchmark_name")
            if name and (r.get("measured_at") or "") == latest.get(name):
                counts.setdefault(name, set()).add(r.get("model_id"))
        return {k: len(v) for k, v in counts.items()}


def _eq_num(a: Optional[float], b: Optional[float], eps: float = 1e-9) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) < eps
