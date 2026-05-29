"""Tests for discovery filtering (core/discovery.py) — the logic that decides
which names seen in the wild are genuinely new vs. just known models / dated
snapshots. Pure, no network.
"""

from __future__ import annotations

from scrapers.core.discovery import filter_unknown, infer_vendor, is_known
from scrapers.core.model_registry import base_form, reset_cache, resolve, resolve_benchmark
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


def test_mode_variants_of_tracked_models_resolve():
    """Leaderboard mode/snapshot variants attach to the base model we track.

    This is the regression Phase B surfaced: exact match alone dropped these.
    """
    cases = {
        "claude-opus-4-7-thinking": "anthropic/claude-opus-4-7",
        "claude-opus-4-6-thinking": "anthropic/claude-opus-4-6",
        "deepseek-v3.1-thinking": "deepseek/deepseek-v3-1",
        "deepseek-v3.2-thinking": "deepseek/deepseek-v3-2",
        "gemma-3-27b-it": "google/gemma-3-27b",
        "claude-sonnet-4-5-20250929-thinking-32k": "anthropic/claude-sonnet-4-5",
        "gemini-2.5-flash-lite-preview-09-2025-no-thinking": "google/gemini-2-5-flash-lite",
    }
    failures = []
    for name, want in cases.items():
        got = resolve_benchmark(name)
        if got != want:
            failures.append(f"{name!r} → {got!r}, expected {want!r}")
    assert not failures, "mode-variant resolution:\n  " + "\n  ".join(failures)


def test_base_form_never_strips_identity_tokens():
    """Size/version tokens must NOT be stripped — that would cross models.

    resolve_benchmark must keep distinct models distinct.
    """
    # 'mini'/'nano'/'lite' are identity-bearing — must not collapse to the base.
    assert resolve_benchmark("gpt-4o-mini") == "openai/gpt-4o-mini"
    assert resolve_benchmark("gpt-5-nano") == "openai/gpt-5-nano"
    # 'gpt-4o-search-preview' strips '-preview' → 'gpt-4o-search' (NOT a model) →
    # must NOT misattribute to gpt-4o.
    assert resolve_benchmark("gpt-4o-search-preview") is None
    # strict resolve still rejects these (loose logic lives in resolve_benchmark)
    assert resolve("claude-opus-4-7-thinking") is None


def test_untracked_models_stay_unknown_after_base_strip():
    # dated/mode variants of models we DON'T track must remain unknown
    assert not is_known("claude-opus-4-5-20251101")  # we track 4.6/4.7/4.8, not 4.5
    assert not is_known("gpt-4.5-preview-2025-02-27")
    assert not is_known("amazon-nova-pro-v1.0")


def test_infer_vendor():
    assert infer_vendor("claude-opus-4-5-20251101") == "anthropic"
    assert infer_vendor("gemini-3-flash") == "google"
    assert infer_vendor("deepseek-v4-pro") == "deepseek"
    assert infer_vendor("glm-5") == "glm"
    assert infer_vendor("amazon-nova-pro-v1.0") is None  # not a tracked vendor
    # prefix match is anchored at the START — 'llama' mid-string doesn't count
    assert infer_vendor("cogvlm2-llama3-chat-19b") is None


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
