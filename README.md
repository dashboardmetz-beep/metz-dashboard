# Metz Operations Platform

Streamlit dashboard for Metz Culinary Management — budgets, labor, operations, and CTUIT imports.

## Run locally

```bash
pip install -r requirements.txt
python3 -c "import init_db; init_db.init_database()"
streamlit run app.py
```

Default login: `admin` / `admin123`

## Publish (Streamlit Community Cloud)

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **Create app** → Repository: `dashboardmetz-beep/metz-dashboard` → Branch: `main` → Main file: `app.py`
3. App URL: `metz-operations` → **Deploy**
4. **App settings → Secrets** (optional):

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

5. Share `https://metz-operations.streamlit.app` with your team.

**Demo logins:** `admin` / `admin123` or `director` / `director123`
