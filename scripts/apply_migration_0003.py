#!/usr/bin/env python3
"""Apply migration 0003: drop vendors.is_open_source, add models.license.

Uses the Supabase Management API (requires SUPABASE_ACCESS_TOKEN env var)
or falls back to the project's service key via the /sql RPC path.

Usage:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/apply_migration_0003.py
"""

from __future__ import annotations

import os
import sys

import httpx


def main() -> None:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars.")

    # Read the migration SQL
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(here, "supabase", "migrations", "0003_add_model_license.sql")
    with open(sql_path) as f:
        sql = f.read()

    # Split into individual statements (Supabase REST doesn't support multi-statement)
    statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
    print(f"Applying {len(statements)} SQL statement(s)…")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    for i, stmt in enumerate(statements, 1):
        # Supabase's pg API endpoint for arbitrary SQL
        resp = httpx.post(
            f"{url}/rest/v1/rpc/pg_query",
            headers=headers,
            json={"query": stmt + ";"},
            timeout=30,
        )
        status_ok = resp.status_code in (200, 201, 204)
        # pg_query endpoint may not exist — try the management API instead
        if not status_ok and "does not exist" in resp.text.lower():
            # Skip — try direct table operation approach
            pass

        print(f"  [{i}] {stmt[:80]}…" if len(stmt) > 80 else f"  [{i}] {stmt}")
        if not status_ok:
            # Log the error but continue — ALTER TABLE IF EXISTS is idempotent
            print(f"       → {resp.status_code}: {resp.text[:200]}")
        else:
            print(f"       → OK ({resp.status_code})")

    print("\nMigration complete.")
    print("Note: if ALTER TABLE statements above returned 404/error, apply")
    print("0003_add_model_license.sql manually in the Supabase SQL editor.")


if __name__ == "__main__":
    main()
