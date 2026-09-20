"""
templates/components.py — Reusable HTML building blocks.
All functions return HTML strings. Keep them small and single-purpose.
"""

# ── Feedback ──────────────────────────────────────────────────────────────────

def alert(message: str, error: bool = False) -> str:
    cls = "alert-err" if error else "alert-ok"
    return f'<div class="alert {cls}">{message}</div>' if message else ""


# ── KPI Cards ─────────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, accent: bool = False) -> str:
    val_cls = "kpi-value accent" if accent else "kpi-value"
    return (
        f'<div class="kpi">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="{val_cls}">{value}</div>'
        f'</div>'
    )


def kpi_grid(*cards: str) -> str:
    return f'<div class="kpi-grid">{"".join(cards)}</div>'


# ── Badges ────────────────────────────────────────────────────────────────────

def badge(text: str, color: str = "purple") -> str:
    return f'<span class="badge badge-{color}">{text}</span>'


def invoice_type_badge(invoice_type: str) -> str:
    color = "purple" if "GST" in invoice_type else "orange"
    return badge(invoice_type, color)


# ── Page Header ───────────────────────────────────────────────────────────────

def page_header(title: str, *actions: str) -> str:
    actions_html = "".join(actions)
    return (
        f'<div class="page-header">'
        f'<h1>{title}</h1>'
        f'<div class="flex gap-2 items-center flex-wrap">{actions_html}</div>'
        f'</div>'
    )


# ── Tables ────────────────────────────────────────────────────────────────────

def table(headers: list[str], rows: list[str], empty_msg: str = "No data found.") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(rows) or f"<tr><td colspan='{len(headers)}' class='text-center muted' style='padding:24px'>{empty_msg}</td></tr>"
    return (
        f'<div class="table-wrap">'
        f'<table><tr>{th}</tr>{body}</table>'
        f'</div>'
    )


# ── Cards ─────────────────────────────────────────────────────────────────────

def card(content: str, extra_class: str = "") -> str:
    return f'<div class="card {extra_class}">{content}</div>'


def card_titled(title: str, content: str, extra_class: str = "") -> str:
    return card(f'<h2>{title}</h2>{content}', extra_class)


# ── Invoice Summary Box ───────────────────────────────────────────────────────

def summary_row(label: str, value: str) -> str:
    return (
        f'<div class="summary-row">'
        f'<span>{label}</span><span>{value}</span>'
        f'</div>'
    )


def summary_box(rows: list[tuple[str, str]]) -> str:
    inner = "".join(summary_row(l, v) for l, v in rows)
    return f'<div class="summary-box">{inner}</div>'


# ── Search Form ───────────────────────────────────────────────────────────────

def search_form(action: str, value: str = "", placeholder: str = "Search...") -> str:
    return (
        f'<form method="get" action="{action}" class="flex gap-2 items-center">'
        f'<input type="search" name="q" placeholder="{placeholder}" value="{value}" style="width:220px">'
        f'<button type="submit" class="btn btn-outline btn-sm">Search</button>'
        f'</form>'
    )


# ── Pagination ────────────────────────────────────────────────────────────────

def pagination(current: int, total_pages: int, base_url: str, extra_qs: str = "") -> str:
    """Render prev/page-numbers/next pagination bar."""
    if total_pages <= 1:
        return ""

    sep = "&" if extra_qs else ""

    def _link(page: int, label: str, disabled: bool = False, active: bool = False) -> str:
        if disabled:
            return (
                f'<span style="padding:7px 12px;border-radius:7px;font-size:13px;'
                f'color:var(--muted);border:1px solid var(--border)">{label}</span>'
            )
        if active:
            return (
                f'<a href="{base_url}?page={page}{sep}{extra_qs}" '
                f'style="padding:7px 12px;border-radius:7px;font-size:13px;font-weight:600;'
                f'background:var(--accent);color:#fff;text-decoration:none">{label}</a>'
            )
        return (
            f'<a href="{base_url}?page={page}{sep}{extra_qs}" '
            f'style="padding:7px 12px;border-radius:7px;font-size:13px;'
            f'color:var(--text);border:1px solid var(--border);text-decoration:none">{label}</a>'
        )

    # Show at most 7 page links around current
    pages_html = _link(current - 1, "&#8592; Prev", disabled=(current <= 1))

    start = max(1, current - 3)
    end   = min(total_pages, current + 3)
    if start > 1:
        pages_html += _link(1, "1")
        if start > 2:
            pages_html += '<span style="color:var(--muted);padding:0 4px">…</span>'
    for p in range(start, end + 1):
        pages_html += _link(p, str(p), active=(p == current))
    if end < total_pages:
        if end < total_pages - 1:
            pages_html += '<span style="color:var(--muted);padding:0 4px">…</span>'
        pages_html += _link(total_pages, str(total_pages))

    pages_html += _link(current + 1, "Next &#8594;", disabled=(current >= total_pages))

    return (
        f'<div style="display:flex;gap:6px;align-items:center;justify-content:center;'
        f'margin-top:20px;flex-wrap:wrap">{pages_html}</div>'
    )


# ── Confirm Delete Button ─────────────────────────────────────────────────────

def delete_form(action: str, label: str = "Delete", confirm_msg: str = "Are you sure?") -> str:
    return (
        f'<form method="post" action="{action}" style="display:inline" '
        f'onsubmit="return confirm(\'{confirm_msg}\')">'
        f'<button type="submit" class="btn btn-danger btn-sm">{label}</button>'
        f'</form>'
    )

