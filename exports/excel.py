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

from config import SUPPLIER, RETAILERS, GST_RATE, get_buyer_name, get_retailer_info
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


# -- Retailer-Specific Invoice Formats -----------------------------------------


def _m(ws, rng, val, bold=False, size=11, color=None, bg=None):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    c.value = val
    c.alignment = CENTER
    kw = {"bold": bold, "size": size}
    if color: kw["color"] = color
    c.font = Font(**kw)
    if bg: c.fill = PatternFill("solid", fgColor=bg)
    return c


def _fmt_shams(ws, inv, items):
    """
    SD BEAUTY LABS General Invoice (no HS Code).
    Used for Shams, Alfatah, Naheed, and other retailers not in SIMPLE set.
    Columns: SR# | Products Description | Units Sold | Retail Price/Unit RS | Retail Price Ex-Sales Tax | Total (RS)
    Totals: Value Ex-Tax -> Tax 18% -> Total Incl Tax -> Additional Discount -> Total add.Disc -> Discount XX% -> Total After Discount
    """
    b = _thin_border()
    rt    = inv.get("retailer", "")
    rinfo = get_retailer_info(rt)
    comm_rate  = RETAILERS.get(rt, {}).get("commission") or 0
    comm_pct   = int(round(comm_rate * 100))
    disc_label = rinfo["discount_label"] or ("Discount " + str(comm_pct) + "%")

    NL = chr(10)

    # Row 1 - Company name (no dark background - white with border like reference)
    ws.merge_cells("A1:F1")
    ws["A1"].value = SUPPLIER["name"]
    ws["A1"].font  = Font(bold=True, size=15)
    ws["A1"].alignment = CENTER
    ws["A1"].border = b

    # Row 2 - SALES TAX INVOICE
    ws.merge_cells("A2:F2")
    ws["A2"].value = "SALES TAX INVOICE"
    ws["A2"].font  = Font(bold=True, size=11)
    ws["A2"].alignment = CENTER
    ws["A2"].border = b

    # Rows 3-5 Supplier info
    for row, lbl, val in [
        (3, "Supplier Address:", SUPPLIER["address"]),
        (4, "Supplier Sales Tax No.", SUPPLIER["sales_tax_no"]),
        (5, "Supplier NTN no.", SUPPLIER["ntn"]),
    ]:
        ws["A"+str(row)] = lbl
        ws["A"+str(row)].font = BOLD
        ws["A"+str(row)].border = b
        ws.merge_cells("B"+str(row)+":F"+str(row))
        ws["B"+str(row)] = val
        ws["B"+str(row)].border = b

    # Row 6 spacer
    ws.merge_cells("A6:F6")
    ws["A6"].border = b

    # Row 7 - Invoice #
    ws.merge_cells("A7:B7")
    ws["A7"].value = "Invoice # :"
    ws["A7"].font  = Font(bold=True, underline="single")
    ws["A7"].border = b
    ws.merge_cells("C7:F7")
    ws["C7"].value = inv["invoice_no"]
    ws["C7"].alignment = RIGHT
    ws["C7"].font  = Font(bold=True)
    ws["C7"].border = b

    # Row 8 - Buyer Name (outlet as buyer name, matching reference)
    ws.merge_cells("A8:B8")
    ws["A8"].value = "Buyer Name:"
    ws["A8"].font  = Font(bold=True, underline="single")
    ws["A8"].border = b
    ws.merge_cells("C8:F8")
    ws["C8"].value = rinfo["buyer_name"]
    ws["C8"].font  = Font(bold=True, size=13)
    ws["C8"].alignment = CENTER
    ws["C8"].border = b

    # Rows 9-13 buyer details
    for row, lbl, val, ul in [
        (9,  "Buyer NTN No",    rinfo["ntn"],            False),
        (10, "Buyer STRN:",     rinfo["strn"],            True),
        (11, "Buyer Address:",  rinfo["address"],         True),
        (12, "Delivery Outlet:",inv["outlet"],            True),
        (13, "Date:",           str(inv["invoice_date"]), True),
    ]:
        ws.merge_cells("A"+str(row)+":B"+str(row))
        ws["A"+str(row)].value = lbl
        ws["A"+str(row)].font  = Font(underline="single" if ul else "none")
        ws["A"+str(row)].border = b
        ws.merge_cells("C"+str(row)+":F"+str(row))
        ws["C"+str(row)].value = val
        ws["C"+str(row)].alignment = CENTER
        ws["C"+str(row)].border = b

    # Row 14 spacer
    ws.merge_cells("A14:F14")
    ws["A14"].border = b

    # Rows 15-16 Column headers (two-row, NO HS Code column)
    hf    = PatternFill("solid", fgColor="1A1A2E")
    hfont = Font(bold=True, color="FFFFFF", size=10)
    cols_hdr = [
        ("A", "SR #"),
        ("B", "Products Description"),
        ("C", "Units"+NL+"Sold"),
        ("D", "Retail Price/Unit"+NL+"RS"),
        ("E", "Retail Price"+NL+"Ex -Sales Tax"),
        ("F", "Total (RS)"),
    ]
    for col, lbl in cols_hdr:
        ws.merge_cells(col+"15:"+col+"16")
        cc = ws[col+"15"]
        cc.value = lbl
        cc.font  = hfont
        cc.fill  = hf
        cc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cc.border = b

    # Data rows starting at row 17
    start = 17
    for idx, it in enumerate(items, 1):
        row     = start + idx - 1
        retail  = float(it["unit_price"])
        qty     = float(it["quantity"])
        ex_unit = round(retail / (1 + GST_RATE), 2)
        line_ex = round(float(it["line_total"]) / (1 + GST_RATE), 2)
        alt = _alt_fill(idx)
        for c, v in enumerate([idx, it["product_name"], qty, retail, ex_unit, line_ex], 1):
            cell = ws.cell(row, c, v)
            cell.border = b
            if alt: cell.fill = alt
            if c in (3,4,5,6) and isinstance(v,(int,float)):
                cell.number_format = NUM_FMT

    # Totals
    gross_val   = float(inv["gross_value"])
    addl_disc   = float(inv["discount"])
    comm_amt    = float(inv["commission_amount"] or 0)
    ex_tax_disp = round(gross_val / (1 + GST_RATE), 2)
    tax_disp    = round(gross_val - ex_tax_disp, 2)
    after_disc  = round(gross_val - addl_disc, 2)
    total_final = round(after_disc - comm_amt, 2)

    tr = start + len(items)

    # Total Units (value in col C = Units Sold column)
    ws.merge_cells("A"+str(tr)+":B"+str(tr))
    ws["A"+str(tr)].value = "Total Units"
    ws["A"+str(tr)].font  = BOLD
    ws["A"+str(tr)].border = b
    uc = ws.cell(tr, 3, float(inv["total_units"]))
    uc.font = BOLD; uc.number_format = "0"; uc.border = b
    for c in range(4, 7): ws.cell(tr, c).border = b
    tr += 1

    def _tot(r, lbl, val, bold=False):
        ws.merge_cells("A"+str(r)+":E"+str(r))
        lc = ws["A"+str(r)]
        lc.value = lbl
        lc.font  = Font(bold=bold)
        lc.alignment = Alignment(horizontal="right")
        lc.border = b
        if val is None:
            ws["F"+str(r)].value = "-"; ws["F"+str(r)].border = b
        else:
            vc = ws.cell(r, 6, float(val))
            vc.number_format = NUM_FMT
            vc.font = Font(bold=bold)
            vc.border = b

    _tot(tr, "Value Ex - Sales Tax",                        ex_tax_disp); tr+=1
    _tot(tr, "Sales Tax 18 %",                              tax_disp);    tr+=1
    _tot(tr, "Total Value Incl - Sales Tax",                gross_val);   tr+=1
    _tot(tr, "Additional Discount",                         addl_disc if addl_disc else None); tr+=1
    _tot(tr, "Total Value Incl - Sales Tax  add. Discount", after_disc);  tr+=1
    _tot(tr, disc_label,                                    comm_amt);    tr+=1
    _tot(tr, "Total Value After Discount (Rs.)",            total_final, bold=True)

    _set_col_widths(ws, [5, 44, 10, 18, 18, 16])
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 18



