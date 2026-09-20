"""
pages/invoices.py — Create Invoice form and POST handler.
"""
import json
from datetime import datetime

from config import RETAILERS, OUTLETS, INVOICE_TYPES
from db import sb_get, sb_post, sb_patch, sb_delete, next_invoice_no
from business import InvoiceItem, InvoiceCalc, calc_invoice, fmt_money, fmt_pkr
from templates.base import html_page
from templates.components import alert, page_header, card, summary_box, summary_row


# ── Invoice Form (GET) ────────────────────────────────────────────────────────

def invoice_form(message: str = "", error: bool = False) -> str:
    products = sb_get("products", {"active": "eq.1", "order": "name.asc", "limit": "500"})

    prices_map   = {p["name"]: (p["price"] if p["price"] is not None else "") for p in products}
    product_opts = "".join(
        f'<option value="{p["name"].replace(chr(34), "&quot;")}">{p["name"]}</option>'
        for p in products
    )
    retailer_opts = "".join(f"<option>{r}</option>" for r in RETAILERS)
    invoice_type_opts = "".join(f"<option>{t}</option>" for t in INVOICE_TYPES)

    today           = datetime.now().strftime("%Y-%m-%d")
    outlets_json    = json.dumps(OUTLETS)
    prices_json     = json.dumps(prices_map, ensure_ascii=False)
    retailer_data   = {k: {"commission": v["commission"], "tax": v["tax"]} for k, v in RETAILERS.items()}
    rd_json         = json.dumps(retailer_data)

    form_body = f"""
<div class="card mb-4">
  <h2>Invoice Details</h2>
  <div class="row">
    <div class="field">
      <label>Retailer</label>
      <select name="retailer" id="retailer" required onchange="updateOutlets();updateSummary()">
        {retailer_opts}
      </select>
    </div>
    <div class="field">
      <label>Outlet</label>
      <select name="outlet" id="outlet" required></select>
    </div>
    <div class="field">
      <label>Invoice Type</label>
      <select name="invoice_type" id="invoice_type" onchange="updateSummary()">
        {invoice_type_opts}
      </select>
    </div>
    <div class="field" style="max-width:160px">
      <label>Date</label>
      <input type="date" name="date" value="{today}" required>
    </div>
    <div class="field" style="max-width:160px">
      <label>Discount (PKR)</label>
      <input type="number" step="0.01" min="0" name="discount" id="discount" value="0" oninput="updateSummary()">
    </div>
  </div>
</div>

<div class="card mb-4">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <h2 style="margin:0">Products</h2>
    <button type="button" class="btn btn-outline btn-sm" onclick="addRow()">+ Add Row</button>
  </div>
  <div style="display:grid;grid-template-columns:1fr 110px 130px 40px;gap:10px;margin-bottom:8px;padding:0 2px">
    <span style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase">Product</span>
    <span style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase">Qty</span>
    <span style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase">Unit Price (PKR)</span>
    <span></span>
  </div>
  <div id="items"></div>
  <datalist id="productlist">{product_opts}</datalist>
</div>

<div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap">
  <div style="flex:1;min-width:280px">
    <div class="summary-box">
      <h3 style="margin-bottom:12px">Invoice Summary</h3>
      <div class="summary-row"><span>Gross Value</span>      <span id="s_gross">PKR 0.00</span></div>
      <div class="summary-row"><span>Discount</span>         <span id="s_disc">PKR 0.00</span></div>
      <div class="summary-row"><span>Taxable Value</span>    <span id="s_taxable">PKR 0.00</span></div>
      <div class="summary-row"><span>GST (18%)</span>        <span id="s_gst">PKR 0.00</span></div>
      <div class="summary-row"><span>Store Commission</span> <span id="s_comm">PKR 0.00</span></div>
      <div class="summary-row"><span>Total Invoice Value</span><span id="s_total">PKR 0.00</span></div>
    </div>
  </div>
  <div style="display:flex;flex-direction:column;gap:10px;min-width:180px">
    <button type="submit" class="btn btn-primary w-full" style="justify-content:center">&#10003; Generate Invoice</button>
    <a href="/" class="btn btn-outline w-full" style="justify-content:center">Cancel</a>
  </div>
</div>

<script>
const OUTLETS = {outlets_json};
const PRICES  = {prices_json};
const RETAILER_DATA = {rd_json};

function updateOutlets() {{
  const r = document.getElementById('retailer').value;
  const sel = document.getElementById('outlet');
  sel.innerHTML = '';
  (OUTLETS[r] || []).forEach(x => {{
    const o = document.createElement('option');
    o.value = o.textContent = x;
    sel.appendChild(o);
  }});
  updateSummary();
}}

function getItems() {{
  return Array.from(document.querySelectorAll('.item-row')).map(row => ({{
    qty:   parseFloat(row.querySelector('.qty-input').value)   || 0,
    price: parseFloat(row.querySelector('.price-input').value) || 0,
  }})).filter(r => r.qty > 0 && r.price > 0);
}}

function fmt(n) {{
  return Number(n).toLocaleString('en-PK', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
}}

function updateSummary() {{
  const items    = getItems();
  const disc     = parseFloat(document.getElementById('discount').value) || 0;
  const retailer = document.getElementById('retailer').value;
  const invType  = document.getElementById('invoice_type').value;
  const rd       = RETAILER_DATA[retailer] || {{}};
  const gross    = items.reduce((s, r) => s + r.qty * r.price, 0);
  const taxable  = Math.max(gross - disc, 0);
  const gst      = (rd.tax && invType === 'GST Invoice') ? taxable * 0.18 : 0;
  const withTax  = taxable + gst;
  const comm     = rd.commission != null ? withTax * rd.commission : 0;

  document.getElementById('s_gross').textContent   = 'PKR ' + fmt(gross);
  document.getElementById('s_disc').textContent    = 'PKR ' + fmt(disc);
  document.getElementById('s_taxable').textContent = 'PKR ' + fmt(taxable);
  document.getElementById('s_gst').textContent     = 'PKR ' + fmt(gst);
  document.getElementById('s_comm').textContent    = 'PKR ' + fmt(comm);
  document.getElementById('s_total').textContent   = 'PKR ' + fmt(withTax);
}}

function wireRow(row) {{
  const inp      = row.querySelector('.prod-input');
  const priceInp = row.querySelector('.price-input');
  inp.addEventListener('input', () => {{
    const p = PRICES[inp.value];
    priceInp.value = (p !== undefined && p !== '' && p !== null) ? p : '';
    updateSummary();
  }});
  priceInp.addEventListener('input', updateSummary);
  row.querySelector('.qty-input').addEventListener('input', updateSummary);
}}

function addRow() {{
  const wrap = document.getElementById('items');
  const div  = document.createElement('div');
  div.className = 'item-row';
  div.innerHTML = `
    <div class="field" style="margin:0">
      <input list="productlist" class="prod-input" name="product" placeholder="Product name..." required>
    </div>
    <div class="field" style="margin:0">
      <input type="number" class="qty-input" name="qty" placeholder="0" min="0.01" step="0.01" required>
    </div>
    <div class="field" style="margin:0">
      <input type="number" class="price-input" name="unit_price" placeholder="0.00" min="0.01" step="0.01" required>
    </div>
    <button type="button" class="btn btn-danger btn-sm"
      onclick="this.closest('.item-row').remove(); updateSummary()"
      style="height:40px;width:40px;padding:0;justify-content:center">&#10005;</button>
  `;
  wrap.appendChild(div);
  wireRow(div);
  div.querySelector('.prod-input').focus();
}}

updateOutlets();
addRow();
</script>
"""

    body = (
        page_header("Create Invoice")
        + alert(message, error)
        + f'<form method="post" action="/invoice" id="invoiceForm">{form_body}</form>'
    )
    return html_page("Create Invoice", body, "invoice")


