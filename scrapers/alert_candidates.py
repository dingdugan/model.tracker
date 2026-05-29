"""Print open discovery candidates as Markdown (for the daily GitHub-issue alert).

Run after the scrape. Emits nothing when there are no candidates awaiting review,
so the workflow only opens/updates an issue when there's something to act on.

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
        print(f"<!-- alert_candidates: cannot connect: {e} -->", file=sys.stderr)
        return 0

    rows = db.open_candidates()
    if not rows:
        return 0  # silence = nothing to review

    by_source: dict[str, list[dict]] = {}
    for r in rows:
        by_source.setdefault(r.get("source", "?"), []).append(r)

    lines = [
        "The discovery layer found model names that are **not in the catalog**. "
        "Each is a model we may be failing to track. To adopt one, add it to the "
        "relevant vendor catalog in `scrapers/vendors/<vendor>.py` (with any "
        "benchmark aliases); it then drops off this list automatically.",
        "",
    ]
    for source in sorted(by_source):
        lines.append(f"### `{source}`")
        for r in sorted(by_source[source], key=lambda x: x.get("reported_name", "")):
            vg = r.get("vendor_guess")
            occ = r.get("occurrences", 1)
            suffix = f" — vendor guess: `{vg}`" if vg else ""
            lines.append(f"- **{r.get('reported_name')}**{suffix}  (seen {occ}×)")
        lines.append("")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
