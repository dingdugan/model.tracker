"""model.tracker scraper entrypoint.

Usage:
  python -m scrapers.run                    # run all scrapers, write to Supabase
  python -m scrapers.run --dry-run          # run all, print, don't write
  python -m scrapers.run --vendor openai    # only one vendor
  python -m scrapers.run --benchmark lmsys  # only one benchmark
  python -m scrapers.run --skip-benchmarks  # vendors only
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date

from dotenv import load_dotenv

from .core.base import BenchmarkScraper, VendorScraper
from .core.db import Database
from .core.differ import build_snapshot_payload
from .core.registry import discover_benchmark_scrapers, discover_vendor_scrapers
from .core.schema import ScrapeResult


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="don't write to Supabase")
    parser.add_argument("--vendor", help="only run this vendor")
    parser.add_argument("--benchmark", help="only run this benchmark source")
    parser.add_argument("--skip-benchmarks", action="store_true")
    parser.add_argument("--skip-vendors", action="store_true")
    args = parser.parse_args()

    db = Database(dry_run=args.dry_run)

    vendor_scrapers = [] if args.skip_vendors else discover_vendor_scrapers()
    bench_scrapers  = [] if args.skip_benchmarks else discover_benchmark_scrapers()

    if args.vendor:
        vendor_scrapers = [s for s in vendor_scrapers if s.vendor_id == args.vendor]
        bench_scrapers = []
    if args.benchmark:
        bench_scrapers = [s for s in bench_scrapers if s.benchmark == args.benchmark]
        vendor_scrapers = []

    print(f"→ Running {len(vendor_scrapers)} vendor scrapers, {len(bench_scrapers)} benchmark scrapers")
    print(f"  dry-run={args.dry_run}")

    results: list[ScrapeResult] = []

    # Snapshot prior state for diff (only useful in real-write mode)
    prior_models = {m["id"]: m for m in db.all_current_models()}
    prior_prices = {p["model_id"]: p for p in db.all_current_prices()}

    for s in vendor_scrapers + bench_scrapers:
        label = getattr(s, "vendor_id", None) or getattr(s, "benchmark", None) or s.__class__.__name__
        print(f"\n• {label} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            result = s.scrape()
            results.append(result)
            print(f"OK ({time.time()-t0:.1f}s) — {result.summary()}")
            try:
                db.persist(result)
            except Exception as e:
                print(f"  [persist] {e}")
                db.record_error(
                    stage="persist",
                    message=str(e),
                    vendor_id=getattr(s, "vendor_id", None),
                    benchmark=getattr(s, "benchmark", None),
                    exc=e,
                )
        except Exception as e:
            print(f"FAIL ({time.time()-t0:.1f}s) — {type(e).__name__}: {e}")
            db.record_error(
                stage="fetch+parse",
                message=str(e),
                vendor_id=getattr(s, "vendor_id", None),
                benchmark=getattr(s, "benchmark", None),
                exc=e,
            )

    # Daily snapshot summarizing diffs
    if results and not args.vendor and not args.benchmark:
        payload = build_snapshot_payload(
            results,
            prior_models=prior_models,
            prior_prices=prior_prices,
            today=date.today(),
        )
        db.write_snapshot(date.today(), payload)
        print(f"\n📸 Snapshot {date.today()}: "
              f"{payload['models_count']} models, "
              f"{len(payload['new_models'])} new, "
              f"{len(payload['price_changes'])} price changes")

    # Vercel revalidation
    hook = os.environ.get("VERCEL_DEPLOY_HOOK_URL")
    if hook and not args.dry_run:
        import httpx
        try:
            httpx.post(hook, timeout=10)
            print("✓ Vercel deploy hook triggered")
        except Exception as e:
            print(f"  [warn] deploy hook failed: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
