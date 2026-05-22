"""Diff today's scrape against the latest persisted snapshot to produce change feed."""

from __future__ import annotations

from datetime import date
from typing import Any

from .schema import ScrapeResult


ELO_DELTA_THRESHOLD = 5.0
PRICE_DELTA_REL = 0.001  # 0.1% — anything bigger is a real change


def build_snapshot_payload(
    results: list[ScrapeResult],
    *,
    prior_models: dict[str, dict[str, Any]],          # id → {status, ...}
    prior_prices: dict[str, dict[str, Any]],          # id → current_prices row
    today: date,
) -> dict[str, Any]:
    new_models: list[dict[str, Any]] = []
    status_changes: list[dict[str, Any]] = []
    price_changes: list[dict[str, Any]] = []
    bench_changes: list[dict[str, Any]] = []

    seen_model_ids: set[str] = set()

    for r in results:
        for m in r.models:
            seen_model_ids.add(m.id)
            prior = prior_models.get(m.id)
            if prior is None:
                new_models.append(
                    {
                        "id":         m.id,
                        "name":       m.name,
                        "vendor":     m.vendor_id,
                        "release_date": m.release_date.isoformat() if m.release_date else None,
                    }
                )
            elif prior.get("status") != m.status:
                status_changes.append(
                    {
                        "id":         m.id,
                        "old_status": prior.get("status"),
                        "new_status": m.status,
                    }
                )

        for p in r.prices:
            prior = prior_prices.get(p.model_id)
            if prior is None:
                # first time we have a price → counts as a change worth noting
                price_changes.append(
                    {
                        "model_id": p.model_id,
                        "field":    "first_price_recorded",
                        "old":      None,
                        "new":      {"in": p.input_per_mtok, "out": p.output_per_mtok},
                    }
                )
                continue
            for field, new in [
                ("input_per_mtok",        p.input_per_mtok),
                ("output_per_mtok",       p.output_per_mtok),
                ("cached_input_per_mtok", p.cached_input_per_mtok),
            ]:
                old = prior.get(field)
                if _changed(old, new):
                    price_changes.append(
                        {"model_id": p.model_id, "field": field, "old": old, "new": new}
                    )

    payload = {
        "vendors_count": len({r.vendor_id for r in results if r.vendor_id}),
        "models_count":  len(seen_model_ids),
        "active_count":  sum(1 for r in results for m in r.models if m.status == "active"),
        "new_models":    new_models,
        "price_changes": price_changes,
        "status_changes": status_changes,
        "bench_changes": bench_changes,
    }
    return payload


def _changed(old: Any, new: Any) -> bool:
    if old is None and new is None:
        return False
    if old is None or new is None:
        return True
    try:
        a, b = float(old), float(new)
    except (TypeError, ValueError):
        return old != new
    if a == 0 and b == 0:
        return False
    if a == 0 or b == 0:
        return True
    return abs(a - b) / max(abs(a), abs(b)) > PRICE_DELTA_REL
