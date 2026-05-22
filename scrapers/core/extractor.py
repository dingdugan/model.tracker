"""Page fetching + structured extraction.

Strategy:
  1. Fetch HTML with httpx (fast) or Playwright (JS-rendered).
  2. Run vendor-specific CSS selector / regex parser → primary path.
  3. If primary returns empty / fails, fall back to Claude (Haiku by default) on the
     cleaned HTML body to extract structured records.

The fallback is rate-limited; vendor scrapers should mostly stay in path 2.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from anthropic import Anthropic
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 model.tracker/0.1"
)


@dataclass
class FetchResult:
    url: str
    status: int
    html: str
    final_url: str


# ──────────────────────────────────────────────────────────────────────────────
# Fetching
# ──────────────────────────────────────────────────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def fetch_static(url: str, *, timeout: float = 30.0, headers: Optional[dict] = None) -> FetchResult:
    h = {"User-Agent": DEFAULT_UA, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.7"}
    if headers:
        h.update(headers)
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=h) as client:
        r = client.get(url)
        r.raise_for_status()
        return FetchResult(url=url, status=r.status_code, html=r.text, final_url=str(r.url))


def fetch_rendered(url: str, *, timeout: float = 45.0, wait_for: Optional[str] = None) -> FetchResult:
    """JS-rendered fetch via Playwright. Lazy-imported so scrapers without it stay fast."""
    from playwright.sync_api import sync_playwright

    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "1") != "0"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            ctx = browser.new_context(
                user_agent=DEFAULT_UA,
                locale="zh-CN",
                viewport={"width": 1440, "height": 900},
            )
            page = ctx.new_page()
            page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            if wait_for:
                page.wait_for_selector(wait_for, timeout=timeout * 1000)
            html = page.content()
            final = page.url
            return FetchResult(url=url, status=200, html=html, final_url=final)
        finally:
            browser.close()


# ──────────────────────────────────────────────────────────────────────────────
# HTML helpers
# ──────────────────────────────────────────────────────────────────────────────
def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def clean_text_for_llm(html: str, max_chars: int = 40_000) -> str:
    """Strip scripts/styles/nav/footer, collapse whitespace, return readable text."""
    s = BeautifulSoup(html, "lxml")
    for tag in s(["script", "style", "noscript", "svg", "iframe", "link", "meta"]):
        tag.decompose()
    # Drop obvious chrome
    for selector in ["nav", "footer", "header", "[role=navigation]", ".navbar", ".footer"]:
        for el in s.select(selector):
            el.decompose()
    text = s.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars]


# Money parsing — handles "$3 / 1M tokens", "￥1.5 / 百万 tokens", "0.50 USD per million", etc.
_PRICE_RE = re.compile(
    r"(?P<currency>[\$￥¥€£]|USD|CNY|EUR|GBP|RMB)\s*"
    r"(?P<amount>\d+(?:\.\d+)?)"
    r"(?:\s*[/／]\s*(?P<denom>(?:1\s*[Mm]|百万|million|百萬)\s*(?:input\s+)?tokens?))?",
    re.IGNORECASE,
)


def parse_price_string(s: str) -> Optional[tuple[float, str]]:
    """Returns (amount, currency_iso) or None."""
    m = _PRICE_RE.search(s)
    if not m:
        return None
    amount = float(m.group("amount"))
    cur_raw = m.group("currency")
    currency = {
        "$":   "USD", "USD": "USD",
        "¥":   "CNY", "￥": "CNY", "CNY": "CNY", "RMB": "CNY",
        "€":   "EUR", "EUR": "EUR",
        "£":   "GBP", "GBP": "GBP",
    }.get(cur_raw.upper() if cur_raw.isalpha() else cur_raw, "USD")
    return amount, currency


# Rough CNY→USD (refreshed periodically by vendors; we use a fixed conversion
# for display normalization, not for trading)
CNY_TO_USD = 0.14


def normalize_to_usd_per_mtok(amount: float, currency: str) -> float:
    if currency == "USD":
        return amount
    if currency == "CNY":
        return round(amount * CNY_TO_USD, 4)
    return amount  # leave other currencies alone


# ──────────────────────────────────────────────────────────────────────────────
# LLM fallback
# ──────────────────────────────────────────────────────────────────────────────
_anthropic_client: Optional[Anthropic] = None


def _client() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic()
    return _anthropic_client


EXTRACTION_PROMPT = """\
You are extracting LLM model information from a vendor's website.

