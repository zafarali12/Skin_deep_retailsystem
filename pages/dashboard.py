"""
pages/dashboard.py — Sales Dashboard page.
"""
from business import fmt_money, fmt_pkr
from db import sb_get
from templates.base import html_page
from templates.components import (
    kpi_card, kpi_grid, page_header, card_titled, table, invoice_type_badge
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
        kpi_card("Total Units",      fmt_money(total_units)),
        kpi_card("Total Sales",      fmt_pkr(total_sales),  accent=True),
        kpi_card("Sales Tax (GST)",  fmt_pkr(total_tax)),
        kpi_card("Store Commission", fmt_pkr(total_comm)),
        kpi_card("Total Discount",   fmt_pkr(total_disc)),
    )

    recent_table = table(
        ["#", "Date", "Retailer", "Outlet", "Type", "Units", "Value", ""],
        recent_rows,
        "No invoices yet.",
    )

    body = (
        page_header("Sales Dashboard", '<a href="/invoice" class="btn btn-primary">+ Create Invoice</a>')
        + kpis
        + card_titled("Retailer Summary", retailer_summary(), "mb-4")
        + card_titled("Recent Invoices",  recent_table)
    )
    return html_page("Dashboard", body, "dashboard")
