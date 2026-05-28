"""Anthropic."""

from __future__ import annotations

from datetime import date

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class AnthropicScraper(CatalogVendorScraper):
    vendor_id = "anthropic"
    pricing_url = "https://platform.claude.com/docs/en/about-claude/pricing"

    catalog = [
        ModelRecord(vendor_id="anthropic", slug="claude-opus-4-8", name="Claude Opus 4.8", family="claude",
                    context_window=1_000_000, max_output_tokens=128_000, modalities=["text","image"],
                    description="Most capable model in the Claude 4 family."),
        ModelRecord(vendor_id="anthropic", slug="claude-opus-4-7", name="Claude Opus 4.7", family="claude",
                    context_window=1_000_000, max_output_tokens=128_000, modalities=["text","image"]),
        ModelRecord(vendor_id="anthropic", slug="claude-opus-4-6", name="Claude Opus 4.6", family="claude",
                    context_window=200_000, max_output_tokens=128_000, modalities=["text","image"]),
        ModelRecord(vendor_id="anthropic", slug="claude-sonnet-4-6", name="Claude Sonnet 4.6", family="claude",
                    context_window=200_000, modalities=["text","image"],
                    description="Balanced performance and cost."),
        ModelRecord(vendor_id="anthropic", slug="claude-sonnet-4-5", name="Claude Sonnet 4.5", family="claude",
                    context_window=200_000, modalities=["text","image"]),
        ModelRecord(vendor_id="anthropic", slug="claude-haiku-4-5", name="Claude Haiku 4.5", family="claude",
                    context_window=200_000, modalities=["text","image"],
                    description="Fastest and most cost-effective Claude."),
        ModelRecord(vendor_id="anthropic", slug="claude-3-5-sonnet", name="Claude 3.5 Sonnet", family="claude",
                    release_date=date(2024, 6, 20),
                    context_window=200_000, modalities=["text","image"], status="deprecated"),
    ]

    # (input, output, cache-hit, currency) per MTok — verified against
    # platform.claude.com/docs/en/about-claude/pricing on 2026-05-28.
    fallback_prices = {
        "claude-opus-4-8":    ( 5.00, 25.00, 0.50, "USD"),
        "claude-opus-4-7":    ( 5.00, 25.00, 0.50, "USD"),
        "claude-opus-4-6":    ( 5.00, 25.00, 0.50, "USD"),
        "claude-sonnet-4-6":  ( 3.00, 15.00, 0.30, "USD"),
        "claude-sonnet-4-5":  ( 3.00, 15.00, 0.30, "USD"),
        "claude-haiku-4-5":   ( 1.00,  5.00, 0.10, "USD"),
        "claude-3-5-sonnet":  ( 3.00, 15.00, 0.30, "USD"),
    }
