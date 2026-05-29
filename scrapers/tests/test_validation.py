"""Tests for the value-anomaly gates (core/validation.py)."""

from __future__ import annotations

from scrapers.core.validation import PRICE_FACTOR, elo_anomaly, price_anomaly


def test_normal_price_moves_pass():
    assert price_anomaly(5.0, 3.0) is None       # a real price cut
    assert price_anomaly(3.0, 5.0) is None        # a real increase
    assert price_anomaly(15.0, 6.0) is None       # 2.5× drop, within tolerance
    assert price_anomaly(10.0, 10.0) is None


def test_exactly_3x_is_flagged_both_directions():
    # the flip-flop was ±3×; the gate must catch both directions at the boundary
    assert price_anomaly(5.0, 15.0) is not None   # ×3 up
    assert price_anomaly(15.0, 5.0) is not None    # ÷3 down


def test_egregious_price_jumps_flagged():
    assert price_anomaly(5.0, 50.0) is not None   # ×10 parse error
    assert price_anomaly(5.0, 0.5) is not None     # ÷10
    assert price_anomaly(1.0, 1.0 * PRICE_FACTOR + 0.1) is not None


def test_price_gate_ignores_null_and_zero():
    assert price_anomaly(None, 50.0) is None       # first price
    assert price_anomaly(5.0, None) is None
    assert price_anomaly(0.0, 5.0) is None          # from free
    assert price_anomaly(5.0, 0.0) is None          # to free (handled as ordinary change)


def test_the_flip_flop_would_be_caught():
    # the real incident: $5 → $15 is ×3 → flagged (would be quarantined)
    assert price_anomaly(5.0, 15.0) is not None


def test_elo_anomaly():
    assert elo_anomaly(1450.0, 1460.0) is None     # normal drift
    assert elo_anomaly(1450.0, 1400.0) is None      # -50 ok
    assert elo_anomaly(1450.0, 1600.0) is not None  # +150 implausible
    assert elo_anomaly(1450.0, 1300.0) is not None  # -150 implausible
    assert elo_anomaly(None, 1500.0) is None        # first measurement