# ── Invoice POST Handler ──────────────────────────────────────────────────────

def handle_invoice_post(form: dict) -> tuple[bool, any, any, any]:
    """
    Validate and save a new invoice.
    Returns (success, inv_id_or_error_msg, invoice_no, InvoiceCalc).
    """
    retailer     = form.get("retailer", [""])[0]
    outlet       = form.get("outlet",   [""])[0]
    invoice_type = form.get("invoice_type", ["General Invoice"])[0]
    date         = form.get("date", [str(datetime.now().date())])[0]
    discount     = float(form.get("discount", ["0"])[0] or 0)

    names  = form.get("product",    [])
    qtys   = form.get("qty",        [])
    prices = form.get("unit_price", [])

    try:
        if retailer not in RETAILERS:
            raise ValueError("Invalid retailer selected.")

        items: list[InvoiceItem] = []
        for name, qty_s, price_s in zip(names, qtys, prices):
            name = name.strip()
            if not name:
                continue
            qty = float(qty_s) if qty_s.strip() else 0
            if qty <= 0:
                raise ValueError(f"Quantity must be > 0 for: {name}")
            price = float(price_s) if price_s.strip() else None
            if price is None or price <= 0:
                raise ValueError(f"Enter a valid price for: {name}")

            product_rows = sb_get("products", {"name": f"ilike.{name}", "active": "eq.1", "limit": "1"})
            prod_id = product_rows[0]["id"] if product_rows else None
            hs_code = (product_rows[0].get("hs_code") or "") if product_rows else ""

            items.append(InvoiceItem(
                product_id=prod_id,
                product_name=name,
                quantity=qty,
                unit_price=price,
                hs_code=hs_code,
            ))

        if not items:
            raise ValueError("Add at least one product with quantity and price.")

        calc   = calc_invoice(retailer, items, discount)
        inv_no = next_invoice_no()

        inv_result = sb_post("invoices", {
            "invoice_no":        inv_no,
            "invoice_date":      date,
            "retailer":          retailer,
            "outlet":            outlet,
            "invoice_type":      invoice_type,
            "total_units":       calc.units,
            "gross_value":       calc.gross,
            "discount":          calc.discount,
            "taxable_value":     calc.taxable,
            "tax":               calc.tax,
            "value_with_tax":    calc.with_tax,
            "commission_rate":   RETAILERS[retailer]["commission"],
            "commission_amount": calc.commission,
            "final_value":       calc.final,
        })
        inv_id = inv_result[0]["id"]

        for it in items:
            sb_post("invoice_items", {
                "invoice_id":   inv_id,
                "product_id":   it.product_id,
                "product_name": it.product_name,
                "quantity":     it.quantity,
                "unit_price":   it.unit_price,
                "hs_code":      it.hs_code,
                "line_total":   it.line_total,
            })

        return True, inv_id, inv_no, calc

    except Exception as exc:
        return False, str(exc), None, None


