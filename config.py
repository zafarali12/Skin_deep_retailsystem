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


# Retailer Legal/Billing Name (shown on Excel as Buyer Name)
# App mein Alfatah naam use hoga, Excel invoice pe ZUBAIDA ASSOCIATES aayega.
RETAILER_BUYER_NAMES = {
    "Alfatah": "M/S. ZUBAIDA ASSOCIATES",
}


def get_buyer_name(retailer):
    return RETAILER_BUYER_NAMES.get(retailer, retailer)


# Per-retailer billing details for GST invoices (NTN, STRN, address)
RETAILER_INFO = {
    "Jalalsons": {
        "buyer_name": "M/S. Jalal Sons",
        "ntn": "1010737-1",
        "strn": "0300999995646",
        "address": "12-E Main Market Gulberg, Lahore",
        "discount_label": None,
    },
    "Alfatah": {
        "buyer_name": "M/S. ZUBAIDA ASSOCIATES",
        "ntn": "4269497-3",
        "strn": "0300426949714",
        "address": "House # 51-B, Mehmood Ali Kassuri Road, Hussain Chowk, Lahore",
        "discount_label": None,
    },
    "Naheed": {
        "buyer_name": "NAHEED SUPER MARKET",
        "ntn": "1328857-1",
        "strn": "1700132885719",
        "address": "156-157, Main Shaeed-E-Millat Road, Block 3, BYJCHS",
        "discount_label": "Store Discount",
    },
    "Shams": {
        "buyer_name": "SHAMS SHOPPING CENTER (SMC PVT) LTD",
        "ntn": "8074177-7",
        "strn": "8074177-7",
        "address": "Office no. 16, Block-8, 1st Floor Shoukat Complex, Super",
        "discount_label": None,
    },
    "Carrefour": {
        "buyer_name": "MAF Hypermarkets Pakistan (Private) Limited",
        "ntn": "3000691-7",
        "strn": "03-03-9999-110-55",
        "address": "MAF Hypermarkets Pakistan (Pvt) Ltd.",
        "discount_label": None,
    },
    "Highfy": {
        "buyer_name": "Highfy",
        "ntn": "",
        "strn": "",
        "address": "",
        "discount_label": None,
    },
    "Dolmen Cart": {
        "buyer_name": "Dolmen Cart",
        "ntn": "",
        "strn": "",
        "address": "",
        "discount_label": None,
    },
}


def get_retailer_info(retailer):
    info = RETAILER_INFO.get(retailer, {})
    buyer = get_buyer_name(retailer)
    return {
        "buyer_name": info.get("buyer_name", buyer),
        "ntn": info.get("ntn", ""),
        "strn": info.get("strn", ""),
        "address": info.get("address", ""),
        "discount_label": info.get("discount_label", None),
    }
