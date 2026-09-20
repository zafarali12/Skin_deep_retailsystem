"""
exports/excel.py — All Excel file generation.

Three public functions:
  make_invoice_xlsx(inv_id)       → bytes  (single invoice)
  make_all_invoices_xlsx()        → bytes  (summary + per-invoice sheets)
  make_product_report_xlsx(filter)→ bytes  (product analytics, 3 sheets)
"""
import io

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

from config import SUPPLIER, RETAILERS, GST_RATE
from business import has_gst
from db import sb_get


# ── Style helpers ─────────────────────────────────────────────────────────────

def _thin_border() -> Border:
    s = Side(style="thin")
    return Border(left=s, right=s, top=s, bottom=s)

def _hdr_fill()  -> PatternFill: return PatternFill("solid", fgColor="17202A")
def _sub_fill()  -> PatternFill: return PatternFill("solid", fgColor="2C3E50")
def _alt_fill(i: int) -> PatternFill | None:
    return PatternFill("solid", fgColor="F8F9FA") if i % 2 == 0 else None

BOLD       = Font(bold=True)
BOLD13     = Font(bold=True, size=13)
BOLD14     = Font(bold=True, size=14)
HDR_FONT   = Font(bold=True, color="FFFFFF")
SUB_FONT   = Font(bold=True, color="A78BFA")
CENTER     = Alignment(horizontal="center", vertical="center")
RIGHT      = Alignment(horizontal="right")
NUM_FMT    = "#,##0.00"

def _set_hdr(cell, text: str) -> None:
    cell.value = text
    cell.font = HDR_FONT
    cell.fill = _hdr_fill()
    cell.border = _thin_border()
    cell.alignment = CENTER

def _set_col_widths(ws, widths: list[int]) -> None:
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ── Single Invoice Excel ──────────────────────────────────────────────────────

def make_invoice_xlsx(inv_id: int) -> bytes:
    inv_list = sb_get("invoices", {"id": f"eq.{inv_id}"})
    if not inv_list:
        raise ValueError(f"Invoice #{inv_id} not found.")
    inv   = inv_list[0]
    items = sb_get("invoice_items", {"invoice_id": f"eq.{inv_id}", "order": "id.asc"})

    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice"

    # Header block
    ws["A1"] = SUPPLIER["name"];      ws["A1"].font = BOLD14; ws.merge_cells("A1:H1")
    ws["A2"] = SUPPLIER["address"];                            ws.merge_cells("A2:H2")
    ws["A3"] = f"Sales Tax No: {SUPPLIER['sales_tax_no']}   NTN: {SUPPLIER['ntn']}"
    ws.merge_cells("A3:H3")

    ws["A5"] = "SALES INVOICE";  ws["A5"].font = BOLD14; ws.merge_cells("A5:D5")
    ws["F5"] = "Invoice No:";    ws["F5"].font = BOLD;   ws["G5"] = inv["invoice_no"]
    ws["F6"] = "Date:";          ws["F6"].font = BOLD;   ws["G6"] = str(inv["invoice_date"])
    ws["F7"] = "Invoice Type:";  ws["F7"].font = BOLD;   ws["G7"] = inv["invoice_type"]
    ws["A7"] = "Retailer:";      ws["A7"].font = BOLD;   ws["B7"] = inv["retailer"]
    ws["A8"] = "Outlet:";        ws["A8"].font = BOLD;   ws["B8"] = inv["outlet"]

    # Column headers row 10
    col_hdrs = ["SR #", "HS Code", "Product Description", "Units",
                "Retail Price/Unit", "Line Total (Ex-GST)", "GST %", "Sales Tax Amount"]
    for c, h in enumerate(col_hdrs, 1):
        _set_hdr(ws.cell(10, c), h)

    gst_flag = has_gst(inv["retailer"], inv["invoice_type"])
    for idx, it in enumerate(items, 1):
        gst_amt = round(float(it["line_total"]) * GST_RATE, 2) if gst_flag else 0
        vals    = [
            idx,
            it["hs_code"] if gst_flag else "",
            it["product_name"],
            it["quantity"],
            it["unit_price"],
            it["line_total"],
            "18%" if gst_flag else "",
            gst_amt   if gst_flag else "",
        ]
        alt = _alt_fill(idx)
        for c, v in enumerate(vals, 1):
            cell = ws.cell(10 + idx, c, v)
            cell.border = _thin_border()
            if alt:
                cell.fill = alt
            if c in (4, 5, 6, 8) and isinstance(v, (int, float)):
                cell.number_format = NUM_FMT

    # Totals block
    row = 11 + len(items)
    totals = [
        ("Total Units",           inv["total_units"]),
        ("Gross Value (Ex-Disc)", inv["gross_value"]),
        ("Discount",              inv["discount"]),
        ("Taxable Value",         inv["taxable_value"]),
        ("Sales Tax (18% GST)",   inv["tax"]),
        ("Total Value Incl. GST", inv["value_with_tax"]),
        ("Store Commission",      inv["commission_amount"] or 0),
        ("Final Invoice Value",   inv["final_value"]),
    ]
    for label, val in totals:
        lc = ws.cell(row, 5, label); lc.font = BOLD; lc.alignment = RIGHT
        vc = ws.cell(row, 6, float(val) if val is not None else 0)
        vc.number_format = NUM_FMT
        row += 1

    _set_col_widths(ws, [6, 15, 48, 10, 18, 20, 10, 20])
    return _wb_bytes(wb)


