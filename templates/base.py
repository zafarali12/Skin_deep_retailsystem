"""
templates/base.py — Page layout wrapper.
Every page goes through html_page() to get consistent nav + styling.
"""
from templates.style import CSS

# ── Navigation Links: (path, label, active_key) ──────────────────────────────
NAV_LINKS = [
    ("/",          "Dashboard",      "dashboard"),
    ("/invoice",   "Create Invoice", "invoice"),
    ("/invoices",  "Invoice History","invoices"),
    ("/reports",   "Reports",        "reports"),
    ("/analytics", "Analytics",      "analytics"),
    ("/products",  "Products",       "products"),
]


def _nav_html(active: str) -> str:
    parts = []
    for path, label, key in NAV_LINKS:
        cls = ' class="active"' if key == active else ""
        parts.append(f'<a href="{path}"{cls}>{label}</a>')
    links = "".join(parts)
    return (
        '<nav>'
        '<div class="nav-brand">&#10022; <span>Skin Deep</span> International</div>'
        + links +
        '</nav>'
    )


def html_page(title: str, body: str, active: str = "") -> str:
    """Wrap body content in the full HTML shell with nav and styles."""
    return (
        '<!doctype html>'
        '<html lang="en">'
        '<head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title} \u2014 Skin Deep International</title>'
        f'{CSS}'
        '</head>'
        '<body>'
        f'{_nav_html(active)}'
        f'<div class="wrap animate">{body}</div>'
        '</body>'
        '</html>'
    )