def _fmt_simple_restock(ws,inv,items):
    b=_thin_border()
    ws.merge_cells("A1:H3"); ws["A1"].value="SKIN DEEP"
    ws["A1"].font=Font(bold=True,size=22); ws["A1"].alignment=CENTER
    inv_no=inv["invoice_no"]
    ws.merge_cells("A4:C4"); ws["A4"]=f"Sr#  RS-{inv_no}"
    ws["A4"].font=BOLD; ws["A4"].border=b
    ws.merge_cells("D4:H4"); ws["D4"]=str(inv["invoice_date"])
    ws["D4"].alignment=CENTER; ws["D4"].border=b
    ws.merge_cells("A5:C5"); ws["A5"]="Restock"
    ws["A5"].font=BOLD; ws["A5"].alignment=CENTER; ws["A5"].border=b
    oname=(inv["outlet"] or inv["retailer"]).upper()
    ws.merge_cells("D5:H5"); ws["D5"]=oname
    ws["D5"].font=Font(bold=True,size=11); ws["D5"].alignment=CENTER; ws["D5"].border=b
    hf=PatternFill("solid",fgColor="1A1A2E")
    ws.merge_cells("A7:F7"); ws["A7"]="Products"
    ws["A7"].font=Font(bold=True,color="FFFFFF"); ws["A7"].fill=hf
    ws["A7"].alignment=CENTER; ws["A7"].border=b
    ws.merge_cells("G7:H7"); ws["G7"]="Quantity"
    ws["G7"].font=Font(bold=True,color="FFFFFF"); ws["G7"].fill=hf
    ws["G7"].alignment=CENTER; ws["G7"].border=b
    for idx,it in enumerate(items,1):
        row=7+idx; ws.merge_cells(f"A{row}:F{row}")
        ws[f"A{row}"]=it["product_name"]; ws[f"A{row}"].border=b
        ws.merge_cells(f"G{row}:H{row}")
        qc=ws[f"G{row}"]; qc.value=float(it["quantity"])
        qc.alignment=CENTER; qc.border=b; qc.number_format="0"
    for extra in range(len(items)+1,len(items)+9):
        row=7+extra; ws.merge_cells(f"A{row}:F{row}"); ws[f"A{row}"].border=b
        ws.merge_cells(f"G{row}:H{row}"); ws[f"G{row}"].border=b
    ws.column_dimensions["A"].width=46
    for col in "BCDEF": ws.column_dimensions[col].width=2
    ws.column_dimensions["G"].width=14; ws.column_dimensions["H"].width=14
    ws.row_dimensions[1].height=40


