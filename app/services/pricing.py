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


def apply_bps(cents: int, bps: int) -> int:
    """Half-up rounding on integers; never goes through float."""
    return (cents * bps + 5_000) // 10_000


def find_promo(code: str | None) -> Promo | None:
    if not code:
        return None
    return PROMOS.get(code.strip().upper())


def compute_totals(lines: list[Line], promo: Promo | None, country: str) -> Totals:
    subtotal = sum(line.total for line in lines)

    discount = 0
    if promo and subtotal >= promo.min_subtotal_cents:
        if promo.percent_bps:
            # Round once on the subtotal: per-line rounding drifted up to 1 cent
            # per line and disagreed with the payment gateway's total.
            discount = apply_bps(subtotal, promo.percent_bps)
        elif promo.amount_off_cents:
            discount = min(promo.amount_off_cents, subtotal)

    taxable = subtotal - discount
    tax = apply_bps(taxable, TAX_RATE_BPS.get(country.upper(), 0))
    return Totals(subtotal, discount, tax, taxable + tax)
