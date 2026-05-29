-- ───────────────────────────────────────────────────────────────────────────
-- Phase C — validation / anomaly gate
--
-- pending_changes: scraped values that are attributed correctly but look wrong
-- (an egregious price jump, an ELO that leapt 100 points). Instead of letting
-- them overwrite known-good data, we quarantine them here and keep the last-good
-- value live. A change is auto-applied once the SAME value persists across
-- `confirm_threshold` runs (a transient bad value never accumulates; a genuine
-- change does). A human can also apply/reject manually.
--
-- This is the defense that would have stopped the $15/$75 price flip-flop from
-- repeatedly overwriting the correct $5/$25.
-- ───────────────────────────────────────────────────────────────────────────

create table if not exists pending_changes (
  id             bigserial primary key,
  kind           text        not null check (kind in ('price', 'benchmark')),
  model_id       text        not null references models(id) on delete cascade,
  field          text        not null,        -- 'input_per_mtok' | 'output_per_mtok' | benchmark_name | ...
  prior_value    numeric,                       -- last known-good value
  proposed_value numeric,                       -- the suspicious new value
  reason         text        not null,          -- why it was quarantined
  occurrences    integer     not null default 1,
  first_seen     timestamptz not null default now(),
  last_seen      timestamptz not null default now(),
  status         text        not null default 'pending'
                   check (status in ('pending', 'applied', 'rejected')),
  source_url     text,
  unique (kind, model_id, field)
);

create index if not exists pending_changes_status_idx on pending_changes (status);

alter table pending_changes enable row level security;
create policy "public read pending_changes"
  on pending_changes for select using (true);
