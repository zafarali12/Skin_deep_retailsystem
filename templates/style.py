"""
templates/style.py — Global CSS design system.
Edit colour tokens here to retheme the entire app.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & Tokens ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:       #0f1117;
  --surface:  #1a1d27;
  --surface2: #222638;
  --border:   #2e3248;
  --accent:   #7c6af7;
  --accent2:  #a78bfa;
  --text:     #e8eaf0;
  --muted:    #6b7280;
  --success:  #22c55e;
  --danger:   #ef4444;
  --warning:  #f59e0b;
}

/* ── Base ── */
body {
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.5;
}

/* ── Navigation ── */
nav {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 28px;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  gap: 0;
}
.nav-brand {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  padding: 18px 0;
  margin-right: 32px;
  white-space: nowrap;
}
.nav-brand span {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
nav a {
  color: var(--muted);
  text-decoration: none;
  padding: 19px 14px;
  font-size: 13.5px;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: color .2s, border-color .2s;
  white-space: nowrap;
}
nav a:hover  { color: var(--text); border-bottom-color: var(--accent); }
nav a.active { color: var(--accent2); border-bottom-color: var(--accent); }

/* ── Layout ── */
.wrap { max-width: 1300px; margin: 0 auto; padding: 32px 24px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}
.page-header h1 { margin: 0; }

/* ── Typography ── */
h1 { font-size: 22px; font-weight: 700; color: #fff; }
h2 { font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 16px; }
h3 { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 12px; }
p  { font-size: 14px; color: var(--muted); }

/* ── Cards ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px;
  margin-bottom: 20px;
}

/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  transition: transform .2s, border-color .2s;
}
.kpi:hover { transform: translateY(-2px); border-color: var(--accent); }
.kpi-label { font-size: 11.5px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-value { font-size: 22px; font-weight: 700; color: #fff; }
.kpi-value.accent {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ── Forms ── */
label {
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
  display: block;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: .04em;
}
input, select {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-family: inherit;
  font-size: 14px;
  padding: 10px 12px;
  width: 100%;
  transition: border-color .2s, box-shadow .2s;
  outline: none;
}
input:focus, select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(124, 106, 247, .15);
}
input::placeholder { color: var(--muted); }
select option { background: var(--surface2); }
.field { display: flex; flex-direction: column; gap: 5px; flex: 1; }
.row   { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 14px; }

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  text-decoration: none;
  transition: all .2s;
  font-family: inherit;
  white-space: nowrap;
}
.btn-primary {
  background: linear-gradient(135deg, var(--accent), #6c5ce7);
  color: #fff;
  box-shadow: 0 4px 14px rgba(124, 106, 247, .3);
}
.btn-primary:hover { box-shadow: 0 6px 20px rgba(124, 106, 247, .45); transform: translateY(-1px); }
.btn-outline { background: transparent; color: var(--text); border: 1px solid var(--border); }
.btn-outline:hover { border-color: var(--accent); color: var(--accent2); }
.btn-danger  { background: rgba(239,68,68,.12);  color: var(--danger);  border: 1px solid rgba(239,68,68,.2); }
.btn-success { background: rgba(34,197,94,.12);  color: var(--success); border: 1px solid rgba(34,197,94,.2); }
.btn-sm { padding: 7px 12px; font-size: 12px; }

/* ── Tables ── */
.table-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); }
table  { width: 100%; border-collapse: collapse; }
th {
  background: var(--surface2);
  color: var(--muted);
  font-size: 11.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .05em;
  padding: 11px 14px;
  text-align: left;
  white-space: nowrap;
}
td { padding: 11px 14px; border-top: 1px solid var(--border); font-size: 13.5px; }
tr:hover td { background: rgba(255,255,255,.02); }

/* ── Badges ── */
.badge { display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11.5px; font-weight: 600; }
.badge-purple { background: rgba(124,106,247,.15); color: var(--accent2); }
.badge-orange { background: rgba(245,158,11,.15);  color: var(--warning); }
.badge-red    { background: rgba(239,68,68,.12);   color: var(--danger); }

/* ── Alerts ── */
.alert { padding: 12px 16px; border-radius: 8px; font-size: 13.5px; margin-bottom: 16px; }
.alert-err { background: rgba(239,68,68,.1);  border: 1px solid rgba(239,68,68,.3);  color: #fca5a5; }
.alert-ok  { background: rgba(34,197,94,.1);  border: 1px solid rgba(34,197,94,.3);  color: #86efac; }

/* ── Invoice Form Specifics ── */
.item-row {
  display: grid;
  grid-template-columns: 1fr 110px 130px 40px;
  gap: 10px;
  align-items: end;
  margin-bottom: 10px;
}
.summary-box { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; }
.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 7px 0;
  font-size: 13.5px;
  border-bottom: 1px solid rgba(255,255,255,.04);
}
.summary-row:last-child { border: none; font-weight: 700; font-size: 15px; padding-top: 10px; color: var(--accent2); }

/* ── Utilities ── */
.flex         { display: flex; }
.gap-2        { gap: 8px; }
.items-center { align-items: center; }
.flex-wrap    { flex-wrap: wrap; }
.mt-4  { margin-top: 16px; }
.mb-4  { margin-bottom: 16px; }
.muted { color: var(--muted); }
.text-right  { text-align: right; }
.text-center { text-align: center; }
.w-full { width: 100%; }

/* ── Animations ── */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate { animation: fadeIn .35s ease; }
</style>
"""
