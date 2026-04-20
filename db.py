"""
All database connection and CRUD functions.
Single source of truth for data access.
"""

import sqlite3
import os
from datetime import date, datetime, timedelta
from typing import Optional, List

from config import DB_PATH


# ─────────────────────── Connection ───────────────────────


def get_conn():
    """Get a SQLite connection. Auto-initializes if DB missing."""
    if not os.path.exists(DB_PATH):
        from init_db import init_database
        init_database()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Ensure newer tables exist (safe migration for existing DBs)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budget_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            uploaded_by TEXT NOT NULL,
            uploaded_at DATETIME NOT NULL,
            updated_by TEXT,
            updated_at DATETIME
        )
    """)
    # Add P&L columns to weekly_financials (safe — ignores if already exist)
    _new_fin_cols = [
        ("gross_profit", "REAL DEFAULT 0"),
        ("total_payroll", "REAL DEFAULT 0"),
        ("tax_fringe", "REAL DEFAULT 0"),
        ("after_prime_costs", "REAL DEFAULT 0"),
        ("pace", "REAL DEFAULT 0"),
        ("non_cont_expenses", "REAL DEFAULT 0"),
        ("insurance", "REAL DEFAULT 0"),
        ("profit_fee", "REAL DEFAULT 0"),
        ("royalties", "REAL DEFAULT 0"),
        ("net_income", "REAL DEFAULT 0"),
        ("management_fees", "REAL DEFAULT 0"),
    ]
    for col_name, col_def in _new_fin_cols:
        try:
            conn.execute("ALTER TABLE weekly_financials ADD COLUMN {} {}".format(col_name, col_def))
        except Exception:
            pass  # Column already exists
    # Ensure invoice_tracker table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoice_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            vendor TEXT NOT NULL,
            sun REAL DEFAULT 0,
            mon REAL DEFAULT 0,
            tue REAL DEFAULT 0,
            wed REAL DEFAULT 0,
            thu REAL DEFAULT 0,
            fri REAL DEFAULT 0,
            sat REAL DEFAULT 0,
            weekly_total REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department, section, vendor)
        )
    """)
    # Add section column if missing (migration for existing DBs)
    try:
        conn.execute("ALTER TABLE invoice_tracker ADD COLUMN section TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass
    # Ensure ar_invoices table exists (Accounts Receivable)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ar_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            due_date TEXT,
            total REAL DEFAULT 0,
            current_amount REAL DEFAULT 0,
            days_0_30 REAL DEFAULT 0,
            days_31_60 REAL DEFAULT 0,
            days_61_90 REAL DEFAULT 0,
            days_91_120 REAL DEFAULT 0,
            days_121_150 REAL DEFAULT 0,
            days_151_plus REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(invoice_number)
        )
    """)
    # Ensure meal_plan_tracker table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meal_plan_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester TEXT NOT NULL,
            section TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            budgeted_daily_rate REAL DEFAULT 0,
            actual_daily_rate REAL DEFAULT 0,
            flex_amount REAL DEFAULT 0,
            budgeted_plans INTEGER DEFAULT 0,
            actual_plans INTEGER DEFAULT 0,
            budgeted_revenue REAL DEFAULT 0,
            actual_revenue REAL DEFAULT 0,
            budgeted_flex REAL DEFAULT 0,
            actual_flex REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(semester, section, plan_name)
        )
    """)
    # Ensure ctuit_detail_items table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctuit_detail_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL,
            line_item TEXT NOT NULL,
            amount REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department, section, line_item)
        )
    """)
    return conn


def get_week_start(d):
    """Return the Sunday of the week containing date d (Sun-Sat week).
    Metz fiscal week runs Sunday through Saturday."""
    days_since_sunday = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sunday)


# Keep old name as alias so nothing breaks
get_monday = get_week_start


# ─────────────────────── Users ───────────────────────


def fetch_all_users(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]


def fetch_user(conn, username):
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    return dict(row) if row else None


# ─────────────────────── Budgets (workflow/status) ───────────────────────


def fetch_budget(conn, week_start, department):
    row = conn.execute(
        "SELECT * FROM budgets WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_budget(conn, week_start, department, revenue, labor_dollars,
                  labor_hours, status, username, submit=False):
    existing = fetch_budget(conn, week_start, department)
    now = datetime.now().isoformat()
    if existing:
        version = existing["version"]
        if submit:
            version += 1
        params = {
            "revenue": revenue,
            "labor_dollars": labor_dollars,
            "labor_hours": labor_hours,
            "status": status,
            "version": version,
            "updated_by": username,
            "updated_at": now,
        }
        if submit:
            params["submitted_by"] = username
            params["submitted_at"] = now
        set_clause = ", ".join("{}=?".format(k) for k in params)
        vals = list(params.values()) + [week_start, department]
        conn.execute(
            "UPDATE budgets SET {} WHERE week_start=? AND department=?".format(set_clause),
            vals,
        )
    else:
        conn.execute(
            """INSERT INTO budgets
               (week_start, department, revenue, labor_dollars, labor_hours,
                status, version, updated_by, updated_at, submitted_by, submitted_at)
               VALUES (?,?,?,?,?,?,1,?,?,?,?)""",
            (week_start, department, revenue, labor_dollars, labor_hours,
             status, username, now,
             username if submit else None,
             now if submit else None),
        )
    conn.commit()


def approve_budget(conn, week_start, department, username):
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE budgets SET status='Approved', approved_by=?, approved_at=?, "
        "updated_by=?, updated_at=? WHERE week_start=? AND department=?",
        (username, now, username, now, week_start, department),
    )
    conn.commit()


def return_budget(conn, week_start, department, username):
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE budgets SET status='Returned', updated_by=?, updated_at=? "
        "WHERE week_start=? AND department=?",
        (username, now, week_start, department),
    )
    conn.commit()


def unlock_budget(conn, week_start, department, username):
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE budgets SET status='Draft', updated_by=?, updated_at=? "
        "WHERE week_start=? AND department=?",
        (username, now, week_start, department),
    )
    conn.commit()


# ─────────────────────── Last Year Actuals ───────────────────────


def fetch_ly_actuals(conn, week_start, department):
    current = date.fromisoformat(week_start)
    ly_week = get_week_start(current - timedelta(weeks=52)).isoformat()
    row = conn.execute(
        "SELECT * FROM last_year_actuals WHERE week_start=? AND department=?",
        (ly_week, department),
    ).fetchone()
    return dict(row) if row else None


def fetch_lw_budget(conn, week_start, department):
    current = date.fromisoformat(week_start)
    lw = (current - timedelta(weeks=1)).isoformat()
    row = conn.execute(
        "SELECT * FROM budgets WHERE week_start=? AND department=?",
        (lw, department),
    ).fetchone()
    return dict(row) if row else None


# ─────────────────────── Targets ───────────────────────


def fetch_targets(conn, department):
    row = conn.execute(
        "SELECT * FROM targets WHERE department=?", (department,)
    ).fetchone()
    return dict(row) if row else None


# ─────────────────────── Comments ───────────────────────


def fetch_comments(conn, week_start, department, open_only=True):
    q = "SELECT * FROM comments WHERE week_start=? AND department=?"
    params = [week_start, department]
    if open_only:
        q += " AND is_open=1"
    q += " ORDER BY created_at DESC"
    return [dict(r) for r in conn.execute(q, params).fetchall()]


def fetch_all_open_comments(conn, week_start):
    """Fetch all open comments across all departments for a given week."""
    q = "SELECT * FROM comments WHERE week_start=? AND is_open=1 ORDER BY created_at DESC"
    return [dict(r) for r in conn.execute(q, (week_start,)).fetchall()]


def add_comment(conn, week_start, department, field, reason_code, comment_text, created_by):
    conn.execute(
        """INSERT INTO comments (week_start, department, field, reason_code,
           comment_text, created_by, created_at, is_open)
           VALUES (?,?,?,?,?,?,?,1)""",
        (week_start, department, field, reason_code, comment_text,
         created_by, datetime.now().isoformat()),
    )
    conn.commit()


def close_comment(conn, comment_id):
    conn.execute("UPDATE comments SET is_open=0 WHERE id=?", (comment_id,))
    conn.commit()


# ─────────────────────── Daily Sales ───────────────────────


def fetch_daily_sales(conn, entry_date, department):
    row = conn.execute(
        "SELECT * FROM daily_sales WHERE entry_date=? AND department=?",
        (entry_date, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_daily_sales(conn, entry_date, department, board_revenue, retail_revenue,
                       flex_revenue, catering_revenue, other_revenue, username):
    now = datetime.now().isoformat()
    existing = fetch_daily_sales(conn, entry_date, department)
    if existing:
        conn.execute(
            """UPDATE daily_sales SET board_revenue=?, retail_revenue=?, flex_revenue=?,
               catering_revenue=?, other_revenue=?, updated_by=?, updated_at=?
               WHERE entry_date=? AND department=?""",
            (board_revenue, retail_revenue, flex_revenue, catering_revenue,
             other_revenue, username, now, entry_date, department),
        )
    else:
        conn.execute(
            """INSERT INTO daily_sales (entry_date, department, board_revenue, retail_revenue,
               flex_revenue, catering_revenue, other_revenue, updated_by, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (entry_date, department, board_revenue, retail_revenue,
             flex_revenue, catering_revenue, other_revenue, username, now),
        )
    conn.commit()


