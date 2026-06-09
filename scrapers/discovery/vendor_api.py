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


class GoogleModelsAPI(DiscoverySource):
    source = "vendor-api:google"
    vendor_id = "google"
    url = "https://generativelanguage.googleapis.com/v1beta/models"

    # The Gemini API list mixes text models with embedding/TTS/image/video SKUs.
    # Keep only generateContent-capable Gemini/Gemma families; everything else
    # would otherwise be auto-promoted into the models table.
    _RELEVANT = re.compile(r"^(gemini-|gemma-)", re.IGNORECASE)
    _IGNORE = re.compile(
        r"(embedding|aqa|imagen|veo|tts|audio|live|image-generation|robotics|computer-use)",
        re.IGNORECASE,
    )

    def discover(self) -> list[DiscoveryCandidate]:
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            print(f"  [{self.source}] no GEMINI_API_KEY/GOOGLE_API_KEY — skipping")
            return []
        items: list[dict] = []
        token: str | None = None
        try:
            for _ in range(5):  # page cap; pageSize=200 fits today's list in one page
                params: dict = {"key": key, "pageSize": 200}
                if token:
                    params["pageToken"] = token
                resp = httpx.get(self.url, params=params, timeout=_TIMEOUT)
                resp.raise_for_status()
                payload = resp.json()
                items.extend(payload.get("models", []))
                token = payload.get("nextPageToken")
                if not token:
                    break
        except Exception as e:
            print(f"  [{self.source}] fetch failed: {e}")
            return []

        out = self._parse(items)
        print(f"  [{self.source}] {len(out)} text models advertised")
        return out

    def _parse(self, items: list[dict]) -> list[DiscoveryCandidate]:
        out = []
        for item in items:
            mid = (item.get("name") or "").strip().removeprefix("models/")
            methods = item.get("supportedGenerationMethods") or []
            if not mid or "generateContent" not in methods:
                continue
            if not self._RELEVANT.match(mid) or self._IGNORE.search(mid):
                continue
            out.append(
                DiscoveryCandidate(
                    source=self.source,
                    reported_name=mid,
                    vendor_guess=self.vendor_id,
                    raw_context={"display_name": item.get("displayName")},
                )
            )
        return out


class QwenModelsAPI(DiscoverySource):
    source = "vendor-api:qwen"
    vendor_id = "qwen"
    # DashScope's OpenAI-compatible listing endpoint. Keys are region-specific:
    # default to the international endpoint, override with DASHSCOPE_BASE_URL
    # (e.g. https://dashscope.aliyuncs.com/compatible-mode/v1 for Beijing).
    default_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # DashScope also hosts third-party open-weight models (deepseek-*, llama-*).
    # The qwen/qwq/qvq prefix gate is what keeps those from being attributed to
    # the qwen vendor — never widen it to "everything the endpoint returns".
    _RELEVANT = re.compile(r"^(qwen|qwq|qvq)", re.IGNORECASE)
    _IGNORE = re.compile(
        r"(embedding|tts|asr|audio|ocr|image|video|realtime|wanx|captioner|[-_]mt[-_])",
        re.IGNORECASE,
    )

    def discover(self) -> list[DiscoveryCandidate]:
        key = os.environ.get("DASHSCOPE_API_KEY")
        if not key:
            print(f"  [{self.source}] no DASHSCOPE_API_KEY — skipping")
            return []
        base = os.environ.get("DASHSCOPE_BASE_URL", self.default_base).rstrip("/")
        try:
            resp = httpx.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except Exception as e:
            print(f"  [{self.source}] fetch failed: {e}")
            return []

        out = self._parse(data)
        print(f"  [{self.source}] {len(out)} qwen-family models advertised")
        return out

    def _parse(self, data: list[dict]) -> list[DiscoveryCandidate]:
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
        return out
