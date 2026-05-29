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

    # High signal: a vendor we already track shipped something we don't have a
    # row for. Low signal: a model from a vendor we don't cover at all.
    tracked: dict[str, list[dict]] = {}
    untracked: list[dict] = []
    for r in rows:
        vg = r.get("vendor_guess")
        if vg:
            tracked.setdefault(vg, []).append(r)
        else:
            untracked.append(r)

    lines = [
        "The discovery layer found model names **not in the catalog** — models we "
        "may be failing to track. To adopt one, add it to its vendor catalog in "
        "`scrapers/vendors/<vendor>.py` (with any benchmark aliases); it then "
        "drops off this list automatically. To ignore one, mark its row "
        "`status='dismissed'` in `discovery_candidates`.",
        "",
        f"**{sum(len(v) for v in tracked.values())}** from vendors we track · "
        f"**{len(untracked)}** from other/unknown vendors.",
        "",
    ]

    if tracked:
        lines.append("## ⭐ From vendors we track (likely should add)")
        for vendor in sorted(tracked):
            lines.append(f"### {vendor}")
            for r in sorted(tracked[vendor], key=lambda x: x.get("reported_name", "")):
                occ = r.get("occurrences", 1)
                lines.append(
                    f"- **{r.get('reported_name')}**  "
                    f"(`{r.get('source')}`, seen {occ}×)"
                )
            lines.append("")

    if untracked:
        SAMPLE = 25
        lines.append("## Other / untracked-vendor models")
        lines.append(
            f"_{len(untracked)} names from vendors we don't currently cover "
            f"(showing first {min(SAMPLE, len(untracked))}). Full list in the "
            f"`discovery_candidates` table._"
        )
        for r in sorted(untracked, key=lambda x: x.get("reported_name", ""))[:SAMPLE]:
            lines.append(f"- {r.get('reported_name')}  (`{r.get('source')}`)")
        if len(untracked) > SAMPLE:
            lines.append(f"- … and {len(untracked) - SAMPLE} more")
        lines.append("")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
