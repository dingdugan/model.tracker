"""Mistral AI."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class MistralScraper(CatalogVendorScraper):
    vendor_id = "mistral"
    pricing_url = "https://mistral.ai/products/la-plateforme"

    catalog = [
        ModelRecord(vendor_id="mistral", slug="mistral-large-2", name="Mistral Large 2", family="mistral",
                    context_window=128_000, modalities=["text"], parameters_b=123.0),
        ModelRecord(vendor_id="mistral", slug="mistral-medium-3", name="Mistral Medium 3", family="mistral",
                    context_window=128_000, modalities=["text","image"]),
        ModelRecord(vendor_id="mistral", slug="mistral-small-3-2", name="Mistral Small 3.2", family="mistral",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=24.0),
        ModelRecord(vendor_id="mistral", slug="codestral-2", name="Codestral 2", family="mistral",
                    context_window=256_000, modalities=["text","code"]),
        ModelRecord(vendor_id="mistral", slug="pixtral-large", name="Pixtral Large", family="mistral",
                    context_window=128_000, modalities=["text","image"], parameters_b=124.0),
        ModelRecord(vendor_id="mistral", slug="ministral-8b", name="Ministral 8B", family="mistral",
                    context_window=128_000, modalities=["text"], is_open_weight=True,
                    parameters_b=8.0),
    ]

    fallback_prices = {
        "mistral-large-2":   (2.00, 6.00, None, "USD"),
        "mistral-medium-3":  (0.40, 2.00, None, "USD"),
        "mistral-small-3-2": (0.10, 0.30, None, "USD"),
        "codestral-2":       (0.30, 0.90, None, "USD"),
        "pixtral-large":     (2.00, 6.00, None, "USD"),
        "ministral-8b":      (0.10, 0.10, None, "USD"),
    }
