-- Remove duplicate benchmark_scores rows, keeping the lowest id in each
-- (model_id, benchmark_name, source, measured_at) group.
--
-- Background: before the Python-side dedupe guard was added (db.py
-- _benchmark_already_recorded), the cron could insert the same row twice.
-- This migration is idempotent — running it on an already-clean DB is safe.

DELETE FROM benchmark_scores
WHERE id NOT IN (
    SELECT MIN(id)
    FROM benchmark_scores
    GROUP BY model_id, benchmark_name, source, measured_at
);