def _fmt_full_gst(ws, inv, items):
    """
    Full GST Invoice - matches reference Image 4.
    Columns A-G: SR# | HS Code | Products Description | Units Sold | Retail/Unit RS | Ex-Sales Tax | Total RS
    Extra cols H-K: tax | Gross | Commission | Ex Comm
    Totals: in col G with correct labels.
    """
    b = _thin_border()
    rt = inv.get("retailer", "")
    rinfo = get_retailer_info(rt)
    comm_rate = RETAILERS.get(rt, {}).get("commission") or 0
    comm_pct  = int(round(comm_rate * 100))
    disc_label = rinfo["discount_label"] or ("Discount " + str(comm_pct) + "%")

    # Row 1 - Company
    ws.merge_cells("A1:K1")
    ws["A1"].value = SUPPLIER["name"]
    ws["A1"].font = Font(bold=True, size=15)
    ws["A1"].alignment = CENTER
    ws["A1"].border = b

    # Row 2 - SALES TAX INVOICE
    ws.merge_cells("A2:K2")
    ws["A2"].value = "SALES TAX INVOICE"
    ws["A2"].font = Font(bold=True, size=11)
    ws["A2"].alignment = CENTER
    ws["A2"].border = b

    # Rows 3-5 Supplier
    for row, lbl, val in [
        (3, "Supplier Address:", SUPPLIER["address"]),
        (4, "Supplier Sales Tax No.", SUPPLIER["sales_tax_no"]),
        (5, "Supplier NTN no.", SUPPLIER["ntn"]),
    ]:
        ws["A"+str(row)] = lbl; ws["A"+str(row)].font = BOLD; ws["A"+str(row)].border = b
        ws.merge_cells("B"+str(row)+":G"+str(row))
        ws["B"+str(row)] = val; ws["B"+str(row)].border = b

    # Row 6 spacer
    ws.merge_cells("A6:G6"); ws["A6"].border = b

    # Row 7 Invoice #
    ws.merge_cells("A7:C7")
    ws["A7"].value = "Invoice # :"
    ws["A7"].font = Font(bold=True, underline="single"); ws["A7"].border = b
    ws.merge_cells("D7:G7")
    ws["D7"].value = inv["invoice_no"]
    ws["D7"].alignment = RIGHT; ws["D7"].font = Font(bold=True); ws["D7"].border = b

    # Row 8 Buyer Name
    ws.merge_cells("A8:C8")
    ws["A8"].value = "Buyer Name:"
    ws["A8"].font = Font(bold=True, underline="single"); ws["A8"].border = b
    ws.merge_cells("D8:G8")
    ws["D8"].value = rinfo["buyer_name"]
    ws["D8"].font = Font(bold=True, size=13); ws["D8"].alignment = CENTER; ws["D8"].border = b

    # Rows 9-13 Buyer details
    for row, lbl, val, ul in [
        (9,  "Buyer NTN No",    rinfo["ntn"],            False),
        (10, "Buyer STRN:",     rinfo["strn"],            True),
        (11, "Buyer Address:",  rinfo["address"],         True),
        (12, "Delivery Outlet:",inv["outlet"],            True),
        (13, "Date:",           str(inv["invoice_date"]), True),
    ]:
        ws.merge_cells("A"+str(row)+":C"+str(row))
        ws["A"+str(row)].value = lbl
        ws["A"+str(row)].font = Font(underline="single" if ul else "none")
        ws["A"+str(row)].border = b
        ws.merge_cells("D"+str(row)+":G"+str(row))
        ws["D"+str(row)].value = val
        ws["D"+str(row)].alignment = CENTER; ws["D"+str(row)].border = b

    # Row 14 spacer
    ws.merge_cells("A14:G14"); ws["A14"].border = b

    # Rows 15-16 Column headers (two-row)
    hf = PatternFill("solid", fgColor="1A1A2E")
    hfont = Font(bold=True, color="FFFFFF", size=10)
    NL = chr(10)
    cols_main = [
        ("A","SR #"),
        ("B","HS Code"),
        ("C","Products Description"),
        ("D","Units"+NL+"Sold"),
        ("E","Retail Price/Unit"+NL+"RS"),
        ("F","Retail Price"+NL+"Ex -Sales Tax"),
        ("G","Total (RS)"),
    ]
    for col, lbl in cols_main:
        ws.merge_cells(col+"15:"+col+"16")
        cc = ws[col+"15"]
        cc.value = lbl; cc.font = hfont; cc.fill = hf
        cc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cc.border = b

    # Extra header cols H-K (single row, row 15)
    for col_n, lbl in [(8,"tax"),(9,"Gross"),(10,"Commission"),(11,"Ex Comm")]:
        cc = ws.cell(15, col_n, lbl)
        cc.font = hfont; cc.fill = hf; cc.alignment = CENTER; cc.border = b
        ws.cell(16, col_n).fill = hf; ws.cell(16, col_n).border = b

    # Data rows starting row 17
    start = 17
    for idx, it in enumerate(items, 1):
        row     = start + idx - 1
        retail  = float(it["unit_price"])
        qty     = float(it["quantity"])
        ex_unit = round(retail / (1 + GST_RATE), 2)
        line_ex = round(float(it["line_total"]) / (1 + GST_RATE), 2)
        # Extra cols
        tax_amt = round(line_ex * GST_RATE, 2)
        gross   = round(float(it["line_total"]), 2)          # = qty * retail
        comm    = round(gross * comm_rate, 2)
        ex_comm = round(gross - comm, 2)

        alt = _alt_fill(idx)
        for c, v in enumerate([idx, it.get("hs_code",""), it["product_name"],
                                qty, retail, ex_unit, line_ex], 1):
            cell = ws.cell(row, c, v); cell.border = b
            if alt: cell.fill = alt
            if c in (4,5,6,7) and isinstance(v,(int,float)):
                cell.number_format = NUM_FMT

        for c, v in [(8,tax_amt),(9,gross),(10,comm),(11,ex_comm)]:
            cc = ws.cell(row, c, v)
            cc.border = b; cc.number_format = NUM_FMT
            if alt: cc.fill = alt

    # Totals
    gross_val   = float(inv["gross_value"])
    addl_disc   = float(inv["discount"])
    comm_amt    = float(inv["commission_amount"] or 0)
    ex_tax_disp = round(gross_val / (1 + GST_RATE), 2)
    tax_disp    = round(gross_val - ex_tax_disp, 2)
    after_disc  = round(gross_val - addl_disc, 2)
    total_final = round(after_disc - comm_amt, 2)

    tr = start + len(items)

    # Total Units
    ws.merge_cells("A"+str(tr)+":C"+str(tr))
    ws["A"+str(tr)].value = "Total Units"; ws["A"+str(tr)].font = BOLD; ws["A"+str(tr)].border = b
    uc = ws.cell(tr, 4, float(inv["total_units"]))
    uc.font = BOLD; uc.number_format = "0"; uc.border = b
    for c in range(5, 12): ws.cell(tr, c).border = b
    tr += 1

    def _tot(r, lbl, val, bold=False):
        ws.merge_cells("A"+str(r)+":F"+str(r))
        lc = ws["A"+str(r)]
        lc.value = lbl; lc.font = Font(bold=bold)
        lc.alignment = Alignment(horizontal="right"); lc.border = b
        if val is None:
            ws["G"+str(r)].value = "-"; ws["G"+str(r)].border = b
        else:
            vc = ws.cell(r, 7, float(val))
            vc.number_format = NUM_FMT; vc.font = Font(bold=bold); vc.border = b
        for c in range(8, 12): ws.cell(r, c).border = b

    _tot(tr, "Value Ex - Sales Tax",                        ex_tax_disp); tr+=1
    _tot(tr, "Sales Tax 18 %",                              tax_disp);    tr+=1
    _tot(tr, "Total Value Incl - Sales Tax",                gross_val);   tr+=1
    _tot(tr, "Additional Discount",                         addl_disc if addl_disc else None); tr+=1
    _tot(tr, "Total Value Incl - Sales Tax  add. Discount", after_disc);  tr+=1
    _tot(tr, disc_label,                                    comm_amt);    tr+=1
    _tot(tr, "Total Value After Discount (Rs.)",            total_final, bold=True)

    _set_col_widths(ws, [5, 12, 40, 10, 18, 18, 16, 12, 14, 14, 14])
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 18


def make_invoice_xlsx(inv_id: int) -> bytes:
    """
    Format selection:
      GST Invoice type                         -> Full GST format (HS Code + tax columns)
      Carrefour / Jalalsons / Dolmen / Highfy  -> Simple SKIN DEEP restock format
      All others (Shams, Alfatah, Naheed ...)  -> SD BEAUTY LABS general format
    """
    inv_list = sb_get("invoices", {"id": f"eq.{inv_id}"})
    if not inv_list:
        raise ValueError("Invoice not found.")
    inv   = inv_list[0]
    items = sb_get("invoice_items", {"invoice_id": f"eq.{inv_id}", "order": "id.asc"})
    wb = Workbook(); ws = wb.active; ws.title = "Invoice"
    rt       = inv.get("retailer", "")
    it_type  = inv.get("invoice_type", "")
    if it_type == "GST Invoice":
        _fmt_full_gst(ws, inv, items)
    else:
        _fmt_shams(ws, inv, items)
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