# ── Success Page ──────────────────────────────────────────────────────────────

def invoice_success_page(inv_id: int, inv_no: int, calc: InvoiceCalc) -> str:
    rows = [
        ("Total Units",      fmt_money(calc.units)),
        ("Gross Value",      fmt_pkr(calc.gross)),
        ("Discount",         fmt_pkr(calc.discount)),
        ("Taxable Value",    fmt_pkr(calc.taxable)),
        ("Sales Tax (GST)",  fmt_pkr(calc.tax)),
        ("Store Commission", fmt_pkr(calc.commission)),
        ("Invoice Value",    fmt_pkr(calc.with_tax)),
    ]

    body = (
        '<div style="max-width:560px;margin:0 auto">'
        + alert(f'&#10003; Invoice <b>#{inv_no}</b> created successfully!')
        + card(
            f'<h2>Invoice Summary</h2>'
            + summary_box(rows)
            + f'<div class="row mt-4" style="justify-content:flex-end">'
            f'<a href="/invoice/{inv_id}/xlsx" class="btn btn-success">&#11015; Download Excel</a>'
            f'<a href="/invoice" class="btn btn-outline">+ Create Another</a>'
            f'<a href="/" class="btn btn-outline">Dashboard</a>'
            f'</div>'
        )
        + '</div>'
    )
    return html_page(f"Invoice #{inv_no} Created", body, "invoice")


