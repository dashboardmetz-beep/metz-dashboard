"""
Employee Scheduling — Weekly shift schedules by department.
"""

from datetime import date, timedelta, datetime
import pandas as pd
import streamlit as st

from config import DEPARTMENTS
from styles import page_header, dash_kpi_card, dash_section_header
import db


def _init_schedule_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'Staff',
            department TEXT DEFAULT 'Board & Catering',
            hourly_rate REAL DEFAULT 0.0,
            max_hours REAL DEFAULT 40.0,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(name, department)
        );

        CREATE TABLE IF NOT EXISTS schedule_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            shift_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            hours REAL DEFAULT 0.0,
            department TEXT DEFAULT 'Board & Catering',
            position TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            UNIQUE(employee_id, shift_date)
        );
    """)
    conn.commit()


_ROLES = ["Staff", "Lead", "Supervisor", "Manager", "Student Worker", "Temp"]
_POSITIONS = ["Grill", "Prep", "Service", "Cashier", "Dish", "Catering", "General"]


def render(conn, user):
    """Main scheduling page."""
    _init_schedule_tables(conn)
    page_header("Employee Scheduling", "Weekly shift planning and labor tracking")

    dept = st.selectbox("Department", DEPARTMENTS, key="sched_dept")

    # Week navigation
    if "sched_week" not in st.session_state:
        st.session_state.sched_week = db.get_week_start(date.today())

    week_start = st.session_state.sched_week
    week_end = week_start + timedelta(days=6)

    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        if st.button("◀ Prev", key="sched_prev"):
            st.session_state.sched_week -= timedelta(weeks=1)
            st.rerun()
    with c3:
        if st.button("Next ▶", key="sched_next"):
            st.session_state.sched_week += timedelta(weeks=1)
            st.rerun()
    with c2:
        st.markdown(
            '<div style="text-align:center;padding:6px 0;">'
            '<span style="font-size:16px;font-weight:600;color:#1E293B;">'
            '{} — {}</span></div>'.format(
                week_start.strftime("%b %d"), week_end.strftime("%b %d, %Y")),
            unsafe_allow_html=True,
        )

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Schedule Grid", "Add Shifts", "Employees"])

    with tab1:
        _render_schedule_grid(conn, dept, week_start)

    with tab2:
        _render_add_shifts(conn, user, dept, week_start)

    with tab3:
        _render_employees(conn, dept)


def _render_schedule_grid(conn, dept, week_start):
    """Show weekly schedule as a grid."""
    employees = conn.execute(
        "SELECT * FROM employees WHERE department=? AND active=1 ORDER BY role, name",
        (dept,)
    ).fetchall()

    if not employees:
        st.caption("No employees set up for {}. Add employees in the Employees tab.".format(dept))
        return

    dates = [(week_start + timedelta(days=i)) for i in range(7)]
    day_labels = [d.strftime("%a %m/%d") for d in dates]

    # Fetch all shifts for this week
    shifts = conn.execute(
        """SELECT * FROM schedule_shifts
           WHERE department=? AND shift_date >= ? AND shift_date <= ?""",
        (dept, week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchall()

    shift_map = {}
    for s in shifts:
        shift_map[(s["employee_id"], s["shift_date"])] = s

    # Build grid
    grid_data = []
    total_hours = 0
    total_cost = 0

    for emp in employees:
        row = {"Employee": emp["name"], "Role": emp["role"]}
        emp_hours = 0
        for d in dates:
            key = (emp["id"], d.isoformat())
            shift = shift_map.get(key)
            if shift:
                row[d.strftime("%a")] = "{}-{}".format(
                    shift["start_time"] or "", shift["end_time"] or "")
                emp_hours += shift["hours"] or 0
            else:
                row[d.strftime("%a")] = ""
        row["Total Hrs"] = emp_hours
        total_hours += emp_hours
        total_cost += emp_hours * (emp["hourly_rate"] or 0)
        grid_data.append(row)

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card("Employees", str(len(employees)), accent="navy")
    with k2:
        scheduled = sum(1 for r in grid_data if r["Total Hrs"] > 0)
        dash_kpi_card("Scheduled", str(scheduled), accent="green")
    with k3:
        dash_kpi_card("Total Hours", "{:.0f}".format(total_hours), accent="gold")
    with k4:
        dash_kpi_card("Labor Cost", "${:,.0f}".format(total_cost), accent="blue")

    # Grid table
    if grid_data:
        df = pd.DataFrame(grid_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_add_shifts(conn, user, dept, week_start):
    """Add/edit shifts for employees."""
    employees = conn.execute(
        "SELECT * FROM employees WHERE department=? AND active=1 ORDER BY name",
        (dept,)
    ).fetchall()

    if not employees:
        st.caption("Add employees first in the Employees tab.")
        return

    emp_options = {e["name"]: e for e in employees}
    selected_emp = st.selectbox("Employee", list(emp_options.keys()), key="shift_emp")
    emp = emp_options[selected_emp]

    dates = [(week_start + timedelta(days=i)) for i in range(7)]

    st.markdown("**Shifts for {} (week of {})**".format(selected_emp, week_start.strftime("%b %d")))

    for d in dates:
        existing = conn.execute(
            "SELECT * FROM schedule_shifts WHERE employee_id=? AND shift_date=?",
            (emp["id"], d.isoformat())
        ).fetchone()

        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c1:
            st.markdown("**{}**".format(d.strftime("%A %m/%d")))
        with c2:
            start = st.text_input(
                "Start", value=existing["start_time"] if existing else "",
                key="shift_start_{}_{}".format(emp["id"], d.isoformat()),
                placeholder="6:00 AM",
            )
        with c3:
            end = st.text_input(
                "End", value=existing["end_time"] if existing else "",
                key="shift_end_{}_{}".format(emp["id"], d.isoformat()),
                placeholder="2:00 PM",
            )
        with c4:
            hours = st.number_input(
                "Hrs", min_value=0.0, max_value=16.0, step=0.5,
                value=float(existing["hours"]) if existing else 0.0,
                key="shift_hrs_{}_{}".format(emp["id"], d.isoformat()),
            )

    if st.button("Save All Shifts", type="primary", key="shift_save"):
        for d in dates:
            start = st.session_state.get("shift_start_{}_{}".format(emp["id"], d.isoformat()), "")
            end = st.session_state.get("shift_end_{}_{}".format(emp["id"], d.isoformat()), "")
            hours = st.session_state.get("shift_hrs_{}_{}".format(emp["id"], d.isoformat()), 0)

            if hours > 0:
                conn.execute(
                    """INSERT OR REPLACE INTO schedule_shifts
                       (employee_id, shift_date, start_time, end_time, hours, department)
                       VALUES (?,?,?,?,?,?)""",
                    (emp["id"], d.isoformat(), start, end, hours, dept),
                )
        conn.commit()
        st.success("Saved shifts for {}".format(selected_emp))
        st.rerun()


def _render_employees(conn, dept):
    """Manage employee list."""
    employees = conn.execute(
        "SELECT * FROM employees WHERE department=? AND active=1 ORDER BY role, name",
        (dept,)
    ).fetchall()

    # Add employee
    with st.expander("Add Employee"):
        c1, c2 = st.columns(2)
        with c1:
            emp_name = st.text_input("Name", key="emp_name")
            emp_role = st.selectbox("Role", _ROLES, key="emp_role")
        with c2:
            emp_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=0.50, key="emp_rate")
            emp_max = st.number_input("Max Hours/Week", min_value=0.0, value=40.0, step=1.0, key="emp_max")

        if st.button("Add Employee", key="emp_add"):
            if emp_name.strip():
                try:
                    conn.execute(
                        "INSERT INTO employees (name, role, department, hourly_rate, max_hours) VALUES (?,?,?,?,?)",
                        (emp_name.strip(), emp_role, dept, emp_rate, emp_max),
                    )
                    conn.commit()
                    st.success("Added {}".format(emp_name))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # Employee list
    if employees:
        df = pd.DataFrame([dict(e) for e in employees])
        display = df[["name", "role", "hourly_rate", "max_hours"]].copy()
        display.columns = ["Name", "Role", "Rate ($/hr)", "Max Hrs/Wk"]
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.caption("No employees for {}. Add one above.".format(dept))