def fetch_daily_sales_range(conn, start_date, end_date, department=None):
    """Fetch daily sales for a date range, optionally filtered by department."""
    if department:
        rows = conn.execute(
            "SELECT * FROM daily_sales WHERE entry_date>=? AND entry_date<=? AND department=? ORDER BY entry_date",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM daily_sales WHERE entry_date>=? AND entry_date<=? ORDER BY entry_date, department",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_all_daily_sales_for_date(conn, entry_date):
    """Fetch daily sales for ALL departments for a single date."""
    rows = conn.execute(
        "SELECT * FROM daily_sales WHERE entry_date=? ORDER BY department",
        (entry_date,),
    ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Daily Labor ───────────────────────


def fetch_daily_labor(conn, entry_date, department):
    row = conn.execute(
        "SELECT * FROM daily_labor WHERE entry_date=? AND department=?",
        (entry_date, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_daily_labor(conn, entry_date, department, labor_hours, username):
    now = datetime.now().isoformat()
    existing = fetch_daily_labor(conn, entry_date, department)
    if existing:
        conn.execute(
            """UPDATE daily_labor SET labor_hours=?, updated_by=?, updated_at=?
               WHERE entry_date=? AND department=?""",
            (labor_hours, username, now, entry_date, department),
        )
    else:
        conn.execute(
            """INSERT INTO daily_labor (entry_date, department, labor_hours, updated_by, updated_at)
               VALUES (?,?,?,?,?)""",
            (entry_date, department, labor_hours, username, now),
        )
    conn.commit()


def fetch_daily_labor_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM daily_labor WHERE entry_date>=? AND entry_date<=? AND department=? ORDER BY entry_date",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM daily_labor WHERE entry_date>=? AND entry_date<=? ORDER BY entry_date, department",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Daily Weather ───────────────────────


def fetch_daily_weather(conn, entry_date):
    row = conn.execute(
        "SELECT * FROM daily_weather WHERE entry_date=?", (entry_date,)
    ).fetchone()
    return dict(row) if row else None


def upsert_daily_weather(conn, entry_date, condition, weather_affected, notes, username):
    now = datetime.now().isoformat()
    existing = fetch_daily_weather(conn, entry_date)
    if existing:
        conn.execute(
            """UPDATE daily_weather SET condition=?, weather_affected_staffing=?,
               notes=?, updated_by=?, updated_at=?
               WHERE entry_date=?""",
            (condition, 1 if weather_affected else 0, notes, username, now, entry_date),
        )
    else:
        conn.execute(
            """INSERT INTO daily_weather (entry_date, condition, weather_affected_staffing,
               notes, updated_by, updated_at) VALUES (?,?,?,?,?,?)""",
            (entry_date, condition, 1 if weather_affected else 0, notes, username, now),
        )
    conn.commit()


# ─────────────────────── Daily Notes ───────────────────────


def fetch_daily_notes(conn, entry_date, department):
    """Fetch all daily notes for a date and department. Returns dict keyed by category."""
    rows = conn.execute(
        "SELECT * FROM daily_notes WHERE entry_date=? AND department=? ORDER BY category",
        (entry_date, department),
    ).fetchall()
    result = {}
    for r in rows:
        r = dict(r)
        result[r["category"]] = r["notes"] or ""
    return result


def upsert_daily_note(conn, entry_date, department, category, notes, username):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM daily_notes WHERE entry_date=? AND department=? AND category=?",
        (entry_date, department, category),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE daily_notes SET notes=?, updated_by=?, updated_at=? WHERE id=?",
            (notes, username, now, existing["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO daily_notes (entry_date, department, category, notes, updated_by, updated_at)
               VALUES (?,?,?,?,?,?)""",
            (entry_date, department, category, notes, username, now),
        )
    conn.commit()


# ─────────────────────── Weekly Financials ───────────────────────


def fetch_weekly_financials(conn, week_start, department):
    row = conn.execute(
        "SELECT * FROM weekly_financials WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_weekly_financials(conn, week_start, department, data, username):
    """
    data: dict with keys matching weekly_financials columns
    (board_revenue, retail_revenue, ..., direct_expenses).
    Only updates keys present in data -- preserves existing values from other sources.
    """
    now = datetime.now().isoformat()
    existing = fetch_weekly_financials(conn, week_start, department)
    cols = ["board_revenue", "retail_revenue", "flex_revenue", "catering_revenue",
            "other_revenue", "cos_dollars", "total_labor_dollars", "total_labor_hours",
            "overtime_dollars", "direct_expenses",
            "gross_profit", "total_payroll", "tax_fringe",
            "after_prime_costs", "pace", "non_cont_expenses",
            "insurance", "profit_fee", "royalties", "net_income", "management_fees"]

    if existing:
        # Only update keys present in data -- preserve existing values
        update_cols = [c for c in cols if c in data]
        if not update_cols:
            return
        sets = ", ".join("{}=?".format(c) for c in update_cols)
        sets += ", updated_by=?, updated_at=?"
        vals = [data[c] for c in update_cols] + [username, now, week_start, department]
        conn.execute(
            "UPDATE weekly_financials SET {} WHERE week_start=? AND department=?".format(sets),
            vals,
        )
    else:
        all_cols = cols + ["week_start", "department", "updated_by", "updated_at"]
        placeholders = ", ".join(["?"] * len(all_cols))
        vals = [data.get(c, 0) for c in cols] + [week_start, department, username, now]
        conn.execute(
            "INSERT INTO weekly_financials ({}) VALUES ({})".format(
                ", ".join(all_cols), placeholders
            ),
            vals,
        )
    conn.commit()


# ─────────────────────── Weekly Flash Targets ───────────────────────


def fetch_weekly_flash_targets(conn, week_start, department):
    row = conn.execute(
        "SELECT * FROM weekly_flash_targets WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_weekly_flash_targets(conn, week_start, department, data, username):
    now = datetime.now().isoformat()
    existing = fetch_weekly_flash_targets(conn, week_start, department)

    cols = [k for k in data.keys() if k.startswith("budget_") or k.startswith("projection_")]

    if existing:
        sets = ", ".join("{}=?".format(c) for c in cols)
        sets += ", updated_by=?, updated_at=?"
        vals = [data[c] for c in cols] + [username, now, week_start, department]
        conn.execute(
            "UPDATE weekly_flash_targets SET {} WHERE week_start=? AND department=?".format(sets),
            vals,
        )
    else:
        all_cols = cols + ["week_start", "department", "updated_by", "updated_at"]
        placeholders = ", ".join(["?"] * len(all_cols))
        vals = [data[c] for c in cols] + [week_start, department, username, now]
        conn.execute(
            "INSERT INTO weekly_flash_targets ({}) VALUES ({})".format(
                ", ".join(all_cols), placeholders
            ),
            vals,
        )
    conn.commit()


# ─────────────────────── Weekly Operational ───────────────────────


def fetch_weekly_operational(conn, week_start, department):
    row = conn.execute(
        "SELECT * FROM weekly_operational WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return dict(row) if row else None


def fetch_weekly_operational_targets(conn, week_start, department):
    row = conn.execute(
        "SELECT * FROM weekly_operational_targets WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return dict(row) if row else None


def fetch_weekly_meal_plan_total(conn, week_start):
    """Sum meal_plan_participation meals_used for a Sun-Sat week, resident plan only."""
    ws = date.fromisoformat(week_start)
    we = ws + timedelta(days=6)
    row = conn.execute(
        "SELECT COALESCE(SUM(meals_used), 0) as total_meals "
        "FROM meal_plan_participation "
        "WHERE entry_date>=? AND entry_date<=? AND plan_type='resident'",
        (ws.isoformat(), we.isoformat()),
    ).fetchone()
    return row["total_meals"] if row else 0


def upsert_weekly_operational(conn, week_start, department, data, username):
    now = datetime.now().isoformat()
    existing = fetch_weekly_operational(conn, week_start, department)

    cols = [
        "students_resident_plan", "students_commuter_plan",
        "meals_used_participation_pct", "board_plan_billing_days",
        "board_plan_labor_hours", "retail_labor_hours",
        "catering_labor_hours", "concession_labor_hours",
        "conference_labor_hours", "ot_hours_included_above",
        "ot_dollars_paid", "temp_hours_included_above",
        "temp_dollars_paid", "management_wages", "hourly_wages",
        "average_hourly_wage", "fee_account_fee", "total_inventory",
    ]

    if existing:
        # Only update keys present in data — preserve existing values from other sources
        update_cols = [c for c in cols if c in data]
        if not update_cols:
            return
        sets = ", ".join("{}=?".format(c) for c in update_cols)
        sets += ", updated_by=?, updated_at=?"
        vals = [data[c] for c in update_cols] + [username, now, week_start, department]
        conn.execute(
            "UPDATE weekly_operational SET {} WHERE week_start=? AND department=?".format(sets),
            vals,
        )
    else:
        all_cols = cols + ["week_start", "department", "updated_by", "updated_at"]
        placeholders = ", ".join(["?"] * len(all_cols))
        vals = [data.get(c, 0) for c in cols] + [week_start, department, username, now]
        conn.execute(
            "INSERT INTO weekly_operational ({}) VALUES ({})".format(
                ", ".join(all_cols), placeholders
            ),
            vals,
        )
    conn.commit()


def upsert_weekly_operational_targets(conn, week_start, department, data, username):
    """Upsert budget/projection values for operational metrics."""
    now = datetime.now().isoformat()
    existing = fetch_weekly_operational_targets(conn, week_start, department)

    cols = [
        "budget_students_resident", "budget_students_commuter",
        "budget_participation_pct", "budget_billing_days",
        "budget_board_labor_hours", "budget_retail_labor_hours",
        "budget_catering_labor_hours", "budget_concession_labor_hours",
        "budget_conference_labor_hours", "budget_ot_hours",
        "budget_ot_dollars", "budget_temp_hours", "budget_temp_dollars",
        "budget_management_wages", "budget_hourly_wages",
        "budget_avg_hourly_wage", "budget_fee_account_fee",
        "budget_total_inventory",
        "projection_students_resident", "projection_students_commuter",
        "projection_participation_pct", "projection_billing_days",
        "projection_board_labor_hours", "projection_retail_labor_hours",
        "projection_catering_labor_hours", "projection_concession_labor_hours",
        "projection_conference_labor_hours", "projection_ot_hours",
        "projection_ot_dollars", "projection_temp_hours",
        "projection_temp_dollars", "projection_management_wages",
        "projection_hourly_wages", "projection_avg_hourly_wage",
        "projection_fee_account_fee", "projection_total_inventory",
    ]

    if existing:
        # Only update keys present in data, preserve existing values
        update_cols = [c for c in cols if c in data]
        if not update_cols:
            return
        sets = ", ".join("{}=?".format(c) for c in update_cols)
        sets += ", updated_by=?, updated_at=?"
        vals = [data[c] for c in update_cols] + [username, now, week_start, department]
        conn.execute(
            "UPDATE weekly_operational_targets SET {} WHERE week_start=? AND department=?".format(sets),
            vals,
        )
    else:
        all_cols = cols + ["week_start", "department", "updated_by", "updated_at"]
        placeholders = ", ".join(["?"] * len(all_cols))
        vals = [data.get(c, 0) for c in cols] + [week_start, department, username, now]
        conn.execute(
            "INSERT INTO weekly_operational_targets ({}) VALUES ({})".format(
                ", ".join(all_cols), placeholders
            ),
            vals,
        )
    conn.commit()


# ─────────────────────── Flash Explanations ───────────────────────


def fetch_flash_explanations(conn, week_start, department):
    """Returns a dict keyed by (line_item, variance_type) -> explanation."""
    rows = conn.execute(
        "SELECT * FROM flash_explanations WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchall()
    result = {}
    for r in rows:
        r = dict(r)
        key = (r["line_item"], r["variance_type"])
        result[key] = r["explanation"]
    return result


def upsert_flash_explanation(conn, week_start, department, line_item, variance_type,
                             explanation, username):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM flash_explanations WHERE week_start=? AND department=? "
        "AND line_item=? AND variance_type=?",
        (week_start, department, line_item, variance_type),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE flash_explanations SET explanation=?, updated_by=?, updated_at=? WHERE id=?",
            (explanation, username, now, existing["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO flash_explanations
               (week_start, department, line_item, variance_type, explanation, updated_by, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (week_start, department, line_item, variance_type, explanation, username, now),
        )
    conn.commit()


# ─────────────────────── Food Cost ───────────────────────


def fetch_food_cost(conn, week_start, department):
    row = conn.execute(
        "SELECT * FROM food_cost WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_food_cost(conn, week_start, department, invoice_total, inv_start,
                     inv_end, adjustments, notes, username):
    now = datetime.now().isoformat()
    existing = fetch_food_cost(conn, week_start, department)
    if existing:
        conn.execute(
            """UPDATE food_cost SET invoice_total=?, inventory_start=?, inventory_end=?,
               adjustments=?, notes=?, updated_by=?, updated_at=?
               WHERE week_start=? AND department=?""",
            (invoice_total, inv_start, inv_end, adjustments, notes, username, now,
             week_start, department),
        )
    else:
        conn.execute(
            """INSERT INTO food_cost (week_start, department, invoice_total, inventory_start,
               inventory_end, adjustments, notes, updated_by, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (week_start, department, invoice_total, inv_start, inv_end, adjustments,
             notes, username, now),
        )
    conn.commit()


# ─────────────────────── Labor Schedule ───────────────────────


def fetch_labor_schedule(conn, entry_date, department):
    row = conn.execute(
        "SELECT * FROM labor_schedule WHERE entry_date=? AND department=?",
        (entry_date, department),
    ).fetchone()
    return dict(row) if row else None


def upsert_labor_schedule(conn, entry_date, department, scheduled_hours, actual_hours,
                          source="manual"):
    now = datetime.now().isoformat()
    variance_hrs = (actual_hours or 0) - (scheduled_hours or 0)
    existing = fetch_labor_schedule(conn, entry_date, department)
    if existing:
        conn.execute(
            """UPDATE labor_schedule SET scheduled_hours=?, actual_hours=?,
               variance_hours=?, source=?, updated_at=?
               WHERE entry_date=? AND department=?""",
            (scheduled_hours, actual_hours, variance_hrs, source, now,
             entry_date, department),
        )
    else:
        conn.execute(
            """INSERT INTO labor_schedule (entry_date, department, scheduled_hours,
               actual_hours, variance_hours, source, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (entry_date, department, scheduled_hours, actual_hours, variance_hrs,
             source, now),
        )
    conn.commit()


def fetch_labor_schedule_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM labor_schedule WHERE entry_date>=? AND entry_date<=? AND department=? ORDER BY entry_date",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM labor_schedule WHERE entry_date>=? AND entry_date<=? ORDER BY entry_date, department",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Door Counts ───────────────────────


def upsert_door_count(conn, entry_date, department, meal_period, count, username="system"):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM door_counts WHERE entry_date=? AND department=? AND meal_period=?",
        (entry_date, department, meal_period),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE door_counts SET count=?, updated_by=?, updated_at=? WHERE id=?",
            (count, username, now, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO door_counts (entry_date, department, meal_period, count, updated_by, updated_at) VALUES (?,?,?,?,?,?)",
            (entry_date, department, meal_period, count, username, now),
        )
    conn.commit()


def fetch_door_counts(conn, entry_date, department):
    rows = conn.execute(
        "SELECT * FROM door_counts WHERE entry_date=? AND department=? ORDER BY meal_period",
        (entry_date, department),
    ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Meal Plan Participation ───────────────────────


def fetch_meal_plan_for_date(conn, entry_date):
    """Fetch all meal plan records for a date."""
    rows = conn.execute(
        "SELECT * FROM meal_plan_participation WHERE entry_date=? ORDER BY plan_type",
        (entry_date,),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_meal_plan(conn, entry_date, plan_type, enrolled_count, meals_used, billing_days, username):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM meal_plan_participation WHERE entry_date=? AND plan_type=?",
        (entry_date, plan_type),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE meal_plan_participation SET enrolled_count=?, meals_used=?,
               billing_days=?, updated_by=?, updated_at=? WHERE id=?""",
            (enrolled_count, meals_used, billing_days, username, now, existing["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO meal_plan_participation (entry_date, plan_type, enrolled_count,
               meals_used, billing_days, updated_by, updated_at) VALUES (?,?,?,?,?,?,?)""",
            (entry_date, plan_type, enrolled_count, meals_used, billing_days, username, now),
        )
    conn.commit()


def fetch_meal_plan_range(conn, start_date, end_date):
    rows = conn.execute(
        "SELECT * FROM meal_plan_participation WHERE entry_date>=? AND entry_date<=? ORDER BY entry_date, plan_type",
        (start_date, end_date),
    ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Meal Exchange (Qdoba & Retail & Mac's Grill) ───────────────────────


def fetch_meal_exchange(conn, entry_date, department):
    row = conn.execute(
        "SELECT * FROM meal_exchange WHERE entry_date=? AND department=?",
        (entry_date, department),
    ).fetchone()
    return dict(row) if row else {}


def upsert_meal_exchange(conn, entry_date, department, exchange_count, dollar_amount, username):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM meal_exchange WHERE entry_date=? AND department=?",
        (entry_date, department),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE meal_exchange SET exchange_count=?, dollar_amount=?,
               updated_by=?, updated_at=? WHERE id=?""",
            (exchange_count, dollar_amount, username, now, existing["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO meal_exchange (entry_date, department, exchange_count,
               dollar_amount, updated_by, updated_at) VALUES (?,?,?,?,?,?)""",
            (entry_date, department, exchange_count, dollar_amount, username, now),
        )
    conn.commit()


def fetch_meal_exchange_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM meal_exchange WHERE entry_date>=? AND entry_date<=? AND department=? ORDER BY entry_date",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM meal_exchange WHERE entry_date>=? AND entry_date<=? ORDER BY entry_date, department",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Split Transactions ───────────────────────


def fetch_split_transactions(conn, transaction_date, department):
    rows = conn.execute(
        "SELECT * FROM split_transactions WHERE transaction_date=? AND department=? ORDER BY id",
        (transaction_date, department),
    ).fetchall()
    return [dict(r) for r in rows]


def add_split_transaction(conn, transaction_date, department, transaction_id,
                          tender1, amount1, tender2, amount2, tender3, amount3, total):
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT INTO split_transactions (transaction_date, department, transaction_id,
           tender_type_1, amount_1, tender_type_2, amount_2, tender_type_3, amount_3,
           total_amount, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (transaction_date, department, transaction_id, tender1, amount1,
         tender2, amount2, tender3, amount3, total, now),
    )
    conn.commit()


def fetch_split_transactions_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM split_transactions WHERE transaction_date>=? AND transaction_date<=? AND department=? ORDER BY transaction_date",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM split_transactions WHERE transaction_date>=? AND transaction_date<=? ORDER BY transaction_date",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_door_counts_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM door_counts WHERE entry_date>=? AND entry_date<=? AND department=? ORDER BY entry_date, meal_period",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM door_counts WHERE entry_date>=? AND entry_date<=? ORDER BY entry_date, department, meal_period",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_food_cost_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM food_cost WHERE week_start>=? AND week_start<=? AND department=? ORDER BY week_start",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM food_cost WHERE week_start>=? AND week_start<=? ORDER BY week_start, department",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Invoice Tracker ───────────────────────


def fetch_invoices(conn, week_start, department):
    """Fetch all vendor invoice rows for a week/department."""
    rows = conn.execute(
        "SELECT * FROM invoice_tracker WHERE week_start=? AND department=? "
        "ORDER BY section, vendor",
        (week_start, department),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_invoice(conn, week_start, department, vendor, day_amounts, username,
                   section=""):
    """Upsert a single vendor invoice row.
    day_amounts: dict with keys sun, mon, tue, wed, thu, fri, sat.
    section: sub-section within department (e.g. 'Hamilton', 'Catering').
    """
    now = datetime.now().isoformat()
    weekly_total = sum(
        float(day_amounts.get(d, 0) or 0)
        for d in ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
    )
    existing = conn.execute(
        "SELECT id FROM invoice_tracker "
        "WHERE week_start=? AND department=? AND section=? AND vendor=?",
        (week_start, department, section, vendor),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE invoice_tracker SET sun=?, mon=?, tue=?, wed=?, thu=?, fri=?, sat=?,
               weekly_total=?, updated_by=?, updated_at=?
               WHERE week_start=? AND department=? AND section=? AND vendor=?""",
            (
                float(day_amounts.get("sun", 0) or 0),
                float(day_amounts.get("mon", 0) or 0),
                float(day_amounts.get("tue", 0) or 0),
                float(day_amounts.get("wed", 0) or 0),
                float(day_amounts.get("thu", 0) or 0),
                float(day_amounts.get("fri", 0) or 0),
                float(day_amounts.get("sat", 0) or 0),
                weekly_total, username, now,
                week_start, department, section, vendor,
            ),
        )
    else:
        conn.execute(
            """INSERT INTO invoice_tracker (week_start, department, section, vendor,
               sun, mon, tue, wed, thu, fri, sat, weekly_total, updated_by, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                week_start, department, section, vendor,
                float(day_amounts.get("sun", 0) or 0),
                float(day_amounts.get("mon", 0) or 0),
                float(day_amounts.get("tue", 0) or 0),
                float(day_amounts.get("wed", 0) or 0),
                float(day_amounts.get("thu", 0) or 0),
                float(day_amounts.get("fri", 0) or 0),
                float(day_amounts.get("sat", 0) or 0),
                weekly_total, username, now,
            ),
        )
    conn.commit()


def delete_invoice(conn, week_start, department, vendor, section=""):
    """Remove a vendor invoice row."""
    conn.execute(
        "DELETE FROM invoice_tracker "
        "WHERE week_start=? AND department=? AND section=? AND vendor=?",
        (week_start, department, section, vendor),
    )
    conn.commit()


def fetch_invoice_total_for_department(conn, week_start, department):
    """Sum all vendor weekly_totals for a department/week. Returns float."""
    row = conn.execute(
        "SELECT COALESCE(SUM(weekly_total), 0) as total FROM invoice_tracker "
        "WHERE week_start=? AND department=?",
        (week_start, department),
    ).fetchone()
    return float(row["total"]) if row else 0.0


# ─────────────────────── Budget Attachments ───────────────────────


def fetch_attachments(conn, week_start, department):
    """Fetch all attachments for a given week and department."""
    rows = conn.execute(
        "SELECT * FROM budget_attachments WHERE week_start=? AND department=? "
        "ORDER BY uploaded_at DESC",
        (week_start, department),
    ).fetchall()
    return [dict(r) for r in rows]


def insert_attachment(conn, week_start, department, original_filename,
                      stored_path, file_type, file_size, username):
    """Insert a new attachment record."""
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT INTO budget_attachments
           (week_start, department, original_filename, stored_path,
            file_type, file_size, uploaded_by, uploaded_at, updated_by, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (week_start, department, original_filename, stored_path,
         file_type, file_size, username, now, username, now),
    )
    conn.commit()


def delete_attachment(conn, attachment_id):
    """Delete an attachment record by ID. Caller must also remove the file."""
    conn.execute("DELETE FROM budget_attachments WHERE id=?", (attachment_id,))
    conn.commit()


# ─────────────────────── CTUIT Detail Items ───────────────────────


def fetch_ctuit_details(conn, week_start, department, section=None):
    """Fetch CTUIT detail line items. Optionally filter by section."""
    if section:
        rows = conn.execute(
            "SELECT * FROM ctuit_detail_items WHERE week_start=? AND department=? AND section=? ORDER BY section, line_item",
            (week_start, department, section),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM ctuit_detail_items WHERE week_start=? AND department=? ORDER BY section, line_item",
            (week_start, department),
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_ctuit_details(conn, week_start, department, details, username):
    """Save CTUIT detail line items. details = list of (section, line_item, amount)."""
    now = datetime.now().isoformat()
    for section, line_item, amount in details:
        conn.execute(
            """INSERT INTO ctuit_detail_items
               (week_start, department, section, line_item, amount, updated_by, updated_at)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(week_start, department, section, line_item)
               DO UPDATE SET amount=?, updated_by=?, updated_at=?""",
            (week_start, department, section, line_item, amount, username, now,
             amount, username, now),
        )
    conn.commit()


# ─────────────────────── Import Logs ───────────────────────


def add_email_import_log(conn, email_subject, email_sender, email_date,
                         import_type, status, records_imported, error_message,
                         triggered_by):
    conn.execute(
        """INSERT INTO email_import_log (import_timestamp, email_subject, email_sender,
           email_date, import_type, status, records_imported, error_message, triggered_by)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (datetime.now().isoformat(), email_subject, email_sender, email_date,
         import_type, status, records_imported, error_message, triggered_by),
    )
    conn.commit()


def fetch_import_logs(conn, limit=50):
    rows = conn.execute(
        "SELECT * FROM email_import_log ORDER BY import_timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_last_import_timestamp(conn):
    """Return the most recent successful import timestamp string, or None."""
    row = conn.execute(
        "SELECT import_timestamp FROM email_import_log "
        "WHERE status='success' ORDER BY import_timestamp DESC LIMIT 1"
    ).fetchone()
    if row:
        return row["import_timestamp"]
    return None


def add_adp_sync_log(conn, sync_type, status, records_synced, error_message, triggered_by):
    conn.execute(
        """INSERT INTO adp_sync_log (sync_timestamp, sync_type, status,
           records_synced, error_message, triggered_by)
           VALUES (?,?,?,?,?,?)""",
        (datetime.now().isoformat(), sync_type, status, records_synced,
         error_message, triggered_by),
    )
    conn.commit()


# ─────────────────────── Daily Rollup to Weekly ───────────────────────


def rollup_daily_to_weekly(conn, week_start, department):
    """
    Sum daily_sales and daily_labor for a week (Sun-Sat) into weekly totals.
    Returns a dict with the rolled-up values.
    """
    ws = date.fromisoformat(week_start)
    we = ws + timedelta(days=6)
    start_str = ws.isoformat()
    end_str = we.isoformat()

    # Sum daily sales
    sales_row = conn.execute(
        """SELECT
            COALESCE(SUM(board_revenue), 0) as board_revenue,
            COALESCE(SUM(retail_revenue), 0) as retail_revenue,
            COALESCE(SUM(flex_revenue), 0) as flex_revenue,
            COALESCE(SUM(catering_revenue), 0) as catering_revenue,
            COALESCE(SUM(other_revenue), 0) as other_revenue
           FROM daily_sales
           WHERE entry_date>=? AND entry_date<=? AND department=?""",
        (start_str, end_str, department),
    ).fetchone()

    # Sum daily labor
    labor_row = conn.execute(
        """SELECT COALESCE(SUM(labor_hours), 0) as total_labor_hours
           FROM daily_labor
           WHERE entry_date>=? AND entry_date<=? AND department=?""",
        (start_str, end_str, department),
    ).fetchone()

    result = dict(sales_row) if sales_row else {}
    result["total_labor_hours"] = labor_row["total_labor_hours"] if labor_row else 0
    return result


# ─────────────────────── Calendar Events ───────────────────────


def fetch_calendar_events(conn, start_date, end_date, category=None):
    """Fetch events in a date range, optionally filtered by category."""
    if category:
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date>=? AND event_date<=? AND category=? ORDER BY event_date",
            (start_date, end_date, category),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date>=? AND event_date<=? ORDER BY event_date",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_dining_impact_events(conn, start_date, end_date):
    """Fetch only events that affect dining operations."""
    rows = conn.execute(
        "SELECT * FROM calendar_events WHERE event_date>=? AND event_date<=? AND affects_dining=1 ORDER BY event_date",
        (start_date, end_date),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_upcoming_events(conn, from_date, days_ahead=14):
    """Fetch events in the next N days for reminders."""
    end = (date.fromisoformat(from_date) + timedelta(days=days_ahead)).isoformat()
    rows = conn.execute(
        "SELECT * FROM calendar_events WHERE event_date>=? AND event_date<=? ORDER BY event_date",
        (from_date, end),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_calendar_event(conn, event_date, title, category, description=None, end_date=None, affects_dining=0, dining_impact=None, username="system"):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM calendar_events WHERE event_date=? AND title=?",
        (event_date, title),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE calendar_events SET end_date=?, description=?, category=?, affects_dining=?, dining_impact=?, created_by=?, created_at=? WHERE id=?",
            (end_date, description, category, affects_dining, dining_impact, username, now, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO calendar_events (event_date, end_date, title, description, category, affects_dining, dining_impact, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (event_date, end_date, title, description, category, affects_dining, dining_impact, username, now),
        )
    conn.commit()


def delete_calendar_event(conn, event_id):
    conn.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    conn.commit()


# ─────────────────────── Catering Events ───────────────────────


def fetch_catering_events(conn, start_date, end_date, status=None):
    if status:
        rows = conn.execute(
            "SELECT * FROM catering_events WHERE event_date>=? AND event_date<=? AND status=? ORDER BY event_date, start_time",
            (start_date, end_date, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM catering_events WHERE event_date>=? AND event_date<=? ORDER BY event_date, start_time",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_catering_event(conn, event_id):
    row = conn.execute("SELECT * FROM catering_events WHERE id=?", (event_id,)).fetchone()
    return dict(row) if row else {}


def upsert_catering_event(conn, event_date, event_name, username, **kwargs):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM catering_events WHERE event_date=? AND event_name=?",
        (event_date, event_name),
    ).fetchone()

    fields = ["client_name", "department", "event_type", "location", "start_time",
              "end_time", "guest_count", "setup_style", "menu_notes", "special_requests",
              "dietary_notes", "equipment_needed", "staffing_notes", "status",
              "total_cost", "billed_amount"]

    if existing:
        sets = []
        vals = []
        for f in fields:
            if f in kwargs:
                sets.append("{}=?".format(f))
                vals.append(kwargs[f])
        sets.append("updated_by=?")
        vals.append(username)
        sets.append("updated_at=?")
        vals.append(now)
        vals.append(existing["id"])
        conn.execute(
            "UPDATE catering_events SET {} WHERE id=?".format(", ".join(sets)),
            vals,
        )
    else:
        cols = ["event_date", "event_name", "created_by", "created_at", "updated_by", "updated_at"]
        vals = [event_date, event_name, username, now, username, now]
        for f in fields:
            if f in kwargs:
                cols.append(f)
                vals.append(kwargs[f])
        placeholders = ", ".join(["?"] * len(vals))
        conn.execute(
            "INSERT INTO catering_events ({}) VALUES ({})".format(", ".join(cols), placeholders),
            vals,
        )
    conn.commit()


def update_catering_status(conn, event_id, status, username):
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE catering_events SET status=?, updated_by=?, updated_at=? WHERE id=?",
        (status, username, now, event_id),
    )
    conn.commit()


def delete_catering_event(conn, event_id):
    conn.execute("DELETE FROM catering_event_items WHERE event_id=?", (event_id,))
    conn.execute("DELETE FROM catering_events WHERE id=?", (event_id,))
    conn.commit()


def fetch_upcoming_catering(conn, from_date, days_ahead=14):
    end = (date.fromisoformat(from_date) + timedelta(days=days_ahead)).isoformat()
    rows = conn.execute(
        "SELECT * FROM catering_events WHERE event_date>=? AND event_date<=? ORDER BY event_date, start_time",
        (from_date, end),
    ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Safety & Compliance ───────────────────────


def fetch_safety_checklist(conn, checklist_date, department, checklist_type):
    row = conn.execute(
        "SELECT * FROM safety_checklists WHERE checklist_date=? AND department=? AND checklist_type=?",
        (checklist_date, department, checklist_type),
    ).fetchone()
    return dict(row) if row else {}


def fetch_checklist_items(conn, checklist_id):
    rows = conn.execute(
        "SELECT * FROM safety_checklist_items WHERE checklist_id=? ORDER BY id",
        (checklist_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_safety_checklist(conn, checklist_date, department, checklist_type, username, status="Incomplete", notes=None):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM safety_checklists WHERE checklist_date=? AND department=? AND checklist_type=?",
        (checklist_date, department, checklist_type),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE safety_checklists SET status=?, notes=?, completed_by=?, completed_at=? WHERE id=?",
            (status, notes, username, now, existing["id"]),
        )
        conn.commit()
        return existing["id"]
    else:
        conn.execute(
            "INSERT INTO safety_checklists (checklist_date, department, checklist_type, completed_by, completed_at, status, notes) VALUES (?,?,?,?,?,?,?)",
            (checklist_date, department, checklist_type, username, now, status, notes),
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def upsert_checklist_item(conn, checklist_id, item_name, is_checked, value=None, notes=None, username=None):
    now = datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM safety_checklist_items WHERE checklist_id=? AND item_name=?",
        (checklist_id, item_name),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE safety_checklist_items SET is_checked=?, value=?, notes=?, checked_by=?, checked_at=? WHERE id=?",
            (is_checked, value, notes, username, now, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO safety_checklist_items (checklist_id, item_name, is_checked, value, notes, checked_by, checked_at) VALUES (?,?,?,?,?,?,?)",
            (checklist_id, item_name, is_checked, value, notes, username, now),
        )
    conn.commit()


def fetch_temp_logs(conn, log_date, department):
    rows = conn.execute(
        "SELECT * FROM temp_logs WHERE log_date=? AND department=? ORDER BY logged_at",
        (log_date, department),
    ).fetchall()
    return [dict(r) for r in rows]


def add_temp_log(conn, log_date, department, equipment_name, temp_reading, in_range, corrective_action, username):
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO temp_logs (log_date, department, equipment_name, temp_reading, in_range, corrective_action, logged_by, logged_at) VALUES (?,?,?,?,?,?,?,?)",
        (log_date, department, equipment_name, temp_reading, in_range, corrective_action or None, username, now),
    )
    conn.commit()


def fetch_safety_history(conn, department, days_back=30):
    cutoff = (date.today() - timedelta(days=days_back)).isoformat()
    rows = conn.execute(
        "SELECT * FROM safety_checklists WHERE department=? AND checklist_date>=? ORDER BY checklist_date DESC",
        (department, cutoff),
    ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────── Waste Tracking ───────────────────────


def fetch_waste_logs(conn, log_date, department):
    rows = conn.execute(
        "SELECT * FROM waste_log WHERE log_date=? AND department=? ORDER BY logged_at",
        (log_date, department),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_waste_logs_range(conn, start_date, end_date, department=None):
    if department:
        rows = conn.execute(
            "SELECT * FROM waste_log WHERE log_date>=? AND log_date<=? AND department=? ORDER BY log_date, logged_at",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM waste_log WHERE log_date>=? AND log_date<=? ORDER BY log_date, department, logged_at",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def add_waste_log(conn, log_date, department, category, item_description, weight_lbs, estimated_cost, reason, meal_period, corrective_action, username):
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO waste_log (log_date, department, category, item_description, weight_lbs, estimated_cost, reason, meal_period, corrective_action, logged_by, logged_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (log_date, department, category, item_description, weight_lbs, estimated_cost, reason or None, meal_period or None, corrective_action or None, username, now),
    )
    conn.commit()


def delete_waste_log(conn, log_id):
    conn.execute("DELETE FROM waste_log WHERE id=?", (log_id,))
    conn.commit()


def fetch_waste_summary(conn, start_date, end_date, department=None):
    """Get waste totals grouped by category."""
    if department:
        rows = conn.execute(
            "SELECT category, SUM(weight_lbs) as total_weight, SUM(estimated_cost) as total_cost, COUNT(*) as entry_count "
            "FROM waste_log WHERE log_date>=? AND log_date<=? AND department=? GROUP BY category ORDER BY total_cost DESC",
            (start_date, end_date, department),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT category, SUM(weight_lbs) as total_weight, SUM(estimated_cost) as total_cost, COUNT(*) as entry_count "
            "FROM waste_log WHERE log_date>=? AND log_date<=? GROUP BY category ORDER BY total_cost DESC",
            (start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════
# PRE-SERVICE MEETINGS
# ═══════════════════════════════════════════════════════

def fetch_preservice_meetings(conn, department, start_date, end_date):
    """Fetch pre-service meetings for a department in a date range."""
    sql = """
        SELECT * FROM preservice_meetings
        WHERE department = ? AND meeting_date BETWEEN ? AND ?
        ORDER BY meeting_date DESC, meal_period
    """
    cur = conn.execute(sql, (department, start_date, end_date))
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


def fetch_preservice_meeting(conn, meeting_id):
    """Fetch a single pre-service meeting by ID."""
    cur = conn.execute("SELECT * FROM preservice_meetings WHERE id = ?", (meeting_id,))
    cur.row_factory = sqlite3.Row
    row = cur.fetchone()
    return dict(row) if row else None


def upsert_preservice_meeting(conn, meeting_date, department, meal_period,
                                led_by, attendee_count, menu_highlights,
                                items_86d, vip_info, event_notes,
                                safety_reminders, general_notes, action_items,
                                username="system"):
    """Insert or update a pre-service meeting."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO preservice_meetings
            (meeting_date, department, meal_period, led_by, attendee_count,
             menu_highlights, items_86d, vip_info, event_notes,
             safety_reminders, general_notes, action_items, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(meeting_date, department, meal_period) DO UPDATE SET
            led_by=excluded.led_by,
            attendee_count=excluded.attendee_count,
            menu_highlights=excluded.menu_highlights,
            items_86d=excluded.items_86d,
            vip_info=excluded.vip_info,
            event_notes=excluded.event_notes,
            safety_reminders=excluded.safety_reminders,
            general_notes=excluded.general_notes,
            action_items=excluded.action_items,
            created_by=excluded.created_by,
            created_at=excluded.created_at
    """, (meeting_date, department, meal_period, led_by, attendee_count,
          menu_highlights, items_86d, vip_info, event_notes,
          safety_reminders, general_notes, action_items, username, now))
    conn.commit()


def delete_preservice_meeting(conn, meeting_id):
    """Delete a pre-service meeting."""
    conn.execute("DELETE FROM preservice_meetings WHERE id = ?", (meeting_id,))
    conn.commit()


def fetch_todays_preservice(conn, department, today_str):
    """Fetch today's pre-service meetings for a department."""
    sql = """
        SELECT * FROM preservice_meetings
        WHERE department = ? AND meeting_date = ?
        ORDER BY meal_period
    """
    cur = conn.execute(sql, (department, today_str))
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


# ═══════════════════════════════════════════════════════
# SHIFT COMMUNICATIONS
# ═══════════════════════════════════════════════════════

def fetch_shift_communications(conn, department, start_date, end_date):
    """Fetch shift communications for a department in a date range."""
    sql = """
        SELECT * FROM shift_communications
        WHERE department = ? AND comm_date BETWEEN ? AND ?
        ORDER BY comm_date DESC, shift_type
    """
    cur = conn.execute(sql, (department, start_date, end_date))
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


def fetch_shift_comm(conn, comm_id):
    """Fetch a single shift communication by ID."""
    cur = conn.execute("SELECT * FROM shift_communications WHERE id = ?", (comm_id,))
    cur.row_factory = sqlite3.Row
    row = cur.fetchone()
    return dict(row) if row else None


def upsert_shift_communication(conn, comm_date, department, shift_type,
                                 author, tasks_completed, tasks_pending,
                                 equipment_issues, inventory_notes,
                                 staff_notes, safety_concerns, general_notes,
                                 urgent_flag, username="system"):
    """Insert or update a shift communication."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO shift_communications
            (comm_date, department, shift_type, author, tasks_completed,
             tasks_pending, equipment_issues, inventory_notes, staff_notes,
             safety_concerns, general_notes, urgent_flag, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(comm_date, department, shift_type) DO UPDATE SET
            author=excluded.author,
            tasks_completed=excluded.tasks_completed,
            tasks_pending=excluded.tasks_pending,
            equipment_issues=excluded.equipment_issues,
            inventory_notes=excluded.inventory_notes,
            staff_notes=excluded.staff_notes,
            safety_concerns=excluded.safety_concerns,
            general_notes=excluded.general_notes,
            urgent_flag=excluded.urgent_flag,
            created_by=excluded.created_by,
            created_at=excluded.created_at
    """, (comm_date, department, shift_type, author, tasks_completed,
          tasks_pending, equipment_issues, inventory_notes, staff_notes,
          safety_concerns, general_notes, urgent_flag, username, now))
    conn.commit()


def mark_shift_comm_read(conn, comm_id, reader_username):
    """Mark a shift communication as read by a user."""
    cur = conn.execute("SELECT read_by FROM shift_communications WHERE id = ?", (comm_id,))
    row = cur.fetchone()
    if row:
        existing = row[0] or ""
        readers = [r.strip() for r in existing.split(",") if r.strip()]
        if reader_username not in readers:
            readers.append(reader_username)
        conn.execute("UPDATE shift_communications SET read_by = ? WHERE id = ?",
                      (", ".join(readers), comm_id))
        conn.commit()


def fetch_latest_shift_comm(conn, department, comm_date, shift_type):
    """Fetch the latest shift comm for a specific date/dept/shift."""
    sql = """
        SELECT * FROM shift_communications
        WHERE department = ? AND comm_date = ? AND shift_type = ?
    """
    cur = conn.execute(sql, (department, comm_date, shift_type))
    cur.row_factory = sqlite3.Row
    row = cur.fetchone()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════
# CONTACTS
# ═══════════════════════════════════════════════════════

def fetch_contacts(conn, department=None, category=None):
    """Fetch contacts, optionally filtered by department and/or category."""
    sql = "SELECT * FROM contacts WHERE 1=1"
    params = []
    if department:
        sql += " AND (department = ? OR department IS NULL)"
        params.append(department)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY is_emergency DESC, name"
    cur = conn.execute(sql, params)
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


def upsert_contact(conn, name, role, department, phone, email,
                    is_emergency, category, notes, username="system"):
    """Insert or update a contact."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO contacts (name, role, department, phone, email,
                              is_emergency, category, notes, created_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, role, department, phone, email, is_emergency, category, notes, username, now))
    conn.commit()


def update_contact(conn, contact_id, name, role, department, phone, email,
                    is_emergency, category, notes, username="system"):
    """Update an existing contact."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE contacts SET name=?, role=?, department=?, phone=?, email=?,
               is_emergency=?, category=?, notes=?, updated_at=?
        WHERE id = ?
    """, (name, role, department, phone, email, is_emergency, category, notes, now, contact_id))
    conn.commit()


def delete_contact(conn, contact_id):
    """Delete a contact."""
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()


# ═══════════════════════════════════════════════════════
# AREA ASSIGNMENTS
# ═══════════════════════════════════════════════════════

def fetch_area_assignments(conn, department=None):
    """Fetch area assignments, optionally filtered by department."""
    sql = "SELECT * FROM area_assignments"
    params = []
    if department:
        sql += " WHERE department = ?"
        params.append(department)
    sql += " ORDER BY department, area_name"
    cur = conn.execute(sql, params)
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


def upsert_area_assignment(conn, area_name, department, assigned_to,
                            shift, responsibilities, notes, username="system"):
    """Insert or update an area assignment."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO area_assignments
            (area_name, department, assigned_to, shift, responsibilities, notes,
             effective_date, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(area_name, department, shift) DO UPDATE SET
            assigned_to=excluded.assigned_to,
            responsibilities=excluded.responsibilities,
            notes=excluded.notes,
            effective_date=excluded.effective_date,
            updated_by=excluded.updated_by,
            updated_at=excluded.updated_at
    """, (area_name, department, assigned_to, shift, responsibilities, notes,
          today, username, now))
    conn.commit()


def delete_area_assignment(conn, assignment_id):
    """Delete an area assignment."""
    conn.execute("DELETE FROM area_assignments WHERE id = ?", (assignment_id,))
    conn.commit()


# ═══════════════════════════════════════════════════════
# KEY INFO
# ═══════════════════════════════════════════════════════

def fetch_key_info(conn, category=None, department=None):
    """Fetch key info entries, optionally filtered."""
    sql = "SELECT * FROM key_info WHERE 1=1"
    params = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    if department:
        sql += " AND (department = ? OR department IS NULL)"
        params.append(department)
    sql += " ORDER BY priority DESC, category, title"
    cur = conn.execute(sql, params)
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


def upsert_key_info(conn, category, title, content, department, priority, username="system"):
    """Insert or update a key info entry."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO key_info (category, title, content, department, priority, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(category, title, department) DO UPDATE SET
            content=excluded.content,
            priority=excluded.priority,
            updated_by=excluded.updated_by,
            updated_at=excluded.updated_at
    """, (category, title, content, department, priority, username, now))
    conn.commit()


def delete_key_info(conn, info_id):
    """Delete a key info entry."""
    conn.execute("DELETE FROM key_info WHERE id = ?", (info_id,))
    conn.commit()


# ═══════════════════════════════════════════════════════
# CONTRACT AREAS
# ═══════════════════════════════════════════════════════

def fetch_contract_areas(conn, department=None):
    """Fetch contract areas, optionally filtered by department."""
    sql = "SELECT * FROM contract_areas"
    params = []
    if department:
        sql += " WHERE department = ?"
        params.append(department)
    sql += " ORDER BY department"
    cur = conn.execute(sql, params)
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.fetchall()]


def fetch_contract_area(conn, department):
    """Fetch a single contract area by department name."""
    cur = conn.execute("SELECT * FROM contract_areas WHERE department = ?", (department,))
    cur.row_factory = sqlite3.Row
    row = cur.fetchone()
    return dict(row) if row else None


def upsert_contract_area(conn, department, contract_type, operator,
                          revenue_share_pct, commission_structure,
                          contract_start, contract_end, renewal_date,
                          operating_hours, operating_days, meal_periods,
                          seating_capacity, square_footage,
                          key_contact_name, key_contact_phone, key_contact_email,
                          performance_kpis, special_terms, notes,
                          username="system"):
    """Insert or update a contract area."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO contract_areas
            (department, contract_type, operator, revenue_share_pct,
             commission_structure, contract_start, contract_end, renewal_date,
             operating_hours, operating_days, meal_periods,
             seating_capacity, square_footage,
             key_contact_name, key_contact_phone, key_contact_email,
             performance_kpis, special_terms, notes, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(department) DO UPDATE SET
            contract_type=excluded.contract_type,
            operator=excluded.operator,
            revenue_share_pct=excluded.revenue_share_pct,
            commission_structure=excluded.commission_structure,
            contract_start=excluded.contract_start,
            contract_end=excluded.contract_end,
            renewal_date=excluded.renewal_date,
            operating_hours=excluded.operating_hours,
            operating_days=excluded.operating_days,
            meal_periods=excluded.meal_periods,
            seating_capacity=excluded.seating_capacity,
            square_footage=excluded.square_footage,
            key_contact_name=excluded.key_contact_name,
            key_contact_phone=excluded.key_contact_phone,
            key_contact_email=excluded.key_contact_email,
            performance_kpis=excluded.performance_kpis,
            special_terms=excluded.special_terms,
            notes=excluded.notes,
            updated_by=excluded.updated_by,
            updated_at=excluded.updated_at
    """, (department, contract_type, operator, revenue_share_pct,
          commission_structure, contract_start, contract_end, renewal_date,
          operating_hours, operating_days, meal_periods,
          seating_capacity, square_footage,
          key_contact_name, key_contact_phone, key_contact_email,
          performance_kpis, special_terms, notes, username, now))
    conn.commit()


# ─────────────────────── Accounts Receivable ───────────────────────


def fetch_ar_invoices(conn):
    """Fetch all AR invoices, ordered by total descending."""
    rows = conn.execute(
        "SELECT * FROM ar_invoices ORDER BY total DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_ar_invoice(conn, invoice_number, due_date, total, current_amount,
                      days_0_30, days_31_60, days_61_90, days_91_120,
                      days_121_150, days_151_plus, username):
    """Insert or update an AR invoice row."""
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO ar_invoices
            (invoice_number, due_date, total, current_amount,
             days_0_30, days_31_60, days_61_90, days_91_120,
             days_121_150, days_151_plus, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(invoice_number) DO UPDATE SET
            due_date=excluded.due_date,
            total=excluded.total,
            current_amount=excluded.current_amount,
            days_0_30=excluded.days_0_30,
            days_31_60=excluded.days_31_60,
            days_61_90=excluded.days_61_90,
            days_91_120=excluded.days_91_120,
            days_121_150=excluded.days_121_150,
            days_151_plus=excluded.days_151_plus,
            updated_by=excluded.updated_by,
            updated_at=excluded.updated_at
    """, (invoice_number, due_date, total, current_amount,
          days_0_30, days_31_60, days_61_90, days_91_120,
          days_121_150, days_151_plus, username, now))
    conn.commit()


def delete_ar_invoice(conn, invoice_id):
    """Delete an AR invoice by id."""
    conn.execute("DELETE FROM ar_invoices WHERE id = ?", (invoice_id,))
    conn.commit()


# ─────────────────────── Meal Plan Tracker ───────────────────────


def fetch_meal_plan_tracker(conn, semester=None):
    """Fetch meal plan tracker rows, optionally filtered by semester."""
    if semester:
        rows = conn.execute(
            "SELECT * FROM meal_plan_tracker WHERE semester=? ORDER BY section, plan_name",
            (semester,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM meal_plan_tracker ORDER BY semester, section, plan_name"
        ).fetchall()
    return [dict(r) for r in rows]


def fetch_meal_plan_tracker_semesters(conn):
    """Get distinct semesters in meal plan tracker."""
    rows = conn.execute(
        "SELECT DISTINCT semester FROM meal_plan_tracker ORDER BY semester"
    ).fetchall()
    return [r["semester"] for r in rows]


def upsert_meal_plan_row(conn, semester, section, plan_name,
                         budgeted_daily_rate, actual_daily_rate, flex_amount,
                         budgeted_plans, actual_plans,
                         budgeted_revenue, actual_revenue,
                         budgeted_flex, actual_flex, username):
    """Insert or update a meal plan tracker row."""
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO meal_plan_tracker
            (semester, section, plan_name,
             budgeted_daily_rate, actual_daily_rate, flex_amount,
             budgeted_plans, actual_plans,
             budgeted_revenue, actual_revenue,
             budgeted_flex, actual_flex,
             updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(semester, section, plan_name) DO UPDATE SET
            budgeted_daily_rate=excluded.budgeted_daily_rate,
            actual_daily_rate=excluded.actual_daily_rate,
            flex_amount=excluded.flex_amount,
            budgeted_plans=excluded.budgeted_plans,
            actual_plans=excluded.actual_plans,
            budgeted_revenue=excluded.budgeted_revenue,
            actual_revenue=excluded.actual_revenue,
            budgeted_flex=excluded.budgeted_flex,
            actual_flex=excluded.actual_flex,
            updated_by=excluded.updated_by,
            updated_at=excluded.updated_at
    """, (semester, section, plan_name,
          budgeted_daily_rate, actual_daily_rate, flex_amount,
          budgeted_plans, actual_plans,
          budgeted_revenue, actual_revenue,
          budgeted_flex, actual_flex, username, now))
    conn.commit()


def clear_meal_plan_tracker(conn, semester):
    """Delete all rows for a semester (used before re-import)."""
    conn.execute("DELETE FROM meal_plan_tracker WHERE semester=?", (semester,))
    conn.commit()