# ── Edit Invoice (GET) ──────────────────────────────────────────────────────

def edit_invoice_form(inv_id: int, message: str = "", error: bool = False) -> str:
    """Pre-populated invoice form for editing an existing invoice."""
    inv_list = sb_get("invoices", {"id": f"eq.{inv_id}"})
    if not inv_list:
        return html_page("Error", '<div class="alert alert-err">Invoice not found.</div>')

    inv   = inv_list[0]
    items = sb_get("invoice_items", {"invoice_id": f"eq.{inv_id}", "order": "id.asc"})

    products = sb_get("products", {"active": "eq.1", "order": "name.asc", "limit": "500"})
    prices_map  = {p["name"]: (p["price"] if p["price"] is not None else "") for p in products}
    product_opts = "".join(
        f'<option value="{p["name"].replace(chr(34), "&quot;")}">'
        f'{p["name"]}</option>'
        for p in products
    )
    retailer_opts = "".join(
        f'<option{" selected" if r == inv["retailer"] else ""}>{r}</option>'
        for r in RETAILERS
    )
    invoice_type_opts = "".join(
        f'<option{" selected" if t == inv["invoice_type"] else ""}>{t}</option>'
        for t in INVOICE_TYPES
    )

    outlets_json  = json.dumps(OUTLETS)
    prices_json   = json.dumps(prices_map, ensure_ascii=False)
    retailer_data = {k: {"commission": v["commission"], "tax": v["tax"]} for k, v in RETAILERS.items()}
    rd_json       = json.dumps(retailer_data)

    # Pre-populate existing items as JS array
    existing_items_json = json.dumps([
        {"name": it["product_name"], "qty": float(it["quantity"]), "price": float(it["unit_price"])}
        for it in items
    ])

    existing_discount = float(inv.get("discount") or 0)
    existing_date     = str(inv["invoice_date"])

    form_body = f"""
<div class="card mb-4">
  <h2>Invoice Details</h2>
  <div class="row">
    <div class="field">
      <label>Retailer</label>
      <select name="retailer" id="retailer" required onchange="updateOutlets();updateSummary()">
        {retailer_opts}
      </select>
    </div>
    <div class="field">
      <label>Outlet</label>
      <select name="outlet" id="outlet" required></select>
    </div>
    <div class="field">
      <label>Invoice Type</label>
      <select name="invoice_type" id="invoice_type" onchange="updateSummary()">
        {invoice_type_opts}
      </select>
    </div>
    <div class="field" style="max-width:160px">
      <label>Date</label>
      <input type="date" name="date" value="{existing_date}" required>
    </div>
    <div class="field" style="max-width:160px">
      <label>Discount (PKR)</label>
      <input type="number" step="0.01" min="0" name="discount" id="discount"
             value="{existing_discount}" oninput="updateSummary()">
    </div>
  </div>
</div>

<div class="card mb-4">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <h2 style="margin:0">Products</h2>
    <button type="button" class="btn btn-outline btn-sm" onclick="addRow()">+ Add Row</button>
  </div>
  <div style="display:grid;grid-template-columns:1fr 110px 130px 40px;gap:10px;margin-bottom:8px;padding:0 2px">
    <span style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase">Product</span>
    <span style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase">Qty</span>
    <span style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase">Unit Price (PKR)</span>
    <span></span>
  </div>
  <div id="items"></div>
  <datalist id="productlist">{product_opts}</datalist>
</div>

<div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap">
  <div style="flex:1;min-width:280px">
    <div class="summary-box">
      <h3 style="margin-bottom:12px">Invoice Summary</h3>
      <div class="summary-row"><span>Gross Value</span>      <span id="s_gross">PKR 0.00</span></div>
      <div class="summary-row"><span>Discount</span>         <span id="s_disc">PKR 0.00</span></div>
      <div class="summary-row"><span>Taxable Value</span>    <span id="s_taxable">PKR 0.00</span></div>
      <div class="summary-row"><span>GST (18%)</span>        <span id="s_gst">PKR 0.00</span></div>
      <div class="summary-row"><span>Store Commission</span> <span id="s_comm">PKR 0.00</span></div>
      <div class="summary-row"><span>Total Invoice Value</span><span id="s_total">PKR 0.00</span></div>
    </div>
  </div>
  <div style="display:flex;flex-direction:column;gap:10px;min-width:180px">
    <button type="submit" class="btn btn-primary w-full" style="justify-content:center">&#10003; Save Changes</button>
    <a href="/invoices" class="btn btn-outline w-full" style="justify-content:center">Cancel</a>
  </div>
</div>

<script>
const OUTLETS       = {outlets_json};
const PRICES        = {prices_json};
const RETAILER_DATA = {rd_json};
const EXISTING_ITEMS= {existing_items_json};
const EXISTING_OUTLET = {json.dumps(inv['outlet'])};

function updateOutlets(selectExisting) {{
  const r   = document.getElementById('retailer').value;
  const sel = document.getElementById('outlet');
  sel.innerHTML = '';
  (OUTLETS[r] || []).forEach(x => {{
    const o   = document.createElement('option');
    o.value   = o.textContent = x;
    if (selectExisting && x === EXISTING_OUTLET) o.selected = true;
    sel.appendChild(o);
  }});
  updateSummary();
}}

function getItems() {{
  return Array.from(document.querySelectorAll('.item-row')).map(row => ({{
    qty:   parseFloat(row.querySelector('.qty-input').value)   || 0,
    price: parseFloat(row.querySelector('.price-input').value) || 0,
  }})).filter(r => r.qty > 0 && r.price > 0);
}}

function fmt(n) {{
  return Number(n).toLocaleString('en-PK', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
}}

function updateSummary() {{
  const items    = getItems();
  const disc     = parseFloat(document.getElementById('discount').value) || 0;
  const retailer = document.getElementById('retailer').value;
  const invType  = document.getElementById('invoice_type').value;
  const rd       = RETAILER_DATA[retailer] || {{}};
  const gross    = items.reduce((s, r) => s + r.qty * r.price, 0);
  const taxable  = Math.max(gross - disc, 0);
  const gst      = (rd.tax && invType === 'GST Invoice') ? taxable * 0.18 : 0;
  const withTax  = taxable + gst;
  const comm     = rd.commission != null ? withTax * rd.commission : 0;
  document.getElementById('s_gross').textContent   = 'PKR ' + fmt(gross);
  document.getElementById('s_disc').textContent    = 'PKR ' + fmt(disc);
  document.getElementById('s_taxable').textContent = 'PKR ' + fmt(taxable);
  document.getElementById('s_gst').textContent     = 'PKR ' + fmt(gst);
  document.getElementById('s_comm').textContent    = 'PKR ' + fmt(comm);
  document.getElementById('s_total').textContent   = 'PKR ' + fmt(withTax);
}}

function wireRow(row) {{
  const inp      = row.querySelector('.prod-input');
  const priceInp = row.querySelector('.price-input');
  inp.addEventListener('input', () => {{
    const p = PRICES[inp.value];
    priceInp.value = (p !== undefined && p !== '' && p !== null) ? p : '';
    updateSummary();
  }});
  priceInp.addEventListener('input', updateSummary);
  row.querySelector('.qty-input').addEventListener('input', updateSummary);
}}

function addRow(name, qty, price) {{
  const wrap = document.getElementById('items');
  const div  = document.createElement('div');
  div.className = 'item-row';
  div.innerHTML = `
    <div class="field" style="margin:0">
      <input list="productlist" class="prod-input" name="product"
             placeholder="Product name..." value="${{name || ''}}" required>
    </div>
    <div class="field" style="margin:0">
      <input type="number" class="qty-input" name="qty"
             placeholder="0" min="0.01" step="0.01" value="${{qty || ''}}" required>
    </div>
    <div class="field" style="margin:0">
      <input type="number" class="price-input" name="unit_price"
             placeholder="0.00" min="0.01" step="0.01" value="${{price || ''}}" required>
    </div>
    <button type="button" class="btn btn-danger btn-sm"
      onclick="this.closest('.item-row').remove(); updateSummary()"
      style="height:40px;width:40px;padding:0;justify-content:center">&#10005;</button>
  `;
  wrap.appendChild(div);
  wireRow(div);
  if (!name) div.querySelector('.prod-input').focus();
}}

// Initialise with existing outlet selected, then load existing items
updateOutlets(true);
EXISTING_ITEMS.forEach(it => addRow(it.name, it.qty, it.price));
updateSummary();
</script>
"""

    from templates.components import alert, page_header
    body = (
        page_header(f"Edit Invoice #{inv['invoice_no']}")
        + alert(message, error)
        + f'<form method="post" action="/invoice/{inv_id}/edit">{form_body}</form>'
    )
    return html_page(f"Edit Invoice #{inv['invoice_no']}", body, "invoices")


