"""
pages/products.py — Product Master: view, edit (full), price update, delete.
"""
import math

from business import fmt_money
from db import sb_get, sb_patch, sb_delete
from templates.base import html_page
from templates.components import alert, page_header, card, table, badge, pagination, delete_form

PAGE_SIZE = 30


def products_page(message: str = "", error: bool = False, page: int = 1) -> str:
    offset = (page - 1) * PAGE_SIZE
    rows   = sb_get("products", {"order": "name.asc", "limit": str(PAGE_SIZE), "offset": str(offset)})

    try:
        from db import sb_count
        total = sb_count("products")
    except Exception:
        total = PAGE_SIZE
    total_pages = max(1, math.ceil(total / PAGE_SIZE))

    table_rows = []
    for r in rows:
        price_val     = str(r["price"]) if r["price"] is not None else ""
        price_display = (
            f"PKR {fmt_money(r['price'])}"
            if r["price"] is not None
            else badge("No price", "red")
        )
        pid = r["id"]
        table_rows.append(
            f"<tr>"
            f"<td><b>{r['name']}</b></td>"
            f"<td class='muted'>{r.get('code') or '—'}</td>"
            f"<td class='muted'>{r.get('barcode') or '—'}</td>"
            f"<td class='muted'>{r.get('hs_code') or '—'}</td>"
            f"<td>{price_display}</td>"
            f"<td>"
            f"<div class='flex gap-2'>"
            # Inline price quick-update
            f"<form method='post' action='/products/update' style='display:flex;gap:6px;align-items:center'>"
            f"<input type='hidden' name='id' value='{pid}'>"
            f"<input type='number' name='price' value='{price_val}' step='0.01' min='0' "
            f"placeholder='Price' style='width:110px;padding:6px 9px;font-size:12px'>"
            f"<button type='submit' class='btn btn-sm btn-primary'>Save</button>"
            f"</form>"
            # Edit full details
            f"<a href='/products/{pid}/edit' class='btn btn-sm btn-outline'>&#9998; Edit</a>"
            # Deactivate
            + delete_form(
                f"/products/{pid}/delete",
                "&#10005; Remove",
                f"Remove product '{r['name']}'?",
            )
            + f"</div>"
            f"</td>"
            f"</tr>"
        )

    product_table = table(
        ["Name", "Code", "Barcode", "HS Code", "Price", "Actions"],
        table_rows,
        "No products found.",
    )

    total_label = f'<span class="muted" style="font-size:13px">{total} products</span>'

    body = (
        page_header("Product Master", total_label)
        + alert(message, error)
        + card(
            '<p class="muted mb-4">"No price" products cannot be invoiced until a price is set.</p>'
            + product_table
            + pagination(page, total_pages, "/products")
        )
    )
    return html_page("Products", body, "products")


def product_edit_page(prod_id: int, message: str = "", error: bool = False) -> str:
    """Full product edit form."""
    rows = sb_get("products", {"id": f"eq.{prod_id}"})
    if not rows:
        return html_page("Error", '<div class="alert alert-err">Product not found.</div>')
    p = rows[0]

    body = (
        page_header("Edit Product", '<a href="/products" class="btn btn-outline btn-sm">&#8592; Back</a>')
        + alert(message, error)
        + card(
            f'<form method="post" action="/products/{prod_id}/edit">'
            f'<div class="row">'
            f'<div class="field"><label>Name</label>'
            f'<input type="text" name="name" value="{p["name"] or ""}" required></div>'
            f'</div>'
            f'<div class="row">'
            f'<div class="field"><label>Code</label>'
            f'<input type="text" name="code" value="{p.get("code") or ""}"></div>'
            f'<div class="field"><label>Barcode</label>'
            f'<input type="text" name="barcode" value="{p.get("barcode") or ""}"></div>'
            f'<div class="field"><label>HS Code</label>'
            f'<input type="text" name="hs_code" value="{p.get("hs_code") or ""}"></div>'
            f'</div>'
            f'<div class="row">'
            f'<div class="field" style="max-width:200px"><label>Price (PKR)</label>'
            f'<input type="number" name="price" step="0.01" min="0" '
            f'value="{p["price"] if p["price"] is not None else ""}"></div>'
            f'</div>'
            f'<div class="row mt-4">'
            f'<button type="submit" class="btn btn-primary">Save Changes</button>'
            f'<a href="/products" class="btn btn-outline">Cancel</a>'
            f'</div>'
            f'</form>'
        )
    )
    return html_page(f"Edit Product", body, "products")


def handle_product_update(form: dict) -> tuple[str, bool]:
    """Quick price update from product list inline form."""
    pid     = form.get("id",    [""])[0]
    price_s = form.get("price", [""])[0].strip()
    try:
        price = float(price_s) if price_s else None
        sb_patch("products", {"id": f"eq.{pid}"}, {"price": price})
        return "Price updated.", False
    except Exception as exc:
        return str(exc), True


def handle_product_edit(prod_id: int, form: dict) -> tuple[str, bool]:
    """Full product save — updates name, code, barcode, hs_code, price."""
    try:
        name    = form.get("name",    [""])[0].strip()
        code    = form.get("code",    [""])[0].strip()
        barcode = form.get("barcode", [""])[0].strip()
        hs_code = form.get("hs_code", [""])[0].strip()
        price_s = form.get("price",   [""])[0].strip()

        if not name:
            raise ValueError("Product name is required.")
        price = float(price_s) if price_s else None

        sb_patch("products", {"id": f"eq.{prod_id}"}, {
            "name":    name,
            "code":    code    or None,
            "barcode": barcode or None,
            "hs_code": hs_code or None,
            "price":   price,
        })
        return "Product updated successfully.", False
    except Exception as exc:
        return str(exc), True


def handle_product_delete(prod_id: int) -> tuple[str, bool]:
    """Soft-delete: set active=0 so invoicing is blocked but data is retained."""
    try:
        sb_patch("products", {"id": f"eq.{prod_id}"}, {"active": 0})
        return "Product removed.", False
    except Exception as exc:
        return str(exc), True
