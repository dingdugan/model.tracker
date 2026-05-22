"""DeepSeek."""

from __future__ import annotations

from datetime import date

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class DeepSeekScraper(CatalogVendorScraper):
    vendor_id = "deepseek"
    pricing_url = "https://api-docs.deepseek.com/quick_start/pricing"

    catalog = [
        ModelRecord(vendor_id="deepseek", slug="deepseek-v3-2", name="DeepSeek V3.2", family="deepseek",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=671.0, description="MoE flagship; ~37B active."),
        ModelRecord(vendor_id="deepseek", slug="deepseek-v3-1", name="DeepSeek V3.1", family="deepseek",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=671.0),
        ModelRecord(vendor_id="deepseek", slug="deepseek-r1", name="DeepSeek R1", family="deepseek",
                    release_date=date(2025, 1, 20),
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=671.0, description="Open reasoning model."),
        ModelRecord(vendor_id="deepseek", slug="deepseek-v2-5", name="DeepSeek V2.5", family="deepseek",
                    release_date=date(2024, 9, 5),
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=236.0, status="deprecated"),
    ]

    fallback_prices = {
        "deepseek-v3-2": (0.27, 1.10, 0.07,  "USD"),
        "deepseek-v3-1": (0.27, 1.10, 0.07,  "USD"),
        "deepseek-r1":   (0.55, 2.19, 0.14,  "USD"),
        "deepseek-v2-5": (0.14, 0.28, 0.014, "USD"),
    }
