"""Tests for discovery vendor-API sources (Google + DashScope filtering).

These sources feed AUTO-PROMOTION (vendor-api:* is trusted), so their filters
are correctness-critical: anything that slips through becomes a model row.
The network call itself is not tested — only the pure parse/filter step and
the graceful no-key skip.
"""

from __future__ import annotations

from scrapers.discovery.vendor_api import GoogleModelsAPI, QwenModelsAPI


def _google_item(name, methods=("generateContent",), display=None):
    return {
        "name": name,
        "displayName": display,
        "supportedGenerationMethods": list(methods),
    }


class TestGoogleParse:
    src = GoogleModelsAPI()

    def test_strips_models_prefix_and_keeps_display_name(self):
        out = self.src._parse([_google_item("models/gemini-3.5-flash", display="Gemini 3.5 Flash")])
        assert len(out) == 1
        assert out[0].reported_name == "gemini-3.5-flash"
        assert out[0].vendor_guess == "google"
        assert out[0].raw_context["display_name"] == "Gemini 3.5 Flash"

    def test_requires_generate_content(self):
        # embeddings advertise embedContent, not generateContent
        out = self.src._parse([_google_item("models/gemini-embedding-001", methods=("embedContent",))])
        assert out == []

    def test_drops_non_text_skus_even_with_generate_content(self):
        items = [
            _google_item("models/gemini-2.5-flash-preview-tts"),
            _google_item("models/gemini-2.0-flash-preview-image-generation"),
            _google_item("models/imagen-3.0-generate-002"),
        ]
        assert self.src._parse(items) == []

    def test_keeps_gemma(self):
        out = self.src._parse([_google_item("models/gemma-4-12b-unified")])
        assert [c.reported_name for c in out] == ["gemma-4-12b-unified"]

    def test_no_key_skips_gracefully(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        assert self.src.discover() == []


class TestQwenParse:
    src = QwenModelsAPI()

    def test_keeps_qwen_family(self):
        out = self.src._parse([{"id": "qwen3.7-max"}, {"id": "qwq-32b"}, {"id": "qvq-72b-preview"}])
        assert [c.reported_name for c in out] == ["qwen3.7-max", "qwq-32b", "qvq-72b-preview"]
        assert all(c.vendor_guess == "qwen" for c in out)

    def test_never_attributes_third_party_hosted_models(self):
        # DashScope hosts other vendors' open models — these must NOT become
        # qwen-vendor candidates (that is the misattribution we forbid).
        out = self.src._parse([{"id": "deepseek-r1"}, {"id": "llama3.3-70b-instruct"}, {"id": "glm-4-plus"}])
        assert out == []

    def test_drops_non_text_skus(self):
        items = [
            {"id": "text-embedding-v3"},
            {"id": "qwen-tts-latest"},
            {"id": "qwen-mt-plus"},
            {"id": "qwen-audio-turbo"},
            {"id": "qwen-vl-ocr"},
            {"id": "wanx-v1"},
        ]
        assert self.src._parse(items) == []

    def test_no_key_skips_gracefully(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        assert self.src.discover() == []
