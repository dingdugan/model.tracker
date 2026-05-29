"""CI guards for the unified model-identity registry.

These tests make the two failure modes we actually hit impossible to merge:
  1. Drift between the catalog and the (former) hand-maintained name map — a model
     reachable for prices but invisible to benchmarks, or vice versa.
  2. Misattribution — two models answering to the same name, or a short name
     silently grabbing an unrelated longer one.
"""

from __future__ import annotations

import pytest

from scrapers.core.model_registry import (
    AliasCollision,
    all_aliases,
    canon,
    reset_cache,
    resolve,
)
from scrapers.core.registry import discover_vendor_scrapers


def _all_models():
    models = []
    for scraper in discover_vendor_scrapers():
        models.extend(getattr(scraper, "catalog", []) or [])
    return models


@pytest.fixture(autouse=True)
def _fresh_cache():
    reset_cache()
    yield
    reset_cache()


def test_registry_builds_without_collision():
    """Building the alias map must not raise — collisions fail loud here."""
    aliases = all_aliases()
    assert aliases, "registry is empty — catalogs failed to load"


def test_every_model_round_trips():
    """Each model resolves from its own slug, display name, and every alias."""
    failures = []
    for m in _all_models():
        for name in (m.slug, m.name, *getattr(m, "aliases", [])):
            got = resolve(name)
            if got != m.id:
                failures.append(f"{name!r} resolved to {got!r}, expected {m.id!r}")
    assert not failures, "round-trip failures:\n  " + "\n  ".join(failures)


def test_no_two_models_share_a_normalized_alias():
    """No canonical name may point at two different models (ambiguous attribution)."""
    seen: dict[str, str] = {}
    dupes = []
    for m in _all_models():
        for name in (m.slug, m.name, *getattr(m, "aliases", [])):
            key = canon(name)
            if not key:
                continue
            if key in seen and seen[key] != m.id:
                dupes.append(f"{key!r}: {seen[key]} vs {m.id}")
            seen[key] = m.id
    assert not dupes, "alias collisions:\n  " + "\n  ".join(dupes)


def test_matching_is_exact_not_substring():
    """A name that merely *contains* a known alias must NOT resolve.

    This is the ``gpt-5`` → ``gpt-5-codex`` misattribution guard. If any of these
    ever becomes a real model, declare it in a catalog (then drop it from here).
    """
    non_models = [
        "gpt-5-codex",
        "claude-opus-4-8-thinking",
        "gemini-3-pro-ultra-max",
        "grok-4-super-heavy",
    ]
    for name in non_models:
        assert resolve(name) is None, (
            f"{name!r} resolved to {resolve(name)!r} via substring — exact match broken"
        )


def test_collision_detection_actually_fires(monkeypatch):
    """Sanity: two catalog entries with the same name DO raise AliasCollision."""
    from scrapers.core import model_registry, registry

    class _Dummy:
        def __init__(self, mid):
            self.id = mid
            self.slug = mid.split("/")[-1]
            self.name = "Duplicate Name"
            self.aliases = []

    class _FakeScraper:
        catalog = [_Dummy("a/one"), _Dummy("b/two")]

    # _build_alias_map does `from .registry import discover_vendor_scrapers`
    # at call time, so patch it on the source module.
    monkeypatch.setattr(
        registry, "discover_vendor_scrapers", lambda: [_FakeScraper()]
    )
    reset_cache()
    with pytest.raises(AliasCollision):
        model_registry._build_alias_map()


def test_known_benchmark_names_resolve():
    """Anti-regression anchor: real leaderboard display names must resolve.

    These are names benchmark sites actually report. If a refactor breaks one,
    that model's ELO would start getting dropped — catch it here, not in prod.
    """
    expected = {
        "Claude Opus 4.8": "anthropic/claude-opus-4-8",
        "Claude Opus 4.6": "anthropic/claude-opus-4-6",
        "GPT-5": "openai/gpt-5",
        "Gemini 2.5 Pro": "google/gemini-2-5-pro",
        "Grok-4": "xai/grok-4",
        "DeepSeek V3.2": "deepseek/deepseek-v3-2",
        "Command R": "cohere/command-r-08-2024",
        "Qwen3 235B": "qwen/qwen3-235b-a22b",
        "Doubao 1.5 Pro": "doubao/doubao-1-5-pro-256k",
    }
    failures = []
    for name, want in expected.items():
        got = resolve(name)
        if got != want:
            failures.append(f"{name!r} → {got!r}, expected {want!r}")
    assert not failures, "benchmark-name regressions:\n  " + "\n  ".join(failures)