# ── All Invoices Excel ────────────────────────────────────────────────────────

def make_all_invoices_xlsx() -> bytes:
    """Summary sheet + one sheet per invoice."""
    invoices = sb_get("invoices", {"order": "invoice_no.asc", "limit": "2000"})
    wb = Workbook()

    # ── Sheet 1: Summary ──
    ws = wb.active
    ws.title = "All Invoices"
    hdrs = ["Invoice #", "Date", "Retailer", "Outlet", "Type", "Units",
            "Gross", "Discount", "Taxable", "GST", "Incl. GST", "Commission", "Final Value"]
    for c, h in enumerate(hdrs, 1):
        _set_hdr(ws.cell(1, c), h)

    for ri, inv in enumerate(invoices, 2):
        vals = [
            inv["invoice_no"], str(inv["invoice_date"]), inv["retailer"], inv["outlet"],
            inv["invoice_type"], float(inv.get("total_units") or 0),
            float(inv.get("gross_value") or 0),   float(inv.get("discount") or 0),
            float(inv.get("taxable_value") or 0), float(inv.get("tax") or 0),
            float(inv.get("value_with_tax") or 0), float(inv.get("commission_amount") or 0),
            float(inv.get("final_value") or 0),
        ]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(ri, c, v)
            cell.border = _thin_border()
            if c >= 6:
                cell.number_format = NUM_FMT
    _set_col_widths(ws, [12, 14, 16, 22, 16, 10, 14, 12, 14, 12, 14, 14, 14])

    # ── One sheet per invoice ──
    for inv in invoices:
        inv_items  = sb_get("invoice_items", {"invoice_id": f"eq.{inv['id']}", "order": "id.asc"})
        sheet_name = f"#{inv['invoice_no']} {inv['retailer']}"[:31]
        ws2 = wb.create_sheet(title=sheet_name)

        ws2["A1"] = SUPPLIER["name"];     ws2["A1"].font = BOLD13; ws2.merge_cells("A1:G1")
        ws2["A2"] = SUPPLIER["address"];                            ws2.merge_cells("A2:G2")
        ws2["A3"] = f"Sales Tax No: {SUPPLIER['sales_tax_no']}   NTN: {SUPPLIER['ntn']}"
        ws2.merge_cells("A3:G3")

        for row, (lbl, val) in enumerate([
            ("Invoice No:", inv["invoice_no"]), ("Date:", str(inv["invoice_date"])),
            ("Retailer:",   inv["retailer"]),   ("Outlet:",  inv["outlet"]),
            ("Type:",       inv["invoice_type"]),
        ], 5):
            ws2.cell(row, 1, lbl).font = BOLD
            ws2.cell(row, 2, val)

        for c, h in enumerate(["SR #", "Product", "Qty", "Unit Price", "Line Total", "GST%", "GST Amt"], 1):
            _set_hdr(ws2.cell(11, c), h)

        gst_flag = has_gst(inv["retailer"], inv["invoice_type"])
        for idx, it in enumerate(inv_items, 1):
            gst_amt = round(float(it["line_total"]) * GST_RATE, 2) if gst_flag else 0
            for c, v in enumerate([
                idx, it["product_name"], float(it["quantity"]), float(it["unit_price"]),
                float(it["line_total"]), "18%" if gst_flag else "", gst_amt if gst_flag else ""
            ], 1):
                cell = ws2.cell(11 + idx, c, v)
                cell.border = _thin_border()
                if c in (3, 4, 5, 7) and isinstance(v, float):
                    cell.number_format = NUM_FMT

        sr = 13 + len(inv_items)
        for lbl, val in [
            ("Total Units",    inv["total_units"]),    ("Gross Value",   inv["gross_value"]),
            ("Discount",       inv["discount"]),        ("Taxable Value", inv["taxable_value"]),
            ("GST (18%)",      inv["tax"]),             ("Incl. GST",     inv["value_with_tax"]),
            ("Commission",     inv["commission_amount"] or 0), ("Final Value", inv["final_value"]),
        ]:
            ws2.cell(sr, 4, lbl).font = BOLD
            vc = ws2.cell(sr, 5, float(val) if val is not None else 0)
            vc.number_format = NUM_FMT
            sr += 1

        _set_col_widths(ws2, [6, 44, 10, 14, 14, 8, 12])

    return _wb_bytes(wb)


# ── Product Analytics Excel ───────────────────────────────────────────────────

