-- ───────────────────────────────────────────────────────────────────────────
-- Phase D — data-health surfacing
--
-- scrape_errors holds tracebacks / URLs (operational, not public). Expose a
-- sanitized view with only safe columns so the public "Data Health" page can
-- show *that* and *where* something broke, without leaking internals.
-- ───────────────────────────────────────────────────────────────────────────

create or replace view recent_scrape_issues as
select
  stage,
  vendor_id,
  benchmark,
  error_class,
  occurred_at
from scrape_errors
order by occurred_at desc
limit 100;

-- Views run with the owner's rights, so anon selecting this view reads only the
-- safe columns we projected — message/traceback/url are never exposed.
grant select on recent_scrape_issues to anon, authenticated;
