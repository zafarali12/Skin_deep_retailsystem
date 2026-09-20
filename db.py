"""
db.py — Supabase REST client and database helpers.
All raw HTTP calls to Supabase live here. No business logic.
"""
import json
import httpx

from config import SUPABASE_URL, SUPABASE_KEY, PRODUCTS_JSON

# ── Singleton HTTP client (connection-pooled) ─────────────────────────────────
# max_connections     : total concurrent connections to Supabase
# max_keepalive_connections: persistent connections kept alive between requests
_client = httpx.Client(
    base_url=SUPABASE_URL,
    headers={
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    },
    limits=httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
        keepalive_expiry=30,
    ),
    timeout=httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0),
)

# ── CRUD Helpers ──────────────────────────────────────────────────────────────

def sb_get(table: str, params: dict | None = None) -> list:
    r = _client.get(f"/rest/v1/{table}", params=params or {})
    r.raise_for_status()
    return r.json()

def sb_post(table: str, data: dict) -> list:
    r = _client.post(f"/rest/v1/{table}", content=json.dumps(data))
    r.raise_for_status()
    return r.json()

def sb_post_many(table: str, data_list: list) -> list:
    r = _client.post(f"/rest/v1/{table}", content=json.dumps(data_list))
    r.raise_for_status()
    return r.json()

def sb_patch(table: str, filters: dict, data: dict) -> list:
    r = _client.patch(f"/rest/v1/{table}", params=filters, content=json.dumps(data))
    r.raise_for_status()
    return r.json()

def sb_delete(table: str, filters: dict) -> list:
    r = _client.delete(f"/rest/v1/{table}", params=filters)
    r.raise_for_status()
    return r.json()

# ── Count Helper ──────────────────────────────────────────────────────────────

def sb_count(table: str, params: dict | None = None) -> int:
    """Return total row count using Supabase range header."""
    p = dict(params or {})
    p["select"] = "id"
    r = _client.get(
        f"/rest/v1/{table}",
        params=p,
        headers={"Prefer": "count=exact"},
    )
    r.raise_for_status()
    # Supabase returns: Content-Range: 0-24/1234
    cr = r.headers.get("content-range", "0/0")
    try:
        return int(cr.split("/")[-1])
    except Exception:
        return 0

# ── Startup Seed ──────────────────────────────────────────────────────────────

def init_db() -> None:
    """Seed initial settings and products if tables are empty."""
    if not sb_get("settings", {"key": "eq.next_invoice_no"}):
        sb_post("settings", {"key": "next_invoice_no", "value": "1"})

    if not sb_get("products", {"select": "id", "limit": "1"}):
        try:
            with open(PRODUCTS_JSON, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            raw = []

        batch = [
            {
                "barcode":  p.get("barcode", ""),
                "code":     p.get("code", ""),
                "name":     p["name"],
                "category": "",
                "price":    p.get("price"),
                "hs_code":  p.get("hs_code", ""),
                "active":   1,
            }
            for p in raw if p.get("name")
        ]
        if batch:
            try:
                sb_post_many("products", batch)
                print(f"  Seeded {len(batch)} products")
            except Exception as exc:
                print(f"  Seed warning: {exc}")

def next_invoice_no() -> int:
    """Atomically read and increment the invoice counter."""
    rows = sb_get("settings", {"key": "eq.next_invoice_no", "select": "value"})
    n = int(rows[0]["value"]) if rows else 1
    sb_patch("settings", {"key": "eq.next_invoice_no"}, {"value": str(n + 1)})
    return n
