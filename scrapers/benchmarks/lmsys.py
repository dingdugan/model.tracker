"""LMSYS / Arena (arena.ai) Chatbot Arena Elo leaderboard.

arena.ai is a Next.js App Router site. The leaderboard data is embedded in the
React Server Components (RSC) payload — fetching with the `RSC: 1` header returns
a text/html stream that contains a large JSON blob with all ranked model entries.

Approach:
  1. GET https://arena.ai/leaderboard  with header  RSC: 1
  2. Locate the ``"leaderboards":[{`` token in the response body.
  3. Use a balanced-bracket extractor to pull the full array (no regex limitations).
  4. Take entries from the text/overall leaderboard (arenaSlug="text").
  5. Map modelDisplayName → canonical model_id via _mapping.resolve_model_id.
  6. Emit one BenchmarkRecord per resolved model; unrecognised models are silently
     dropped (they are fine — we only track catalog-known models).
"""

from __future__ import annotations

import json
from datetime import date

from ..core.base import BenchmarkScraper
from ..core.extractor import fetch_static
from ..core.schema import BenchmarkRecord, ScrapeResult
from ._mapping import resolve_model_id


SOURCE_LABEL = "lmsys"
HOMEPAGE = "https://arena.ai/leaderboard"

# Fetch the RSC payload (text/html) — much smaller than running full JS.
RSC_URL = "https://arena.ai/leaderboard"
RSC_HEADERS = {
    "RSC": "1",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

# (arenaSlug, leaderboardSlug) → benchmark_name stored in DB
LEADERBOARDS: list[tuple[str, str, str]] = [
    ("text",   "overall", "arena-elo"),
    ("code",   "overall", "arena-elo-coding"),   # arena.ai restructured: coding is now a top-level category
    ("vision", "overall", "arena-elo-vision"),
    # math / hard-prompts / instruction-following no longer exist as separate leaderboards on arena.ai
]


class LMSysArenaScraper(BenchmarkScraper):
    benchmark = "lmsys"

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(benchmark=self.benchmark)
        today = date.today()

        try:
            resp = fetch_static(RSC_URL, timeout=30, headers=RSC_HEADERS)
            body = resp.html
        except Exception as e:
            print(f"  [lmsys] fetch failed: {e}")
            return result

        leaderboards = _extract_leaderboards(body)
        if not leaderboards:
            print("  [lmsys] could not extract leaderboards from RSC payload")
            return result

        # Index available leaderboards for O(1) lookup
        lb_index: dict[tuple[str, str], list[dict]] = {}
        for lb in leaderboards:
            key = (lb.get("arenaSlug", ""), lb.get("leaderboardSlug", ""))
            lb_index[key] = lb.get("entries", [])

        available = list(lb_index.keys())
        total = 0

        for arena_slug, lb_slug, bench_name in LEADERBOARDS:
            entries = lb_index.get((arena_slug, lb_slug))
            if entries is None:
                print(f"  [lmsys] {arena_slug}/{lb_slug} not found; available: {available}")
                continue

            seen: set[str] = set()
            count = 0
            for entry in entries:
                name = entry.get("modelDisplayName", "")
                rating = entry.get("rating")
                if not name or rating is None:
                    continue
                model_id = resolve_model_id(name)
                if not model_id or model_id in seen:
                    continue
                seen.add(model_id)
                try:
                    score = float(rating)
                except (TypeError, ValueError):
                    continue
                result.benchmarks.append(
                    BenchmarkRecord(
                        model_id=model_id,
                        benchmark_name=bench_name,
                        score=score,
                        score_unit="elo",
                        source=SOURCE_LABEL,
                        source_url=HOMEPAGE,
                        measured_at=today,
                    )
                )
                count += 1
            total += count
            print(f"  [lmsys] {bench_name}: {count} entries")

        if total == 0:
            print("  [lmsys] warning: 0 entries resolved across all leaderboards")
        return result


# ---------------------------------------------------------------------------
# RSC payload parser
# ---------------------------------------------------------------------------

_MARKER = '"leaderboards":[{"arenaSlug"'


def _extract_leaderboards(body: str) -> list[dict]:
    """
    Locate the ``"leaderboards":[...]`` JSON inside the RSC text stream and
    return the parsed Python list.  Returns [] on any parse failure.
    """
    idx = body.find(_MARKER)
    if idx < 0:
        return []

    # Skip to the '[' character that opens the array.
    arr_start = body.index(":[{", idx) + 1
    arr_text = _extract_json_array(body, arr_start)
    if not arr_text:
        return []

    try:
        return json.loads(arr_text)
    except json.JSONDecodeError as e:
        print(f"  [lmsys] JSON parse error: {e}")
        return []


def _extract_json_array(s: str, start: int) -> str | None:
    """
    Starting at ``s[start]`` (which must be '['), walk forward counting
    brackets to find the matching ']' and return the complete array substring.
    Handles nested objects, arrays, and quoted strings with escapes.
    """
    depth = 0
    in_str = False
    escape = False

    for i in range(start, len(s)):
        c = s[i]
        if escape:
            escape = False
            continue
        if c == "\\" and in_str:
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]

    return None  # unbalanced
