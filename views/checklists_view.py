"""
Checklists & Audits — Daily opening/closing checklists, health inspections.
"""

from datetime import date, datetime
import pandas as pd
import streamlit as st

from config import DEPARTMENTS
from styles import page_header, dash_kpi_card, dash_section_header
import db


def _init_checklist_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS checklist_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            checklist_type TEXT DEFAULT 'daily',
            department TEXT DEFAULT 'Board & Catering',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(name, department)
        );

        CREATE TABLE IF NOT EXISTS checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            item_text TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (template_id) REFERENCES checklist_templates(id)
        );

        CREATE TABLE IF NOT EXISTS checklist_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            department TEXT DEFAULT 'Board & Catering',
            completed_items TEXT DEFAULT '[]',
            total_items INTEGER DEFAULT 0,
            completed_count INTEGER DEFAULT 0,
            completed_by TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(template_id, entry_date, department)
        );
    """)

    # Seed default templates if empty
    existing = conn.execute("SELECT COUNT(*) FROM checklist_templates").fetchone()[0]
    if existing == 0:
        _seed_defaults(conn)
    conn.commit()


def _seed_defaults(conn):
    """Seed default checklist templates."""
    templates = [
        ("Opening Checklist", "daily", [
            "Check all equipment is operational",
            "Verify temperature logs (walk-in, freezer)",
            "Stock service stations",
            "Set up POS terminals",
            "Review menu and specials",
            "Check staffing levels",
            "Inspect dining area cleanliness",
            "Unlock doors at scheduled time",
        ]),
        ("Closing Checklist", "daily", [
            "Clean all cooking equipment",
            "Sanitize prep surfaces",
            "Record final temperature logs",
            "Secure leftover food properly",
            "Empty trash and recycling",
            "Sweep and mop floors",
            "Lock all doors and windows",
            "Set alarm system",
        ]),
        ("Health & Safety Inspection", "weekly", [
            "Hand washing stations stocked",
            "Food storage temperatures in range",
            "Expiration dates checked",
            "Cross-contamination prevention verified",
            "Cleaning schedule followed",
            "Fire extinguishers inspected",
            "First aid kit stocked",
            "Employee hygiene compliance",
            "Pest control check",
            "Allergen labeling verified",
        ]),
    ]

    for dept in DEPARTMENTS:
        for name, ctype, items in templates:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO checklist_templates (name, checklist_type, department) VALUES (?,?,?)",
                (name, ctype, dept),
            )
            tid = cursor.lastrowid
            if tid:
                for i, text in enumerate(items):
                    conn.execute(
                        "INSERT INTO checklist_items (template_id, item_text, sort_order) VALUES (?,?,?)",
                        (tid, text, i),
                    )
    conn.commit()


def render(conn, user):
    """Main checklists page."""
    _init_checklist_tables(conn)
    page_header("Checklists & Audits", "Daily tasks, inspections, and compliance tracking")

    dept = st.selectbox("Department", DEPARTMENTS, key="cl_dept")
    today = date.today()

    # Today's completion stats
    entries_today = conn.execute(
        """SELECT ct.name, ce.completed_count, ce.total_items, ce.completed_by
           FROM checklist_entries ce
           JOIN checklist_templates ct ON ce.template_id = ct.id
           WHERE ce.entry_date = ? AND ce.department = ?""",
        (today.isoformat(), dept)
    ).fetchall()

    templates = conn.execute(
        "SELECT * FROM checklist_templates WHERE department=? AND active=1 ORDER BY checklist_type, name",
        (dept,)
    ).fetchall()

    total_templates = len(templates)
    completed_today = sum(1 for e in entries_today if e["completed_count"] == e["total_items"] and e["total_items"] > 0)

    k1, k2, k3 = st.columns(3)
    with k1:
        dash_kpi_card("Checklists", str(total_templates), accent="navy")
    with k2:
        dash_kpi_card("Completed Today", "{}/{}".format(completed_today, total_templates), accent="green")
    with k3:
        pct = (completed_today / total_templates * 100) if total_templates > 0 else 0
        dash_kpi_card("Compliance", "{:.0f}%".format(pct), accent="gold" if pct < 100 else "green")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Today's Checklists", "History", "Manage Templates"])

    with tab1:
        _render_today_checklists(conn, user, dept, today, templates)

    with tab2:
        _render_history(conn, dept)

    with tab3:
        _render_manage_templates(conn, dept)


def _render_today_checklists(conn, user, dept, today, templates):
    """Render today's checklists for completion."""
    import json

    for tmpl in templates:
        items = conn.execute(
            "SELECT * FROM checklist_items WHERE template_id=? ORDER BY sort_order",
            (tmpl["id"],)
        ).fetchall()

        if not items:
            continue

        # Load existing entry
        entry = conn.execute(
            "SELECT * FROM checklist_entries WHERE template_id=? AND entry_date=? AND department=?",
            (tmpl["id"], today.isoformat(), dept)
        ).fetchone()

        completed_ids = set()
        if entry and entry["completed_items"]:
            try:
                completed_ids = set(json.loads(entry["completed_items"]))
            except Exception:
                pass

        type_badge = "daily" if tmpl["checklist_type"] == "daily" else "weekly"
        badge_color = "#3B82F6" if type_badge == "daily" else "#D97706"

        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;margin:20px 0 8px;">'
            '<span style="font-size:15px;font-weight:600;color:#1E293B;">{}</span>'
            '<span style="font-size:10px;font-weight:600;color:{};'
            'background:{}15;padding:2px 8px;border-radius:8px;'
            'text-transform:uppercase;">{}</span>'
            '</div>'.format(tmpl["name"], badge_color, badge_color, type_badge),
            unsafe_allow_html=True,
        )

        # Progress bar
        done = len(completed_ids & {i["id"] for i in items})
        total = len(items)
        pct = done / total * 100 if total > 0 else 0
        bar_color = "#16A34A" if pct == 100 else ("#D97706" if pct > 50 else "#EF4444")
        st.markdown(
            '<div style="height:4px;background:#E5E7EB;border-radius:2px;margin-bottom:12px;">'
            '<div style="height:100%;width:{:.0f}%;background:{};border-radius:2px;'
            'transition:width 0.3s ease;"></div></div>'.format(pct, bar_color),
            unsafe_allow_html=True,
        )

        # Checklist items
        for item in items:
            checked = item["id"] in completed_ids
            new_val = st.checkbox(
                item["item_text"],
                value=checked,
                key="cl_{}_{}_{}".format(tmpl["id"], item["id"], today),
            )
            if new_val and item["id"] not in completed_ids:
                completed_ids.add(item["id"])
            elif not new_val and item["id"] in completed_ids:
                completed_ids.discard(item["id"])

        # Save button
        if st.button("Save", key="cl_save_{}".format(tmpl["id"])):
            conn.execute(
                """INSERT OR REPLACE INTO checklist_entries
                   (template_id, entry_date, department, completed_items,
                    total_items, completed_count, completed_by)
                   VALUES (?,?,?,?,?,?,?)""",
                (tmpl["id"], today.isoformat(), dept,
                 json.dumps(list(completed_ids)), total,
                 len(completed_ids & {i["id"] for i in items}),
                 user.get("username", "")),
            )
            conn.commit()
            st.success("Saved!")
            st.rerun()


