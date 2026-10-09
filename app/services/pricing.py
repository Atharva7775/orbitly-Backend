"""Order pricing in integer cents. Kept in step with orbitly-frontend src/lib/pricing/totals.ts."""

from dataclasses import dataclass

# Basis points: 100 bps = 1 %.
TAX_RATE_BPS: dict[str, int] = {"US": 0, "CA": 500, "GB": 2000, "DE": 1900, "FR": 2000, "NL": 2100}


@dataclass(frozen=True)
class Promo:
    code: str
    percent_bps: int = 0
    amount_off_cents: int = 0
    min_subtotal_cents: int = 0


PROMOS: dict[str, Promo] = {
    "ORBIT10": Promo("ORBIT10", percent_bps=1000),
    "LAUNCH15": Promo("LAUNCH15", percent_bps=1500, min_subtotal_cents=5_000),
    "SHIPFREE": Promo("SHIPFREE", amount_off_cents=599, min_subtotal_cents=3_500),
}


@dataclass(frozen=True)
class Line:
    unit_price_cents: int
    quantity: int

    @property
    def total(self) -> int:
        return self.unit_price_cents * self.quantity


@dataclass(frozen=True)
class Totals:
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int


# Experimental volume tiers: (minimum quantity, basis points off the unit price).
VOLUME_TIERS: tuple[tuple[int, int], ...] = ((12, 1500), (6, 1000), (3, 500))


def apply_bps(cents: int, bps: int) -> int:
    """Half-up rounding on integers; never goes through float."""
    return (cents * bps + 5_000) // 10_000


def find_promo(code: str | None) -> Promo | None:
    if not code:
        return None
    return PROMOS.get(code.strip().upper())


def tier_bps(quantity: int) -> int:
    for min_qty, bps in VOLUME_TIERS:
        if quantity >= min_qty:
            return bps
    return 0


def compute_totals(lines: list[Line], promo: Promo | None, country: str) -> Totals:
    subtotal = sum(line.total for line in lines)
    tier_savings = sum(apply_bps(line.unit_price_cents, tier_bps(line.quantity)) * line.quantity for line in lines)

    promo_discount = 0
    if promo and subtotal >= promo.min_subtotal_cents:
        if promo.percent_bps:
            promo_discount = apply_bps(subtotal, promo.percent_bps)
        elif promo.amount_off_cents:
            promo_discount = min(promo.amount_off_cents, subtotal)

    # Tiers and promos do not stack: the customer gets whichever saves more.
    discount = max(tier_savings, promo_discount)

    taxable = subtotal - discount
    tax = apply_bps(taxable, TAX_RATE_BPS.get(country.upper(), 0))
    return Totals(subtotal, discount, tax, taxable + tax)
