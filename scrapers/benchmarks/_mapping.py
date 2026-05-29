"""Maps benchmark-reported model names → our canonical model_id.

This used to be a hand-maintained substring-match dict that lived separately from
the vendor catalogs — which meant adding a model required editing two places, and
forgetting one silently dropped that model's benchmark scores (we hit exactly
that with Opus 4.8).

It now delegates to the single source of truth: ``core.model_registry``, which
derives every name → id mapping from the vendor catalogs (slug + display name +
each model's declared ``aliases``). Matching is normalized-exact, never
substring, so a short name can no longer grab an unrelated longer one
(``gpt-5`` no longer matches ``gpt-5-codex``).

To make a benchmark name resolve, add it to the target model's ``aliases`` in
``scrapers/vendors/<vendor>.py``. ``tests/test_registry.py`` fails the build if a
model is unreachable or two models share a name.
"""

from __future__ import annotations

from ..core.model_registry import resolve as _resolve


def resolve_model_id(reported_name: str) -> str | None:
    """Find a canonical model_id for a benchmark-reported model name, or None.

    None means "no confident match" — the caller must log it as an unresolved
    observation (a discovery candidate), never fall back to a guess.
    """
    return _resolve(reported_name)