def _render_history(conn, dept):
    """Show checklist completion history."""
    rows = conn.execute(
        """SELECT ce.entry_date, ct.name, ce.completed_count, ce.total_items,
                  ce.completed_by
           FROM checklist_entries ce
           JOIN checklist_templates ct ON ce.template_id = ct.id
           WHERE ce.department = ?
           ORDER BY ce.entry_date DESC, ct.name
           LIMIT 50""",
        (dept,)
    ).fetchall()

    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        df["Completion"] = df.apply(
            lambda r: "{}/{}".format(r["completed_count"], r["total_items"]), axis=1
        )
        df["Status"] = df.apply(
            lambda r: "Complete" if r["completed_count"] == r["total_items"] else "Incomplete",
            axis=1
        )
        display = df[["entry_date", "name", "Completion", "Status", "completed_by"]].copy()
        display.columns = ["Date", "Checklist", "Progress", "Status", "By"]
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.caption("No checklist history yet.")


def _render_manage_templates(conn, dept):
    """Add/edit checklist templates."""
    with st.expander("Create New Checklist"):
        new_name = st.text_input("Checklist Name", key="cl_new_name")
        new_type = st.selectbox("Type", ["daily", "weekly"], key="cl_new_type")
        new_items_text = st.text_area(
            "Items (one per line)",
            placeholder="Check equipment\nVerify temperatures\nStock stations",
            key="cl_new_items",
        )

        if st.button("Create Checklist", key="cl_create_btn"):
            if new_name.strip() and new_items_text.strip():
                try:
                    cursor = conn.execute(
                        "INSERT INTO checklist_templates (name, checklist_type, department) VALUES (?,?,?)",
                        (new_name.strip(), new_type, dept),
                    )
                    tid = cursor.lastrowid
                    for i, line in enumerate(new_items_text.strip().split("\n")):
                        if line.strip():
                            conn.execute(
                                "INSERT INTO checklist_items (template_id, item_text, sort_order) VALUES (?,?,?)",
                                (tid, line.strip(), i),
                            )
                    conn.commit()
                    st.success("Created '{}'".format(new_name))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # List existing templates
    templates = conn.execute(
        "SELECT * FROM checklist_templates WHERE department=? ORDER BY name",
        (dept,)
    ).fetchall()

    for tmpl in templates:
        items = conn.execute(
            "SELECT item_text FROM checklist_items WHERE template_id=? ORDER BY sort_order",
            (tmpl["id"],)
        ).fetchall()
        items_text = ", ".join(r["item_text"][:30] for r in items[:5])
        if len(items) > 5:
            items_text += "..."
        st.markdown(
            "**{}** ({}) — {} items: {}".format(
                tmpl["name"], tmpl["checklist_type"], len(items), items_text),
        )
