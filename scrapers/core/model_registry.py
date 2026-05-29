"""Unified model identity registry — the single source of truth for "which
name belongs to which model".

Every model is defined exactly once, in its vendor's ``catalog``
(``scrapers/vendors/<vendor>.py``). Each ``ModelRecord`` carries its ``aliases``:
every external name — benchmark display names, dated snapshots, platform-specific
IDs — that should resolve to its canonical ``id``.

Both matchers resolve names through THIS registry:
  * price matching   — ``vendors/_helpers.py``
  * benchmark matching — ``benchmarks/_mapping.py``

There is no second hand-maintained list to drift out of sync. Adding a model in
one place (its catalog) is enough; CI (``tests/test_registry.py``) fails the build
if two models share an alias or a model fails to round-trip.

Matching is **normalized-exact, never substring**. A name resolves only if its
canonical form exactly equals the canonical form of the model's slug, display
name, or one declared alias. Anything else returns ``None`` — the caller logs it
as an unresolved observation / discovery candidate (Phase B). We never guess,
because a wrong guess is exactly the "A's price shows up on B" failure we are
trying to make impossible.

Why exact and not substring: substring matching lets a short alias (``gpt-5``)
silently grab an unrelated longer name (``gpt-5-codex``). The cost of exact
matching is that a name with extra qualifiers (``Command A (March 2025)``) won't
resolve until its form is added as an alias — but that surfaces loudly as a
candidate rather than corrupting data silently.
"""

from __future__ import annotations

import re
from functools import lru_cache


def canon(s: str) -> str:
    """Canonicalize a name for matching: lowercase, unify separators, collapse.

    ``/``, ``_``, ``.``, whitespace all become ``-``; runs of ``-`` collapse.
    "Claude Opus 4.6", "claude_opus_4.6", "claude-opus-4-6" → "claude-opus-4-6".
    """
    s = (s or "").strip().lower()
    s = re.sub(r"[\s/_.]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


class AliasCollision(ValueError):
    """Two distinct models declare the same canonical alias."""


def _build_alias_map() -> dict[str, str]:
    """Build ``canon(alias) -> canonical_id`` from every vendor catalog.

    Raises ``AliasCollision`` if two different models map to the same key — that
    is a precision bug (it would make attribution ambiguous) and must fail loud.
    """
    # Imported lazily to avoid a circular import at module load time
    # (registry → vendors → _helpers → core).
    from .registry import discover_vendor_scrapers

    alias_to_id: dict[str, str] = {}
    collisions: list[str] = []

    for scraper in discover_vendor_scrapers():
        for m in getattr(scraper, "catalog", []) or []:
            for raw in (m.slug, m.name, *getattr(m, "aliases", [])):
                key = canon(raw)
                if not key:
                    continue
                existing = alias_to_id.get(key)
                if existing is not None and existing != m.id:
                    collisions.append(f"{key!r}: {existing} vs {m.id}")
                    continue
                alias_to_id[key] = m.id

    if collisions:
        raise AliasCollision(
            "alias collisions across catalogs (same name → two models):\n  "
            + "\n  ".join(sorted(collisions))
        )
    return alias_to_id


@lru_cache(maxsize=1)
def _alias_map() -> dict[str, str]:
    return _build_alias_map()


def resolve(name: str) -> str | None:
    """Return the canonical model_id for an external name, or ``None``.

    Normalized-exact match against every model's slug / display name / aliases.
    ``None`` means "no confident match" — callers must treat that as an
    unresolved observation, never as a fallback guess.
    """
    if not name:
        return None
    return _alias_map().get(canon(name))


# Trailing tokens that denote a *mode/snapshot* of a model, not a different
# model: thinking mode, instruction-tuned, dated snapshots, previews. Stripping
# these lets a leaderboard's "claude-opus-4-7-thinking" or
# "gemma-3-27b-it" resolve to the base model we track.
#
# CRITICAL: this list must NEVER contain identity-bearing tokens (sizes like
# 8b/32b/mini/lite/pro/flash/nano/air/turbo, or version numbers). Stripping one
# of those would map model A onto model B — the exact misattribution we forbid.
# Because the base must still EXACTLY match a catalog entry (and catalog aliases
# are collision-checked), a strip can only ever land on the genuine base model.
_VARIANT_SUFFIXES = [
    r"\s*\([^)]*\)\s*$",            # trailing "(thinking-minimal)" etc.
    r"[-@\s]\d{4}-\d{2}-\d{2}$",    # ISO date  -2025-04-14
    r"[-@\s]\d{6,8}$",              # compact snapshot  -20251101
    r"[-\s]\d{1,2}-\d{4}$",         # MM-YYYY  -09-2025
    # no-/non-thinking must precede the bare 'thinking' rule, else the latter
    # strips '-thinking' out of '-no-thinking' and leaves a dangling '-no'.
    r"[-\s]no[-\s]?thinking$",
    r"[-\s]non[-\s]?thinking$",
    r"[-\s]thinking(?:[-\s]\d+k)?$",
    r"[-\s]it$",                    # instruction-tuned
    r"[-\s]latest$",
    r"[-\s]preview$",
    r"[-\s]exp$",
    r"[-\s]beta$",
    r"[-\s]terminus$",
]
_VARIANT_RE = [re.compile(p, re.IGNORECASE) for p in _VARIANT_SUFFIXES]


def base_form(name: str) -> str:
    """Strip trailing mode/snapshot qualifiers to reach the base model name."""
    cur = (name or "").strip()
    prev = None
    while cur != prev:
        prev = cur
        for rx in _VARIANT_RE:
            cur = rx.sub("", cur).strip()
        cur = cur.strip("-@ ")
    return cur


def resolve_benchmark(name: str) -> str | None:
    """Resolve a benchmark/leaderboard model name to a canonical id.

    Exact match first; if that fails, strip mode/snapshot qualifiers and exact-
    match the base. Used by benchmark scrapers so that variant rows
    (``-thinking``, ``-it``, dated snapshots) attach to the base model we track,
    while still never guessing — the stripped base must itself exactly resolve.
    """
    if not name:
        return None
    hit = _alias_map().get(canon(name))
    if hit is not None:
        return hit
    base = base_form(name)
    if base and base != name:
        return _alias_map().get(canon(base))
    return None


def all_aliases() -> dict[str, str]:
    """Full ``canon(alias) -> id`` map (copy). For tests / introspection."""
    return dict(_alias_map())


def reset_cache() -> None:
    """Drop the memoized map. For tests that mutate catalogs."""
    _alias_map.cache_clear()
