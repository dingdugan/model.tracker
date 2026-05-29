"""Discovery filtering — pure logic, no network.

Given names seen in the wild, decide which are genuinely *unknown* (i.e. not
already a model in our registry, and not just a dated/regional snapshot of a
known model). Unknown names become discovery candidates for human review.

Kept separate from the network adapters (``scrapers/discovery/``) so the
decision logic is unit-testable without API keys.
"""

from __future__ import annotations

import re

from .model_registry import canon, resolve

# Trailing version/snapshot tokens vendors append to a base model id:
#   claude-haiku-4-5-20251001, claude-opus-4-5@20251101, gpt-4o-2024-08-06,
#   ...-v1:0, ...-preview, ...-latest
_DATE_SUFFIX = re.compile(
    r"[-@](?:\d{6,8}|\d{4}-\d{2}-\d{2}|v\d+(?::\d+)?|latest|preview|exp|beta)$",
    re.IGNORECASE,
)


def _strip_variant_suffixes(name: str) -> str:
    """Iteratively drop trailing date/version tokens to reach the base name."""
    prev = None
    cur = name.strip()
    while cur != prev:
        prev = cur
        cur = _DATE_SUFFIX.sub("", cur).strip().strip("-@")
    return cur


def is_known(reported_name: str) -> bool:
    """True if the name is a known model, or a dated/regional variant of one.

    Uses the strict (exact) registry resolver, but first also tries the name
    with trailing date/version tokens stripped — so we don't flag
    ``claude-haiku-4-5-20251001`` as "new" when ``claude-haiku-4-5`` is known.
    """
    if not reported_name:
        return True  # nothing to discover
    if resolve(reported_name) is not None:
        return True
    base = _strip_variant_suffixes(reported_name)
    if base and base != reported_name and resolve(base) is not None:
        return True
    return False


def filter_unknown(candidates):
    """Keep only candidates whose reported_name is not already known.

    De-dupes within the batch by (source, canon(reported_name)) so one run never
    proposes the same thing twice.
    """
    seen: set[tuple[str, str]] = set()
    out = []
    for c in candidates:
        if is_known(c.reported_name):
            continue
        key = (c.source, canon(c.reported_name))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out
