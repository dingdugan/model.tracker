"""Discovery filtering — pure logic, no network.

Given names seen in the wild, decide which are genuinely *unknown* (i.e. not
already a model in our registry, and not just a dated/regional snapshot of a
known model). Unknown names become discovery candidates for human review.

Kept separate from the network adapters (``scrapers/discovery/``) so the
decision logic is unit-testable without API keys.
"""

from __future__ import annotations

import re

from .model_registry import base_form, canon, resolve_benchmark

# Name prefix → vendor we already track. Lets us tell a high-signal candidate
# ("a vendor you cover shipped something you're missing") from a low-signal one
# ("a model from a vendor you don't track at all"). Longest prefix wins.
_VENDOR_PREFIXES: list[tuple[str, str]] = [
    ("claude", "anthropic"),
    ("chatgpt", "openai"), ("gpt-", "openai"), ("gpt4", "openai"),
    ("o1", "openai"), ("o3", "openai"), ("o4", "openai"),
    ("gemini", "google"), ("gemma", "google"),
    ("llama", "meta"),
    ("mistral", "mistral"), ("mixtral", "mistral"), ("codestral", "mistral"),
    ("ministral", "mistral"), ("pixtral", "mistral"), ("devstral", "mistral"),
    ("grok", "xai"),
    ("command", "cohere"), ("aya", "cohere"), ("c4ai", "cohere"),
    ("deepseek", "deepseek"),
    ("qwen", "qwen"), ("qwq", "qwen"),
    ("glm", "glm"), ("chatglm", "glm"),
    ("doubao", "doubao"),
    ("kimi", "kimi"), ("moonshot", "kimi"),
    ("baichuan", "baichuan"),
    ("hunyuan", "hunyuan"),
]


def infer_vendor(name: str) -> str | None:
    """Best-effort: which tracked vendor does this leaderboard name belong to?

    Returns a tracked vendor_id, or None if the name doesn't look like any
    vendor we cover (i.e. a lower-priority "expand coverage" candidate).
    """
    n = re.sub(r"[\s/_]+", "-", (name or "").strip().lower())
    best: tuple[int, str] | None = None
    for prefix, vendor in _VENDOR_PREFIXES:
        if n.startswith(prefix) and (best is None or len(prefix) > best[0]):
            best = (len(prefix), vendor)
    return best[1] if best else None


def is_known(reported_name: str) -> bool:
    """True if the name resolves to a tracked model (incl. mode/dated variants).

    Mirrors benchmark resolution: exact, then qualifier-stripped base — so we
    don't flag ``claude-opus-4-7-thinking`` or ``claude-haiku-4-5-20251001`` as
    "new" when the base model is tracked.
    """
    if not reported_name:
        return True  # nothing to discover
    return resolve_benchmark(reported_name) is not None


def filter_unknown(candidates):
    """Keep only candidates whose reported_name is not already known.

    De-dupes within the batch by (source, canon(base_form(reported_name))) so
    dated/mode variants of the same unknown base collapse to one candidate, and
    tags each with an inferred vendor when one isn't already set.
    """
    seen: set[tuple[str, str]] = set()
    out = []
    for c in candidates:
        if is_known(c.reported_name):
            continue
        key = (c.source, canon(base_form(c.reported_name)) or canon(c.reported_name))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        if not c.vendor_guess:
            c.vendor_guess = infer_vendor(c.reported_name)
        out.append(c)
    return out