# ── Edit Invoice POST ──────────────────────────────────────────────────────

def handle_invoice_edit(inv_id: int, form: dict) -> tuple[bool, str]:
    """
    Update an existing invoice:
    1. Validate items
    2. Recalculate all totals
    3. Update the invoice row
    4. Delete old items and insert fresh ones
    Returns (success, message).
    """
    retailer     = form.get("retailer",     [""])[0]
    outlet       = form.get("outlet",       [""])[0]
    invoice_type = form.get("invoice_type", ["General Invoice"])[0]
    date         = form.get("date",         [str(datetime.now().date())])[0]
    discount     = float(form.get("discount", ["0"])[0] or 0)

    names  = form.get("product",    [])
    qtys   = form.get("qty",        [])
    prices = form.get("unit_price", [])

    try:
        if retailer not in RETAILERS:
            raise ValueError("Invalid retailer.")

        items: list[InvoiceItem] = []
        for name, qty_s, price_s in zip(names, qtys, prices):
            name = name.strip()
            if not name:
                continue
            qty = float(qty_s) if qty_s.strip() else 0
            if qty <= 0:
                raise ValueError(f"Quantity must be > 0 for: {name}")
            price = float(price_s) if price_s.strip() else None
            if price is None or price <= 0:
                raise ValueError(f"Enter a valid price for: {name}")

            product_rows = sb_get("products", {"name": f"ilike.{name}", "active": "eq.1", "limit": "1"})
            prod_id = product_rows[0]["id"] if product_rows else None
            hs_code = (product_rows[0].get("hs_code") or "") if product_rows else ""

            items.append(InvoiceItem(
                product_id=prod_id,
                product_name=name,
                quantity=qty,
                unit_price=price,
                hs_code=hs_code,
            ))

        if not items:
            raise ValueError("At least one product is required.")

        calc = calc_invoice(retailer, items, discount)

        # 1. Update invoice header
        sb_patch("invoices", {"id": f"eq.{inv_id}"}, {
            "invoice_date":      date,
            "retailer":          retailer,
            "outlet":            outlet,
            "invoice_type":      invoice_type,
            "total_units":       calc.units,
            "gross_value":       calc.gross,
            "discount":          calc.discount,
            "taxable_value":     calc.taxable,
            "tax":               calc.tax,
            "value_with_tax":    calc.with_tax,
            "commission_rate":   RETAILERS[retailer]["commission"],
            "commission_amount": calc.commission,
            "final_value":       calc.final,
        })

        # 2. Replace line items atomically
        sb_delete("invoice_items", {"invoice_id": f"eq.{inv_id}"})
        for it in items:
            sb_post("invoice_items", {
                "invoice_id":   inv_id,
                "product_id":   it.product_id,
                "product_name": it.product_name,
                "quantity":     it.quantity,
                "unit_price":   it.unit_price,
                "hs_code":      it.hs_code,
                "line_total":   it.line_total,
            })

        return True, "Invoice updated successfully."

    except Exception as exc:
        return False, str(exc)
