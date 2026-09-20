"""
business.py — Pure business logic. No HTTP, no HTML, no DB calls.
All functions are stateless and unit-testable.
"""
from dataclasses import dataclass
from config import RETAILERS, GST_RATE


# ── Types ─────────────────────────────────────────────────────────────────────

@dataclass
class InvoiceItem:
    product_id:   int | None
    product_name: str
    quantity:     float
    unit_price:   float
    hs_code:      str
    line_total:   float = 0.0

    def __post_init__(self):
        self.line_total = round(self.quantity * self.unit_price, 2)


@dataclass
class InvoiceCalc:
    gross:       float   # sum of line totals (before discount)
    discount:    float
    taxable:     float   # gross - discount
    tax:         float   # GST amount (0 if not taxable)
    with_tax:    float   # taxable + tax
    commission:  float   # retailer cut (info only, not deducted)
    final:       float   # = with_tax  (what supplier receives)
    units:       float   # total quantity across all items


# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_money(x) -> str:
    """Format a number as PKR with commas: 1,234.56"""
    if x is None:
        return "0.00"
    return "{:,.2f}".format(float(x))


def fmt_pkr(x) -> str:
    """PKR-prefixed money string."""
    return f"PKR {fmt_money(x)}"


# ── Core Calculation ──────────────────────────────────────────────────────────

def calc_invoice(retailer: str, items: list[InvoiceItem], discount: float) -> InvoiceCalc:
    """
    Calculate all invoice totals for a given retailer + items + discount.

    Business rules:
    - GST (18%) applies only to taxable retailers.
    - Commission is calculated on (taxable + GST), but is for reporting only
      (the invoice value the supplier collects is with_tax, not with_tax - commission).
    - Dolmen Cart has no commission rate (None).
    """
    r = RETAILERS[retailer]

    gross    = round(sum(it.line_total for it in items), 2)
    taxable  = round(max(gross - discount, 0), 2)
    tax      = round(taxable * GST_RATE, 2) if r["tax"] else 0.0
    with_tax = round(taxable + tax, 2)
    commission = round(with_tax * r["commission"], 2) if r["commission"] is not None else 0.0
    units    = sum(it.quantity for it in items)

    return InvoiceCalc(
        gross=gross,
        discount=round(discount, 2),
        taxable=taxable,
        tax=tax,
        with_tax=with_tax,
        commission=commission,
        final=with_tax,
        units=units,
    )


def has_gst(retailer: str, invoice_type: str) -> bool:
    """True when GST line items should appear on the invoice."""
    return RETAILERS[retailer]["tax"] and invoice_type == "GST Invoice"
