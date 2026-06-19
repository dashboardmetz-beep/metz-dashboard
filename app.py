"""
Metz Operations Platform — Main Router
Login, grouped navigation with sub-sections, page dispatch.
"""

import os
import streamlit as st
from auth import login_page, render_user_sidebar, can_access_imports
from config import APP_NAME, PAGE_ICON, PLATFORM_TITLE
from styles import inject_css, app_footer, sidebar_brand
import db

st.set_page_config(
    page_title=APP_NAME,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
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


# Searchable page index
_SEARCH_INDEX = {
    "Daily Entry": ("Daily Entry", None),
    "Weekly Budget": ("Weekly Budget", "Revenue"),
    "Weekly Budget - Revenue": ("Weekly Budget", "Revenue"),
    "Weekly Budget - Food Cost": ("Weekly Budget", "Food Cost"),
    "Weekly Budget - Labor": ("Weekly Budget", "Labor"),
    "Weekly Budget - Targets": ("Weekly Budget", "Targets"),
    "Weekly Budget - Invoice Tracker": ("Weekly Budget", "Invoice Tracker"),
    "Flash Report": ("Flash Report", "Financial Summary"),
    "Dashboard": ("Dashboard", "Operations Dashboard"),
    "Operations Dashboard": ("Dashboard", "Operations Dashboard"),
    "Operations Overview": ("Dashboard", "Operations Overview"),
    "Accounts Receivable": ("Dashboard", "Accounts Receivable"),
    "Meal Plan Tracker": ("Dashboard", "Meal Plan Tracker"),
    "Digital Meal Counts": ("Dashboard", "Digital Meal Counts"),
    "Tender Totals": ("Dashboard", "Tender Totals"),
    "Forecast & Allowable": ("Forecast & Allowable", None),
    "YoY & Alerts": ("YoY & Alerts", None),
    "Inventory": ("Inventory", None),
    "Checklists": ("Checklists", None),
    "Scheduling": ("Scheduling", None),
    "Training": ("Training", None),
    "Calendar": ("Calendar", None),
    "Pre-Service Meeting": ("Pre-Service Meeting", None),
    "Shift Communication": ("Shift Communication", None),
    "Contract Areas": ("Contract Areas", None),
    "Data Import": ("Data Import", None),
}


# Horizontal nav tabs config
# Each child is (label_shown, current_page, current_subsection)
_NAV_TABS = [
    ("Overview", "Dashboard", "grid",
     [("Operations Dashboard", "Dashboard", "Operations Dashboard"),
      ("Overview", "Dashboard", "Overview"),
      ("Operations Overview", "Dashboard", "Operations Overview"),
      ("Accounts Receivable", "Dashboard", "Accounts Receivable"),
      ("Meal Plan Tracker", "Dashboard", "Meal Plan Tracker"),
      ("Digital Meal Counts", "Dashboard", "Digital Meal Counts"),
      ("Tender Totals", "Dashboard", "Tender Totals")]),
    ("Operations", "Daily Operations", "briefcase",
     [("Daily Entry", "Daily Entry", None),
      ("Weekly Budget", "Weekly Budget", "Revenue"),
      ("Flash Report", "Flash Report", "Financial Summary")]),
    ("Forecasting", "Forecast & Allowable", "trending-up",
     [("Forecast & Allowable", "Forecast & Allowable", None),
      ("YoY & Alerts", "YoY & Alerts", None)]),
    ("Reports", "Analytics & Reports", "file-text",
     [("Financial Summary", "Flash Report", "Financial Summary"),
      ("Operational Metrics", "Flash Report", "Operational Metrics"),
      ("Budget & Projections", "Flash Report", "Budget & Projections")]),
    ("Management", "Inventory, Checklists", "users",
     [("Inventory", "Inventory", None),
      ("Checklists", "Checklists", None),
      ("Scheduling", "Scheduling", None),
      ("Training", "Training", None)]),
    ("Alerts", "YoY & Alerts", "bell",
     [("YoY & Alerts", "YoY & Alerts", None)]),
    ("Settings", "System Settings", "settings",
     [("Data Import", "Data Import", None)]),
]


_TAB_ICONS = {
    "grid": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
    "briefcase": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "trending-up": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "file-text": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "users": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "bell": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "settings": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
}


def _get_active_tab(current_page, current_sub):
    """Determine which top-level tab is active.

    Prefers the tab the user most recently clicked (stored in session_state),
    so pages that appear under multiple tabs (e.g. Flash Report under both
    Operations and Reports) highlight the right one.
    """
    intent = st.session_state.get("active_tab_intent")
    if intent:
        for tab in _NAV_TABS:
            if tab[0] != intent:
                continue
            for child in tab[3]:
                c_page = child[1] if len(child) == 3 else child[0]
                c_sub = child[2] if len(child) == 3 else child[1]
                if current_page == c_page and (
                    c_sub is None or current_sub == c_sub
                ):
                    return intent
            break

    for tab in _NAV_TABS:
        tab_name, _, _, children = tab
        for child in children:
            if len(child) == 3:
                _label, c_page, c_sub = child
            else:
                c_page, c_sub = child
            if current_page == c_page and (
                c_sub is None or current_sub == c_sub
            ):
                return tab_name
    if current_page == "Dashboard":
        return "Overview"
    return "Operations"


def _official_logo_html():
    """Embed the official Metz logo (assets/metz_logo.png) as a base64 data URL."""
    import base64 as _b64
    from config import LOGO_PATH as _LP
    try:
        with open(_LP, "rb") as _f:
            data = _b64.b64encode(_f.read()).decode("ascii")
        return (
            '<div class="ms-logo-pill">'
            '<img src="data:image/png;base64,{d}" alt="Metz Culinary Management" />'
            '</div>'
        ).format(d=data)
    except Exception:
        return '<div class="ms-logo-pill" style="color:#C9A34E;font-weight:700;">METZ</div>'


_LAUREL_LOGO_SVG = _official_logo_html()

_BREADCRUMB_SECTION = {
    "Overview": "OVERVIEW",
    "Operations": "OPERATIONS",
    "Forecasting": "FORECASTING",
    "Reports": "REPORTS",
    "Management": "MANAGEMENT",
    "Alerts": "ALERTS",
    "Settings": "SETTINGS",
}


def _render_top_bar(user):
    """Premium corporate nav: plain-text tabs inside dark header, white subnav below."""
    from urllib.parse import quote as _qp

    page = st.session_state.get("current_page", "Daily Entry")
    sub = st.session_state.get("current_subsection")
    name = user.get("display_name", user.get("username", "User"))
    role = user.get("role", "user").title()
    initials = "".join([p[0] for p in name.split()[:2]]).upper() or "A"
    active_tab = _get_active_tab(page, sub)

    # Build inline primary nav (anchor links inside dark header)
    primary_html = '<nav class="ms-primary-nav">'
    for tab_name, _sub, _ico, children in _NAV_TABS:
        if children:
            fc = children[0]
            fc_page = fc[1] if len(fc) == 3 else fc[0]
            fc_sub = fc[2] if len(fc) == 3 else fc[1]
        else:
            fc_page, fc_sub = tab_name, None
        is_active = tab_name == active_tab
        active_cls = " active" if is_active else ""
        badge_html = (
            '<span class="ms-pnav-badge">3</span>'
            if tab_name == "Alerts" else ""
        )
        href = "?nav_page={}&nav_sub={}&nav_intent={}".format(
            _qp(fc_page or ""), _qp(fc_sub or ""), _qp(tab_name),
        )
        primary_html += (
            '<a href="{href}" target="_top" class="ms-pnav-link{active}">'
            '{name}{badge}</a>'
        ).format(
            href=href, active=active_cls, name=tab_name, badge=badge_html,
        )
    primary_html += '</nav>'

    # ─── DARK HEADER (brand + primary nav + search + admin) ───
    st.markdown(
        '<div class="metz-shell">'
        '<div class="ms-brand">{logo}</div>'
        '{primary}'
        '<div class="ms-search">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'
        '<input type="text" placeholder="Search pages, departments, metrics..." />'
        '<span class="ms-kbd">⌘ K</span>'
        '</div>'
        '<div class="ms-admin">'
        '<button class="ms-bell" type="button">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>'
        '<path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
        '</button>'
        '<div class="ms-userinfo"><span class="ms-uname">{n}</span>'
        '<span class="ms-urole">{r}</span></div>'
        '<div class="ms-avatar">{i}</div>'
        '<svg class="ms-chev" width="12" height="12" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="6 9 12 15 18 9"/></svg>'
        '</div>'
        '</div>'.format(
            logo=_LAUREL_LOGO_SVG, primary=primary_html,
            n=name, r=role.title(), i=initials,
        ),
        unsafe_allow_html=True,
    )

    # ─── SECONDARY NAV (anchor links, only when active tab has multiple children) ───
    active_tab_children = []
    for tab_name, _, _, children in _NAV_TABS:
        if tab_name == active_tab:
            active_tab_children = children
            break

    if len(active_tab_children) > 1:
        sub_html = '<div class="ms-subnav-row">'
        for child in active_tab_children:
            if len(child) == 3:
                label_full, child_page, child_sub = child
            else:
                child_page, child_sub = child
                label_full = child_sub if child_sub else child_page
            is_active_child = (
                child_page == page
                and (child_sub is None or child_sub == sub)
            )
            href = "?nav_page={}&nav_sub={}&nav_intent={}".format(
                _qp(child_page or ""), _qp(child_sub or ""), _qp(active_tab),
            )
            cls = "ms-subnav-link active" if is_active_child else "ms-subnav-link"
            sub_html += '<a href="{h}" target="_top" class="{c}">{l}</a>'.format(
                h=href, c=cls, l=label_full,
            )
        sub_html += '</div>'
        st.markdown(sub_html, unsafe_allow_html=True)

def main():
    conn = db.get_conn()

    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Daily Entry"
    if "current_subsection" not in st.session_state:
        st.session_state.current_subsection = None

    # ─── Handle nav clicks from query params (read every run, don't clear) ───
    qp = st.query_params
    if "nav_page" in qp:
        target_page = qp.get("nav_page", "")
        target_sub = qp.get("nav_sub", "")
        target_intent = qp.get("nav_intent", "")
        if target_page and target_page != st.session_state.current_page:
            st.session_state.current_page = target_page
            st.session_state.current_subsection = target_sub if target_sub else None
        elif target_sub and target_sub != st.session_state.current_subsection:
            st.session_state.current_subsection = target_sub
        if target_intent:
            st.session_state.active_tab_intent = target_intent

    user = st.session_state.user

    if not user:
        user = login_page(conn, db.fetch_user)
        if not user:
            app_footer()
            return

    # ─── Auto-import: Gmail PDFs → database (Odyssey + CTUIT) ───
    # Skip on Streamlit Cloud (where Postgres is in use) — the filesystem is
    # ephemeral, downloaded PDFs would be wiped on the next restart, and the
    # Gmail API calls add 5–30s to every cold-start. Locally with SQLite, run
    # it as before.
    _is_cloud = bool(os.environ.get("DATABASE_URL"))
    try:
        _is_cloud = _is_cloud or ("DATABASE_URL" in st.secrets)
    except Exception:
        pass
    if not _is_cloud and "gmail_checked" not in st.session_state:
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

    # ─── Top Bar (search + breadcrumbs + user) ───
    _render_top_bar(user)

    # ─── Page Dispatch ───
    page = st.session_state.current_page

    if page == "Daily Entry":
        from views.daily_entry_new import page_daily_entry
        page_daily_entry(conn, user)
    elif page == "Weekly Budget":
        from views.weekly_entry_new import page_weekly_entry
        page_weekly_entry(conn, user)
    elif page == "Flash Report":
        from views.flash_report_new import page_flash_report
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
