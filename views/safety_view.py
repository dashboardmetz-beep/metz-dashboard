"""Safety & Compliance — Daily Checklists, Temperature Logs, Inspection Prep."""
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime

import db
from config import DEPARTMENTS
from auth import get_user_departments
from styles import page_header, section_title, mini_divider, app_footer, event_reminders


# Default checklist items per type
_OPENING_ITEMS = [
    "Handwashing stations stocked (soap, towels)",
    "All employees in proper uniform/hair nets",
    "Floor mats in place and clean",
    "All prep surfaces sanitized",
    "Walk-in cooler temps in range",
    "Walk-in freezer temps in range",
    "Hot holding equipment preheated",
    "Sanitizer buckets filled (correct concentration)",
    "First aid kit stocked and accessible",
    "Fire extinguisher accessible and inspected",
    "Wet floor signs available",
    "Allergen information posted and visible",
]

_CLOSING_ITEMS = [
    "All food properly stored and labeled",
    "All prep surfaces cleaned and sanitized",
    "Floors swept and mopped",
    "Trash removed and bins lined",
    "Walk-in cooler temps logged",
    "Walk-in freezer temps logged",
    "All equipment turned off (except refrigeration)",
    "Handwashing stations restocked",
    "Doors locked and secured",
    "Lights turned off (except safety lights)",
]

_EQUIPMENT_TEMPS = [
    ("Walk-in Cooler #1", 33.0, 40.0),
    ("Walk-in Cooler #2", 33.0, 40.0),
    ("Walk-in Freezer", -10.0, 0.0),
    ("Prep Cooler", 33.0, 40.0),
    ("Hot Holding Unit", 135.0, 165.0),
    ("Salad Bar", 33.0, 41.0),
    ("Dessert Cooler", 33.0, 40.0),
]


def render(conn, user):
    page_header("Safety & Compliance", "Checklists, Temperature Logs & Inspection Prep")
    event_reminders(conn)

    today = date.today()

    # Department
    user_depts = get_user_departments(user, DEPARTMENTS)
    if len(user_depts) == 1:
        dept = user_depts[0]
    else:
        dept = st.selectbox("Department", user_depts, key="safety_dept")

    tab_open, tab_close, tab_temp, tab_history = st.tabs([
        "Opening Checklist", "Closing Checklist",
        "Temperature Log", "History & Compliance"
    ])

    with tab_open:
        _render_checklist(conn, user, today, dept, "opening", _OPENING_ITEMS)

    with tab_close:
        _render_checklist(conn, user, today, dept, "closing", _CLOSING_ITEMS)

    with tab_temp:
        _render_temp_log(conn, user, today, dept)

    with tab_history:
        _render_history(conn, dept)



def _render_checklist(conn, user, today, dept, checklist_type, default_items):
    label = checklist_type.title()
    section_title(
        "",
        "{} Checklist \u2014 {} \u2014 {}".format(label, dept, today.strftime("%B %d, %Y")),
    )

    # Get or create checklist
    existing = db.fetch_safety_checklist(conn, today.isoformat(), dept, checklist_type)

    if existing:
        checklist_id = existing["id"]
        status = existing.get("status", "Incomplete")
        items = db.fetch_checklist_items(conn, checklist_id)
        item_map = {}
        for it in items:
            item_map[it["item_name"]] = it
    else:
        checklist_id = None
        status = "Incomplete"
        item_map = {}

    # Status indicator
    if status == "Complete":
        st.markdown(
            '<div style="background:#F7F8FA;padding:0.6rem 1rem;border-radius:6px;color:#1F2A44;border:1px solid #D1D5DB;">'
            '<strong>Completed</strong> by {} at {}</div>'.format(
                existing.get("completed_by", ""), existing.get("completed_at", "")[:16] if existing.get("completed_at") else ""),
            unsafe_allow_html=True,
        )
    else:
        checked_count = sum(1 for v in item_map.values() if v.get("is_checked"))
        total_count = len(default_items)
        pct = int((checked_count / total_count * 100)) if total_count > 0 else 0
        st.progress(pct / 100.0, text="{}/{} items checked ({}%)".format(checked_count, total_count, pct))

    # Render items
    checks = {}
    notes_map = {}
    for item_name in default_items:
        existing_item = item_map.get(item_name, {})
        c1, c2 = st.columns([3, 2])
        with c1:
            checks[item_name] = st.checkbox(
                item_name,
                value=bool(existing_item.get("is_checked", 0)),
                key="{}_{}_{}".format(checklist_type, dept, item_name),
            )
        with c2:
            notes_map[item_name] = st.text_input(
                "Note",
                value=existing_item.get("notes", "") or "",
                key="{}_note_{}_{}".format(checklist_type, dept, item_name),
                label_visibility="collapsed",
                placeholder="Optional note...",
            )

    mini_divider()
    general_notes = st.text_area(
        "General Notes",
        value=existing.get("notes", "") or "" if existing else "",
        height=68,
        key="{}_{}_general_notes".format(checklist_type, dept),
    )

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("Save Progress", key="save_{}_{}".format(checklist_type, dept)):
            cid = db.upsert_safety_checklist(
                conn, today.isoformat(), dept, checklist_type,
                user["username"], status="In Progress", notes=general_notes or None,
            )
            for item_name in default_items:
                db.upsert_checklist_item(
                    conn, cid, item_name,
                    1 if checks.get(item_name) else 0,
                    notes=notes_map.get(item_name) or None,
                    username=user["username"],
                )
            st.success("Progress saved!")
            st.rerun()

    with bc2:
        all_checked = all(checks.get(item_name, False) for item_name in default_items)
        if all_checked:
            if st.button("Mark Complete", type="primary", key="complete_{}_{}".format(checklist_type, dept)):
                cid = db.upsert_safety_checklist(
                    conn, today.isoformat(), dept, checklist_type,
                    user["username"], status="Complete", notes=general_notes or None,
                )
                for item_name in default_items:
                    db.upsert_checklist_item(
                        conn, cid, item_name, 1,
                        notes=notes_map.get(item_name) or None,
                        username=user["username"],
                    )
                st.success("{} checklist marked complete!".format(label))
                st.rerun()
        else:
            st.caption("Check all items to mark complete.")


