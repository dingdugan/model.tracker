"""Google (Gemini)."""

from __future__ import annotations

from datetime import date

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class GoogleScraper(CatalogVendorScraper):
    vendor_id = "google"
    pricing_url = "https://ai.google.dev/gemini-api/docs/pricing"

    catalog = [
        ModelRecord(vendor_id="google", slug="gemini-3-pro", name="Gemini 3 Pro", family="gemini",
                    context_window=2_000_000, modalities=["text","image","audio","video"],
                    description="Latest flagship Gemini model."),
        ModelRecord(vendor_id="google", slug="gemini-2-5-pro", name="Gemini 2.5 Pro", family="gemini",
                    context_window=2_000_000, modalities=["text","image","audio","video"]),
        ModelRecord(vendor_id="google", slug="gemini-2-5-flash", name="Gemini 2.5 Flash", family="gemini",
                    context_window=1_000_000, modalities=["text","image","audio","video"]),
        ModelRecord(vendor_id="google", slug="gemini-2-5-flash-lite", name="Gemini 2.5 Flash-Lite", family="gemini",
                    context_window=1_000_000, modalities=["text","image"]),
        ModelRecord(vendor_id="google", slug="gemini-2-0-flash", name="Gemini 2.0 Flash", family="gemini",
                    release_date=date(2024, 12, 11),
                    context_window=1_000_000, modalities=["text","image","audio","video"]),
        ModelRecord(vendor_id="google", slug="gemma-3-27b", name="Gemma 3 27B", family="gemma",
                    context_window=128_000, modalities=["text","image"], is_open_weight=True,
                    parameters_b=27.0),
    ]

    fallback_prices = {
        "gemini-3-pro":          (1.25,  10.00, None,  "USD"),
        "gemini-2-5-pro":        (1.25,  10.00, 0.31,  "USD"),
        "gemini-2-5-flash":      (0.30,   2.50, 0.075, "USD"),
        "gemini-2-5-flash-lite": (0.10,   0.40, 0.025, "USD"),
        "gemini-2-0-flash":      (0.10,   0.40, 0.025, "USD"),
        "gemma-3-27b":           (None,   None, None,  "USD"),
    }
