"""
pages/dashboard.py â€” Sales Dashboard page.
"""
from business import fmt_money, fmt_pkr
from db import sb_get
from templates.base import html_page
from templates.components import (
    kpi_card, kpi_grid, page_header, card_titled, table, invoice_type_badge
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_setting(key: str, default: float = 0.0) -> float:
    """Read a single numeric setting from Supabase settings table."""
    rows = sb_get("settings", {"key": f"eq.{key}", "select": "value"})
    try:
        return float(rows[0]["value"]) if rows else default
    except Exception:
        return default


def _manual_kpi_card(
    card_id: str,
    label: str,
    computed_value: float,
    manual_value: float,
    setting_key: str,
    is_units: bool = False,
    accent: bool = False,
    danger: bool = False,
) -> str:
    """
    KPI card with a pencil-edit button that expands an inline form.
    computed_value = derived figure shown as main metric
    manual_value   = baseline stored in settings, user can update it
    is_units       = True -> plain number, False -> PKR prefix
    """
    if danger:
        color = "color:#e55;"
    elif accent:
        color = "color:var(--accent);"
    else:
        color = ""

    headline   = fmt_money(computed_value)
    prefix     = "" if is_units else "PKR "
    step_val   = "1" if is_units else "0.01"
    stored_val = str(int(manual_value)) if is_units else f"{manual_value:.2f}"
    inp_label  = "Opening Stock (units):" if is_units else "Amount Received (PKR):"
    toggle_js  = f"toggleDashEdit('{card_id}')"

    lines = [
        f"<div class=\"kpi\" style=\"position:relative\" id=\"kpi_{card_id}\">" ,
        f"  <div class=\"kpi-label\">{label}</div>",
        f"  <div class=\"kpi-value\" style=\"{color}\">{prefix}{headline}</div>",
        f"  <button type=\"button\" title=\"Update\" onclick=\"{toggle_js}\""
        f" style=\"position:absolute;top:10px;right:10px;background:none;"
        f"border:none;cursor:pointer;font-size:15px;color:var(--muted);"
        f"padding:2px 6px;border-radius:5px\">&#9998;</button>",
        f"  <div id=\"edit_{card_id}\" style=\"display:none;margin-top:10px;"
        f"border-top:1px solid var(--border);padding-top:10px\">",
        f"    <form method=\"post\" action=\"/dashboard/settings\""
        f" style=\"display:flex;gap:8px;align-items:center;flex-wrap:wrap\">",
        f"      <input type=\"hidden\" name=\"key\" value=\"{setting_key}\">",
        f"      <label style=\"font-size:12px;color:var(--muted)\">{inp_label}</label>",
        f"      <input type=\"number\" name=\"value\" value=\"{stored_val}\""
        f" min=\"0\" step=\"{step_val}\""
        f" style=\"width:130px;padding:5px 8px;border-radius:6px;"
        f"border:1px solid var(--border);background:var(--surface);"
        f"color:var(--text);font-size:13px\" required>",
        f"      <button type=\"submit\" class=\"btn btn-primary btn-sm\">Save</button>",
        f"      <button type=\"button\" class=\"btn btn-outline btn-sm\""
        f" onclick=\"{toggle_js}\">Cancel</button>",
        "    </form>",
        "  </div>",
        "</div>",
    ]
    return "\n".join(lines)


_TOGGLE_SCRIPT = (
    "<script>\n"
    "function toggleDashEdit(id) {\n"
    "  var el = document.getElementById('edit_' + id);\n"
    "  el.style.display = (el.style.display === 'none') ? 'block' : 'none';\n"
    "}\n"
    "</script>"
)


def retailer_summary() -> str:
    invoices = sb_get("invoices", {
        "select": "retailer,total_units,final_value,tax,commission_amount"
    })

    agg: dict[str, dict] = {}
    for r in invoices:
        rt = r["retailer"]
        if rt not in agg:
            agg[rt] = {"invoices": 0, "units": 0.0, "sales": 0.0, "tax": 0.0, "commission": 0.0}
        agg[rt]["invoices"]   += 1
        agg[rt]["units"]      += float(r.get("total_units") or 0)
        agg[rt]["sales"]      += float(r.get("final_value") or 0)
        agg[rt]["tax"]        += float(r.get("tax") or 0)
        agg[rt]["commission"] += float(r.get("commission_amount") or 0)

    if not agg:
        return "<p class='muted' style='padding:12px 0'>No sales data yet.</p>"

    rows = [
        f"<tr>"
        f"<td><b>{rt}</b></td>"
        f"<td>{d['invoices']}</td>"
        f"<td>{fmt_money(d['units'])}</td>"
        f"<td>{fmt_pkr(d['sales'])}</td>"
        f"<td>{fmt_pkr(d['tax'])}</td>"
        f"<td>{fmt_pkr(d['commission'])}</td>"
        f"</tr>"
        for rt, d in sorted(agg.items(), key=lambda x: -x[1]["sales"])
    ]
    return table(
        ["Retailer", "Invoices", "Units", "Sales (PKR)", "GST", "Commission"],
        rows,
    )


def dashboard() -> str:
    invoices = sb_get("invoices", {
        "select": "total_units,final_value,tax,discount,commission_amount"
    })

    total_n     = len(invoices)
    total_units = sum(float(r.get("total_units") or 0)       for r in invoices)
    total_sales = sum(float(r.get("final_value") or 0)       for r in invoices)
    total_tax   = sum(float(r.get("tax") or 0)               for r in invoices)
    total_disc  = sum(float(r.get("discount") or 0)          for r in invoices)
    total_comm  = sum(float(r.get("commission_amount") or 0) for r in invoices)

    # ── Manual KPI baselines ─────────────────────────────────────────────────
    opening_stock   = _get_setting("opening_stock")    # units, entered manually
    received_amount = _get_setting("received_amount")  # PKR, entered manually
    stock_in_hand    = opening_stock - total_units     # remaining units
    outstanding_recv = total_sales - received_amount   # PKR still unpaid

    recent = sb_get("invoices", {"order": "id.desc", "limit": "8"})

    recent_rows = [
        f"<tr>"
        f"<td><b>#{r['invoice_no']}</b></td>"
        f"<td>{r['invoice_date']}</td>"
        f"<td>{r['retailer']}</td>"
        f"<td>{r['outlet']}</td>"
        f"<td>{invoice_type_badge(r['invoice_type'])}</td>"
        f"<td>{fmt_money(r['total_units'])}</td>"
        f"<td class='text-right'>{fmt_pkr(r['final_value'])}</td>"
        f"<td><a href='/invoice/{r['id']}/xlsx' class='btn btn-sm btn-success'>&#11015; Excel</a></td>"
        f"</tr>"
        for r in recent
    ]

    kpis = kpi_grid(
        kpi_card("Total Invoices",   str(total_n)),
        kpi_card("Total Units Sold", fmt_money(total_units)),
        kpi_card("Total Sales",      fmt_pkr(total_sales),  accent=True),
        kpi_card("Sales Tax (GST)",  fmt_pkr(total_tax)),
        kpi_card("Store Commission", fmt_pkr(total_comm)),
        kpi_card("Total Discount",   fmt_pkr(total_disc)),
    )

    # ── Manual KPI row (editable inline) ─────────────────────────────────────
    manual_kpis = (
        "<div class='kpi-grid' style='margin-bottom:24px'>"
        + _manual_kpi_card(
            card_id="stock",
            label="In-Hand Stock (Units)",
            computed_value=stock_in_hand,
            manual_value=opening_stock,
            setting_key="opening_stock",
            is_units=True,
            accent=(stock_in_hand > 0),
            danger=(stock_in_hand < 0),
        )
        + _manual_kpi_card(
            card_id="recv",
            label="Outstanding Receivables",
            computed_value=outstanding_recv,
            manual_value=received_amount,
            setting_key="received_amount",
            is_units=False,
            danger=(outstanding_recv > 0),
        )
        + "</div>"
        + _TOGGLE_SCRIPT
    )

    recent_table = table(
        ["#", "Date", "Retailer", "Outlet", "Type", "Units", "Value", ""],
        recent_rows,
        "No invoices yet.",
    )

    body = (
        page_header("Sales Dashboard", '<a href="/invoice" class="btn btn-primary">+ Create Invoice</a>')
        + kpis
        + manual_kpis
        + card_titled("Retailer Summary", retailer_summary(), "mb-4")
        + card_titled("Recent Invoices",  recent_table)
    )
    return html_page("Dashboard", body, "dashboard")
