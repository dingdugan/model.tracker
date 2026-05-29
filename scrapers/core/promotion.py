"""Auto-promotion logic — pure, no DB/network.

Turns a high-trust discovery candidate (from a vendor's official Models API) into
the fields for a new model row. Only vendor-API sources are eligible; noisy
leaderboard names are never auto-promoted.

Grounding note: every field here is derived from the vendor's OWN authoritative
API response (id, display_name) — nothing is fabricated. Metadata the API does
not provide (context window, pricing) is left absent and filled later by the
normal scrapers, never guessed.
"""

from __future__ import annotations

from typing import Optional

from .discovery import infer_vendor
from .model_registry import base_form, canon

# Only these sources are authoritative enough to auto-create a model.
TRUSTED_SOURCE_PREFIX = "vendor-api:"


def is_trusted(candidate) -> bool:
    return str(getattr(candidate, "source", "")).startswith(TRUSTED_SOURCE_PREFIX)


def derive_model(candidate) -> Optional[dict]:
    """Build a model dict {vendor_id, slug, name, aliases, id} from a trusted
    candidate, or None if it can't be safely attributed to a vendor.

    The canonical slug is the base form (dated/mode qualifiers stripped) so a
    dated API id like ``claude-opus-4-5-20251101`` becomes model
    ``claude-opus-4-5`` with the dated id kept as an alias.
    """
    if not is_trusted(candidate):
        return None

    reported = (candidate.reported_name or "").strip()
    if not reported:
        return None

    vendor = candidate.vendor_guess or infer_vendor(reported)
    if not vendor:
        return None  # can't place it under a known vendor → don't auto-create

    base = base_form(reported) or reported
    slug = _slugify(base)
    if not slug:
        return None

    display = (candidate.raw_context or {}).get("display_name") or _titleize(base)
    aliases = [reported] if canon(reported) != canon(slug) else []

    return {
        "id": f"{vendor}/{slug}",
        "vendor_id": vendor,
        "slug": slug,
        "name": display,
        "aliases": aliases,
    }


def _slugify(name: str) -> str:
    """A catalog-style slug: lowercase, spaces/underscores → dash. Keeps dots
    (catalog slugs like ``gpt-4.1`` do)."""
    s = (name or "").strip().lower()
    out = []
    for ch in s:
        if ch.isalnum() or ch in ".-":
            out.append(ch)
        elif ch in " _/":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-.")


def _titleize(base: str) -> str:
    """Fallback display name when the API gives no display_name."""
    return base.replace("-", " ").replace("_", " ").strip() or base
