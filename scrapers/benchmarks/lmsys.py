"""LMSYS Chatbot Arena Elo leaderboard.

The HuggingFace Space publishes a snapshot CSV/JSON of the leaderboard.
We try a couple of known endpoints, then fall back to scraping the rendered page.
"""

from __future__ import annotations

import csv
import io
from datetime import date

from ..core.base import BenchmarkScraper
from ..core.extractor import fetch_static
from ..core.schema import BenchmarkRecord, ScrapeResult
from ._mapping import resolve_model_id


# Known mirrors that publish the Arena leaderboard as plain CSV.
CSV_CANDIDATES = [
    "https://storage.googleapis.com/arena-elo/elo_results.csv",
    "https://raw.githubusercontent.com/lm-sys/FastChat/main/fastchat/serve/monitor/leaderboard.csv",
]

SOURCE_LABEL = "lmsys"
HOMEPAGE = "https://lmarena.ai/leaderboard"


class LMSysArenaScraper(BenchmarkScraper):
    benchmark = "lmsys"

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(benchmark=self.benchmark)
        today = date.today()

        rows = self._fetch_rows()
        for r in rows:
            name = r.get("model") or r.get("Model") or r.get("name")
            score_raw = r.get("rating") or r.get("arena_score") or r.get("elo") or r.get("Arena Elo")
            if not name or score_raw is None:
                continue
            model_id = resolve_model_id(name)
            if not model_id:
                continue
            try:
                score = float(str(score_raw).replace(",", ""))
            except ValueError:
                continue
            result.benchmarks.append(
                BenchmarkRecord(
                    model_id=model_id,
                    benchmark_name="arena-elo",
                    score=score,
                    score_unit="elo",
                    source=SOURCE_LABEL,
                    source_url=HOMEPAGE,
                    measured_at=today,
                )
            )
        return result

    def _fetch_rows(self) -> list[dict]:
        last_error: Exception | None = None
        for url in CSV_CANDIDATES:
            try:
                csv_text = fetch_static(url, timeout=20).html
                reader = csv.DictReader(io.StringIO(csv_text))
                rows = list(reader)
                if rows:
                    return rows
            except Exception as e:
                last_error = e
                continue
        # Final fallback — empty list; differ won't complain.
        if last_error:
            print(f"  [lmsys] all CSV mirrors failed: {last_error}")
        return []
