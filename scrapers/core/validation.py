"""Value-anomaly detection — pure logic, no DB.

Attribution can be correct yet the *value* be wrong: a pricing-page parse error
turns $5 into $50, a unit slip makes ELO leap 300 points. These gates flag
egregious changes so they can be quarantined (held in ``pending_changes``) rather
than silently overwriting known-good data.

Thresholds are deliberately loose — normal moves (a real price cut, ELO drift)
must pass untouched; only clearly-broken values trip the gate.
"""

from __future__ import annotations

from typing import Optional

# A price changing by more than this factor in one step is suspicious.
# 3× covers genuine repricings (halving, doubling) without tripping; a parse
# error (×10, ÷10) or unit confusion does trip.
PRICE_FACTOR = 3.0

# ELO is a slow-moving rating; a single-measurement jump beyond this is suspect.
ELO_JUMP = 100.0

# How many consecutive runs a quarantined value must persist before we trust it
# and auto-apply. A transient flip-flop never accumulates; a real change does.
CONFIRM_THRESHOLD = 2


def price_anomaly(old: Optional[float], new: Optional[float]) -> Optional[str]:
    """Return a reason string if old→new is an egregious price move, else None.

    Going to/from null or zero is not treated as anomalous here (first price, or
    a field becoming available) — those are handled as ordinary changes.
    """
    if old is None or new is None:
        return None
    try:
        old_f, new_f = float(old), float(new)
    except (TypeError, ValueError):
        return None
    if old_f <= 0 or new_f <= 0:
        return None
    ratio = new_f / old_f
    if ratio >= PRICE_FACTOR:
        return f"price ×{ratio:.1f} ({old_f}→{new_f})"
    if ratio <= 1.0 / PRICE_FACTOR:
        return f"price ÷{1 / ratio:.1f} ({old_f}→{new_f})"
    return None


def elo_anomaly(old: Optional[float], new: Optional[float]) -> Optional[str]:
    """Return a reason string if old→new is an implausible ELO jump, else None."""
    if old is None or new is None:
        return None
    try:
        old_f, new_f = float(old), float(new)
    except (TypeError, ValueError):
        return None
    if abs(new_f - old_f) > ELO_JUMP:
        return f"elo {old_f:.0f}→{new_f:.0f} (Δ{new_f - old_f:+.0f})"
    return None
