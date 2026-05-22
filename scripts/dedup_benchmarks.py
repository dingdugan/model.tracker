#!/usr/bin/env python3
"""One-off script: remove duplicate benchmark_scores rows.

Keeps the row with the lowest id in each
(model_id, benchmark_name, source, measured_at) group.

Usage:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/dedup_benchmarks.py
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict

from supabase import create_client


def main() -> None:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars.")

    client = create_client(url, key)

    print("Fetching all benchmark_scores rows …")
    res = client.table("benchmark_scores").select("id, model_id, benchmark_name, source, measured_at").execute()
    rows = res.data
    print(f"  total rows: {len(rows)}")

    # Group by (model_id, benchmark_name, source, measured_at)
    groups: dict[tuple, list[int]] = defaultdict(list)
    for row in rows:
        key_tuple = (
            row["model_id"],
            row["benchmark_name"],
            row["source"],
            row["measured_at"],  # may be None
        )
        groups[key_tuple].append(row["id"])

    to_delete: list[int] = []
    for key_tuple, ids in groups.items():
        if len(ids) > 1:
            ids.sort()
            to_delete.extend(ids[1:])  # keep lowest id, delete the rest

    if not to_delete:
        print("No duplicates found — nothing to delete.")
        return

    print(f"  duplicates to delete: {len(to_delete)}")

    # Delete in batches of 100
    batch_size = 100
    deleted = 0
    for i in range(0, len(to_delete), batch_size):
        batch = to_delete[i : i + batch_size]
        client.table("benchmark_scores").delete().in_("id", batch).execute()
        deleted += len(batch)
        print(f"  deleted {deleted}/{len(to_delete)} …")

    print(f"Done. Removed {len(to_delete)} duplicate rows.")

    # Final count
    res2 = client.table("benchmark_scores").select("id", count="exact").execute()
    print(f"Rows remaining: {res2.count}")


if __name__ == "__main__":
    main()
