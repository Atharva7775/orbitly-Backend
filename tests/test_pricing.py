from app.services.pricing import Line, apply_bps, compute_totals, find_promo


def test_apply_bps_rounds_half_up():
    assert apply_bps(1_000, 1000) == 100
    assert apply_bps(5, 1000) == 1  # 0.5 -> 1
    assert apply_bps(4, 1000) == 0


def test_totals_without_promo_us():
    t = compute_totals([Line(1999, 2), Line(500, 1)], None, "US")
    assert (t.subtotal_cents, t.discount_cents, t.tax_cents, t.total_cents) == (4498, 0, 0, 4498)


def test_percent_promo_and_vat():
    t = compute_totals([Line(10_000, 1)], find_promo("orbit10"), "DE")
    assert t.discount_cents == 1_000
    assert t.tax_cents == 1_710
    assert t.total_cents == 10_710


def test_min_subtotal_is_enforced():
    t = compute_totals([Line(1_000, 1)], find_promo("LAUNCH15"), "US")
    assert t.discount_cents == 0


def test_amount_off_never_exceeds_subtotal():
    t = compute_totals([Line(4_000, 1)], find_promo("SHIPFREE"), "US")
    assert t.discount_cents == 599
    assert t.total_cents == 3_401


def test_unknown_promo():
    assert find_promo("NOPE") is None
    assert find_promo(None) is None
