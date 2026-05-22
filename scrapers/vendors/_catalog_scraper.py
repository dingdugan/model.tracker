"""Reusable base for vendors that publish a stable model catalog + pricing page.

Pattern:
  class FooScraper(CatalogVendorScraper):
      vendor_id = "foo"
      pricing_url = "https://foo.com/pricing"
      catalog = [ModelRecord(...), ...]
      fallback_prices = {"slug": (input, output, cached, currency), ...}

`scrape()` will:
  1. Emit every model in `catalog`.
  2. Try fetching `pricing_url` and running LLM extraction over it.
  3. Backfill any model lacking a live price with `fallback_prices`.

Override `live_scrape()` for custom selector-first logic.
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Optional

from ..core.base import VendorScraper
from ..core.extractor import fetch_static
from ..core.schema import ModelRecord, PriceRecord, ScrapeResult
from ._helpers import llm_fallback_into_result


class CatalogVendorScraper(VendorScraper):
    vendor_id: ClassVar[str] = ""
    pricing_url: ClassVar[Optional[str]] = None
    catalog: ClassVar[list[ModelRecord]] = []
    fallback_prices: ClassVar[dict[str, tuple]] = {}        # slug -> (in, out, cached?, currency?)
    use_playwright: ClassVar[bool] = False                  # set True for SPA pricing pages

    def live_scrape(self, result: ScrapeResult) -> None:
        """Default: fetch pricing page (static or rendered) and run LLM fallback."""
        if not self.pricing_url:
            return
        try:
            if self.use_playwright:
                from ..core.extractor import fetch_rendered
                html = fetch_rendered(self.pricing_url).html
            else:
                html = fetch_static(self.pricing_url).html
        except Exception:
            return
        try:
            llm_fallback_into_result(
                result=result,
                html=html,
                source_url=self.pricing_url,
                vendor_id=self.vendor_id,
            )
        except Exception:
            return

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(vendor_id=self.vendor_id)
        for m in self.catalog:
            result.models.append(m)

        self.live_scrape(result)

        existing_model_ids = {p.model_id for p in result.prices}
        today = date.today()
        for m in self.catalog:
            if m.id in existing_model_ids:
                continue
            fb = self.fallback_prices.get(m.slug)
            if not fb:
                continue
            in_p   = fb[0] if len(fb) > 0 else None
            out_p  = fb[1] if len(fb) > 1 else None
            cache_p = fb[2] if len(fb) > 2 else None
            currency = fb[3] if len(fb) > 3 else "USD"
            result.prices.append(
                PriceRecord(
                    model_id=m.id,
                    input_per_mtok=in_p,
                    output_per_mtok=out_p,
                    cached_input_per_mtok=cache_p,
                    currency=currency,
                    effective_date=today,
                    source_url=self.pricing_url,
                )
            )
        return result
