-- model.tracker initial schema
-- Run this in Supabase SQL Editor

set check_function_bodies = off;

create extension if not exists "pgcrypto";

-- ───────────────────────────────────────────────────────────────────────────
-- vendors
-- ───────────────────────────────────────────────────────────────────────────
create table if not exists vendors (
  id              text primary key,                 -- slug: 'openai', 'anthropic', 'qwen'
  name            text not null,                    -- display: 'OpenAI', '通义千问'
  country         text not null,                    -- ISO-3166 alpha-2: 'US', 'CN', 'FR'
  website         text,
  homepage_url    text,
  pricing_url     text,
  models_url      text,
  blog_url        text,
  is_open_source  boolean not null default false,
  logo_url        text,
  created_at      timestamptz not null default now()
);

-- ───────────────────────────────────────────────────────────────────────────
-- models
-- ───────────────────────────────────────────────────────────────────────────
create table if not exists models (
  id                  text primary key,             -- 'openai/gpt-5', 'anthropic/claude-opus-4-7'
  vendor_id           text not null references vendors(id) on delete cascade,
  slug                text not null,                -- 'gpt-5', 'claude-opus-4-7'
  name                text not null,                -- 'GPT-5'
  family              text,                         -- 'gpt', 'claude', 'gemini', 'qwen'
  release_date        date,
  context_window      integer,                      -- tokens
  max_output_tokens   integer,
  modalities          text[] not null default array['text']::text[],
  is_open_weight      boolean not null default false,
  parameters_b        numeric,                      -- billions; null if not disclosed
  status              text not null default 'active',  -- 'active' | 'preview' | 'deprecated' | 'retired'
  announcement_url    text,
  description         text,
  first_seen          timestamptz not null default now(),
  last_seen           timestamptz not null default now(),
  unique (vendor_id, slug)
);

create index if not exists models_vendor_idx on models(vendor_id);
create index if not exists models_status_idx on models(status);
create index if not exists models_release_idx on models(release_date desc);

-- ───────────────────────────────────────────────────────────────────────────
-- prices  (append-only price snapshots)
-- ───────────────────────────────────────────────────────────────────────────
create table if not exists prices (
  id                      bigserial primary key,
  model_id                text not null references models(id) on delete cascade,
  input_per_mtok          numeric,                  -- USD per million input tokens
  output_per_mtok         numeric,
  cached_input_per_mtok   numeric,                  -- prompt-cache hit price
  cache_write_per_mtok    numeric,                  -- some vendors charge for cache writes
  batch_input_per_mtok    numeric,                  -- batch API discount
  batch_output_per_mtok   numeric,
  currency                text not null default 'USD',
  effective_date          date not null,            -- when this price took effect
  source_url              text,
  scraped_at              timestamptz not null default now()
);

create index if not exists prices_model_date_idx on prices(model_id, effective_date desc);

-- ───────────────────────────────────────────────────────────────────────────
-- benchmark_scores  (append-only)
-- ───────────────────────────────────────────────────────────────────────────
create table if not exists benchmark_scores (
  id              bigserial primary key,
  model_id        text not null references models(id) on delete cascade,
  benchmark_name  text not null,                    -- 'arena-elo', 'mmlu', 'gpqa', 'humaneval', 'swe-bench-verified', 'math', 'mmlu-pro'
  score           numeric not null,
  score_unit      text not null,                    -- 'elo', 'pct', 'pass@1'
  score_max       numeric,                          -- null for elo, 100 for pct
  source          text not null,                    -- 'lmsys', 'artificial-analysis', 'official', 'papers-with-code'
  source_url      text,
  measured_at     date,
  scraped_at      timestamptz not null default now()
);

create index if not exists bench_model_idx on benchmark_scores(model_id);
create index if not exists bench_name_score_idx on benchmark_scores(benchmark_name, score desc);

