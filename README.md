# 🧴 Skin Deep International — Retail System

A local web-based retail management system for **Skin Deep International** — handles invoice creation, product management, sales reporting, and Excel exports. Built with pure Python (no Django/Flask), uses **Supabase** as the cloud database.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Step 1 — Clone the Repository](#step-1--clone-the-repository)
- [Step 2 — Setup Supabase (Database)](#step-2--setup-supabase-database)
- [Step 3 — Configure Environment Variables](#step-3--configure-environment-variables)
- [Step 4 — Install Dependencies](#step-4--install-dependencies)
- [Step 5 — Run the Server](#step-5--run-the-server)
- [Business Rules](#business-rules)
- [Project Structure](#project-structure)

---

## ✨ Features

- 📄 Create, edit, and delete GST invoices
- 📦 Product catalogue management (prices, barcodes, HS codes)
- 📊 Dashboard with monthly sales summary
- 📈 Product analytics and sales history
- 📥 Export invoices to Excel (single or all)
- ☁️ Cloud database via Supabase (accessible from anywhere)

---

## 🛠 Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Language   | Python 3.10+                      |
| Server     | Python built-in `http.server`     |
| Database   | Supabase (PostgreSQL)             |
| Exports    | openpyxl                          |
| HTTP       | httpx                             |
| Config     | python-dotenv                     |

---

## ✅ Prerequisites

Make sure the following are installed on your machine:

- **Python 3.10 or higher** → [Download here](https://www.python.org/downloads/)
  - During installation, check ✅ **"Add Python to PATH"**
- **Git** → [Download here](https://git-scm.com/downloads)
- A **Supabase account** (free) → [supabase.com](https://supabase.com)

---

## Step 1 — Clone the Repository

Open a terminal (Command Prompt or PowerShell) and run:

```bash
git clone https://github.com/zafarali12/Skin_deep_retailsystem.git
cd Skin_deep_retailsystem
```

---

## Step 2 — Setup Supabase (Database)

This project uses **Supabase** as its cloud database. Follow these steps carefully:

### 2.1 — Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and **Sign Up / Log In**
2. Click **"New Project"**
3. Fill in:
   - **Name**: `SkinDeep` (or anything you prefer)
   - **Database Password**: Choose a strong password (save it somewhere safe)
   - **Region**: Select the closest to you (e.g., `ap-south-1` for Pakistan/India)
4. Click **"Create new project"** and wait ~1 minute for it to initialize

### 2.2 — Run the Database Setup SQL

1. In your Supabase project dashboard, click **"SQL Editor"** in the left sidebar
2. Click **"New Query"**
3. Open the file [`supabase_setup.sql`](./supabase_setup.sql) from this repo
4. **Copy all its contents** and **paste** into the SQL Editor
5. Click the **"Run"** button (▶)
6. You should see: `Success. No rows returned` — this means all tables were created

> ⚠️ **Important:** This creates 4 tables: `settings`, `products`, `invoices`, `invoice_items`

### 2.3 — Get Your Supabase Credentials

You need two values from your Supabase project:

1. In your Supabase dashboard, go to **Project Settings** → **API** (left sidebar)
2. Copy the following:
   - **Project URL** → looks like `https://abcdefghijklm.supabase.co`
   - **`service_role` key** (under "Project API Keys") → a long string starting with `eyJ...`
     > ⚠️ Use the **`service_role`** key (not the `anon` key) — it bypasses Row Level Security for server-side access

---

## Step 3 — Configure Environment Variables

1. In the project folder, find the file **`.env.example`**
2. **Copy** it and rename the copy to **`.env`**:

   ```bash
   # Windows (PowerShell)
   Copy-Item .env.example .env

   # Mac/Linux
   cp .env.example .env
   ```

3. Open `.env` in any text editor and fill in your Supabase credentials:

   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_service_role_key_here
   PORT=8080
   ```

   Replace the placeholder values with the actual URL and key you copied in Step 2.3.

> 🔒 **`.env` is in `.gitignore`** — it will never be pushed to GitHub. Your credentials are safe.

---

## Step 4 — Install Dependencies

In the project folder, run:

```bash
pip install -r requirements.txt
```

This installs:
- `openpyxl` — for Excel export
- `httpx` — for Supabase API calls
- `python-dotenv` — for reading the `.env` file

---

## Step 5 — Run the Server

```bash
python app.py
```

You should see:

```
  ** Skin Deep International - Retail System
  Connecting to Supabase...
  Running at: http://127.0.0.1:8080
  Database : Supabase
```

Now open your browser and go to: **[http://127.0.0.1:8080](http://127.0.0.1:8080)**

To stop the server, press `Ctrl + C` in the terminal.

---

## 💼 Business Rules

### Tax (GST)
| Retailer                                    | GST Rate |
|---------------------------------------------|----------|
| Carrefour, Jalalsons, Alfatah, Shams, Naheed | 18%     |
| Highfy, Dolmen Cart                         | 0%       |

### Commission Rates
| Retailer     | Commission |
|--------------|------------|
| Carrefour    | 28.5%      |
| Jalalsons    | 23%        |
| Alfatah      | 30%        |
| Shams        | 25%        |
| Naheed       | 32%        |
| Highfy       | 15%        |
| Dolmen Cart  | —          |

### Invoice Workflow
`Create Invoice → Select Retailer / Outlet / Type → Add Products + Quantities → Generate → Download Excel`

Invoice numbers are **sequential** and stored in the `settings` table in Supabase.

---

## 📁 Project Structure

```
Skin_deep_retailsystem/
│
├── app.py                  # Main server & URL router
├── business.py             # Business logic (tax, commission calculations)
├── config.py               # App configuration & constants
├── db.py                   # Supabase database calls
│
├── pages/                  # Page rendering functions
│   ├── dashboard.py
│   ├── invoices.py
│   ├── history.py
│   ├── products.py
│   ├── reports.py
│   └── analytics.py
│
├── exports/
│   └── excel.py            # Excel file generation
│
├── templates/
│   └── base.py             # Shared HTML layout
│
├── supabase_setup.sql      # ⬅ Run this in Supabase SQL Editor
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .env                    # ⚠️ Your secrets (NOT committed to Git)
└── .gitignore
```

---

## ❓ Common Issues

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `Connection refused` / Supabase error | Check your `.env` — make sure URL and KEY are correct |
| Tables don't exist error | Re-run `supabase_setup.sql` in Supabase SQL Editor |
| Port already in use | Change `PORT=8080` to `PORT=8081` (or any free port) in `.env` |
| `python` not found | Try `python3 app.py` instead, or reinstall Python with PATH enabled |

---

## 👤 Author

**Skin Deep International** — Internal retail management system.
