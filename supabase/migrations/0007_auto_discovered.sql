-- ───────────────────────────────────────────────────────────────────────────
-- Phase E — auto-promotion from vendor Models APIs
--
-- A model can now originate two ways:
--   * curated      — hand-written in a vendor catalog (rich metadata, CI-checked)
--   * auto_discovered — created automatically from a vendor's OWN official Models
--     API (authoritative: cannot hallucinate, cannot cross-vendor contaminate),
--     starting sparse and enriched by the normal price/benchmark scrapers.
--
-- Only high-trust vendor-API sightings auto-promote. Noisy leaderboard names
-- (arena/AA) never do — they stay in discovery_candidates for optional review.
-- ───────────────────────────────────────────────────────────────────────────

alter table models
  add column if not exists auto_discovered boolean not null default false;

-- Rebuild models_overview to expose the new flag (the site shows an "auto" badge
-- and the data-health page lists auto-discovered models pending enrichment).
drop view if exists models_overview;
create view models_overview as
select
  m.id, m.vendor_id, v.name as vendor_name, v.country as vendor_country,
  m.slug, m.name, m.family, m.release_date, m.context_window, m.max_output_tokens,
  m.modalities, m.is_open_weight, m.parameters_b, m.license, m.status,
  m.announcement_url, m.description, m.auto_discovered,
  cp.input_per_mtok, cp.output_per_mtok, cp.cached_input_per_mtok, cp.currency,
  cp.effective_date as price_effective_date,
  cb_overall.score as arena_elo,
  cb_coding.score  as arena_elo_coding,
  cb_vision.score  as arena_elo_vision,
  m.first_seen, m.last_seen
from models m
join vendors v              on v.id = m.vendor_id
left join current_prices cp on cp.model_id = m.id
left join current_benchmarks cb_overall on cb_overall.model_id = m.id and cb_overall.benchmark_name = 'arena-elo'
left join current_benchmarks cb_coding  on cb_coding.model_id  = m.id and cb_coding.benchmark_name  = 'arena-elo-coding'
left join current_benchmarks cb_vision  on cb_vision.model_id  = m.id and cb_vision.benchmark_name  = 'arena-elo-vision';