-- ───────────────────────────────────────────────────────────────────────────
-- daily_snapshots  (one row per day)
-- ───────────────────────────────────────────────────────────────────────────
create table if not exists daily_snapshots (
  snapshot_date   date primary key,
  vendors_count   integer not null,
  models_count    integer not null,
  active_count    integer not null,
  new_models      jsonb not null default '[]'::jsonb,    -- [{id, name, vendor}]
  price_changes   jsonb not null default '[]'::jsonb,    -- [{model_id, field, old, new}]
  status_changes  jsonb not null default '[]'::jsonb,    -- [{model_id, old_status, new_status}]
  bench_changes   jsonb not null default '[]'::jsonb,    -- [{model_id, benchmark, old, new}]
  created_at      timestamptz not null default now()
);

-- ───────────────────────────────────────────────────────────────────────────
-- scrape_errors
-- ───────────────────────────────────────────────────────────────────────────
create table if not exists scrape_errors (
  id            bigserial primary key,
  vendor_id     text,                               -- nullable: benchmark scrapers don't have a vendor
  benchmark     text,
  stage         text not null,                      -- 'fetch' | 'parse' | 'llm-fallback' | 'persist'
  error_class   text,
  message       text not null,
  traceback     text,
  url           text,
  occurred_at   timestamptz not null default now()
);

create index if not exists scrape_errors_recent_idx on scrape_errors(occurred_at desc);

-- ───────────────────────────────────────────────────────────────────────────
-- Views for the frontend
-- ───────────────────────────────────────────────────────────────────────────

-- Current price for each model (latest by effective_date)
create or replace view current_prices as
select distinct on (model_id)
  model_id,
  input_per_mtok,
  output_per_mtok,
  cached_input_per_mtok,
  cache_write_per_mtok,
  batch_input_per_mtok,
  batch_output_per_mtok,
  currency,
  effective_date,
  source_url,
  scraped_at
from prices
order by model_id, effective_date desc, scraped_at desc;

-- Current score per (model, benchmark) — latest scrape wins
create or replace view current_benchmarks as
select distinct on (model_id, benchmark_name)
  model_id,
  benchmark_name,
  score,
  score_unit,
  score_max,
  source,
  source_url,
  measured_at,
  scraped_at
from benchmark_scores
order by model_id, benchmark_name, coalesce(measured_at, scraped_at::date) desc, scraped_at desc;

-- Models with vendor + current price + arena elo joined, for the main listing
create or replace view models_overview as
select
  m.id,
  m.vendor_id,
  v.name              as vendor_name,
  v.country           as vendor_country,
  m.slug,
  m.name,
  m.family,
  m.release_date,
  m.context_window,
  m.max_output_tokens,
  m.modalities,
  m.is_open_weight,
  m.parameters_b,
  m.status,
  m.announcement_url,
  m.description,
  cp.input_per_mtok,
  cp.output_per_mtok,
  cp.cached_input_per_mtok,
  cp.currency,
  cp.effective_date   as price_effective_date,
  cb.score            as arena_elo,
  m.first_seen,
  m.last_seen
from models m
join vendors v on v.id = m.vendor_id
left join current_prices cp on cp.model_id = m.id
left join current_benchmarks cb on cb.model_id = m.id and cb.benchmark_name = 'arena-elo';

-- ───────────────────────────────────────────────────────────────────────────
-- Row-Level Security: public read, service-role writes
-- ───────────────────────────────────────────────────────────────────────────
alter table vendors             enable row level security;
alter table models              enable row level security;
alter table prices              enable row level security;
alter table benchmark_scores    enable row level security;
alter table daily_snapshots     enable row level security;
alter table scrape_errors       enable row level security;

-- Anonymous read for everything except scrape_errors (operational data)
create policy "public read vendors"          on vendors             for select using (true);
create policy "public read models"           on models              for select using (true);
create policy "public read prices"           on prices              for select using (true);
create policy "public read benchmarks"       on benchmark_scores    for select using (true);
create policy "public read snapshots"        on daily_snapshots     for select using (true);

-- service_role bypasses RLS automatically; no policy needed for writes
