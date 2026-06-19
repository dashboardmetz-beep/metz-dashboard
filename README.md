# Metz Operations Platform

Streamlit dashboard for Metz Culinary Management — budgets, labor, operations, and CTUIT imports.

## Run locally

```bash
pip install -r requirements.txt
python3 -c "import init_db; init_db.init_database()"
streamlit run app.py
```

Default login: `admin` / `admin123`

Local runs use SQLite (`budget.db`). No env vars required.

---

## Publish (Streamlit Community Cloud + Supabase)

### One-time: provision Supabase

1. Go to **[supabase.com](https://supabase.com)** → sign in with GitHub → **New project**.
   - Name: `metz-dashboard`
   - Password: strong, save it
   - Region: closest to users (e.g. East US)
2. Wait for provisioning (~2 min).
3. Open **SQL Editor**, paste contents of `migration/supabase_schema.sql`, run.
4. Copy contents of `budget.db` into the cloud DB:
   ```bash
   export DATABASE_URL='postgresql://postgres:PWD@db.xxx.supabase.co:5432/postgres'
   python3 migration/load_to_supabase.py
   ```

### Deploy on Streamlit Cloud

1. Push to GitHub:
   ```bash
   git add -A && git commit -m "Deploy" && git push origin main
   ```
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → sign in with GitHub → **Create app**.
   - Repository: `dashboardmetz-beep/metz-dashboard`
   - Branch: `main`
   - Main file: `app.py`
   - App URL slug: `metz-operations`
3. **App settings → Secrets** — paste this (filling in real values):

```toml
DATABASE_URL = "postgresql://postgres:PWD@db.xxx.supabase.co:5432/postgres"
ANTHROPIC_API_KEY = "sk-ant-..."
gmail_token = """
<paste contents of your local token.json here, as JSON text>
"""
```

4. **Deploy.** Live at `https://metz-operations.streamlit.app`.

### Reconnect Gmail later

Gmail's OAuth browser flow only works locally. When the token expires:

1. On your machine: open the dashboard → Settings → Data Import → **🔗 Reconnect Gmail**.
2. Approve in browser. A fresh `token.json` is written.
3. Copy the contents of `token.json` → paste into Streamlit Cloud Secrets under `gmail_token`.

---

## Architecture

- **Frontend + backend:** Streamlit (Python).
- **DB:** SQLite locally / Supabase Postgres in production (set `DATABASE_URL` to switch).
- **Auth:** Custom bcrypt-based user table in `users`. Default `admin`/`admin123`.
- **AI Insights:** Anthropic Claude via `anthropic` SDK.
- **Gmail auto-import:** runs on every dashboard load, pulls Odyssey / CTUIT PDFs.

---

**Demo logins:** `admin` / `admin123` · `director` / `director123`
