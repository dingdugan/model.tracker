"""Tests for auto-promotion (core/promotion.py) and registry runtime extras."""

from __future__ import annotations

from scrapers.core.model_registry import register_extra, reset_cache, resolve, resolve_benchmark
from scrapers.core.promotion import derive_model, is_trusted
from scrapers.core.schema import DiscoveryCandidate


def setup_function(_):
    reset_cache()


def _api(name, vendor="anthropic", display=None):
    return DiscoveryCandidate(
        source=f"vendor-api:{vendor}",
        reported_name=name,
        vendor_guess=vendor,
        raw_context={"display_name": display} if display else {},
    )


def test_only_vendor_api_is_trusted():
    assert is_trusted(_api("claude-opus-4-9"))
    assert not is_trusted(DiscoveryCandidate(source="benchmark:lmsys", reported_name="muse-spark"))


def test_derive_clean_anthropic_model():
    spec = derive_model(_api("claude-opus-4-9", display="Claude Opus 4.9"))
    assert spec["id"] == "anthropic/claude-opus-4-9"
    assert spec["slug"] == "claude-opus-4-9"
    assert spec["name"] == "Claude Opus 4.9"
    assert spec["vendor_id"] == "anthropic"
    assert spec["aliases"] == []  # reported == slug, no extra alias needed


def test_derive_dated_variant_collapses_to_base_with_alias():
    spec = derive_model(_api("claude-opus-4-5-20251101"))
    assert spec["id"] == "anthropic/claude-opus-4-5"
    assert spec["slug"] == "claude-opus-4-5"
    assert "claude-opus-4-5-20251101" in spec["aliases"]


def test_derive_rejects_leaderboard_source():
    c = DiscoveryCandidate(source="benchmark:lmsys", reported_name="muse-spark")
    assert derive_model(c) is None


def test_derive_rejects_unknown_vendor():
    # vendor_guess None and prefix not recognized → can't place it
    c = DiscoveryCandidate(source="vendor-api:mystery", reported_name="zzz-model-1")
    assert derive_model(c) is None


def test_register_extra_makes_model_resolvable():
    assert resolve("claude-opus-4-9") is None  # not in catalog yet
    spec = derive_model(_api("claude-opus-4-9", display="Claude Opus 4.9"))
    register_extra([spec])
    assert resolve("claude-opus-4-9") == "anthropic/claude-opus-4-9"
    # dated/mode variants of the now-registered model also resolve via base form
    assert resolve_benchmark("claude-opus-4-9-thinking") == "anthropic/claude-opus-4-9"


def test_register_extra_never_overrides_catalog():
    # try to hijack a catalog model's name → catalog must win
    register_extra([{"id": "evil/x", "slug": "claude-opus-4-8", "name": "Claude Opus 4.8", "aliases": []}])
    assert resolve("claude-opus-4-8") == "anthropic/claude-opus-4-8"
