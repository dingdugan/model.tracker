"""xAI (Grok)."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class XAIScraper(CatalogVendorScraper):
    vendor_id = "xai"
    pricing_url = "https://docs.x.ai/docs/models"

    catalog = [
        ModelRecord(vendor_id="xai", slug="grok-4", name="Grok 4", family="grok",
                    context_window=256_000, modalities=["text","image"],
                    description="Latest Grok reasoning model."),
        ModelRecord(vendor_id="xai", slug="grok-4-fast", name="Grok 4 Fast", family="grok",
                    context_window=2_000_000, modalities=["text","image"]),
        ModelRecord(vendor_id="xai", slug="grok-4-heavy", name="Grok 4 Heavy", family="grok",
                    context_window=256_000, modalities=["text","image"]),
        ModelRecord(vendor_id="xai", slug="grok-3", name="Grok 3", family="grok",
                    context_window=131_072, modalities=["text","image"], status="deprecated"),
        ModelRecord(vendor_id="xai", slug="grok-3-mini", name="Grok 3 mini", family="grok",
                    context_window=131_072, modalities=["text"], status="deprecated"),
    ]

    fallback_prices = {
        "grok-4":      (3.00, 15.00, 0.75, "USD"),
        "grok-4-fast": (0.20,  0.50, 0.05, "USD"),
        "grok-4-heavy":(3.00, 15.00, 0.75, "USD"),
        "grok-3":      (3.00, 15.00, None, "USD"),
        "grok-3-mini": (0.30,  0.50, None, "USD"),
    }
