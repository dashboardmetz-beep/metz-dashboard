"""AM/PM Shift Communication — Handoff logs between shifts."""
import streamlit as st
from datetime import date, timedelta
from typing import Optional

import db
from config import DEPARTMENTS
from auth import get_user_departments
from styles import (
    page_header, section_title, kpi_card,
    status_badge, mini_divider, event_reminders, app_footer,
)


def render(conn, user):
    page_header(
        "Shift Communication",
        "AM / PM Shift Handoff Logs"
    )
    event_reminders(conn)

    today = date.today()

    # Department selection based on role
    user_depts = get_user_departments(user, DEPARTMENTS)
    if len(user_depts) == 1:
        dept = user_depts[0]
    else:
        dept = st.selectbox("Department", user_depts, key="sc_dept_sel")

    # ── Tabs ──
    tab_write, tab_read, tab_history = st.tabs([
        "Write Shift Log",
        "Read Shift Handoff",
        "Communication History",
    ])

    with tab_write:
        _render_write_tab(conn, user, today, dept)

    with tab_read:
        _render_read_tab(conn, user, today, dept)

    with tab_history:
        _render_history_tab(conn, user, today, dept)



# ═══════════════════════════════════════════════════════
# TAB 1 — WRITE SHIFT LOG
# ═══════════════════════════════════════════════════════

