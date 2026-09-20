"""
pages/reports.py — Monthly Sales Reports page.
"""
from business import fmt_money, fmt_pkr
from db import sb_get
from templates.base import html_page
from templates.components import page_header, card_titled, table


def reports_page() -> str:
    invoices = sb_get("invoices", {
        "select": "invoice_date,total_units,gross_value,discount,taxable_value,tax,value_with_tax,commission_amount",
        "order":  "invoice_date.desc",
    })

    # Aggregate by YYYY-MM
    monthly: dict[str, dict] = {}
    for r in invoices:
        month = str(r["invoice_date"])[:7]
        if month not in monthly:
            monthly[month] = {
                "n": 0, "units": 0.0, "gross": 0.0, "discount": 0.0,
                "ex_tax": 0.0, "tax": 0.0, "incl_tax": 0.0, "commission": 0.0,
            }
        d = monthly[month]
        d["n"]          += 1
        d["units"]      += float(r.get("total_units")      or 0)
        d["gross"]      += float(r.get("gross_value")      or 0)
        d["discount"]   += float(r.get("discount")         or 0)
        d["ex_tax"]     += float(r.get("taxable_value")    or 0)
        d["tax"]        += float(r.get("tax")              or 0)
        d["incl_tax"]   += float(r.get("value_with_tax")   or 0)
        d["commission"] += float(r.get("commission_amount") or 0)

    rows = [
        f"<tr>"
        f"<td><b>{m}</b></td>"
        f"<td>{d['n']}</td>"
        f"<td>{fmt_money(d['units'])}</td>"
        f"<td>{fmt_pkr(d['gross'])}</td>"
        f"<td>{fmt_pkr(d['discount'])}</td>"
        f"<td>{fmt_pkr(d['ex_tax'])}</td>"
        f"<td>{fmt_pkr(d['tax'])}</td>"
        f"<td>{fmt_pkr(d['incl_tax'])}</td>"
        f"<td>{fmt_pkr(d['commission'])}</td>"
        f"</tr>"
        for m in sorted(monthly, reverse=True)
        for d in [monthly[m]]
    ]

    monthly_table = table(
        ["Month", "Invoices", "Units", "Gross", "Discount", "Ex-GST", "GST", "Incl-GST", "Commission"],
        rows,
        "No data yet.",
    )

    body = (
        page_header("Reports")
        + card_titled("Monthly Summary", monthly_table)
    )
    return html_page("Reports", body, "reports")
