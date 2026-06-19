"""
Training Tracker — Employee training modules, certifications, and progress.
"""

from datetime import date
import pandas as pd
import streamlit as st

from config import DEPARTMENTS
from styles import page_header, dash_kpi_card, dash_section_header, hero_header
import db


def _init_training_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS training_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            required INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            duration_hours REAL DEFAULT 1.0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(name)
        );

        CREATE TABLE IF NOT EXISTS training_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            module_id INTEGER NOT NULL,
            status TEXT DEFAULT 'not_started',
            started_date TEXT,
            completed_date TEXT,
            score REAL,
            notes TEXT DEFAULT '',
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (module_id) REFERENCES training_modules(id),
            UNIQUE(employee_id, module_id)
        );
    """)

    # Seed defaults
    existing = conn.execute("SELECT COUNT(*) FROM training_modules").fetchone()[0]
    if existing == 0:
        defaults = [
            ("Food Safety (ServSafe)", "Safety", 1, "FDA food safety certification", 8.0),
            ("Allergen Awareness", "Safety", 1, "Common allergens and cross-contamination prevention", 2.0),
            ("Fire Safety & Extinguisher", "Safety", 1, "Fire prevention and extinguisher use", 1.0),
            ("HACCP Principles", "Safety", 0, "Hazard Analysis and Critical Control Points", 4.0),
            ("Customer Service Excellence", "Service", 0, "Guest interaction and complaint handling", 2.0),
            ("POS System Training", "Operations", 1, "Point of sale system operation", 1.5),
            ("Inventory Management", "Operations", 0, "Stock counting and ordering procedures", 2.0),
            ("Opening Procedures", "Operations", 1, "Daily opening tasks and checklist", 1.0),
            ("Closing Procedures", "Operations", 1, "Daily closing tasks and checklist", 1.0),
            ("Workplace Harassment Prevention", "Compliance", 1, "Required workplace training", 1.0),
        ]
        for name, cat, req, desc, dur in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO training_modules (name, category, required, description, duration_hours) VALUES (?,?,?,?,?)",
                (name, cat, req, desc, dur),
            )
    conn.commit()


_CATEGORIES = ["Safety", "Service", "Operations", "Compliance", "Leadership"]
_STATUSES = ["not_started", "in_progress", "completed"]


def render(conn, user):
    """Main training page."""
    _init_training_tables(conn)
    hero_header("Training Tracker", "Employee development, certifications, and compliance")

    dept = st.selectbox("Department", DEPARTMENTS, key="train_dept")

    # Get employees for this department
    employees = conn.execute(
        "SELECT * FROM employees WHERE department=? AND active=1 ORDER BY name",
        (dept,)
    ).fetchall()

    modules = conn.execute(
        "SELECT * FROM training_modules ORDER BY category, name"
    ).fetchall()

    # KPIs
    total_modules = len(modules)
    required = sum(1 for m in modules if m["required"])

    if employees:
        total_assignments = len(employees) * total_modules
        completed = conn.execute(
            """SELECT COUNT(*) FROM training_progress tp
               JOIN employees e ON tp.employee_id = e.id
               WHERE e.department = ? AND tp.status = 'completed'""",
            (dept,)
        ).fetchone()[0]
        pct = (completed / total_assignments * 100) if total_assignments > 0 else 0
    else:
        completed = 0
        pct = 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card("Modules", str(total_modules), accent="navy")
    with k2:
        dash_kpi_card("Required", str(required), accent="red")
    with k3:
        dash_kpi_card("Completed", str(completed), accent="green")
    with k4:
        dash_kpi_card("Compliance", "{:.0f}%".format(pct), accent="gold" if pct < 100 else "green")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Progress by Employee", "Training Modules", "Assign Training"])

    with tab1:
        _render_progress(conn, dept, employees, modules)

    with tab2:
        _render_modules(conn, modules)

    with tab3:
        _render_assign(conn, dept, employees, modules)


def _render_progress(conn, dept, employees, modules):
    """Show training progress per employee."""
    if not employees:
        st.caption("No employees in {}. Add employees in Scheduling first.".format(dept))
        return

    for emp in employees:
        progress = conn.execute(
            """SELECT tp.*, tm.name as module_name, tm.required
               FROM training_progress tp
               JOIN training_modules tm ON tp.module_id = tm.id
               WHERE tp.employee_id = ?
               ORDER BY tm.category, tm.name""",
            (emp["id"],)
        ).fetchall()

        total = len(modules)
        done = sum(1 for p in progress if p["status"] == "completed")
        in_prog = sum(1 for p in progress if p["status"] == "in_progress")
        pct = (done / total * 100) if total > 0 else 0

        bar_color = "#16A34A" if pct == 100 else ("#D97706" if pct > 50 else "#EF4444")

        st.markdown(
            '<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;'
            'padding:16px 20px;margin-bottom:10px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;">'
            '<div><span style="font-size:14px;font-weight:600;color:#1E293B;">{}</span>'
            '<span style="font-size:12px;color:#94A3B8;margin-left:8px;">{}</span></div>'
            '<span style="font-size:13px;font-weight:600;color:{};">{}/{} ({:.0f}%)</span>'
            '</div>'
            '<div style="height:4px;background:#E5E7EB;border-radius:2px;margin-top:8px;">'
            '<div style="height:100%;width:{:.0f}%;background:{};border-radius:2px;"></div>'
            '</div></div>'.format(
                emp["name"], emp["role"], bar_color,
                done, total, pct, pct, bar_color),
            unsafe_allow_html=True,
        )


def _render_modules(conn, modules):
    """List and manage training modules."""
    with st.expander("Add New Module"):
        c1, c2 = st.columns(2)
        with c1:
            mod_name = st.text_input("Module Name", key="mod_name")
            mod_cat = st.selectbox("Category", _CATEGORIES, key="mod_cat")
        with c2:
            mod_dur = st.number_input("Duration (hours)", min_value=0.5, step=0.5, value=1.0, key="mod_dur")
            mod_req = st.checkbox("Required", key="mod_req")
        mod_desc = st.text_input("Description", key="mod_desc")

        if st.button("Add Module", key="mod_add"):
            if mod_name.strip():
                try:
                    conn.execute(
                        "INSERT INTO training_modules (name, category, required, description, duration_hours) VALUES (?,?,?,?,?)",
                        (mod_name.strip(), mod_cat, 1 if mod_req else 0, mod_desc, mod_dur),
                    )
                    conn.commit()
                    st.success("Added '{}'".format(mod_name))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # Module list
    if modules:
        df = pd.DataFrame([dict(m) for m in modules])
        display = df[["name", "category", "required", "duration_hours"]].copy()
        display["required"] = display["required"].apply(lambda x: "Yes" if x else "")
        display.columns = ["Module", "Category", "Required", "Hours"]
        st.dataframe(display, use_container_width=True, hide_index=True)


def _render_assign(conn, dept, employees, modules):
    """Assign training and update status."""
    if not employees:
        st.caption("No employees to assign. Add employees in Scheduling first.")
        return

    emp_options = {e["name"]: e for e in employees}
    selected = st.selectbox("Employee", list(emp_options.keys()), key="assign_emp")
    emp = emp_options[selected]

    st.markdown("**Training for {}:**".format(selected))

    for mod in modules:
        progress = conn.execute(
            "SELECT * FROM training_progress WHERE employee_id=? AND module_id=?",
            (emp["id"], mod["id"])
        ).fetchone()

        current_status = progress["status"] if progress else "not_started"

        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            req_badge = " *" if mod["required"] else ""
            st.markdown("**{}**{}".format(mod["name"], req_badge))
        with c2:
            new_status = st.selectbox(
                "Status",
                _STATUSES,
                index=_STATUSES.index(current_status),
                key="assign_{}_{}".format(emp["id"], mod["id"]),
                label_visibility="collapsed",
            )
        with c3:
            status_colors = {
                "not_started": "#94A3B8",
                "in_progress": "#D97706",
                "completed": "#16A34A",
            }
            st.markdown(
                '<span style="color:{};">●</span>'.format(status_colors.get(new_status, "#94A3B8")),
                unsafe_allow_html=True,
            )

    if st.button("Save All", type="primary", key="assign_save"):
        today = date.today().isoformat()
        for mod in modules:
            new_status = st.session_state.get("assign_{}_{}".format(emp["id"], mod["id"]), "not_started")
            completed_date = today if new_status == "completed" else None
            started_date = today if new_status in ("in_progress", "completed") else None

            conn.execute(
                """INSERT OR REPLACE INTO training_progress
                   (employee_id, module_id, status, started_date, completed_date)
                   VALUES (?,?,?,?,?)""",
                (emp["id"], mod["id"], new_status, started_date, completed_date),
            )
        conn.commit()
        st.success("Saved training for {}".format(selected))
        st.rerun()
