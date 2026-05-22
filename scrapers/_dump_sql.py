"""One-off: run every scraper and emit a single SQL file with all inserts.

Used for the initial seed when we don't have the service_role key handy
(the Supabase MCP only exposes execute_sql, which can absorb this directly).

Usage:
    python -m scrapers._dump_sql > /tmp/seed.sql
"""

from __future__ import annotations

import sys
from datetime import date

from .core.registry import discover_benchmark_scrapers, discover_vendor_scrapers
from .core.schema import BenchmarkRecord, ModelRecord, PriceRecord


def q(s):
    """Quote a SQL string literal, doubling embedded single quotes."""
    if s is None:
        return "null"
    return "'" + str(s).replace("'", "''") + "'"


def num(v):
    return "null" if v is None else str(v)


def bool_(v):
    return "true" if v else "false"


def text_array(arr):
    if not arr:
        return "array[]::text[]"
    inside = ", ".join(q(x) for x in arr)
    return f"array[{inside}]::text[]"


def model_insert(m: ModelRecord) -> str:
    return (
        "insert into models (id, vendor_id, slug, name, family, release_date, "
        "context_window, max_output_tokens, modalities, is_open_weight, "
        "parameters_b, status, announcement_url, description) values ("
        f"{q(m.id)}, {q(m.vendor_id)}, {q(m.slug)}, {q(m.name)}, "
        f"{q(m.family)}, "
        f"{q(m.release_date.isoformat()) if m.release_date else 'null'}, "
        f"{num(m.context_window)}, {num(m.max_output_tokens)}, "
        f"{text_array(m.modalities)}, {bool_(m.is_open_weight)}, "
        f"{num(m.parameters_b)}, {q(m.status)}, "
        f"{q(m.announcement_url)}, {q(m.description)}"
        ") on conflict (id) do update set "
        "name=excluded.name, family=excluded.family, "
        "context_window=excluded.context_window, "
        "max_output_tokens=excluded.max_output_tokens, "
        "modalities=excluded.modalities, "
        "is_open_weight=excluded.is_open_weight, "
        "parameters_b=excluded.parameters_b, "
        "status=excluded.status, description=excluded.description, "
        "last_seen=now();"
    )


def price_insert(p: PriceRecord) -> str:
    return (
        "insert into prices (model_id, input_per_mtok, output_per_mtok, "
        "cached_input_per_mtok, currency, effective_date, source_url) values ("
        f"{q(p.model_id)}, {num(p.input_per_mtok)}, {num(p.output_per_mtok)}, "
        f"{num(p.cached_input_per_mtok)}, {q(p.currency)}, "
        f"{q(p.effective_date.isoformat())}, {q(p.source_url)});"
    )


def bench_insert(b: BenchmarkRecord) -> str:
    return (
        "insert into benchmark_scores (model_id, benchmark_name, score, "
        "score_unit, score_max, source, source_url, measured_at) values ("
        f"{q(b.model_id)}, {q(b.benchmark_name)}, {num(b.score)}, "
        f"{q(b.score_unit)}, {num(b.score_max)}, {q(b.source)}, "
        f"{q(b.source_url)}, "
        f"{q(b.measured_at.isoformat()) if b.measured_at else 'null'}"
        ");"
    )


def main() -> int:
    out = sys.stdout
    out.write("-- Auto-generated. Run once to seed initial data.\n\n")

    today = date.today()
    new_models: list[dict] = []

    out.write("-- ===== Models + Prices =====\n")
    for scraper in discover_vendor_scrapers():
        try:
            result = scraper.scrape()
        except Exception as e:
            sys.stderr.write(f"[skip] {scraper.vendor_id}: {e}\n")
            continue

        out.write(f"\n-- {scraper.vendor_id} ({len(result.models)} models / {len(result.prices)} prices)\n")
        for m in result.models:
            out.write(model_insert(m) + "\n")
            new_models.append({"id": m.id, "name": m.name, "vendor": m.vendor_id, "release_date": None})
        for p in result.prices:
            out.write(price_insert(p) + "\n")

    out.write("\n-- ===== Benchmarks =====\n")
    bench_count = 0
    for scraper in discover_benchmark_scrapers():
        try:
            result = scraper.scrape()
        except Exception as e:
            sys.stderr.write(f"[skip] {scraper.benchmark}: {e}\n")
            continue
        out.write(f"\n-- {scraper.benchmark} ({len(result.benchmarks)} scores)\n")
        for b in result.benchmarks:
            out.write(bench_insert(b) + "\n")
        bench_count += len(result.benchmarks)

    # Initial daily snapshot
    import json
    out.write(f"\n-- ===== Initial daily snapshot =====\n")
    out.write(
        "insert into daily_snapshots (snapshot_date, vendors_count, "
        "models_count, active_count, new_models, price_changes, "
        "status_changes, bench_changes) values ("
        f"'{today.isoformat()}', "
        f"(select count(*) from vendors), "
        f"(select count(*) from models), "
        f"(select count(*) from models where status='active'), "
        f"{q(json.dumps(new_models))}::jsonb, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb"
        ") on conflict (snapshot_date) do nothing;\n"
    )
    sys.stderr.write(f"\nDone. Models seeded across {len(list(discover_vendor_scrapers()))} vendors. {bench_count} benchmark scores.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
