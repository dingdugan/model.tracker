-- Remove is_open_source from vendors (concept belongs at model layer).
-- Add license to models (e.g. 'apache-2.0', 'mit', 'llama-4', 'gemma', 'proprietary').

alter table vendors drop column if exists is_open_source;

alter table models add column if not exists license text;

-- Rebuild models_overview view to include license.
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
  m.license,
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
