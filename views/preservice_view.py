"""Pre-Service Meeting — Daily Communication & Briefing Tool."""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

import db
from config import DEPARTMENTS
from auth import get_user_departments
from styles import (
    page_header, section_title, kpi_card,
    status_badge, mini_divider, event_reminders, app_footer,
)

_MEAL_PERIODS = ["Breakfast", "Lunch", "Dinner"]


def render(conn, user):
    page_header(
        "Pre-Service Meeting",
        "Daily briefing notes, 86'd items, VIP alerts & action items",
    )
    event_reminders(conn)

    today = date.today()

    # Department access
    user_depts = get_user_departments(user, DEPARTMENTS)

    tab_today, tab_history = st.tabs([
        "Today's Meeting",
        "Meeting History",
    ])

    with tab_today:
        _render_today(conn, user, today, user_depts)

    with tab_history:
        _render_history(conn, user, today, user_depts)



# ═══════════════════════════════════════════════════════
# TAB 1 — TODAY'S MEETING
# ═══════════════════════════════════════════════════════

def _render_today(conn, user, today, user_depts):
    # --- Date display ---
    st.markdown(
        '<div style="background:#1F2A44;color:white;'
        'padding:1rem 1.5rem;border-radius:10px;margin-bottom:1rem;text-align:center;">'
        '<div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;'
        'opacity:0.85;">Today\'s Date</div>'
        '<div style="font-size:1.6rem;font-weight:700;">{}</div>'
        '</div>'.format(today.strftime("%A, %B %d, %Y")),
        unsafe_allow_html=True,
    )

    # --- Department & meal period selectors ---
    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        if len(user_depts) == 1:
            dept = user_depts[0]
            st.markdown(
                '<div style="background:#F7F8FA;padding:0.6rem 1rem;border-radius:8px;'
                'border:1px solid #D1D5DB;margin-bottom:0.5rem;">'
                '<span style="color:#64748B;font-size:0.8rem;text-transform:uppercase;'
                'letter-spacing:0.5px;">Department</span><br>'
                '<span style="font-weight:600;color:#1F2A44;">{}</span></div>'.format(dept),
                unsafe_allow_html=True,
            )
        else:
            dept = st.selectbox("Department", user_depts, key="preservice_dept")

    with sel_col2:
        meal_period = st.selectbox("Meal Period", _MEAL_PERIODS, key="preservice_meal")

    # --- Load existing meeting for pre-population ---
    existing = _get_existing_meeting(conn, today, dept, meal_period)

    mini_divider()

    # --- Meeting Form ---
    with st.form("preservice_form", clear_on_submit=False):

        # ---- Meeting Info ----
        section_title("", "Meeting Info")
        info_c1, info_c2 = st.columns(2)
        with info_c1:
            led_by = st.text_input(
                "Led By",
                value=existing.get("led_by", "") if existing else user.get("display_name", ""),
                key="ps_led_by",
                placeholder="Name of meeting leader...",
            )
        with info_c2:
            attendee_count = st.number_input(
                "Attendee Count",
                min_value=0,
                max_value=200,
                value=int(existing.get("attendee_count", 0)) if existing else 0,
                step=1,
                key="ps_attendees",
            )

        mini_divider()

        # ---- Menu & 86'd Items ----
        section_title("", "Menu & 86'd Items")
        menu_highlights = st.text_area(
            "Menu Highlights",
            value=existing.get("menu_highlights", "") if existing else "",
            height=100,
            key="ps_menu",
            placeholder="Today's specials, features, new items...",
        )

        # 86'd items with red warning styling
        st.markdown(
            '<div style="background:#FFF3CD;border-left:4px solid #DC3545;'
            'padding:0.5rem 0.8rem;border-radius:0 6px 6px 0;margin-bottom:0.5rem;'
            'font-size:0.85rem;color:#856404;">'
            '<strong>86\'d Items</strong> &mdash; Items unavailable for this service</div>',
            unsafe_allow_html=True,
        )
        items_86d = st.text_area(
            "86'd Items",
            value=existing.get("items_86d", "") if existing else "",
            height=80,
            key="ps_86d",
            placeholder="List any items that are 86'd (unavailable)...",
            label_visibility="collapsed",
        )

        mini_divider()

        # ---- VIP & Events ----
        section_title("", "VIP & Events")
        vip_c1, vip_c2 = st.columns(2)
        with vip_c1:
            vip_info = st.text_area(
                "VIP / Special Guest Info",
                value=existing.get("vip_info", "") if existing else "",
                height=80,
                key="ps_vip",
                placeholder="VIP guests, dietary needs, seating arrangements...",
            )
        with vip_c2:
            event_notes = st.text_area(
                "Event Notes",
                value=existing.get("event_notes", "") if existing else "",
                height=80,
                key="ps_events",
                placeholder="Campus events, catering impacts, special setups...",
            )

        mini_divider()

        # ---- Safety & General ----
        section_title("", "Safety & General")
        safety_c1, safety_c2 = st.columns(2)
        with safety_c1:
            safety_reminders = st.text_area(
                "Safety Reminders",
                value=existing.get("safety_reminders", "") if existing else "",
                height=80,
                key="ps_safety",
                placeholder="Safety alerts, allergen reminders, equipment notes...",
            )
        with safety_c2:
            general_notes = st.text_area(
                "General Notes",
                value=existing.get("general_notes", "") if existing else "",
                height=80,
                key="ps_general",
                placeholder="Staffing notes, shift changes, other announcements...",
            )

        mini_divider()

        # ---- Action Items ----
        section_title("", "Action Items")
        action_items = st.text_area(
            "Action Items",
            value=existing.get("action_items", "") if existing else "",
            height=100,
            key="ps_actions",
            placeholder="Follow-up tasks, assignments, deadlines...",
        )

        mini_divider()

        # ---- Submit ----
        submitted = st.form_submit_button(
            "Save Meeting Notes",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            db.upsert_preservice_meeting(
                conn,
                today.isoformat(),
                dept,
                meal_period.lower(),
                led_by or None,
                int(float(attendee_count)),
                menu_highlights or None,
                items_86d or None,
                vip_info or None,
                event_notes or None,
                safety_reminders or None,
                general_notes or None,
                action_items or None,
                username=user["username"],
            )
            if existing:
                st.success("Meeting notes updated for {} {} on {}.".format(
                    dept, meal_period, today.strftime("%B %d, %Y"),
                ))
            else:
                st.success("Meeting notes saved for {} {} on {}.".format(
                    dept, meal_period, today.strftime("%B %d, %Y"),
                ))
            st.rerun()

    # --- Show summary if meeting exists ---
    if existing:
        mini_divider()
        st.markdown(
            '<div style="background:#F7F8FA;padding:0.6rem 1rem;border-radius:8px;'
            'border:1px solid #D1D5DB;color:#1F2A44;font-size:0.9rem;">'
            'Meeting notes on file for <strong>{} {}</strong> &mdash; '
            'last saved by <strong>{}</strong> at {}</div>'.format(
                dept, meal_period,
                existing.get("created_by", "unknown"),
                (existing.get("created_at", "") or "")[:16],
            ),
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════
# TAB 2 — MEETING HISTORY
# ═══════════════════════════════════════════════════════

def _render_history(conn, user, today, user_depts):
    section_title("", "Meeting History")

    # --- Filters ---
    filter_c1, filter_c2, filter_c3 = st.columns(3)
    with filter_c1:
        days_back = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 14 Days", "Last 30 Days"],
            key="ps_history_range",
        )
        days_map = {
            "Last 7 Days": 7,
            "Last 14 Days": 14,
            "Last 30 Days": 30,
        }
        num_days = days_map.get(days_back, 7)
        start_date = today - timedelta(days=num_days)

    with filter_c2:
        if len(user_depts) == 1:
            hist_dept = user_depts[0]
            st.markdown(
                '<div style="background:#F7F8FA;padding:0.6rem 1rem;border-radius:8px;'
                'border:1px solid #D1D5DB;margin-top:1.5rem;">'
                '<span style="font-weight:600;color:#1F2A44;">{}</span></div>'.format(hist_dept),
                unsafe_allow_html=True,
            )
        else:
            hist_dept = st.selectbox(
                "Department",
                user_depts,
                key="ps_history_dept",
            )

    with filter_c3:
        meal_filter = st.selectbox(
            "Meal Period",
            ["All"] + _MEAL_PERIODS,
            key="ps_history_meal",
        )

    mini_divider()

    # --- Fetch meetings ---
    meetings = db.fetch_preservice_meetings(
        conn, hist_dept, start_date.isoformat(), today.isoformat(),
    )

    # Filter by meal period if not "All"
    if meal_filter != "All":
        meetings = [m for m in meetings if m.get("meal_period", "").lower() == meal_filter.lower()]

    if not meetings:
        st.info("No meeting records found for {} in the selected date range.".format(hist_dept))
        return

    # --- KPI summary ---
    total_meetings = len(meetings)
    total_attendees = sum(m.get("attendee_count", 0) or 0 for m in meetings)
    avg_attendees = int(total_attendees / total_meetings) if total_meetings > 0 else 0
    meetings_with_86 = sum(1 for m in meetings if m.get("items_86d"))

    kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
    with kpi_c1:
        kpi_card("Total Meetings", str(total_meetings), "kpi-green")
    with kpi_c2:
        kpi_card("Total Attendees", str(total_attendees), "kpi-blue")
    with kpi_c3:
        kpi_card("Avg Attendees", str(avg_attendees), "kpi-amber")
    with kpi_c4:
        kpi_card("Had 86'd Items", str(meetings_with_86), "kpi-red")

    mini_divider()

    # --- Expandable cards ---
    for mtg in meetings:
        mtg_date = mtg.get("meeting_date", "")
        mtg_meal = (mtg.get("meal_period", "") or "").title()
        mtg_led = mtg.get("led_by", "") or "Not specified"
        mtg_count = mtg.get("attendee_count", 0) or 0

        header_text = "{} | {} | Led by: {} | Attendees: {}".format(
            mtg_date, mtg_meal, mtg_led, mtg_count,
        )

        with st.expander(header_text, expanded=False):
            # Meeting details in columns
            det_c1, det_c2 = st.columns(2)
            with det_c1:
                st.markdown("**Date:** {}".format(mtg_date))
                st.markdown("**Meal Period:** {}".format(mtg_meal))
                st.markdown("**Led By:** {}".format(mtg_led))
                st.markdown("**Attendees:** {}".format(mtg_count))
            with det_c2:
                st.markdown("**Created By:** {}".format(mtg.get("created_by", "-")))
                st.markdown("**Created At:** {}".format(
                    (mtg.get("created_at", "") or "")[:16]
                ))

            mini_divider()

            # Content sections
            _history_field(
                "Menu Highlights",
                mtg.get("menu_highlights"),
            )

            if mtg.get("items_86d"):
                st.markdown(
                    '<div style="background:#FFF3CD;border-left:4px solid #DC3545;'
                    'padding:0.5rem 0.8rem;border-radius:0 6px 6px 0;margin:0.5rem 0;'
                    'font-size:0.9rem;color:#856404;">'
                    '<strong>86\'d Items:</strong> {}</div>'.format(
                        mtg.get("items_86d", "").replace("\n", "<br>"),
                    ),
                    unsafe_allow_html=True,
                )

            _history_field(
                "VIP / Special Guests",
                mtg.get("vip_info"),
            )
            _history_field(
                "Event Notes",
                mtg.get("event_notes"),
            )
            _history_field(
                "Safety Reminders",
                mtg.get("safety_reminders"),
            )
            _history_field(
                "General Notes",
                mtg.get("general_notes"),
            )
            _history_field(
                "Action Items",
                mtg.get("action_items"),
            )


def _history_field(label, value):
    """Render a labeled field in the history view, only if value is present."""
    if value:
        st.markdown("**{}:**".format(label))
        st.markdown(
            '<div style="background:#F7F8FA;padding:0.5rem 0.8rem;border-radius:6px;'
            'margin-bottom:0.5rem;font-size:0.9rem;white-space:pre-wrap;">{}</div>'.format(
                value.replace("\n", "<br>"),
            ),
            unsafe_allow_html=True,
        )


def _get_existing_meeting(conn, today, dept, meal_period):
    """Look up an existing meeting for today/dept/meal to pre-populate the form."""
    todays = db.fetch_todays_preservice(conn, dept, today.isoformat())
    for m in todays:
        if (m.get("meal_period", "") or "").lower() == meal_period.lower():
            return m
    return None
