"""Catering & Events — BEO (Banquet Event Order) Management."""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

import db
from styles import page_header, section_title, mini_divider, app_footer, event_reminders


_EVENT_TYPES = ["catering", "admissions", "board_meeting", "commencement", "camp", "conference", "private", "other"]
_SETUP_STYLES = ["Buffet", "Plated", "Reception", "Boxed Lunch", "Family Style", "Coffee/Tea Service", "Other"]
_STATUSES = ["Pending", "Confirmed", "In Progress", "Completed", "Cancelled"]
_STATUS_COLORS = {
    "Pending": "#FFC107",
    "Confirmed": "#2E3A59",
    "In Progress": "#0077B6",
    "Completed": "#64748B",
    "Cancelled": "#DC3545",
}


def render(conn, user):
    page_header("Catering & Events", "Banquet Event Orders & Event Management")
    event_reminders(conn)

    today = date.today()

    # ─── Upcoming Events Summary ───
    upcoming = db.fetch_upcoming_catering(conn, today.isoformat(), days_ahead=14)
    if upcoming:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#E85D04,#DC2F02);color:white;'
            'padding:0.8rem 1.2rem;border-radius:8px;margin-bottom:1rem;">'
            '<strong>{} upcoming event{} in the next 14 days</strong></div>'.format(
                len(upcoming), "s" if len(upcoming) != 1 else ""),
            unsafe_allow_html=True,
        )

    # ─── Tabs ───
    tab_list, tab_new, tab_calendar = st.tabs([
        "Event List", "New Event", "Calendar View"
    ])

    with tab_list:
        _render_event_list(conn, user, today)

    with tab_new:
        _render_new_event_form(conn, user)

    with tab_calendar:
        _render_calendar_overview(conn, today)



def _render_event_list(conn, user, today):
    section_title("", "Event List")

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        view_range = st.selectbox("Time Range", [
            "This Week", "Next 2 Weeks", "This Month", "All Upcoming", "Past Events"
        ], key="cat_range")
    with c2:
        filter_status = st.selectbox("Status", ["All"] + _STATUSES, key="cat_status_filter")
    with c3:
        filter_type = st.selectbox("Event Type", ["All"] + _EVENT_TYPES, key="cat_type_filter")

    # Calculate date range
    if view_range == "This Week":
        days_since_sun = (today.weekday() + 1) % 7
        start = today - timedelta(days=days_since_sun)
        end = start + timedelta(days=6)
    elif view_range == "Next 2 Weeks":
        start = today
        end = today + timedelta(days=14)
    elif view_range == "This Month":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    elif view_range == "Past Events":
        start = today - timedelta(days=90)
        end = today - timedelta(days=1)
    else:  # All Upcoming
        start = today
        end = today + timedelta(days=180)

    status_filter = None if filter_status == "All" else filter_status
    events = db.fetch_catering_events(conn, start.isoformat(), end.isoformat(), status_filter)

    if filter_type != "All":
        events = [e for e in events if e.get("event_type") == filter_type]

    if not events:
        st.info("No events found for the selected filters.")
        return

    for ev in events:
        status = ev.get("status", "Pending")
        color = _STATUS_COLORS.get(status, "#64748B")
        guest_count = ev.get("guest_count", 0) or 0
        location = ev.get("location", "") or ""
        ev_type = (ev.get("event_type", "") or "").replace("_", " ").title()
        time_str = ""
        if ev.get("start_time"):
            time_str = ev["start_time"]
            if ev.get("end_time"):
                time_str += " - {}".format(ev["end_time"])

        st.markdown(
            '<div style="border-left:4px solid {};padding:0.7rem 1rem;margin-bottom:0.5rem;'
            'background:rgba(0,0,0,0.02);border-radius:0 6px 6px 0;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;">'
            '<div>'
            '<strong style="font-size:1.05rem;">{}</strong>'
            '<span style="color:#888;margin-left:0.75rem;font-size:0.85rem;">{}</span>'
            '</div>'
            '<span style="background:{};color:white;padding:2px 10px;border-radius:10px;'
            'font-size:0.75rem;">{}</span>'
            '</div>'
            '<div style="color:#555;font-size:0.88rem;margin-top:0.3rem;">'
            '{}'
            '{}'
            '{}'
            '</div>'
            '</div>'.format(
                color, ev["event_name"], ev["event_date"],
                color, status,
                "{} guests &nbsp;".format(guest_count) if guest_count else "",
                "{} &nbsp;".format(location) if location else "",
                "{} &nbsp;".format(time_str) if time_str else "",
            ),
            unsafe_allow_html=True,
        )

        # Expand details
        with st.expander("Details & Actions \u2014 {}".format(ev["event_name"])):
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.markdown("**Client:** {}".format(ev.get("client_name") or "N/A"))
                st.markdown("**Type:** {}".format(ev_type))
                st.markdown("**Setup:** {}".format(ev.get("setup_style") or "N/A"))
            with dc2:
                st.markdown("**Menu Notes:**\n{}".format(ev.get("menu_notes") or "None"))
                st.markdown("**Dietary Notes:**\n{}".format(ev.get("dietary_notes") or "None"))
            with dc3:
                st.markdown("**Equipment:** {}".format(ev.get("equipment_needed") or "None"))
                st.markdown("**Staffing:** {}".format(ev.get("staffing_notes") or "None"))
                st.markdown("**Special Requests:** {}".format(ev.get("special_requests") or "None"))

            if ev.get("total_cost"):
                st.markdown("**Estimated Cost:** ${:,.2f}".format(float(ev["total_cost"])))
            if ev.get("billed_amount"):
                st.markdown("**Billed Amount:** ${:,.2f}".format(float(ev["billed_amount"])))

            # Status update
            mini_divider()
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                new_status = st.selectbox(
                    "Update Status",
                    _STATUSES,
                    index=_STATUSES.index(status) if status in _STATUSES else 0,
                    key="status_{}".format(ev["id"]),
                )
            with sc2:
                if st.button("Update", key="update_status_{}".format(ev["id"])):
                    db.update_catering_status(conn, ev["id"], new_status, user["username"])
                    st.success("Status updated to {}".format(new_status))
                    st.rerun()