def _render_temp_log(conn, user, today, dept):
    section_title("", "Temperature Log \u2014 {} \u2014 {}".format(dept, today.strftime("%B %d, %Y")))

    # Show existing logs
    existing_logs = db.fetch_temp_logs(conn, today.isoformat(), dept)
    if existing_logs:
        st.markdown("**Today's Readings:**")
        log_df = pd.DataFrame(existing_logs)
        display_cols = ["equipment_name", "temp_reading", "in_range", "corrective_action", "logged_by", "logged_at"]
        available = [c for c in display_cols if c in log_df.columns]
        log_df = log_df[available]
        rename = {
            "equipment_name": "Equipment",
            "temp_reading": "Temp (\u00b0F)",
            "in_range": "In Range",
            "corrective_action": "Corrective Action",
            "logged_by": "Logged By",
            "logged_at": "Time",
        }
        log_df.rename(columns=rename, inplace=True)
        if "In Range" in log_df.columns:
            log_df["In Range"] = log_df["In Range"].map({1: "Yes", 0: "No"})
        if "Time" in log_df.columns:
            log_df["Time"] = log_df["Time"].str[:16]
        st.dataframe(log_df, use_container_width=True, hide_index=True)

    mini_divider()
    st.markdown("**Log New Temperature Reading:**")

    with st.form("temp_log_form_{}".format(dept)):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            equip_options = [e[0] for e in _EQUIPMENT_TEMPS] + ["Other"]
            equip = st.selectbox("Equipment", equip_options, key="temp_equip_{}".format(dept))
        with tc2:
            temp_val = st.number_input("Temperature (\u00b0F)", value=38.0, step=0.5, format="%.1f", key="temp_val_{}".format(dept))
        with tc3:
            # Auto-check if in range
            in_range_default = True
            for eq_name, low, high in _EQUIPMENT_TEMPS:
                if eq_name == equip:
                    in_range_default = low <= temp_val <= high
                    break
            in_range = st.checkbox("In Range", value=in_range_default, key="temp_range_{}".format(dept))

        corrective = ""
        if not in_range:
            corrective = st.text_input(
                "Corrective Action Taken *",
                placeholder="Describe what action was taken...",
                key="temp_corrective_{}".format(dept),
            )

        if equip == "Other":
            equip = st.text_input("Equipment Name", key="temp_other_name_{}".format(dept))

        submitted = st.form_submit_button("Log Temperature", type="primary")
        if submitted:
            if not equip:
                st.error("Please enter equipment name.")
            elif not in_range and not corrective:
                st.error("Corrective action is required for out-of-range temps.")
            else:
                db.add_temp_log(
                    conn, today.isoformat(), dept, equip,
                    temp_val, 1 if in_range else 0, corrective, user["username"],
                )
                st.success("Temperature logged: {} at {}\u00b0F".format(equip, temp_val))
                st.rerun()


def _render_history(conn, dept):
    section_title("", "Compliance History \u2014 {}".format(dept))

    history = db.fetch_safety_history(conn, dept, days_back=30)

    if not history:
        st.info("No checklist history for the past 30 days.")
        return

    rows = []
    for h in history:
        status = h.get("status", "Incomplete")
        rows.append({
            "Date": h["checklist_date"],
            "Type": h["checklist_type"].title(),
            "Status": status,
            "Completed By": h.get("completed_by") or "-",
            "Notes": h.get("notes") or "-",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Compliance score
    mini_divider()
    total = len(history)
    complete = sum(1 for h in history if h.get("status") == "Complete")
    pct = int((complete / total * 100)) if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Checklists", total)
    with c2:
        st.metric("Completed", complete)
    with c3:
        color = "#1F2A44" if pct >= 90 else "#E85D04" if pct >= 70 else "#DC3545"
        st.markdown(
            '<div style="text-align:center;"><span style="font-size:2rem;font-weight:700;color:{};">{}%</span>'
            '<br><span style="color:#888;font-size:0.85rem;">Compliance Rate</span></div>'.format(color, pct),
            unsafe_allow_html=True,
        )
