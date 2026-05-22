"""OpenAI."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class OpenAIScraper(CatalogVendorScraper):
    vendor_id = "openai"
    pricing_url = "https://openai.com/api/pricing"

    catalog = [
        ModelRecord(vendor_id="openai", slug="gpt-5", name="GPT-5", family="gpt",
                    context_window=400_000, modalities=["text","image"],
                    description="Flagship multimodal reasoning model."),
        ModelRecord(vendor_id="openai", slug="gpt-5-mini", name="GPT-5 mini", family="gpt",
                    context_window=400_000, modalities=["text","image"]),
        ModelRecord(vendor_id="openai", slug="gpt-5-nano", name="GPT-5 nano", family="gpt",
                    context_window=400_000, modalities=["text","image"]),
        ModelRecord(vendor_id="openai", slug="gpt-4.1", name="GPT-4.1", family="gpt",
                    context_window=1_047_576, modalities=["text","image"]),
        ModelRecord(vendor_id="openai", slug="gpt-4.1-mini", name="GPT-4.1 mini", family="gpt",
                    context_window=1_047_576, modalities=["text","image"]),
        ModelRecord(vendor_id="openai", slug="gpt-4o", name="GPT-4o", family="gpt",
                    context_window=128_000, modalities=["text","image","audio"]),
        ModelRecord(vendor_id="openai", slug="gpt-4o-mini", name="GPT-4o mini", family="gpt",
                    context_window=128_000, modalities=["text","image"]),
        ModelRecord(vendor_id="openai", slug="o3", name="o3", family="o",
                    context_window=200_000, modalities=["text","image"],
                    description="Advanced reasoning model."),
        ModelRecord(vendor_id="openai", slug="o4-mini", name="o4-mini", family="o",
                    context_window=200_000, modalities=["text","image"]),
    ]

    fallback_prices = {
        # slug:        (input, output, cached_input, currency)
        "gpt-5":       (1.25, 10.00, 0.125, "USD"),
        "gpt-5-mini":  (0.25,  2.00, 0.025, "USD"),
        "gpt-5-nano":  (0.05,  0.40, 0.005, "USD"),
        "gpt-4.1":     (2.00,  8.00, 0.50,  "USD"),
        "gpt-4.1-mini":(0.40,  1.60, 0.10,  "USD"),
        "gpt-4o":      (2.50, 10.00, 1.25,  "USD"),
        "gpt-4o-mini": (0.15,  0.60, 0.075, "USD"),
        "o3":          (2.00,  8.00, 0.50,  "USD"),
        "o4-mini":     (1.10,  4.40, 0.275, "USD"),
    }