def _render_new_event_form(conn, user):
    section_title("", "Create New Event / BEO")

    with st.form("new_catering_event"):
        c1, c2 = st.columns(2)
        with c1:
            ev_name = st.text_input("Event Name *", placeholder="e.g., Board of Trustees Luncheon")
            ev_date = st.date_input("Event Date *", date.today() + timedelta(days=7), key="new_cat_date")
            ev_type = st.selectbox("Event Type", _EVENT_TYPES, key="new_cat_type")
            client = st.text_input("Client / Contact", placeholder="e.g., Admissions Office")
        with c2:
            location = st.text_input("Location", placeholder="e.g., Hamilton Commons, Room 201")
            start_time = st.text_input("Start Time", placeholder="e.g., 11:30 AM")
            end_time = st.text_input("End Time", placeholder="e.g., 1:00 PM")
            guest_count = st.number_input("Expected Guests", min_value=0, value=0, step=5, key="new_cat_guests")

        setup_style = st.selectbox("Setup Style", _SETUP_STYLES, key="new_cat_setup")

        mini_divider()
        st.markdown("#### Menu & Requirements")

        mc1, mc2 = st.columns(2)
        with mc1:
            menu_notes = st.text_area("Menu Details", height=100, placeholder="Describe the menu...", key="new_cat_menu")
            dietary_notes = st.text_area("Dietary / Allergen Notes", height=80, placeholder="Gluten-free, nut-free, halal, etc.", key="new_cat_dietary")
        with mc2:
            equipment = st.text_area("Equipment Needed", height=80, placeholder="Chafing dishes, linens, AV, etc.", key="new_cat_equip")
            staffing = st.text_area("Staffing Notes", height=80, placeholder="Number of servers needed, etc.", key="new_cat_staff")

        special = st.text_area("Special Requests", height=68, placeholder="Any other requirements...", key="new_cat_special")

        mc3, mc4 = st.columns(2)
        with mc3:
            total_cost = st.number_input("Estimated Cost ($)", min_value=0.0, value=0.0, step=25.0, format="%.2f", key="new_cat_cost")
        with mc4:
            billed_amount = st.number_input("Billed Amount ($)", min_value=0.0, value=0.0, step=25.0, format="%.2f", key="new_cat_billed")

        submitted = st.form_submit_button("Create Event", type="primary")
        if submitted:
            if not ev_name:
                st.error("Event name is required.")
            else:
                db.upsert_catering_event(
                    conn, ev_date.isoformat(), ev_name, user["username"],
                    client_name=client or None,
                    event_type=ev_type,
                    location=location or None,
                    start_time=start_time or None,
                    end_time=end_time or None,
                    guest_count=guest_count,
                    setup_style=setup_style,
                    menu_notes=menu_notes or None,
                    special_requests=special or None,
                    dietary_notes=dietary_notes or None,
                    equipment_needed=equipment or None,
                    staffing_notes=staffing or None,
                    status="Pending",
                    total_cost=total_cost,
                    billed_amount=billed_amount,
                )
                st.success("Event '{}' created!".format(ev_name))
                st.rerun()


def _render_calendar_overview(conn, today):
    section_title("", "Monthly Calendar Overview")

    # Next 60 days
    events = db.fetch_catering_events(conn, today.isoformat(), (today + timedelta(days=60)).isoformat())

    if not events:
        st.info("No catering events in the next 60 days.")
        return

    rows = []
    for ev in events:
        status = ev.get("status", "Pending")
        rows.append({
            "Date": ev["event_date"],
            "Event": ev["event_name"],
            "Type": (ev.get("event_type") or "").replace("_", " ").title(),
            "Guests": ev.get("guest_count", 0) or 0,
            "Location": ev.get("location") or "-",
            "Status": status,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
