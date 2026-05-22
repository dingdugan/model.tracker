"""Maps benchmark-reported model names → our canonical model_id.

Benchmark sites use their own naming. This is the bridge.
Keep this updated as the catalog grows.
"""

from __future__ import annotations

import re


# Lowercase substring → canonical model_id. Longer keys win.
# Use distinctive substrings; e.g. "claude opus 4.7" not just "opus".
NAME_TO_MODEL_ID: dict[str, str] = {
    # OpenAI
    "gpt-5-nano":               "openai/gpt-5-nano",
    "gpt-5-mini":               "openai/gpt-5-mini",
    "gpt-5":                    "openai/gpt-5",
    "gpt-4.1-mini":             "openai/gpt-4.1-mini",
    "gpt-4.1":                  "openai/gpt-4.1",
    "gpt-4o-mini":              "openai/gpt-4o-mini",
    "gpt-4o":                   "openai/gpt-4o",
    "o4-mini":                  "openai/o4-mini",
    "o3":                       "openai/o3",

    # Anthropic
    "claude opus 4.7":          "anthropic/claude-opus-4-7",
    "claude-opus-4-7":          "anthropic/claude-opus-4-7",
    "claude opus 4.6":          "anthropic/claude-opus-4-6",
    "claude-opus-4-6":          "anthropic/claude-opus-4-6",
    "claude sonnet 4.6":        "anthropic/claude-sonnet-4-6",
    "claude-sonnet-4-6":        "anthropic/claude-sonnet-4-6",
    "claude sonnet 4.5":        "anthropic/claude-sonnet-4-5",
    "claude-sonnet-4-5":        "anthropic/claude-sonnet-4-5",
    "claude haiku 4.5":         "anthropic/claude-haiku-4-5",
    "claude-haiku-4-5":         "anthropic/claude-haiku-4-5",
    "claude 3.5 sonnet":        "anthropic/claude-3-5-sonnet",

    # Google
    "gemini 3 pro":             "google/gemini-3-pro",
    "gemini-3-pro":             "google/gemini-3-pro",
    "gemini 2.5 pro":           "google/gemini-2-5-pro",
    "gemini-2.5-pro":           "google/gemini-2-5-pro",
    "gemini 2.5 flash-lite":    "google/gemini-2-5-flash-lite",
    "gemini 2.5 flash":         "google/gemini-2-5-flash",
    "gemini-2.5-flash":         "google/gemini-2-5-flash",
    "gemini 2.0 flash":         "google/gemini-2-0-flash",
    "gemma-3-27b":              "google/gemma-3-27b",

    # Meta
    "llama 4 behemoth":         "meta/llama-4-behemoth",
    "llama-4-behemoth":         "meta/llama-4-behemoth",
    "llama 4 maverick":         "meta/llama-4-maverick",
    "llama-4-maverick":         "meta/llama-4-maverick",
    "llama 4 scout":            "meta/llama-4-scout",
    "llama-4-scout":            "meta/llama-4-scout",
    "llama 3.3 70b":            "meta/llama-3-3-70b",
    "llama-3.3-70b":            "meta/llama-3-3-70b",
    "llama 3.1 405b":           "meta/llama-3-1-405b",

    # Mistral
    "mistral large 2":          "mistral/mistral-large-2",
    "mistral-large-2":          "mistral/mistral-large-2",
    "mistral medium 3":         "mistral/mistral-medium-3",
    "mistral-medium-3":         "mistral/mistral-medium-3",
    "mistral small 3.2":        "mistral/mistral-small-3-2",
    "codestral 2":              "mistral/codestral-2",
    "pixtral large":            "mistral/pixtral-large",
    "ministral 8b":             "mistral/ministral-8b",

    # xAI
    "grok 4 heavy":             "xai/grok-4-heavy",
    "grok-4-heavy":             "xai/grok-4-heavy",
    "grok 4 fast":              "xai/grok-4-fast",
    "grok-4-fast":              "xai/grok-4-fast",
    "grok 4":                   "xai/grok-4",
    "grok-4":                   "xai/grok-4",
    "grok 3 mini":              "xai/grok-3-mini",
    "grok 3":                   "xai/grok-3",

    # Cohere
    "command a":                "cohere/command-a-03-2025",
    "command-a":                "cohere/command-a-03-2025",
    "command r+":               "cohere/command-r-plus",
    "command-r-plus":           "cohere/command-r-plus",
    "command r7b":              "cohere/command-r7b",
    "command-r7b":              "cohere/command-r7b",
    "command r":                "cohere/command-r-08-2024",
    "aya expanse 32b":          "cohere/aya-expanse-32b",

    # DeepSeek
    "deepseek v3.2":            "deepseek/deepseek-v3-2",
    "deepseek-v3.2":            "deepseek/deepseek-v3-2",
    "deepseek v3.1":            "deepseek/deepseek-v3-1",
    "deepseek-v3.1":            "deepseek/deepseek-v3-1",
    "deepseek r1":              "deepseek/deepseek-r1",
    "deepseek-r1":              "deepseek/deepseek-r1",
    "deepseek v2.5":            "deepseek/deepseek-v2-5",

    # Qwen
    "qwen3 max":                "qwen/qwen3-max",
    "qwen3-max":                "qwen/qwen3-max",
    "qwen3 235b":               "qwen/qwen3-235b-a22b",
    "qwen3-235b":               "qwen/qwen3-235b-a22b",
    "qwen3 72b":                "qwen/qwen3-72b",
    "qwen3-72b":                "qwen/qwen3-72b",
    "qwen3 32b":                "qwen/qwen3-32b",
    "qwen3 coder":              "qwen/qwen3-coder",
    "qwen2.5 vl 72b":           "qwen/qwen2-5-vl-72b",

    # GLM
    "glm-4.6":                  "glm/glm-4-6",
    "glm-4.5":                  "glm/glm-4-5",
    "glm-4.5-air":              "glm/glm-4-5-air",
    "glm-4v-plus":              "glm/glm-4v-plus",

    # Doubao
    "doubao 1.5 pro":           "doubao/doubao-1-5-pro-256k",
    "doubao-1.5-pro":           "doubao/doubao-1-5-pro-256k",
    "doubao 1.5 lite":          "doubao/doubao-1-5-lite-32k",
    "doubao 1.5 thinking pro":  "doubao/doubao-1-5-thinking-pro",
    "doubao seed 1.6":          "doubao/doubao-seed-1-6",

    # Kimi
    "kimi k2":                  "kimi/kimi-k2",
    "kimi-k2":                  "kimi/kimi-k2",
    "moonshot v1 128k":         "kimi/moonshot-v1-128k",
    "moonshot v1 32k":          "kimi/moonshot-v1-32k",
    "moonshot v1 8k":           "kimi/moonshot-v1-8k",

    # Baichuan
    "baichuan4 turbo":          "baichuan/baichuan4-turbo",
    "baichuan4 air":            "baichuan/baichuan4-air",
    "baichuan4":                "baichuan/baichuan4",

    # Hunyuan
    "hunyuan turbos":           "hunyuan/hunyuan-turbos",
    "hunyuan-turbos":           "hunyuan/hunyuan-turbos",
    "hunyuan large":            "hunyuan/hunyuan-large",
    "hunyuan-large":            "hunyuan/hunyuan-large",
    "hunyuan standard":         "hunyuan/hunyuan-standard",
    "hunyuan lite":             "hunyuan/hunyuan-lite",
    "hunyuan vision":           "hunyuan/hunyuan-vision",
    "hunyuan t1":               "hunyuan/hunyuan-t1",
}

# Sort keys longest-first so that "claude opus 4.7" matches before "claude".
_SORTED_KEYS = sorted(NAME_TO_MODEL_ID.keys(), key=len, reverse=True)


def resolve_model_id(reported_name: str) -> str | None:
    """Try to find a canonical model_id for a benchmark-reported model name."""
    if not reported_name:
        return None
    n = re.sub(r"\s+", " ", reported_name.strip().lower())
    for key in _SORTED_KEYS:
        if key in n:
            return NAME_TO_MODEL_ID[key]
    return None
