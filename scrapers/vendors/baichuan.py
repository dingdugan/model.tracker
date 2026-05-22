"""百川智能 (Baichuan)."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class BaichuanScraper(CatalogVendorScraper):
    vendor_id = "baichuan"
    pricing_url = "https://platform.baichuan-ai.com/price"
    use_playwright = True

    catalog = [
        ModelRecord(vendor_id="baichuan", slug="baichuan4-turbo", name="Baichuan4 Turbo", family="baichuan",
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="baichuan", slug="baichuan4-air", name="Baichuan4 Air", family="baichuan",
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="baichuan", slug="baichuan4", name="Baichuan4", family="baichuan",
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="baichuan", slug="baichuan3-turbo", name="Baichuan3 Turbo", family="baichuan",
                    context_window=32_000, modalities=["text"], status="deprecated"),
    ]

    fallback_prices = {
        "baichuan4-turbo": (2.10, 2.10, None, "USD"),
        "baichuan4-air":   (0.14, 0.14, None, "USD"),
        "baichuan4":       (13.0, 13.0, None, "USD"),
        "baichuan3-turbo": (1.68, 1.68, None, "USD"),
    }
