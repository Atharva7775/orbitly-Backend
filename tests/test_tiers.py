from app.services.pricing import Line, compute_totals, find_promo, tier_bps


def test_tier_thresholds():
    assert tier_bps(1) == 0
    assert tier_bps(3) == 500
    assert tier_bps(6) == 1000
    assert tier_bps(40) == 1500


def test_better_of_tier_or_promo():
    lines = [Line(1_000, 12)]
    # 15 % tier beats ORBIT10's 10 %.
    assert compute_totals(lines, find_promo("ORBIT10"), "US").discount_cents == 1_800
