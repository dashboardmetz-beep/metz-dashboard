"""Calendar View — Academic, Fiscal & Key Events with Reminders."""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

import db
from config import DEPARTMENTS
from styles import page_header, section_title, mini_divider, app_footer, event_reminders


# Category color/icon mapping
_CAT_CONFIG = {
    "academic": {"icon": "", "color": "#2E3A59"},
    "fiscal": {"icon": "", "color": "#1F2A44"},
    "dining": {"icon": "", "color": "#64748B"},
    "holiday": {"icon": "", "color": "#B7094C"},
    "admissions": {"icon": "", "color": "#0077B6"},
    "catering": {"icon": "", "color": "#E85D04"},
    "other": {"icon": "", "color": "#64748B"},
}


def render(conn, user):
    page_header("Event Calendar", "Academic \u2022 Fiscal \u2022 Dining Key Dates")
    today = date.today()

    # ─── Upcoming Reminders Banner ───
    _render_reminders(conn, today)

    mini_divider()

    # ─── Calendar Filters ───
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        view_mode = st.selectbox("View", ["This Week", "This Month", "Next 30 Days", "Custom Range"], key="cal_view")
    with col2:
        cat_options = ["All"] + list(_CAT_CONFIG.keys())
        selected_cat = st.selectbox("Category", cat_options, key="cal_cat")
    with col3:
        show_dining_only = st.checkbox("Only events affecting dining", key="cal_dining_only")

    # Calculate date range based on view mode
    if view_mode == "This Week":
        # Sun-Sat week
        days_since_sun = (today.weekday() + 1) % 7
        start = today - timedelta(days=days_since_sun)
        end = start + timedelta(days=6)
    elif view_mode == "This Month":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    elif view_mode == "Next 30 Days":
        start = today
        end = today + timedelta(days=30)
    else:
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("From", today, key="cal_start")
        with c2:
            end = st.date_input("To", today + timedelta(days=30), key="cal_end")

    # Fetch events
    cat_filter = None if selected_cat == "All" else selected_cat
    if show_dining_only:
        events = db.fetch_dining_impact_events(conn, start.isoformat(), end.isoformat())
        if cat_filter:
            events = [e for e in events if e["category"] == cat_filter]
    else:
        events = db.fetch_calendar_events(conn, start.isoformat(), end.isoformat(), cat_filter)

    # ─── Display Events ───
    mini_divider()
    section_title("", "Events ({} \u2013 {})".format(start.strftime("%b %d"), end.strftime("%b %d, %Y")))

    if not events:
        st.info("No events found for the selected period and filters.")
    else:
        for ev in events:
            cat = ev.get("category", "other")
            cfg = _CAT_CONFIG.get(cat, _CAT_CONFIG["other"])
            icon = cfg["icon"]
            color = cfg["color"]

            # Date display
            ev_date = ev["event_date"]
            end_date = ev.get("end_date")
            if end_date:
                date_str = "{} \u2013 {}".format(ev_date, end_date)
            else:
                date_str = ev_date

            # Build description and impact lines
            desc_html = ""
            if ev.get("description"):
                desc_html = '<div style="color:#555;font-size:0.9rem;margin-top:0.3rem;">{}</div>'.format(ev["description"])

            impact_html = ""
            if ev.get("dining_impact"):
                impact_html = '<div style="color:{};font-size:0.85rem;margin-top:0.2rem;"><em>{}</em></div>'.format(
                    color, ev["dining_impact"]
                )

            # Build the card
            st.markdown(
                '<div style="border-left:4px solid {};padding:0.6rem 1rem;margin-bottom:0.5rem;'
                'background:rgba(0,0,0,0.02);border-radius:0 6px 6px 0;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<div>'
                '<strong>{}</strong>'
                '<span style="color:#888;margin-left:0.5rem;font-size:0.85rem;">{}</span></div>'
                '<span style="background:{};color:white;padding:2px 8px;border-radius:10px;'
                'font-size:0.75rem;text-transform:uppercase;">{}</span>'
                '</div>'
                '{}{}'
                '</div>'.format(
                    color, ev["title"], date_str, color, cat,
                    desc_html, impact_html,
                ),
                unsafe_allow_html=True,
            )

    # ─── Monthly Overview Table ───
    mini_divider()
    section_title("", "Monthly Summary")
    _render_monthly_table(conn, today)

    # ─── Add Custom Event (admin/director only) ───
    if user and user.get("role") in ("admin", "approver"):
        mini_divider()
        section_title("", "Add Custom Event")
        _render_add_event_form(conn, user)



