"""Tests for discovery filtering (core/discovery.py) — the logic that decides
which names seen in the wild are genuinely new vs. just known models / dated
snapshots. Pure, no network.
"""

from __future__ import annotations

from scrapers.core.discovery import filter_unknown, is_known
from scrapers.core.model_registry import reset_cache
from scrapers.core.schema import DiscoveryCandidate


def setup_function(_):
    reset_cache()


def test_known_model_is_known():
    assert is_known("Claude Opus 4.8")
    assert is_known("claude-opus-4-8")
    assert is_known("GPT-5")


def test_dated_snapshot_of_known_model_is_known():
    # API ids carry date/version suffixes; these are the SAME model, not new.
    assert is_known("claude-haiku-4-5-20251001")
    assert is_known("gpt-4o-2024-08-06")
    assert is_known("claude-opus-4-8@20260115")
    assert is_known("gpt-5-latest")


def test_genuinely_new_model_is_unknown():
    assert not is_known("claude-opus-4-9")
    assert not is_known("gpt-6")
    assert not is_known("some-random-llm-9000")


def test_filter_unknown_drops_known_keeps_new():
    cands = [
        DiscoveryCandidate(source="vendor-api:anthropic", reported_name="claude-opus-4-8"),
        DiscoveryCandidate(source="vendor-api:anthropic", reported_name="claude-opus-4-9"),
        DiscoveryCandidate(source="vendor-api:anthropic", reported_name="claude-haiku-4-5-20251001"),
    ]
    out = filter_unknown(cands)
    names = [c.reported_name for c in out]
    assert names == ["claude-opus-4-9"]


def test_filter_unknown_dedupes_within_batch():
    cands = [
        DiscoveryCandidate(source="benchmark:lmsys", reported_name="Mystery Model X"),
        DiscoveryCandidate(source="benchmark:lmsys", reported_name="mystery-model-x"),  # same after canon
        DiscoveryCandidate(source="vendor-api:openai", reported_name="Mystery Model X"),  # diff source → kept
    ]
    out = filter_unknown(cands)
    keys = sorted((c.source, c.reported_name.lower()) for c in out)
    assert keys == [
        ("benchmark:lmsys", "mystery model x"),
        ("vendor-api:openai", "mystery model x"),
    ]
