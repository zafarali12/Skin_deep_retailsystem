"""
config.py — All application-wide constants.
Edit this file to update retailer commissions, outlets, or supplier info.

Secrets (API keys etc.) are loaded from the .env file.
Copy .env.example -> .env and fill in your values.
"""
import os
from pathlib import Path

# ── Load .env file (no external library needed) ───────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

# ── Server ────────────────────────────────────────────────────────────────────
PORT = int(os.environ.get("PORT", "8080"))

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

# ── Retailer Master ───────────────────────────────────────────────────────────
# commission: fraction of (price + GST) taken by retailer
# tax:        whether GST (18%) applies to this retailer
# type:       Retail / Etail / Cart (informational)
RETAILERS: dict[str, dict] = {
    "Carrefour":   {"commission": 0.285, "tax": True,  "type": "Retail"},
    "Jalalsons":   {"commission": 0.23,  "tax": True,  "type": "Retail"},
    "Alfatah":     {"commission": 0.30,  "tax": True,  "type": "Retail"},
    "Shams":       {"commission": 0.25,  "tax": True,  "type": "Retail"},
    "Naheed":      {"commission": 0.32,  "tax": True,  "type": "Etail"},
    "Highfy":      {"commission": 0.15,  "tax": False,  "type": "Etail"},
    "Dolmen Cart": {"commission": None,  "tax": False,  "type": "Cart"},
}

# ── Outlet Master ─────────────────────────────────────────────────────────────
OUTLETS: dict[str, list[str]] = {
    "Carrefour":   ["Packages", "Emporium", "Fortress", "Giga", "Lucky One"],
    "Jalalsons":   ["Main Market", "Lake City", "Izmir Town", "Askari X Sector S", "Askari X Sector F"],
    "Alfatah":     ["HCL", "Goldcrest", "AF DML", "AF Faisalabad", "AF Johar Town", "AF Centaurus", "AF Sialkot"],
    "Shams":       ["Shams Shopping Center F-6"],
    "Naheed":      ["Naheed"],
    "Highfy":      ["Highfy"],
    "Dolmen Cart": ["Dolmen Cart"],
}

# ── Supplier / Company Info ───────────────────────────────────────────────────
SUPPLIER: dict[str, str] = {
    "name":         "SD BEAUTY LABS (SMC-PVT) LTD",
    "address":      "House no 24/8, Race Cource Road, Shadman Lahore, Pakistan.",
    "sales_tax_no": "F612515",
    "ntn":          "F612515",
}

# ── Invoice Types ─────────────────────────────────────────────────────────────
INVOICE_TYPES = ["General Invoice", "GST Invoice"]
GST_RATE      = 0.18
