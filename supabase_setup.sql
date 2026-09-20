-- Run this in Supabase SQL Editor
-- Go to: Supabase Dashboard -> SQL Editor -> New Query -> Paste -> Run

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    barcode TEXT,
    code TEXT,
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    price REAL,
    hs_code TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS invoices (
    id BIGSERIAL PRIMARY KEY,
    invoice_no INTEGER UNIQUE NOT NULL,
    invoice_date TEXT NOT NULL,
    retailer TEXT NOT NULL,
    outlet TEXT NOT NULL,
    invoice_type TEXT NOT NULL,
    total_units REAL NOT NULL,
    gross_value REAL NOT NULL,
    discount REAL NOT NULL DEFAULT 0,
    taxable_value REAL NOT NULL,
    tax REAL NOT NULL,
    value_with_tax REAL NOT NULL,
    commission_rate REAL,
    commission_amount REAL,
    final_value REAL NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES invoices(id),
    product_id BIGINT,
    product_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    hs_code TEXT,
    line_total REAL NOT NULL
);

-- Seed initial invoice counter
INSERT INTO settings (key, value) VALUES ('next_invoice_no', '1')
ON CONFLICT (key) DO NOTHING;

-- Disable Row Level Security (for server-side access with secret key)
ALTER TABLE settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE products DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoices DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items DISABLE ROW LEVEL SECURITY;
