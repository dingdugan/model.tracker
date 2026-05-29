-- ───────────────────────────────────────────────────────────────────────────
-- Phase B — Discovery layer
--
-- discovery_candidates: model names seen "in the wild" (vendor Models APIs,
-- benchmark leaderboards) that do NOT resolve to any model in our registry.
-- The discovery layer ONLY proposes — it never writes to `models`. A human (or
-- a future high-confidence auto-rule) promotes a candidate by adding it to the
-- relevant vendor catalog, after which it stops being reported.
--
-- This single table covers both signals the design called "discovery_candidates"
-- (from vendor APIs/pages) and "unresolved_observations" (names dropped during
-- benchmark/price ingestion): same schema, same review workflow, distinguished
-- by the `source` column (e.g. 'vendor-api:anthropic' vs 'benchmark:lmsys').
-- ───────────────────────────────────────────────────────────────────────────

create table if not exists discovery_candidates (
  id            bigserial primary key,
  source        text        not null,          -- 'vendor-api:anthropic' | 'benchmark:lmsys' | ...
  reported_name text        not null,          -- raw name/id exactly as the source reported it
  normalized    text        not null,          -- canon(reported_name)
  vendor_guess  text,                           -- best-effort vendor id, nullable
  occurrences   integer     not null default 1, -- how many runs have seen it
  first_seen    timestamptz not null default now(),
  last_seen     timestamptz not null default now(),
  status        text        not null default 'new'
                  check (status in ('new', 'promoted', 'dismissed')),
  raw_context   jsonb,
  notes         text,
  unique (source, normalized)
);

create index if not exists discovery_candidates_status_idx on discovery_candidates (status);
create index if not exists discovery_candidates_last_seen_idx on discovery_candidates (last_seen desc);

-- Surface discovered candidates in the daily snapshot / changelog feed.
alter table daily_snapshots
  add column if not exists discovery_candidates jsonb not null default '[]'::jsonb;

-- RLS: public read (so the site's data-health surface can show them), service-role writes.
alter table discovery_candidates enable row level security;
create policy "public read discovery_candidates"
  on discovery_candidates for select using (true);
