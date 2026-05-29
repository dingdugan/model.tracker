"""字节豆包 (ByteDance Doubao / Volcengine)."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class DoubaoScraper(CatalogVendorScraper):
    vendor_id = "doubao"
    pricing_url = "https://www.volcengine.com/docs/82379/1099320"
    use_playwright = True

    catalog = [
        ModelRecord(vendor_id="doubao", slug="doubao-1-5-pro-256k", name="Doubao 1.5 Pro 256k", family="doubao",
                    aliases=["Doubao 1.5 Pro"],  # unqualified name on leaderboards → the 256k variant
                    context_window=256_000, modalities=["text"]),
        ModelRecord(vendor_id="doubao", slug="doubao-1-5-pro-32k", name="Doubao 1.5 Pro 32k", family="doubao",
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="doubao", slug="doubao-1-5-lite-32k", name="Doubao 1.5 Lite 32k", family="doubao",
                    aliases=["Doubao 1.5 Lite"],
                    context_window=32_000, modalities=["text"]),
        ModelRecord(vendor_id="doubao", slug="doubao-1-5-thinking-pro", name="Doubao 1.5 Thinking Pro",
                    family="doubao", context_window=128_000, modalities=["text"],
                    description="Reasoning-tuned Doubao."),
        ModelRecord(vendor_id="doubao", slug="doubao-1-5-vision-pro", name="Doubao 1.5 Vision Pro",
                    family="doubao", context_window=32_000, modalities=["text","image"]),
        ModelRecord(vendor_id="doubao", slug="doubao-seed-1-6", name="Doubao Seed 1.6", family="doubao",
                    context_window=256_000, modalities=["text","image"]),
    ]

    fallback_prices = {
        "doubao-1-5-pro-256k":     (0.07, 0.13, None, "USD"),
        "doubao-1-5-pro-32k":      (0.11, 0.28, None, "USD"),
        "doubao-1-5-lite-32k":     (0.04, 0.08, None, "USD"),
        "doubao-1-5-thinking-pro": (0.11, 0.28, None, "USD"),
        "doubao-1-5-vision-pro":   (0.11, 0.28, None, "USD"),
        "doubao-seed-1-6":         (0.14, 0.42, None, "USD"),
    }
