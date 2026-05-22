"""Meta (Llama). Open-weight, no first-party pricing."""

from __future__ import annotations

from datetime import date

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class MetaScraper(CatalogVendorScraper):
    vendor_id = "meta"
    pricing_url = None  # open-weight, no first-party API

    catalog = [
        ModelRecord(vendor_id="meta", slug="llama-4-behemoth", name="Llama 4 Behemoth", family="llama",
                    context_window=10_000_000, modalities=["text","image"], is_open_weight=True,
                    parameters_b=2000.0, status="preview",
                    description="Largest Llama model, mixture-of-experts."),
        ModelRecord(vendor_id="meta", slug="llama-4-maverick", name="Llama 4 Maverick", family="llama",
                    context_window=1_000_000, modalities=["text","image"], is_open_weight=True,
                    parameters_b=400.0),
        ModelRecord(vendor_id="meta", slug="llama-4-scout", name="Llama 4 Scout", family="llama",
                    context_window=10_000_000, modalities=["text","image"], is_open_weight=True,
                    parameters_b=109.0),
        ModelRecord(vendor_id="meta", slug="llama-3-3-70b", name="Llama 3.3 70B", family="llama",
                    release_date=date(2024, 12, 6),
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=70.0),
        ModelRecord(vendor_id="meta", slug="llama-3-1-405b", name="Llama 3.1 405B", family="llama",
                    release_date=date(2024, 7, 23),
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=405.0),
    ]

    fallback_prices = {}  # open-weight: no first-party price
