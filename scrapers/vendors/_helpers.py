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
from ..core.schema import ModelRecord, PriceRecord, ScrapeResult


def llm_fallback_into_result(
    *,
    result: ScrapeResult,
    html: str,
    source_url: str,
    vendor_id: str,
) -> None:
    """Run LLM extraction on cleaned HTML and merge results into `result`."""
    text = clean_text_for_llm(html)
    if not text:
        return
    data = llm_extract(text)
    today = date.today()
    existing_slugs = {m.slug for m in result.models}

    for m in data.get("models", []):
        slug = (m.get("slug") or m.get("name") or "").strip().lower().replace(" ", "-")
        if not slug or slug in existing_slugs:
            continue
        existing_slugs.add(slug)
        record = ModelRecord(
            vendor_id=vendor_id,
            slug=slug,
            name=m.get("name") or slug,
            family=m.get("family"),
            release_date=_parse_iso_date(m.get("release_date")),
            context_window=m.get("context_window"),
            max_output_tokens=m.get("max_output_tokens"),
            modalities=m.get("modalities") or ["text"],
            is_open_weight=bool(m.get("is_open_weight", False)),
            parameters_b=m.get("parameters_b"),
            status=m.get("status") or "active",
            description=m.get("description"),
        )
        result.models.append(record)

    slug_to_id = {m.slug: m.id for m in result.models}
    for p in data.get("prices", []):
        slug = (p.get("model_slug") or "").strip().lower().replace(" ", "-")
        model_id = slug_to_id.get(slug)
        if not model_id:
            continue
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
