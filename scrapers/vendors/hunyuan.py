"""腾讯混元 (Tencent Hunyuan)."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class HunyuanScraper(CatalogVendorScraper):
    vendor_id = "hunyuan"
    pricing_url = "https://cloud.tencent.com/document/product/1729/97731"
    use_playwright = True

    catalog = [
        ModelRecord(vendor_id="hunyuan", slug="hunyuan-turbos", name="Hunyuan TurboS", family="hunyuan",
                    context_window=256_000, modalities=["text"],
                    description="Tencent Hunyuan flagship hybrid model."),
        ModelRecord(vendor_id="hunyuan", slug="hunyuan-large", name="Hunyuan Large", family="hunyuan",
                    context_window=256_000, modalities=["text"], is_open_weight=True,
                    parameters_b=389.0),
        ModelRecord(vendor_id="hunyuan", slug="hunyuan-standard", name="Hunyuan Standard", family="hunyuan",
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="hunyuan", slug="hunyuan-lite", name="Hunyuan Lite", family="hunyuan",
                    context_window=256_000, modalities=["text"]),
        ModelRecord(vendor_id="hunyuan", slug="hunyuan-vision", name="Hunyuan Vision", family="hunyuan",
                    context_window=8_000, modalities=["text","image"]),
        ModelRecord(vendor_id="hunyuan", slug="hunyuan-t1", name="Hunyuan T1", family="hunyuan",
                    context_window=64_000, modalities=["text"],
                    description="Reasoning-tuned Hunyuan."),
    ]

    fallback_prices = {
        "hunyuan-turbos":    (0.11, 0.28, None, "USD"),
        "hunyuan-large":     (0.56, 1.68, None, "USD"),
        "hunyuan-standard":  (0.06, 0.07, None, "USD"),
        "hunyuan-lite":      (0.00, 0.00, None, "USD"),
        "hunyuan-vision":    (1.68, 1.68, None, "USD"),
        "hunyuan-t1":        (0.14, 0.56, None, "USD"),
    }
