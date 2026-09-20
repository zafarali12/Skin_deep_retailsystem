"""
app.py — HTTP router and entry point.

This file ONLY handles:
  1. Mapping URL paths to page/handler functions
  2. Sending HTTP responses
  3. Starting the server

Business logic  -> business.py
Database calls  -> db.py
Configuration   -> config.py
Page rendering  -> pages/
Excel exports   -> exports/excel.py
HTML templates  -> templates/
"""
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from config import PORT
from db import init_db

# Pages
from pages.dashboard import dashboard
from pages.invoices  import (
    invoice_form, handle_invoice_post, invoice_success_page,
    edit_invoice_form, handle_invoice_edit,
)
from pages.history   import invoices_page, handle_invoice_delete
from pages.products  import (
    products_page, product_edit_page,
    handle_product_update, handle_product_edit, handle_product_delete,
)
from pages.reports   import reports_page
from pages.analytics import product_analytics_page

# Exports
from exports.excel import make_invoice_xlsx, make_all_invoices_xlsx, make_product_report_xlsx

# Error page
from templates.base import html_page


# ── Constants ─────────────────────────────────────────────────────────────────

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        from datetime import datetime
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")

    # ── Response helpers ──────────────────────────────────────────────────────

    def send_html(self, html: str, status: int = 200) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_xlsx(self, data: bytes, filename: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", XLSX_CONTENT_TYPE)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_error_page(self, message: str, status: int = 500) -> None:
        self.send_html(
            html_page("Error", f'<div class="alert alert-err">{message}</div>'),
            status,
        )

    def send_redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    # ── GET Routes ────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)

        def _int(key: str, default: int = 1) -> int:
            try:
                return max(1, int(qs.get(key, [str(default)])[0]))
            except Exception:
                return default

        try:
            # ── Simple page routes ──
            if path == "/":
                return self.send_html(dashboard())
            if path == "/invoice":
                return self.send_html(invoice_form())
            if path == "/invoices":
                return self.send_html(invoices_page(qs.get("q", [""])[0], page=_int("page")))
            if path == "/reports":
                return self.send_html(reports_page())
            if path == "/products":
                return self.send_html(products_page(page=_int("page")))
            if path == "/analytics":
                return self.send_html(product_analytics_page(qs.get("q", [""])[0]))

            # ── Excel: all invoices ──
            if path == "/invoices/xlsx":
                return self.send_xlsx(make_all_invoices_xlsx(), "SkinDeep_All_Invoices.xlsx")

            # ── Excel: product analytics ──
            if path == "/analytics/xlsx":
                pf    = qs.get("product", [""])[0]
                fname = (
                    f"SkinDeep_Product_{re.sub(r'[^\\w]', '_', pf)[:30]}.xlsx"
                    if pf else "SkinDeep_Product_Analytics.xlsx"
                )
                return self.send_xlsx(make_product_report_xlsx(pf or None), fname)

            # ── Invoice: edit form (GET) ──
            m = re.match(r"^/invoice/(\d+)/edit$", path)
            if m:
                return self.send_html(edit_invoice_form(int(m.group(1))))

            # ── Excel: single invoice ──
            m = re.match(r"^/invoice/(\d+)/xlsx$", path)
            if m:
                inv_id = int(m.group(1))
                return self.send_xlsx(
                    make_invoice_xlsx(inv_id),
                    f"SkinDeep_Invoice_{inv_id}.xlsx",
                )

            # ── Product: edit form (GET) ──
            m = re.match(r"^/products/(\d+)/edit$", path)
            if m:
                return self.send_html(product_edit_page(int(m.group(1))))

            # ── 404 ──
            self.send_error_page("Page not found.", 404)

        except Exception as exc:
            self.send_error_page(str(exc))

    # ── POST Routes ───────────────────────────────────────────────────────────

    def do_POST(self) -> None:
        path   = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        raw    = self.rfile.read(length).decode("utf-8")
        form   = parse_qs(raw, keep_blank_values=True)

        try:
            # ── Create invoice ──
            if path == "/invoice":
                ok, result, inv_no, calc = handle_invoice_post(form)
                if ok:
                    return self.send_html(invoice_success_page(result, inv_no, calc))
                return self.send_html(invoice_form(result, error=True), 400)

            # ── Edit invoice ──
            m = re.match(r"^/invoice/(\d+)/edit$", path)
            if m:
                inv_id = int(m.group(1))
                ok, msg = handle_invoice_edit(inv_id, form)
                if ok:
                    return self.send_redirect("/invoices")
                return self.send_html(edit_invoice_form(inv_id, msg, error=True), 400)

            # ── Delete invoice ──
            m = re.match(r"^/invoice/(\d+)/delete$", path)
            if m:
                ok, msg = handle_invoice_delete(int(m.group(1)))
                if ok:
                    return self.send_redirect("/invoices")
                return self.send_error_page(msg)

            # ── Quick price update ──
            if path == "/products/update":
                msg, is_err = handle_product_update(form)
                return self.send_html(products_page(msg, is_err))

            # ── Full product edit ──
            m = re.match(r"^/products/(\d+)/edit$", path)
            if m:
                prod_id = int(m.group(1))
                msg, is_err = handle_product_edit(prod_id, form)
                if is_err:
                    return self.send_html(product_edit_page(prod_id, msg, error=True), 400)
                return self.send_redirect("/products")

            # ── Delete / deactivate product ──
            m = re.match(r"^/products/(\d+)/delete$", path)
            if m:
                msg, is_err = handle_product_delete(int(m.group(1)))
                return self.send_html(products_page(msg, is_err))

            self.send_error_page("Route not found.", 404)

        except Exception as exc:
            self.send_error_page(str(exc))


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("\n  ** Skin Deep International - Retail System")
    print("  Connecting to Supabase...")
    init_db()
    print(f"  Running at: http://127.0.0.1:{PORT}")
    print("  Database : Supabase\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
