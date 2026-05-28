"""
Metz Operations Platform — Main Router
Login, grouped navigation with sub-sections, page dispatch.
"""

import streamlit as st
from auth import login_page, render_user_sidebar, can_access_imports
from config import APP_NAME, PAGE_ICON, PLATFORM_TITLE
from styles import inject_css, app_footer, sidebar_brand
import db

st.set_page_config(
    page_title=APP_NAME,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ─── Sub-section definitions ───
_PAGE_SUBSECTIONS = {
    "Weekly Budget": [
        "Revenue", "Food Cost", "Labor",
        "Financials & Costs", "Targets", "Invoice Tracker",
    ],
    "Flash Report": [
        "Financial Summary", "Operational Metrics", "Budget & Projections",
    ],
    "Dashboard": [
        "Operations Dashboard",
        "Overview", "Operations Overview",
        "Accounts Receivable", "Meal Plan Tracker",
        "Digital Meal Counts", "Tender Totals",
    ],
    "Planning": [
        "Calendar",
        "Pre-Service Meeting",
        "Catering & Events",
        "Waste Tracking",
    ],
    "Communication": [
        "Shift Communication",
        "Contract Areas",
        "Safety",
    ],
    "Data Import": [
        "CTUIT — Weekly Budget", "CTUIT — Consolidated",
        "Odyssey Reports", "Labor Hours", "Total Inventory",
        "Projections", "ADP Sync", "Import History",
    ],
}


def _nav_group(label):
    """Render a navigation group label in the sidebar."""
    st.sidebar.markdown(
        '<div class="nav-group-label">{}</div>'.format(label),
        unsafe_allow_html=True,
    )


def _nav_item(name, current_page):
    """Render a single navigation item. Returns True if clicked."""
    is_active = current_page == name
    if is_active:
        st.sidebar.markdown(
            '<div class="nav-active-item">{}</div>'.format(name),
            unsafe_allow_html=True,
        )
        return False
    return st.sidebar.button(
        name,
        key="nav_{}".format(name.replace(" ", "_").lower()),
        use_container_width=True,
    )


def _nav_subsections(page_name):
    """Render sub-section radio below the active page."""
    subs = _PAGE_SUBSECTIONS.get(page_name, [])
    if not subs:
        return

    current_sub = st.session_state.get("current_subsection", subs[0])
    if current_sub not in subs:
        current_sub = subs[0]
        st.session_state.current_subsection = current_sub

    idx = subs.index(current_sub) if current_sub in subs else 0
    selected = st.sidebar.radio(
        "subsections",
        subs,
        index=idx,
        key="subsec_{}".format(page_name.replace(" ", "_").lower()),
        label_visibility="collapsed",
    )
    if selected != current_sub:
        st.session_state.current_subsection = selected
        st.rerun()


def _nav_item_with_subs(name, current_page):
    """Render nav item + subsections if active."""
    clicked = _nav_item(name, current_page)
    if clicked:
        return True
    if current_page == name:
        _nav_subsections(name)
    return False


def _dispatch_planning(conn, user, subsection):
    """Route Planning sub-sections to their views."""
    if subsection == "Calendar":
        from views.calendar_view import render as calendar_render
        calendar_render(conn, user)
    elif subsection == "Pre-Service Meeting":
        from views.preservice_view import render as preservice_render
        preservice_render(conn, user)
    elif subsection == "Catering & Events":
        from views.catering_view import render as catering_render
        catering_render(conn, user)
    elif subsection == "Waste Tracking":
        from views.waste_view import render as waste_render
        waste_render(conn, user)


def _dispatch_communication(conn, user, subsection):
    """Route Communication sub-sections to their views."""
    if subsection == "Shift Communication":
        from views.shift_comm_view import render as shift_render
        shift_render(conn, user)
    elif subsection == "Contract Areas":
        from views.contacts_view import render as contacts_render
        contacts_render(conn, user)
    elif subsection == "Safety":
        from views.safety_view import render as safety_render
        safety_render(conn, user)


def main():
    conn = db.get_conn()

    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Daily Entry"
    if "current_subsection" not in st.session_state:
        st.session_state.current_subsection = None

    user = st.session_state.user

    if not user:
        user = login_page(conn, db.fetch_user)
        if not user:
            app_footer()
            return

    # ─── Auto-import: Gmail PDFs → database (Odyssey + CTUIT) ───
    if "gmail_checked" not in st.session_state:
        st.session_state.gmail_checked = True
        uname = user["username"] if user else "system"
        try:
            from gmail_import import check_new_emails, check_new_ctuit_emails
            from odyssey_parser import auto_import_all
            from ctuit_import import auto_import_ctuit

            check_new_ctuit_emails()
            ctuit_results = auto_import_ctuit(
                conn, uname, download_from_gmail=False
            )
            for r in ctuit_results:
                if r.get("success") and r.get("records", 0) > 0:
                    st.toast(
                        "CTUIT synced: {} — {} records".format(
                            r.get("department", "dept"),
                            r["records"],
                        ),
                        icon="✅",
                    )

            new_files = check_new_emails()
            if new_files:
                results = auto_import_all(conn)
                for r in results:
                    if r.get("records", 0) > 0:
                        st.toast(
                            "Imported {} ({} records)".format(
                                r["type"], r["records"]
                            ),
                            icon="✅",
                        )
        except Exception:
            pass

    sidebar_brand()

    # ─── Navigation ───
    current = st.session_state.current_page

    _nav_group("Operations")
    for item in ["Daily Entry", "Weekly Budget", "Flash Report", "Dashboard"]:
        if item in _PAGE_SUBSECTIONS:
            if _nav_item_with_subs(item, current):
                st.session_state.current_page = item
                st.session_state.current_subsection = _PAGE_SUBSECTIONS[item][0]
                st.rerun()
        elif _nav_item(item, current):
            st.session_state.current_page = item
            st.session_state.current_subsection = None
            st.rerun()

    _nav_group("Forecasting")
    for item in ["Forecast & Allowable", "YoY & Alerts"]:
        if _nav_item(item, current):
            st.session_state.current_page = item
            st.session_state.current_subsection = None
            st.rerun()

    _nav_group("Management")
    for item in ["Inventory", "Checklists", "Scheduling", "Training"]:
        if _nav_item(item, current):
            st.session_state.current_page = item
            st.session_state.current_subsection = None
            st.rerun()

    if _nav_item_with_subs("Planning", current):
        st.session_state.current_page = "Planning"
        st.session_state.current_subsection = _PAGE_SUBSECTIONS["Planning"][0]
        st.rerun()

    if _nav_item_with_subs("Communication", current):
        st.session_state.current_page = "Communication"
        st.session_state.current_subsection = _PAGE_SUBSECTIONS["Communication"][0]
        st.rerun()

    if can_access_imports(user):
        _nav_group("Admin")
        if _nav_item_with_subs("Data Import", current):
            st.session_state.current_page = "Data Import"
            st.session_state.current_subsection = _PAGE_SUBSECTIONS["Data Import"][0]
            st.rerun()

    from copilot_ui import render_copilot_panel
    render_copilot_panel(conn, user, st.session_state.current_page, user.get("department"))

    st.sidebar.markdown(
        '<div style="border-top:1px solid rgba(255,255,255,0.06);'
        'margin:16px 16px 0 16px;"></div>',
        unsafe_allow_html=True,
    )
    render_user_sidebar(user)

    # ─── Page Dispatch ───
    page = st.session_state.current_page

    if page == "Daily Entry":
        from views.daily_entry import page_daily_entry
        page_daily_entry(conn, user)
    elif page == "Weekly Budget":
        from views.weekly_entry import page_weekly_entry
        page_weekly_entry(conn, user)
    elif page == "Flash Report":
        from views.flash_report_view import page_flash_report
        page_flash_report(conn, user)
    elif page == "Dashboard":
        from views.dashboard import page_dashboard
        page_dashboard(conn, user)
    elif page == "Forecast & Allowable":
        from views.forecast_view import render as forecast_render
        forecast_render(conn, user)
    elif page == "YoY & Alerts":
        from views.yoy_view import render as yoy_render
        yoy_render(conn, user)
    elif page == "Inventory":
        from views.inventory_view import render as inventory_render
        inventory_render(conn, user)
    elif page == "Checklists":
        from views.checklists_view import render as checklists_render
        checklists_render(conn, user)
    elif page == "Scheduling":
        from views.scheduling_view import render as scheduling_render
        scheduling_render(conn, user)
    elif page == "Training":
        from views.training_view import render as training_render
        training_render(conn, user)
    elif page == "Planning":
        subsection = st.session_state.get(
            "current_subsection", _PAGE_SUBSECTIONS["Planning"][0]
        )
        _dispatch_planning(conn, user, subsection)
    elif page == "Communication":
        subsection = st.session_state.get(
            "current_subsection", _PAGE_SUBSECTIONS["Communication"][0]
        )
        _dispatch_communication(conn, user, subsection)
    elif page == "Data Import":
        from views.data_import import page_data_import
        page_data_import(conn, user)

    app_footer()


if __name__ == "__main__":
    main()
