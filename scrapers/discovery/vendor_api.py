"""Discovery via vendors' official Models APIs.

These are the strongest discovery signal: an authoritative list of the model IDs
a vendor currently serves. When a vendor ships a new model it shows up here
immediately, with no page-scraping fragility.

Each source is gated on its API key — if the key is absent the source logs and
returns ``[]`` (multi-signal discovery degrades gracefully rather than failing).
"""

from __future__ import annotations

import os
import re

import httpx

from ..core.schema import DiscoveryCandidate
from .base import DiscoverySource

_TIMEOUT = 20


class AnthropicModelsAPI(DiscoverySource):
    source = "vendor-api:anthropic"
    vendor_id = "anthropic"
    url = "https://api.anthropic.com/v1/models?limit=100"

    def discover(self) -> list[DiscoveryCandidate]:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            print(f"  [{self.source}] no ANTHROPIC_API_KEY — skipping")
            return []
        try:
            resp = httpx.get(
                self.url,
                headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except Exception as e:
            print(f"  [{self.source}] fetch failed: {e}")
            return []

        out = []
        for item in data:
            mid = (item.get("id") or "").strip()
            if not mid or not mid.lower().startswith("claude"):
                continue
            out.append(
                DiscoveryCandidate(
                    source=self.source,
                    reported_name=mid,
                    vendor_guess=self.vendor_id,
                    raw_context={"display_name": item.get("display_name")},
                )
            )
        print(f"  [{self.source}] {len(out)} models advertised")
        return out


class OpenAIModelsAPI(DiscoverySource):
    source = "vendor-api:openai"
    vendor_id = "openai"
    url = "https://api.openai.com/v1/models"

    # OpenAI's list includes embeddings/audio/image/deprecated SKUs — keep only
    # chat-completion-style families so discovery isn't flooded with noise.
    _RELEVANT = re.compile(r"^(gpt-|o\d|chatgpt-)", re.IGNORECASE)
    _IGNORE = re.compile(
        r"(embedding|whisper|tts|audio|realtime|image|dall-e|moderation|transcribe|search|instruct)",
        re.IGNORECASE,
    )

    def discover(self) -> list[DiscoveryCandidate]:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            print(f"  [{self.source}] no OPENAI_API_KEY — skipping")
            return []
        try:
            resp = httpx.get(
                self.url,
                headers={"Authorization": f"Bearer {key}"},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except Exception as e:
            print(f"  [{self.source}] fetch failed: {e}")
            return []

        out = []
        for item in data:
            mid = (item.get("id") or "").strip()
            if not mid or not self._RELEVANT.match(mid) or self._IGNORE.search(mid):
                continue
            out.append(
                DiscoveryCandidate(
                    source=self.source,
                    reported_name=mid,
                    vendor_guess=self.vendor_id,
                    raw_context={},
                )
            )
        print(f"  [{self.source}] {len(out)} chat models advertised")
        return out
