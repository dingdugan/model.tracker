"""Shared helpers for vendor scrapers."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..core.extractor import (
    clean_text_for_llm,
    fetch_static,
    llm_extract,
    normalize_to_usd_per_mtok,
    parse_price_string,
    soup,
)
from ..core.model_registry import canon as _canon
from ..core.schema import ModelRecord, PriceRecord, ScrapeResult


def llm_fallback_into_result(
    *,
    result: ScrapeResult,
    html: str,
    source_url: str,
    vendor_id: str,
) -> None:
    """Run LLM extraction on cleaned HTML and merge results into `result`.

    SAFETY POLICY (after 2026-05-21 LLM-hallucination incident):
    LLM output is used ONLY to refresh prices on models that are already
    declared in the scraper's static catalog. New model rows are NEVER
    created from LLM output — they must be added to the vendor's catalog
    list by hand. This prevents two failure modes we hit in production:
      1. Cross-vendor contamination (vendor pages list third-party models
         hosted on their platform; LLM attributes them to the wrong vendor).
      2. Hallucinated future-dated model names (claude-opus-47, qwen3.7-max,
         mistral-large-3, etc. that don't exist yet).
    """
    text = clean_text_for_llm(html)
    if not text:
        return
    try:
        data = llm_extract(text)
    except Exception:
        return  # No Anthropic key, or LLM returned non-JSON — fail closed.

    today = date.today()

    # Build a lookup from canonicalized name/slug → canonical model_id.
    # Include both the slug and the display name so we tolerate either in LLM output.
    lookup: dict[str, str] = {}
    for m in result.models:
        if m.vendor_id != vendor_id:
            continue
        for raw in (m.slug, m.name, *getattr(m, "aliases", [])):
            key = _canon(raw)
            if key:
                lookup[key] = m.id

    if not lookup:
        return  # Empty catalog — nothing safe to map LLM output to.

    seen_model_ids: set[str] = set()

    for p in data.get("prices", []):
        raw = (p.get("model_slug") or p.get("model_name") or "").strip()
        if not raw:
            continue
        model_id = lookup.get(_canon(raw))
        if not model_id:
            continue  # LLM mentioned a model not in our catalog — IGNORE.
        if model_id in seen_model_ids:
            continue  # Skip duplicate price rows in same payload
        seen_model_ids.add(model_id)

        currency = (p.get("currency") or "USD").upper()
        result.prices.append(
            PriceRecord(
                model_id=model_id,
                input_per_mtok=_num_to_usd(p.get("input_per_mtok"), currency),
                output_per_mtok=_num_to_usd(p.get("output_per_mtok"), currency),
                cached_input_per_mtok=_num_to_usd(p.get("cached_input_per_mtok"), currency),
                currency="USD",
                effective_date=today,
                source_url=source_url,
            )
        )


def _parse_iso_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _num_to_usd(v, currency: str):
    if v is None:
        return None
    try:
        return normalize_to_usd_per_mtok(float(v), currency)
    except (TypeError, ValueError):
        return None


__all__ = [
    "fetch_static",
    "soup",
    "parse_price_string",
    "llm_fallback_into_result",
    "ModelRecord",
    "PriceRecord",
    "ScrapeResult",
]
