# Contributing

Thanks for considering a contribution.

## Quick start

See [README.md](README.md) for local setup. TL;DR:

```bash
# Frontend
cd apps/web && npm install && npm run dev

# Scrapers
python3 -m venv .venv && source .venv/bin/activate
pip install -r scrapers/requirements.txt
playwright install chromium
python -m scrapers.run --dry-run
```

## Adding a new vendor

1. Create `scrapers/vendors/your_vendor.py` extending `CatalogVendorScraper`
   (see `scrapers/vendors/_catalog_scraper.py`).
2. Add a row to `supabase/seed.sql` so the vendor is known.
3. If the vendor has Arena / Artificial Analysis / academic benchmark scores,
   add name → model_id mappings in `scrapers/benchmarks/_mapping.py`.
4. Run `python -m scrapers.run --dry-run --vendor your_vendor` to validate.

## Updating prices

Prices are append-only history. The scraper writes a new row in `prices` only
when the value changes from the latest snapshot — that way the price chart
stays readable.

If a vendor changes their pricing page structure and the LLM fallback fails,
update the `fallback_prices` dict in that vendor's file.

## Benchmark scores

Academic scores (MMLU / GPQA / HumanEval / SWE-bench / MATH) come from
official vendor announcements. We curate them by hand in
`scrapers/benchmarks/academic.py`. PRs welcome — please link the official
source (vendor blog, paper, system card) in the commit message.

LMSYS Arena and Artificial Analysis are scraped automatically.

## PR guidelines

- One vendor / one benchmark / one feature per PR keeps reviews fast.
- Run `npm run type-check` in `apps/web/` before pushing frontend changes.
- For scraper changes, attach the output of `python -m scrapers.run --dry-run --vendor X`.

## Data ethics

- Don't increase scrape frequency without a good reason — daily is enough.
- Always credit the source in `source_url` on every price / benchmark row.
- Don't use this tool to bulk-mirror vendor docs.
