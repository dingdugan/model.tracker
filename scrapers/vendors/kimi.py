"""Moonshot AI Kimi."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class KimiScraper(CatalogVendorScraper):
    vendor_id = "kimi"
    pricing_url = "https://platform.moonshot.cn/docs/pricing/chat"
    use_playwright = True

    catalog = [
        ModelRecord(vendor_id="kimi", slug="kimi-k2", name="Kimi K2", family="kimi",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=1000.0, description="Moonshot's flagship MoE model."),
        ModelRecord(vendor_id="kimi", slug="moonshot-v1-128k", name="Moonshot v1 128k", family="kimi",
                    context_window=128_000, modalities=["text"]),
        ModelRecord(vendor_id="kimi", slug="moonshot-v1-32k", name="Moonshot v1 32k", family="kimi",
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="kimi", slug="moonshot-v1-8k", name="Moonshot v1 8k", family="kimi",
                    context_window=8_000, modalities=["text"]),
        ModelRecord(vendor_id="kimi", slug="kimi-vl-a3b", name="Kimi VL A3B", family="kimi",
                    context_window=128_000, modalities=["text","image"], is_open_weight=True,
                    parameters_b=16.0),
    ]

    fallback_prices = {
        "kimi-k2":          (0.56, 2.24, None, "USD"),
        "moonshot-v1-128k": (8.40, 8.40, None, "USD"),
        "moonshot-v1-32k":  (3.36, 3.36, None, "USD"),
        "moonshot-v1-8k":   (1.68, 1.68, None, "USD"),
        "kimi-vl-a3b":      (0.28, 0.84, None, "USD"),
    }
