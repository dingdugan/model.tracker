"""智谱 GLM (Zhipu)."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class GLMScraper(CatalogVendorScraper):
    vendor_id = "glm"
    pricing_url = "https://bigmodel.cn/pricing"
    use_playwright = True

    catalog = [
        ModelRecord(vendor_id="glm", slug="glm-4-6", name="GLM-4.6", family="glm",
                    context_window=200_000, modalities=["text"],
                    description="Zhipu flagship."),
        ModelRecord(vendor_id="glm", slug="glm-4-5", name="GLM-4.5", family="glm",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    license="glm-4",
                    parameters_b=355.0),
        ModelRecord(vendor_id="glm", slug="glm-4-5-air", name="GLM-4.5-Air", family="glm",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    license="glm-4",
                    parameters_b=106.0),
        ModelRecord(vendor_id="glm", slug="glm-4v-plus", name="GLM-4V-Plus", family="glm",
                    context_window=8_192, modalities=["text","image","video"]),
        ModelRecord(vendor_id="glm", slug="glm-zero-preview", name="GLM-Zero-Preview", family="glm",
                    context_window=16_384, modalities=["text"], status="preview"),
    ]

    fallback_prices = {
        "glm-4-6":           (0.42, 1.68, None, "USD"),
        "glm-4-5":           (0.14, 0.28, None, "USD"),
        "glm-4-5-air":       (0.07, 0.14, None, "USD"),
        "glm-4v-plus":       (0.14, 0.14, None, "USD"),
        "glm-zero-preview":  (0.14, 0.14, None, "USD"),
    }
