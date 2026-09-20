"""
pages/analytics.py — Product-level sales analytics across all outlets.
"""
from business import fmt_money, fmt_pkr
from db import sb_get
from templates.base import html_page
from templates.components import page_header, card, table, search_form


def _build_agg(items: list, inv_map: dict) -> dict:
    """Build a product → outlet aggregation dict from invoice_items."""
    agg: dict[str, dict] = {}
    for it in items:
        pname = it["product_name"]
        inv   = inv_map.get(it["invoice_id"], {})
        retailer = inv.get("retailer", "")
        outlet   = inv.get("outlet", "")
        outlet_key = f"{retailer} \u2013 {outlet}" if outlet else retailer

        qty = float(it.get("quantity") or 0)
        rev = float(it.get("line_total") or 0)

        if pname not in agg:
            agg[pname] = {"qty": 0.0, "revenue": 0.0, "outlets": {}}

        agg[pname]["qty"]     += qty
        agg[pname]["revenue"] += rev

        if outlet_key not in agg[pname]["outlets"]:
            agg[pname]["outlets"][outlet_key] = {"qty": 0.0, "revenue": 0.0}
        agg[pname]["outlets"][outlet_key]["qty"]     += qty
        agg[pname]["outlets"][outlet_key]["revenue"] += rev

    return agg


def product_analytics_page(search: str = "") -> str:
    items    = sb_get("invoice_items", {
        "select": "product_name,quantity,unit_price,line_total,invoice_id",
        "limit":  "5000",
    })
    invoices = sb_get("invoices", {"select": "id,retailer,outlet,invoice_date", "limit": "2000"})
    inv_map  = {inv["id"]: inv for inv in invoices}

    agg = _build_agg(items, inv_map)

    if search:
        agg = {k: v for k, v in agg.items() if search.lower() in k.lower()}

    sorted_products = sorted(agg.items(), key=lambda x: -x[1]["revenue"])

    rows = []
    for pname, d in sorted_products:
        pid = abs(hash(pname))

        outlet_rows = "".join(
            f"<tr id='ob_{pid}_{i}' style='display:none;background:rgba(124,106,247,.04)'>"
            f"<td style='padding-left:32px;font-size:12.5px;color:var(--muted)'>&#8627; {ok}</td>"
            f"<td style='font-size:12.5px'>{fmt_money(od['qty'])}</td>"
            f"<td style='font-size:12.5px'>{fmt_pkr(od['revenue'])}</td>"
            f"<td></td>"
            f"</tr>"
            for i, (ok, od) in enumerate(sorted(d["outlets"].items(), key=lambda x: -x[1]["qty"]))
        )

        safe = pname.replace('"', "&quot;").replace("'", "&#39;")
        count = len(d["outlets"])

        rows.append(
            f"<tr style='cursor:pointer' onclick=\"toggleProduct({pid}, {count})\">"
            f"<td><b>{pname}</b> "
            f"<span style='font-size:11px;color:var(--muted)'>"
            f"({count} outlet{'s' if count != 1 else ''}) &#9660;</span></td>"
            f"<td><b>{fmt_money(d['qty'])}</b></td>"
            f"<td><b>{fmt_pkr(d['revenue'])}</b></td>"
            f"<td>"
            f"<a href='/analytics/xlsx?product={safe}' "
            f"class='btn btn-sm btn-success' onclick='event.stopPropagation()'>&#11015; Excel</a>"
            f"</td>"
            f"</tr>"
            + outlet_rows
        )

    toggle_script = """
<script>
function toggleProduct(pid, count) {
  for (let i = 0; i < count; i++) {
    const el = document.getElementById('ob_' + pid + '_' + i);
    if (el) el.style.display = el.style.display === 'none' ? 'table-row' : 'none';
  }
}
</script>"""

    product_table = table(
        ["Product", "Total Units Sold", "Total Revenue (Ex-GST)", ""],
        rows,
        "No product sales data found.",
    )

    body = (
        page_header(
            "Product Analytics",
            search_form("/analytics", search, "Search product name..."),
            '<a href="/analytics/xlsx" class="btn btn-success btn-sm">&#11015; Full Report (Excel)</a>',
        )
        + card(
            '<p class="muted mb-4">Click any product to expand outlet-wise breakdown. Amounts are Ex-GST.</p>'
            + product_table
        )
        + toggle_script
    )
    return html_page("Product Analytics", body, "analytics")