def make_product_report_xlsx(product_filter: str | None = None) -> bytes:
    """
    3-sheet product report:
      Sheet 1 — Product Summary (totals per product)
      Sheet 2 — Outlet Breakdown (product → outlet rows)
      Sheet 3 — Transaction Detail (every line item)
    """
    items    = sb_get("invoice_items", {
        "select": "product_name,quantity,unit_price,line_total,invoice_id", "limit": "5000"
    })
    invoices = sb_get("invoices", {"select": "id,retailer,outlet,invoice_date,invoice_no", "limit": "2000"})
    inv_map  = {inv["id"]: inv for inv in invoices}

    agg: dict  = {}
    detail: list = []

    for it in items:
        pname = it["product_name"]
        if product_filter and product_filter.lower() not in pname.lower():
            continue
        inv      = inv_map.get(it["invoice_id"], {})
        retailer = inv.get("retailer", "")
        outlet   = inv.get("outlet",   "")
        ok       = f"{retailer} \u2013 {outlet}" if outlet else retailer
        qty      = float(it.get("quantity") or 0)
        rev      = float(it.get("line_total") or 0)

        if pname not in agg:
            agg[pname] = {"qty": 0.0, "revenue": 0.0, "outlets": {}}
        agg[pname]["qty"]     += qty
        agg[pname]["revenue"] += rev
        if ok not in agg[pname]["outlets"]:
            agg[pname]["outlets"][ok] = {"qty": 0.0, "revenue": 0.0}
        agg[pname]["outlets"][ok]["qty"]     += qty
        agg[pname]["outlets"][ok]["revenue"] += rev

        detail.append({
            "product": pname, "invoice_no": inv.get("invoice_no", ""),
            "date": str(inv.get("invoice_date", "")), "retailer": retailer, "outlet": outlet,
            "qty": qty, "unit_price": float(it.get("unit_price") or 0), "revenue": rev,
        })

    wb = Workbook()

    # ── Sheet 1: Product Summary ──
    ws = wb.active
    ws.title = "Product Summary"
    for c, h in enumerate(["Product Name", "Total Units Sold", "Total Revenue (Ex-GST)", "# Outlets"], 1):
        _set_hdr(ws.cell(1, c), h)
    for ri, (pname, d) in enumerate(sorted(agg.items(), key=lambda x: -x[1]["revenue"]), 2):
        for c, v in enumerate([pname, d["qty"], d["revenue"], len(d["outlets"])], 1):
            cell = ws.cell(ri, c, v)
            cell.border = _thin_border()
            if c in (2, 3):
                cell.number_format = NUM_FMT
    _set_col_widths(ws, [60, 18, 24, 12])

    # ── Sheet 2: Outlet Breakdown ──
    ws2 = wb.create_sheet("Outlet Breakdown")
    for c, h in enumerate(["Product", "Retailer \u2013 Outlet", "Units Sold", "Revenue (Ex-GST)"], 1):
        _set_hdr(ws2.cell(1, c), h)
    ri = 2
    for pname, d in sorted(agg.items(), key=lambda x: -x[1]["revenue"]):
        for c in range(1, 5):
            ws2.cell(ri, c).fill = _sub_fill()
            ws2.cell(ri, c).font = SUB_FONT
        ws2.cell(ri, 1, pname)
        ws2.cell(ri, 2, "TOTAL")
        ws2.cell(ri, 3, d["qty"]).number_format     = NUM_FMT
        ws2.cell(ri, 4, d["revenue"]).number_format = NUM_FMT
        ri += 1
        for ok, od in sorted(d["outlets"].items(), key=lambda x: -x[1]["qty"]):
            ws2.cell(ri, 2, ok)
            ws2.cell(ri, 3, od["qty"]).number_format     = NUM_FMT
            ws2.cell(ri, 4, od["revenue"]).number_format = NUM_FMT
            for c in range(1, 5):
                ws2.cell(ri, c).border = _thin_border()
            ri += 1
    _set_col_widths(ws2, [60, 30, 16, 20])

    # ── Sheet 3: Transaction Detail ──
    ws3 = wb.create_sheet("Transaction Detail")
    for c, h in enumerate(["Product", "Invoice #", "Date", "Retailer", "Outlet",
                            "Qty", "Unit Price", "Line Total"], 1):
        _set_hdr(ws3.cell(1, c), h)
    for ri, dr in enumerate(sorted(detail, key=lambda x: x["product"]), 2):
        vals = [dr["product"], dr["invoice_no"], dr["date"], dr["retailer"],
                dr["outlet"], dr["qty"], dr["unit_price"], dr["revenue"]]
        for c, v in enumerate(vals, 1):
            cell = ws3.cell(ri, c, v)
            cell.border = _thin_border()
            if c in (6, 7, 8):
                cell.number_format = NUM_FMT
    _set_col_widths(ws3, [60, 12, 14, 16, 22, 10, 14, 14])

    return _wb_bytes(wb)


# ── Utility ───────────────────────────────────────────────────────────────────

def _wb_bytes(wb: Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
