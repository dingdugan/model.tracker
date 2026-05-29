"""Alibaba Qwen (通义千问)."""

from __future__ import annotations

from ..core.schema import ModelRecord
from ._catalog_scraper import CatalogVendorScraper


class QwenScraper(CatalogVendorScraper):
    vendor_id = "qwen"
    pricing_url = "https://help.aliyun.com/zh/model-studio/models"
    use_playwright = True  # aliyun docs are JS-rendered

    catalog = [
        ModelRecord(vendor_id="qwen", slug="qwen3-max", name="Qwen3 Max", family="qwen",
                    context_window=262_144, modalities=["text"],
                    description="Alibaba's flagship Qwen3 model."),
        ModelRecord(vendor_id="qwen", slug="qwen3-235b-a22b", name="Qwen3 235B A22B", family="qwen",
                    aliases=["Qwen3 235B"],
                    context_window=131_072, modalities=["text"], is_open_weight=True,
                    license="apache-2.0",
                    parameters_b=235.0),
        ModelRecord(vendor_id="qwen", slug="qwen3-72b", name="Qwen3 72B", family="qwen",
                    context_window=131_072, modalities=["text"], is_open_weight=True,
                    license="apache-2.0",
                    parameters_b=72.0),
        ModelRecord(vendor_id="qwen", slug="qwen3-32b", name="Qwen3 32B", family="qwen",
                    context_window=131_072, modalities=["text"], is_open_weight=True,
                    license="apache-2.0",
                    parameters_b=32.0),
        ModelRecord(vendor_id="qwen", slug="qwen3-coder", name="Qwen3 Coder", family="qwen",
                    context_window=131_072, modalities=["text","code"], is_open_weight=True,
                    license="apache-2.0"),
        ModelRecord(vendor_id="qwen", slug="qwen2-5-vl-72b", name="Qwen2.5 VL 72B", family="qwen",
                    context_window=131_072, modalities=["text","image"], is_open_weight=True,
                    license="apache-2.0",
                    parameters_b=72.0),
        ModelRecord(vendor_id="qwen", slug="qwen2-5-omni-7b", name="Qwen2.5 Omni 7B", family="qwen",
                    context_window=32_768, modalities=["text","image","audio","video"], is_open_weight=True,
                    license="apache-2.0",
                    parameters_b=7.0),
    ]

    # CNY per Mtok (will be converted to USD on insert via fallback path).
    # We populate them directly in USD to keep semantics simple.
    fallback_prices = {
        "qwen3-max":        (1.40, 5.60,  None, "USD"),
        "qwen3-235b-a22b":  (0.28, 1.12,  None, "USD"),
        "qwen3-72b":        (0.56, 1.68,  None, "USD"),
        "qwen3-32b":        (0.28, 0.84,  None, "USD"),
        "qwen3-coder":      (0.56, 1.68,  None, "USD"),
        "qwen2-5-vl-72b":   (0.56, 1.68,  None, "USD"),
        "qwen2-5-omni-7b":  (0.07, 0.14,  None, "USD"),
    }