def _render_write_tab(conn, user, today, dept):
    """Render the Write Shift Log tab."""

    # Today's date shown prominently
    st.markdown(
        '<div style="background:#FFFFFF;border-radius:10px;padding:1rem 1.5rem;'
        'margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.06);'
        'border:1px solid #E5E7EB;text-align:center;">'
        '<span style="font-size:1.5rem;font-weight:700;color:#1F2A44;">'
        '{date_str}</span>'
        '</div>'.format(
            date_str=today.strftime("%A, %B %d, %Y")
        ),
        unsafe_allow_html=True,
    )

    # Shift type selector
    shift_type = st.radio(
        "Shift Type",
        ["AM", "PM"],
        format_func=lambda x: "AM Shift" if x == "AM" else "PM Shift",
        horizontal=True,
        key="sc_shift_type",
    )

    # Check for existing log to pre-populate
    existing = db.fetch_latest_shift_comm(conn, dept, today.isoformat(), shift_type)

    # ── Form ──
    with st.form("shift_comm_form", clear_on_submit=False):
        section_title("", "Author")
        author = st.text_input(
            "Who is writing this log?",
            value=existing["author"] if existing else user["display_name"],
            key="sc_author",
        )

        section_title("", "Tasks Completed")
        tasks_completed = st.text_area(
            "What was accomplished this shift?",
            value=existing["tasks_completed"] if existing and existing["tasks_completed"] else "",
            height=120,
            key="sc_tasks_done",
        )

        section_title("", "Tasks Pending")
        tasks_pending = st.text_area(
            "What still needs to be done?",
            value=existing["tasks_pending"] if existing and existing["tasks_pending"] else "",
            height=120,
            key="sc_tasks_pending",
        )

        col_left, col_right = st.columns(2)

        with col_left:
            section_title("", "Equipment Issues")
            equipment_issues = st.text_area(
                "Any equipment problems?",
                value=existing["equipment_issues"] if existing and existing["equipment_issues"] else "",
                height=100,
                key="sc_equip",
            )

            section_title("", "Inventory Notes")
            inventory_notes = st.text_area(
                "Stock alerts, deliveries, shortages",
                value=existing["inventory_notes"] if existing and existing["inventory_notes"] else "",
                height=100,
                key="sc_inventory",
            )

        with col_right:
            section_title("", "Staff Notes")
            staff_notes = st.text_area(
                "Callouts, coverage, performance notes",
                value=existing["staff_notes"] if existing and existing["staff_notes"] else "",
                height=100,
                key="sc_staff",
            )

            section_title("", "Safety Concerns")
            safety_concerns = st.text_area(
                "Any safety issues?",
                value=existing["safety_concerns"] if existing and existing["safety_concerns"] else "",
                height=100,
                key="sc_safety",
            )

        section_title("", "General Notes")
        general_notes = st.text_area(
            "Anything else the next shift should know?",
            value=existing["general_notes"] if existing and existing["general_notes"] else "",
            height=100,
            key="sc_general",
        )

        urgent_flag = st.checkbox(
            "Mark as Urgent",
            value=bool(existing["urgent_flag"]) if existing else False,
            key="sc_urgent",
        )

        mini_divider()

        submitted = st.form_submit_button(
            "Save Shift Log",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            db.upsert_shift_communication(
                conn,
                comm_date=today.isoformat(),
                department=dept,
                shift_type=shift_type,
                author=author,
                tasks_completed=tasks_completed,
                tasks_pending=tasks_pending,
                equipment_issues=equipment_issues,
                inventory_notes=inventory_notes,
                staff_notes=staff_notes,
                safety_concerns=safety_concerns,
                general_notes=general_notes,
                urgent_flag=1 if urgent_flag else 0,
                username=user["username"],
            )
            st.success(
                "{shift} shift log for {dept} saved successfully!".format(
                    shift=shift_type, dept=dept
                )
            )
            st.rerun()

    # Show existing log indicator
    if existing:
        st.info(
            "A {shift} shift log already exists for {dept} today. "
            "Editing will update the existing entry.".format(
                shift=shift_type, dept=dept
            )
        )


# ═══════════════════════════════════════════════════════
# TAB 2 — READ SHIFT HANDOFF
# ═══════════════════════════════════════════════════════

def _render_read_tab(conn, user, today, dept):
    """Render the Read Shift Handoff tab."""

    # Determine which shift to display and corresponding selector
    view_shift = st.radio(
        "You are starting",
        ["AM", "PM"],
        format_func=lambda x: "AM Shift (show last PM log)" if x == "AM" else "PM Shift (show today's AM log)",
        horizontal=True,
        key="sc_read_shift",
    )

    # Determine opposite shift details
    if view_shift == "AM":
        # Starting AM — show the previous PM log (yesterday)
        handoff_date = (today - timedelta(days=1)).isoformat()
        handoff_shift = "PM"
        handoff_label = "PM Shift Log from Yesterday ({})".format(
            (today - timedelta(days=1)).strftime("%A, %B %d")
        )
    else:
        # Starting PM — show today's AM log
        handoff_date = today.isoformat()
        handoff_shift = "AM"
        handoff_label = "AM Shift Log from Today ({})".format(
            today.strftime("%A, %B %d")
        )

    st.markdown(
        '<div style="background:#1F2A44;'
        'color:white;padding:1rem 1.5rem;border-radius:10px;margin:1rem 0;'
        'text-align:center;">'
        '<h3 style="color:white !important;margin:0 !important;">'
        '{label}</h3>'
        '<p style="color:rgba(255,255,255,0.7);margin:0.25rem 0 0 0;opacity:0.9;">'
        '{dept}</p>'
        '</div>'.format(
            label=handoff_label,
            dept=dept,
        ),
        unsafe_allow_html=True,
    )

    handoff = db.fetch_latest_shift_comm(conn, dept, handoff_date, handoff_shift)

    if not handoff:
        st.markdown(
            '<div style="background:#FFF8E1;border-radius:10px;padding:2rem;'
            'text-align:center;border:1px solid #FFE082;margin:1rem 0;">'
            '<p style="font-size:1.1rem;margin:0;"></p>'
            '<p style="font-size:1.1rem;font-weight:600;color:#F57F17;'
            'margin:0.5rem 0 0 0;">No handoff log from the previous shift yet.</p>'
            '<p style="color:#795548;font-size:0.9rem;margin:0.25rem 0 0 0;">'
            'The {shift} shift has not submitted a log for {date}.</p>'
            '</div>'.format(shift=handoff_shift, date=handoff_date),
            unsafe_allow_html=True,
        )
        return

    # ── Urgent banner ──
    if handoff.get("urgent_flag"):
        st.markdown(
            '<div style="background:#DC3545;color:white;padding:0.75rem 1.5rem;'
            'border-radius:8px;margin-bottom:1rem;text-align:center;'
            'font-weight:700;font-size:1.1rem;">'
            'URGENT — Please review immediately!</div>',
            unsafe_allow_html=True,
        )

    # ── Author + timestamp ──
    st.markdown(
        '<div style="background:#F7F8FA;border-radius:8px;padding:0.75rem 1rem;'
        'margin-bottom:1rem;border:1px solid #E5E7EB;">'
        '<strong>Written by:</strong> {author} &nbsp;&nbsp;|&nbsp;&nbsp;'
        '<strong>Submitted:</strong> {time}</div>'.format(
            author=handoff.get("author", "Unknown"),
            time=handoff.get("created_at", "N/A"),
        ),
        unsafe_allow_html=True,
    )

    # ── Display sections with color coding ──
    _handoff_section(
        "Tasks Completed", "",
        handoff.get("tasks_completed", ""),
        "#F7F8FA", "#2E7D32",
    )
    _handoff_section(
        "Tasks Pending", "",
        handoff.get("tasks_pending", ""),
        "#FFF3E0", "#E65100",
    )
    _handoff_section(
        "Equipment Issues", "",
        handoff.get("equipment_issues", ""),
        "#FFEBEE" if handoff.get("equipment_issues") else "#F7F8FA",
        "#C62828" if handoff.get("equipment_issues") else "#64748B",
    )
    _handoff_section(
        "Inventory Notes", "",
        handoff.get("inventory_notes", ""),
        "#F7F8FA", "#1F2A44",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        _handoff_section(
            "Staff Notes", "",
            handoff.get("staff_notes", ""),
            "#F7F8FA", "#1F2A44",
        )
    with col_b:
        _handoff_section(
            "Safety Concerns", "",
            handoff.get("safety_concerns", ""),
            "#FFEBEE" if handoff.get("safety_concerns") else "#F7F8FA",
            "#C62828" if handoff.get("safety_concerns") else "#64748B",
        )

    _handoff_section(
        "General Notes", "",
        handoff.get("general_notes", ""),
        "#F7F8FA", "#1F2A44",
    )

    # ── Mark as Read ──
    mini_divider()

    already_read = False
    read_by_str = handoff.get("read_by", "") or ""
    readers = [r.strip() for r in read_by_str.split(",") if r.strip()]
    if user["username"] in readers:
        already_read = True

    if already_read:
        st.success(
            "You have already marked this handoff as read."
        )
    else:
        if st.button(
            "Mark as Read",
            key="sc_mark_read",
            type="primary",
            use_container_width=True,
        ):
            db.mark_shift_comm_read(conn, handoff["id"], user["username"])
            st.success("Marked as read!")
            st.rerun()

    # Show who has read it
    if readers:
        st.caption("Read by: {}".format(", ".join(readers)))


def _handoff_section(title, icon, content, bg_color, text_color):
    """Render a color-coded handoff section."""
    display_content = content if content else "No notes."
    st.markdown(
        '<div style="background:{bg};border-radius:8px;padding:0.75rem 1rem;'
        'margin-bottom:0.75rem;border-left:4px solid {color};">'
        '<div style="font-weight:600;color:{color};margin-bottom:0.25rem;">'
        '{title}</div>'
        '<div style="color:#333;white-space:pre-wrap;">{content}</div>'
        '</div>'.format(
            bg=bg_color,
            color=text_color,
            icon=icon,
            title=title,
            content=display_content,
        ),
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════
# TAB 3 — COMMUNICATION HISTORY
# ═══════════════════════════════════════════════════════

def _render_history_tab(conn, user, today, dept):
    """Render the Communication History tab."""

    col_date, col_dept = st.columns([2, 1])

    with col_date:
        date_range = st.date_input(
            "Date Range",
            value=(today - timedelta(days=7), today),
            key="sc_hist_dates",
        )

    with col_dept:
        # Department filter
        user_depts = get_user_departments(user, DEPARTMENTS)
        hist_dept = st.selectbox(
            "Department",
            user_depts,
            index=user_depts.index(dept) if dept in user_depts else 0,
            key="sc_hist_dept",
        )

    # Parse date range
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date = date_range[0].isoformat()
        end_date = date_range[1].isoformat()
    else:
        start_date = today.isoformat()
        end_date = today.isoformat()

    comms = db.fetch_shift_communications(conn, hist_dept, start_date, end_date)

    if not comms:
        st.info("No shift logs found for {dept} in the selected date range.".format(
            dept=hist_dept
        ))
        return

    st.markdown(
        '<div style="background:#F7F8FA;border-radius:8px;padding:0.5rem 1rem;'
        'margin-bottom:1rem;border:1px solid #E5E7EB;">'
        '<strong>{count}</strong> shift log(s) found for '
        '<strong>{dept}</strong></div>'.format(
            count=len(comms),
            dept=hist_dept,
        ),
        unsafe_allow_html=True,
    )

    for comm in comms:
        # Build the card header
        shift_icon = ""
        urgent_badge = ""
        if comm.get("urgent_flag"):
            urgent_badge = (
                '  <span style="background:#DC3545;color:white;'
                'padding:0.15rem 0.5rem;border-radius:12px;font-size:0.75rem;'
                'font-weight:600;">URGENT</span>'
            )

        header_text = "{date} — {shift} Shift | Author: {author}{urgent}".format(
            date=comm["comm_date"],
            shift=comm["shift_type"],
            author=comm.get("author", "Unknown"),
            urgent=urgent_badge,
        )

        # Use markdown in expander label (plain text only)
        expander_label = "{date} - {shift} Shift | {author}{urgent_text}".format(
            date=comm["comm_date"],
            shift=comm["shift_type"],
            author=comm.get("author", "Unknown"),
            urgent_text=" [URGENT]" if comm.get("urgent_flag") else "",
        )

        with st.expander(expander_label, expanded=False):
            # Urgent banner inside
            if comm.get("urgent_flag"):
                st.markdown(
                    '<div style="background:#DC3545;color:white;'
                    'padding:0.5rem 1rem;border-radius:6px;margin-bottom:0.75rem;'
                    'text-align:center;font-weight:600;">'
                    'URGENT</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div style="color:#64748B;font-size:0.85rem;margin-bottom:0.75rem;">'
                'Submitted by <strong>{user}</strong> at {time}</div>'.format(
                    user=comm.get("created_by", "Unknown"),
                    time=comm.get("created_at", "N/A"),
                ),
                unsafe_allow_html=True,
            )

            _history_detail("Tasks Completed", "", comm.get("tasks_completed", ""))
            _history_detail("Tasks Pending", "", comm.get("tasks_pending", ""))
            _history_detail("Equipment Issues", "", comm.get("equipment_issues", ""))
            _history_detail("Inventory Notes", "", comm.get("inventory_notes", ""))
            _history_detail("Staff Notes", "", comm.get("staff_notes", ""))
            _history_detail("Safety Concerns", "", comm.get("safety_concerns", ""))
            _history_detail("General Notes", "", comm.get("general_notes", ""))

            # Read-by info
            read_by = comm.get("read_by", "") or ""
            if read_by:
                st.caption("Read by: {}".format(read_by))
            else:
                st.caption("Not yet read by anyone.")


def _history_detail(title, icon, content):
    """Render a detail row in the history expansion."""
    if not content:
        return
    st.markdown(
        '<div style="margin-bottom:0.5rem;padding:0.5rem 0.75rem;'
        'background:#F7F8FA;border-radius:6px;">'
        '<strong>{title}:</strong><br/>'
        '<span style="white-space:pre-wrap;">{content}</span>'
        '</div>'.format(
            icon=icon,
            title=title,
            content=content,
        ),
        unsafe_allow_html=True,
    )
