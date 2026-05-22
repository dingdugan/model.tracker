"""Cohere."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class CohereScraper(CatalogVendorScraper):
    vendor_id = "cohere"
    pricing_url = "https://cohere.com/pricing"

    catalog = [
        ModelRecord(vendor_id="cohere", slug="command-a-03-2025", name="Command A", family="command",
                    context_window=256_000, modalities=["text"], parameters_b=111.0,
                    description="Cohere's flagship enterprise model."),
        ModelRecord(vendor_id="cohere", slug="command-r-plus", name="Command R+", family="command",
                    context_window=128_000, modalities=["text"], parameters_b=104.0),
        ModelRecord(vendor_id="cohere", slug="command-r-08-2024", name="Command R 08-2024", family="command",
                    context_window=128_000, modalities=["text"], parameters_b=35.0),
        ModelRecord(vendor_id="cohere", slug="command-r7b", name="Command R7B", family="command",
                    context_window=128_000, modalities=["text"], parameters_b=7.0),
        ModelRecord(vendor_id="cohere", slug="aya-expanse-32b", name="Aya Expanse 32B", family="aya",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=32.0),
    ]

    fallback_prices = {
        "command-a-03-2025":   (2.50, 10.00, None, "USD"),
        "command-r-plus":      (2.50, 10.00, None, "USD"),
        "command-r-08-2024":   (0.15,  0.60, None, "USD"),
        "command-r7b":         (0.04,  0.15, None, "USD"),
        "aya-expanse-32b":     (None, None,  None, "USD"),
    }