def _render_reminders(conn, today):
    """Show upcoming events in the next 7 days as alerts."""
    upcoming = db.fetch_upcoming_events(conn, today.isoformat(), days_ahead=7)
    dining_events = [e for e in upcoming if e.get("affects_dining")]

    if dining_events:
        st.markdown(
            '<div style="background:#1F2A44;color:white;'
            'padding:1rem 1.2rem;border-radius:8px;margin-bottom:1rem;">'
            '<strong>Upcoming Dining Alerts (Next 7 Days)</strong></div>',
            unsafe_allow_html=True,
        )
        for ev in dining_events:
            cat = ev.get("category", "other")
            cfg = _CAT_CONFIG.get(cat, _CAT_CONFIG["other"])
            impact = ev.get("dining_impact", "")
            st.markdown(
                '&nbsp;&nbsp; **{}** \u2014 {} {}'.format(
                    ev["event_date"], ev["title"],
                    "\u2014 *{}*".format(impact) if impact else "",
                ),
            )
    else:
        st.markdown(
            '<div style="background:#F7F8FA;padding:0.8rem 1rem;border-radius:8px;'
            'margin-bottom:1rem;color:#1F2A44;border:1px solid #D1D5DB;">'
            '<strong>No dining-impacting events in the next 7 days.</strong></div>',
            unsafe_allow_html=True,
        )


def _render_monthly_table(conn, today):
    """Show a compact table of events by month for the next 3 months."""
    months_data = []
    for i in range(3):
        if today.month + i > 12:
            m = (today.month + i) % 12 or 12
            y = today.year + 1
        else:
            m = today.month + i
            y = today.year
        first = date(y, m, 1)
        if m == 12:
            last = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(y, m + 1, 1) - timedelta(days=1)

        events = db.fetch_calendar_events(conn, first.isoformat(), last.isoformat())
        for ev in events:
            cfg = _CAT_CONFIG.get(ev.get("category", "other"), _CAT_CONFIG["other"])
            months_data.append({
                "Month": first.strftime("%B %Y"),
                "Date": ev["event_date"],
                "Event": ev["title"],
                "Category": ev.get("category", "other").title(),
                "Dining Impact": ev.get("dining_impact") or "-",
            })

    if months_data:
        mdf = pd.DataFrame(months_data)
        st.dataframe(mdf, use_container_width=True, hide_index=True)
    else:
        st.caption("No events in the next 3 months.")


def _render_add_event_form(conn, user):
    """Form to add custom events (admin/director only)."""
    with st.form("add_event_form"):
        c1, c2 = st.columns(2)
        with c1:
            ev_date = st.date_input("Event Date", date.today(), key="new_ev_date")
        with c2:
            ev_end = st.date_input("End Date (optional, for multi-day)", value=None, key="new_ev_end")

        ev_title = st.text_input("Title", key="new_ev_title")
        ev_desc = st.text_area("Description (optional)", key="new_ev_desc", height=68)

        c3, c4 = st.columns(2)
        with c3:
            ev_cat = st.selectbox("Category", list(_CAT_CONFIG.keys()), key="new_ev_cat")
        with c4:
            ev_dining = st.checkbox("Affects dining operations?", key="new_ev_dining")

        ev_impact = ""
        if ev_dining:
            ev_impact = st.text_input("Dining impact description", key="new_ev_impact")

        submitted = st.form_submit_button("Add Event", type="primary")
        if submitted:
            if not ev_title:
                st.error("Title is required.")
            else:
                end_str = ev_end.isoformat() if ev_end else None
                db.upsert_calendar_event(
                    conn,
                    ev_date.isoformat(),
                    ev_title,
                    ev_cat,
                    description=ev_desc or None,
                    end_date=end_str,
                    affects_dining=1 if ev_dining else 0,
                    dining_impact=ev_impact or None,
                    username=user["username"],
                )
                st.success("Event '{}' added!".format(ev_title))
                st.rerun()
