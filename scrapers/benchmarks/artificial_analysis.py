"""Artificial Analysis (artificialanalysis.ai).

They publish quality, speed, price metrics across models. The site is React-rendered;
we use Playwright + LLM extraction.
"""

from __future__ import annotations

from datetime import date

from ..core.base import BenchmarkScraper
from ..core.extractor import clean_text_for_llm, fetch_rendered, llm_extract
from ..core.schema import BenchmarkRecord, DiscoveryCandidate, ScrapeResult
from ._mapping import resolve_model_id


LEADERBOARD_URL = "https://artificialanalysis.ai/leaderboards/models"
SOURCE_LABEL = "artificial-analysis"


# We ask the LLM for a structured leaderboard rather than reuse the generic prompt.
PROMPT = """\
Extract the model leaderboard from this page text.
Return STRICT JSON: {"models": [{"name": "...", "quality": number_or_null,
                                  "output_tps": number_or_null}, ...]}

Quality is a percentage score 0-100 ("Artificial Analysis Intelligence Index").
output_tps is output tokens per second (speed). Use null when missing.
Skip header rows.

Page text:
---
{TEXT}
"""


class ArtificialAnalysisScraper(BenchmarkScraper):
    benchmark = "artificial-analysis"

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(benchmark=self.benchmark)
        today = date.today()

        try:
            html = fetch_rendered(LEADERBOARD_URL, wait_for="table, [role=table]").html
        except Exception as e:
            print(f"  [artificial-analysis] fetch failed: {e}")
            return result

        text = clean_text_for_llm(html, max_chars=60_000)
        if not text:
            return result

        try:
            data = self._call_llm(text)
        except Exception as e:
            print(f"  [artificial-analysis] LLM extraction failed: {e}")
            return result

        unresolved_seen: set[str] = set()
        for entry in data.get("models", []):
            name = entry.get("name")
            if not name:
                continue
            model_id = resolve_model_id(name)
            if not model_id:
                if name not in unresolved_seen:
                    unresolved_seen.add(name)
                    result.unresolved.append(
                        DiscoveryCandidate(
                            source="benchmark:artificial-analysis",
                            reported_name=name,
                            raw_context={},
                        )
                    )
                continue

            quality = entry.get("quality")
            if quality is not None:
                try:
                    result.benchmarks.append(
                        BenchmarkRecord(
                            model_id=model_id,
                            benchmark_name="aa-intelligence",
                            score=float(quality),
                            score_unit="pct",
                            score_max=100.0,
                            source=SOURCE_LABEL,
                            source_url=LEADERBOARD_URL,
                            measured_at=today,
                        )
                    )
                except (TypeError, ValueError):
                    pass

            tps = entry.get("output_tps")
            if tps is not None:
                try:
                    result.benchmarks.append(
                        BenchmarkRecord(
                            model_id=model_id,
                            benchmark_name="aa-output-tps",
                            score=float(tps),
                            score_unit="raw",
                            source=SOURCE_LABEL,
                            source_url=LEADERBOARD_URL,
                            measured_at=today,
                        )
                    )
                except (TypeError, ValueError):
                    pass

        return result

    def _call_llm(self, text: str) -> dict:
        # Reuse the generic LLM client with a custom prompt
        import json
        import os
        import re
        from anthropic import Anthropic

        from ..core.extractor import _repair_truncated_json

        client = Anthropic()
        model = os.environ.get("EXTRACTOR_MODEL", "claude-haiku-4-5")
        resp = client.messages.create(
            model=model,
            max_tokens=16384,
            messages=[{"role": "user", "content": PROMPT.replace("{TEXT}", text)}],
            system=[{"type": "text", "text": "You output STRICT JSON only.",
                     "cache_control": {"type": "ephemeral"}}],
        )
        raw = "".join(b.text for b in resp.content if hasattr(b, "text"))
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        raw = _repair_truncated_json(raw)
        return json.loads(raw)
