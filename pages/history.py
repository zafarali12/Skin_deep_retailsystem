"""
pages/history.py — Invoice History list page with pagination and delete.
"""
import math

from business import fmt_money, fmt_pkr
from db import sb_get, sb_delete
from templates.base import html_page
from templates.components import (
    page_header, card, table, invoice_type_badge,
    search_form, pagination, delete_form,
)

PAGE_SIZE = 25


def invoices_page(search: str = "", page: int = 1) -> str:
    # Build query params
    offset = (page - 1) * PAGE_SIZE
    params: dict = {
        "order":  "id.desc",
        "limit":  str(PAGE_SIZE),
        "offset": str(offset),
    }
    if search:
        params["or"] = f"retailer.ilike.*{search}*,outlet.ilike.*{search}*"

    rows  = sb_get("invoices", params)
    total = _count_invoices(search)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))

    # Extra client-side filter for invoice number search
    if search:
        rows = [
            r for r in rows
            if search.lower() in (r["retailer"] + r["outlet"] + str(r["invoice_no"])).lower()
        ]

    table_rows = []
    for r in rows:
        inv_id   = r["id"]
        inv_no   = r["invoice_no"]
        del_form = delete_form(
            f"/invoice/{inv_id}/delete",
            "&#10005;",
            f"Delete Invoice #{inv_no}? This cannot be undone.",
        )
        table_rows.append(
            f"<tr>"
            f"<td><b>#{inv_no}</b></td>"
            f"<td>{r['invoice_date']}</td>"
            f"<td>{r['retailer']}</td>"
            f"<td>{r['outlet']}</td>"
            f"<td>{invoice_type_badge(r['invoice_type'])}</td>"
            f"<td>{fmt_money(r['total_units'])}</td>"
            f"<td class='text-right'>{fmt_pkr(r['final_value'])}</td>"
            f"<td class='text-right'>{fmt_pkr(r['tax'])}</td>"
            f"<td class='text-right'>{fmt_pkr(r['commission_amount'] or 0)}</td>"
            f"<td>"
            f"<div class='flex gap-2'>"
            f"<a href='/invoice/{inv_id}/edit' class='btn btn-sm btn-outline'>&#9998; Edit</a>"
            f"<a href='/invoice/{inv_id}/xlsx' class='btn btn-sm btn-success'>&#11015; Excel</a>"
            f"{del_form}"
            f"</div>"
            f"</td>"
            f"</tr>"
        )

    # Build pagination extra_qs
    extra_qs = f"q={search}" if search else ""

    invoice_table = table(
        ["#", "Date", "Retailer", "Outlet", "Type", "Units", "Value", "GST", "Commission", ""],
        table_rows,
        "No invoices found.",
    )

    total_label = f'<span class="muted" style="font-size:13px">{total} total</span>'

    body = (
        page_header(
            "Invoice History",
            total_label,
            search_form("/invoices", search, "Search retailer, outlet, #..."),
            '<a href="/invoices/xlsx" class="btn btn-success btn-sm">&#11015; Download All (Excel)</a>',
        )
        + card(invoice_table + pagination(page, total_pages, "/invoices", extra_qs))
    )
    return html_page("Invoice History", body, "invoices")


def _count_invoices(search: str) -> int:
    """Get total invoice count for pagination."""
    params: dict = {}
    if search:
        params["or"] = f"retailer.ilike.*{search}*,outlet.ilike.*{search}*"
    try:
        from db import sb_count
        return sb_count("invoices", params)
    except Exception:
        return PAGE_SIZE  # fallback


def handle_invoice_delete(inv_id: int) -> tuple[bool, str]:
    """Delete an invoice and all its line items."""
    try:
        # Delete items first (foreign key order)
        sb_delete("invoice_items", {"invoice_id": f"eq.{inv_id}"})
        sb_delete("invoices", {"id": f"eq.{inv_id}"})
        return True, "Invoice deleted successfully."
    except Exception as exc:
        return False, str(exc)