Given the page text below, return a STRICT JSON object with this shape:

{
  "models": [
    {
      "slug":              "stable-id-like-string",
      "name":              "Display Name",
      "family":            "gpt|claude|gemini|...",
      "release_date":      "YYYY-MM-DD or null",
      "context_window":    integer or null,
      "max_output_tokens": integer or null,
      "modalities":        ["text", "image", ...],
      "is_open_weight":    boolean,
      "license":           "apache-2.0|mit|llama-4|gemma|proprietary|null",
      "parameters_b":      number or null,
      "status":            "active|preview|deprecated|retired",
      "description":       "one-sentence summary or null"
    }
  ],
  "prices": [
    {
      "model_slug":             "matches a slug above",
      "input_per_mtok":         number or null,
      "output_per_mtok":        number or null,
      "cached_input_per_mtok":  number or null,
      "currency":               "USD|CNY|EUR"
    }
  ]
}

Rules:
- ONLY return the JSON object, no prose, no markdown fences.
- All token prices must be normalized to "per 1,000,000 tokens" in the listed currency.
- If a price is listed per 1K tokens, multiply by 1000.
- If two prices appear (input/output), include both.
- Skip models you can't find a clear name for.
- "preview" status applies to beta/experimental models.

Page text:
---
{TEXT}
"""


def _repair_truncated_json(text: str) -> str:
    """Attempt to close incomplete/truncated JSON.

    Strategy (in order of preference, to recover the most clean data possible):
      1. If it already parses, return as-is.
      2. Trim back to the last complete array element (`},` boundary) and try
         a small set of bracket-only closures. This drops any partial tail
         object — cleaner than closing it with garbage data.
      3. As a last resort, append quote-closing suffixes to keep whatever is
         in the buffer (may leave a truncated trailing string value).
    """
    # Fast path: already parses.
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    bracket_closures = [
        ']}',
        ']}}',
        '}]}',
        '}]}}',
        ']}, "prices": []}',
        '}], "prices": []}',
    ]

    # Prefer trim-back to last complete array element. This drops a partial
    # tail object entirely — better than recovering it with garbage data.
    cut_points: list[int] = []
    for match in re.finditer(r'\},', text):
        cut_points.append(match.start())  # position of the `}` (comma excluded by slice)
    for cut in sorted(set(cut_points), reverse=True):
        trimmed = text[: cut + 1]
        for suffix in bracket_closures:
            try:
                json.loads(trimmed + suffix)
                return trimmed + suffix
            except json.JSONDecodeError:
                continue

    # Truncation at a bracket boundary (no partial tail) — just append closures.
    for suffix in bracket_closures:
        try:
            json.loads(text + suffix)
            return text + suffix
        except json.JSONDecodeError:
            continue

    # Last resort: close a dangling string so at least the well-formed prefix
    # parses (the consumer can filter out partial entries by name lookup).
    for suffix in ['"}]}', '"}]}}', '"}], "prices": []}']:
        try:
            json.loads(text + suffix)
            return text + suffix
        except json.JSONDecodeError:
            continue

    return text


def llm_extract(page_text: str, *, model: Optional[str] = None) -> dict[str, Any]:
    """Returns {'models': [...], 'prices': [...]} as a dict. Raises on JSON parse failure."""
    model = model or os.environ.get("EXTRACTOR_MODEL", "claude-haiku-4-5")
    prompt = EXTRACTION_PROMPT.replace("{TEXT}", page_text)

    resp = _client().messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
        # cache the long prompt prefix — Anthropic returns better $$ for repeated calls
        system=[
            {
                "type": "text",
                "text": "You output STRICT JSON only. No prose, no markdown.",
                "cache_control": {"type": "ephemeral"},
            }
        ],
    )

    text = "".join(block.text for block in resp.content if hasattr(block, "text"))
    # Trim accidental markdown fences if the model misbehaves
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)

    # Attempt to repair truncated JSON
    text = _repair_truncated_json(text)
    return json.loads(text)
