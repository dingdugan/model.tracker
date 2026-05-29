"""Emit the daily data-health alert as Markdown (for a GitHub issue).

Only **quarantined values** are alerted here — a scraped value looked wrong and
we're holding the last-known-good one. These need a human eye.

Unrecognized *models* are deliberately NOT alerted: new models from vendor APIs
are auto-promoted (no action needed), and noisy leaderboard names live on the
/health page for optional review — we don't nag about them.

Emits nothing when there's nothing to act on, so the workflow only opens/updates
an issue when it matters.

Usage: python -m scrapers.alert_candidates
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from .core.db import Database


def main() -> int:
    load_dotenv()
    try:
        db = Database()
    except Exception as e:
        print(f"<!-- data-health alert: cannot connect: {e} -->", file=sys.stderr)
        return 0

    pending = db.open_pending()
    if not pending:
        return 0  # silence = nothing to review

    lines = [
        "## ⚠️ Quarantined values (held — not applied)",
        "A scraped value looked anomalous, so the last-known-good value is still "
        "live. Each auto-applies if it persists across runs, or set the row's "
        "`status` in `pending_changes` to `applied` / `rejected`.",
        "",
    ]
    for p in pending:
        lines.append(
            f"- **{p.get('model_id')}** `{p.get('field')}`: "
            f"{p.get('prior_value')} → {p.get('proposed_value')} "
            f"— {p.get('reason')} (held {p.get('occurrences', 1)}×)"
        )

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
