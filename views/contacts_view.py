"""Contract Areas & Key Info — department contracts, operating details, and key information."""
import streamlit as st
from datetime import date, datetime

import db
from config import DEPARTMENTS
from auth import get_user_departments
from styles import (
    page_header, section_title, kpi_card,
    status_badge, mini_divider, event_reminders, app_footer,
)


# ─── Helpers ───

_DEPT_COLORS = {
    "Board & Catering": "#1F2A44",
    "Starbucks": "#2E3A59",
    "Qdoba": "#D42A1E",
    "Retail & Mac's Grill": "#0077B6",
}

_DEPT_ICONS = {
    "Board & Catering": "",
    "Starbucks": "",
    "Qdoba": "",
    "Retail & Mac's Grill": "",
}

_CONTRACT_TYPES = ["Managed", "Licensed", "Franchise", "Lease", "Other"]

_INFO_CATEGORY_MAP = {
    "All": None,
    "Hours": "hours",
    "Emergency Procedures": "emergency",
    "Policies": "policy",
}


def _can_manage(user):
    """Return True if user is admin or approver."""
    return user["role"] in ("admin", "approver")


def _dept_color(dept):
    return _DEPT_COLORS.get(dept, "#64748B")


def _dept_icon(dept):
    return _DEPT_ICONS.get(dept, "")


# ═══════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════

def render(conn, user):
    page_header(
        "Contract Areas & Key Info",
        "Department contracts, operating details, and key operational information"
    )
    event_reminders(conn)

    user_depts = get_user_departments(user, DEPARTMENTS)

    tab1, tab2, tab3 = st.tabs([
        "Contract Overview",
        "Contract Details",
        "Key Info",
    ])

    with tab1:
        _render_overview_tab(conn, user, user_depts)

    with tab2:
        _render_details_tab(conn, user, user_depts)

    with tab3:
        _render_key_info_tab(conn, user, user_depts)


# ═══════════════════════════════════════════════════════
# TAB 1: CONTRACT OVERVIEW (all departments at a glance)
# ═══════════════════════════════════════════════════════

def _render_overview_tab(conn, user, user_depts):
    section_title("", "All Contract Areas")

    contracts = db.fetch_contract_areas(conn)

    if not contracts:
        st.info("No contract areas set up yet. Go to the Contract Details tab to add them.")
        return

    # Filter to user's visible departments
    visible = [c for c in contracts if c["department"] in user_depts]
    if not visible:
        visible = contracts  # fallback for admin

    # KPI row
    cols = st.columns(4)
    for idx, c in enumerate(visible):
        dept = c["department"]
        color = _dept_color(dept)
        icon = _dept_icon(dept)
        ct = c.get("contract_type") or "N/A"
        with cols[idx % 4]:
            st.markdown(
                '<div style="background:linear-gradient(135deg, {color} 0%, {color}DD 100%);'
                'color:white;border-radius:12px;padding:1.25rem;text-align:center;'
                'margin-bottom:1rem;box-shadow:0 4px 12px rgba(0,0,0,0.15);">'
                '<div style="font-size:2rem;margin-bottom:0.25rem;"></div>'
                '<div style="font-size:1.1rem;font-weight:700;">{dept}</div>'
                '<div style="font-size:0.8rem;opacity:0.9;margin-top:0.25rem;">{ct}</div>'
                '</div>'.format(color=color, dept=dept, ct=ct),
                unsafe_allow_html=True,
            )

    st.markdown("")

    # Summary cards for each department
    for c in visible:
        dept = c["department"]
        color = _dept_color(dept)
        icon = _dept_icon(dept)
        ct = c.get("contract_type") or "N/A"
        operator = c.get("operator") or "N/A"
        hours = c.get("operating_hours") or "Not set"
        days = c.get("operating_days") or "Not set"
        meals = c.get("meal_periods") or "Not set"
        seats = c.get("seating_capacity") or 0
        start = c.get("contract_start") or "N/A"
        end = c.get("contract_end") or "N/A"
        renewal = c.get("renewal_date") or "N/A"
        notes = c.get("notes") or ""

        # Check if renewal is coming up
        renewal_badge = ""
        if c.get("renewal_date"):
            try:
                rd = datetime.strptime(c["renewal_date"], "%Y-%m-%d").date()
                days_until = (rd - date.today()).days
                if days_until <= 90 and days_until > 0:
                    renewal_badge = (
                        '<span style="background:#FFC107;color:#000;padding:0.15rem 0.5rem;'
                        'border-radius:12px;font-size:0.7rem;font-weight:700;margin-left:0.5rem;">'
                        'Renewal in {} days</span>'.format(days_until)
                    )
                elif days_until <= 0:
                    renewal_badge = (
                        '<span style="background:#DC3545;color:white;padding:0.15rem 0.5rem;'
                        'border-radius:12px;font-size:0.7rem;font-weight:700;margin-left:0.5rem;">'
                        'Renewal Overdue</span>'
                    )
            except Exception:
                pass

        hours_html = hours.replace("\n", "<br>")

        card = (
            '<div style="background:#FFFFFF;border-left:5px solid {color};border-radius:10px;'
            'padding:1.25rem 1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);'
            'border:1px solid #E5E7EB;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;'
            'margin-bottom:0.75rem;">'
            '<div style="font-size:1.15rem;font-weight:700;color:{color};">'
            '{dept}{renewal_badge}</div>'
            '<span style="background:{color}22;color:{color};padding:0.2rem 0.6rem;'
            'border-radius:6px;font-size:0.8rem;font-weight:600;">{ct}</span>'
            '</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;'
            'font-size:0.88rem;">'
            '<div><span style="color:#64748B;font-weight:600;">Operator</span><br>{operator}</div>'
            '<div><span style="color:#64748B;font-weight:600;">Contract Period</span><br>'
            '{start} \u2014 {end}</div>'
            '<div><span style="color:#64748B;font-weight:600;">Renewal Date</span><br>'
            '{renewal}</div>'
            '<div><span style="color:#64748B;font-weight:600;">Operating Days</span><br>{days}</div>'
            '<div><span style="color:#64748B;font-weight:600;">Meal Periods</span><br>{meals}</div>'
            '<div><span style="color:#64748B;font-weight:600;">Seating</span><br>{seats} seats</div>'
            '</div>'
            '<div style="margin-top:0.75rem;">'
            '<span style="color:#64748B;font-weight:600;font-size:0.88rem;">Hours</span>'
            '<div style="background:#F7F8FA;border-radius:6px;padding:0.5rem 0.75rem;'
            'margin-top:0.25rem;font-size:0.88rem;">{hours}</div>'
            '</div>'
        ).format(
            color=color, dept=dept, renewal_badge=renewal_badge,
            ct=ct, operator=operator, start=start, end=end,
            renewal=renewal, days=days, meals=meals, seats=seats,
            hours=hours_html,
        )

        if notes:
            card += (
                '<div style="margin-top:0.5rem;font-size:0.85rem;color:#64748B;'
                'font-style:italic;">{}</div>'.format(notes)
            )

        card += '</div>'
        st.markdown(card, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2: CONTRACT DETAILS (edit individual contracts)
# ═══════════════════════════════════════════════════════

def _render_details_tab(conn, user, user_depts):
    section_title("", "Edit Contract Details")

    if not _can_manage(user):
        st.info("Only Directors and Admins can edit contract details. "
                "Switch to the Overview tab to view contracts.")
        # Still show read-only view
        contracts = db.fetch_contract_areas(conn)
        dept_val = user["department"] if user["department"] else None
        if dept_val:
            contracts = [c for c in contracts if c["department"] == dept_val]
        if contracts:
            for c in contracts:
                _render_readonly_contract(c)
        else:
            st.info("No contract data for your department yet.")
        return

    # Admin/approver can edit
    dept_select = st.selectbox(
        "Select Department to Edit",
        list(DEPARTMENTS),
        key="contract_edit_dept",
    )

    existing = db.fetch_contract_area(conn, dept_select)
    color = _dept_color(dept_select)

    st.markdown(
        '<div style="background:linear-gradient(135deg, {c} 0%, {c}CC 100%);'
        'color:white;padding:0.6rem 1rem;border-radius:8px;font-weight:600;'
        'margin-bottom:1rem;">{dept} — Contract Configuration</div>'.format(
            c=color, dept=dept_select
        ),
        unsafe_allow_html=True,
    )

    with st.form("edit_contract_{}".format(dept_select), clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            section_title("", "Contract Info")
            ct = st.selectbox(
                "Contract Type",
                _CONTRACT_TYPES,
                index=_CONTRACT_TYPES.index(existing["contract_type"])
                if existing and existing.get("contract_type") in _CONTRACT_TYPES else 0,
                key="ct_type_{}".format(dept_select),
            )
            operator = st.text_input(
                "Operator",
                value=existing.get("operator", "Metz Culinary Management") if existing else "Metz Culinary Management",
                key="ct_operator_{}".format(dept_select),
            )
            rev_share = st.number_input(
                "Revenue Share %",
                min_value=float(0), max_value=float(100), step=float(0.5),
                value=float(existing.get("revenue_share_pct", 0)) if existing else float(0),
                key="ct_rev_{}".format(dept_select),
            )
            commission = st.text_area(
                "Commission / Fee Structure",
                value=existing.get("commission_structure", "") if existing else "",
                height=80,
                key="ct_commission_{}".format(dept_select),
            )

        with col2:
            section_title("", "Contract Dates")
            c_start = st.text_input(
                "Contract Start (YYYY-MM-DD)",
                value=existing.get("contract_start", "") if existing else "",
                key="ct_start_{}".format(dept_select),
            )
            c_end = st.text_input(
                "Contract End (YYYY-MM-DD)",
                value=existing.get("contract_end", "") if existing else "",
                key="ct_end_{}".format(dept_select),
            )
            c_renewal = st.text_input(
                "Renewal Date (YYYY-MM-DD)",
                value=existing.get("renewal_date", "") if existing else "",
                key="ct_renewal_{}".format(dept_select),
            )

        st.markdown("")
        col3, col4 = st.columns(2)

        with col3:
            section_title("", "Operating Details")
            op_hours = st.text_area(
                "Operating Hours",
                value=existing.get("operating_hours", "") if existing else "",
                height=100,
                key="ct_hours_{}".format(dept_select),
                help="e.g. Breakfast: 7:00 AM - 9:30 AM",
            )
            op_days = st.text_input(
                "Operating Days",
                value=existing.get("operating_days", "") if existing else "",
                key="ct_days_{}".format(dept_select),
            )
            meal_per = st.text_input(
                "Meal Periods Served",
                value=existing.get("meal_periods", "") if existing else "",
                key="ct_meals_{}".format(dept_select),
            )

        with col4:
            section_title("", "Facility & Contact")
            seats = st.number_input(
                "Seating Capacity",
                min_value=0, step=1,
                value=int(existing.get("seating_capacity", 0)) if existing else 0,
                key="ct_seats_{}".format(dept_select),
            )
            sqft = st.number_input(
                "Square Footage",
                min_value=0, step=1,
                value=int(existing.get("square_footage", 0)) if existing else 0,
                key="ct_sqft_{}".format(dept_select),
            )
            k_name = st.text_input(
                "Key Contact Name",
                value=existing.get("key_contact_name", "") if existing else "",
                key="ct_kname_{}".format(dept_select),
            )
            k_phone = st.text_input(
                "Key Contact Phone",
                value=existing.get("key_contact_phone", "") if existing else "",
                key="ct_kphone_{}".format(dept_select),
            )
            k_email = st.text_input(
                "Key Contact Email",
                value=existing.get("key_contact_email", "") if existing else "",
                key="ct_kemail_{}".format(dept_select),
            )

        st.markdown("")
        section_title("", "Performance & Terms")
        col5, col6 = st.columns(2)
        with col5:
            kpis = st.text_area(
                "Performance KPIs",
                value=existing.get("performance_kpis", "") if existing else "",
                height=100,
                key="ct_kpis_{}".format(dept_select),
                help="Key metrics this contract is measured on",
            )
        with col6:
            special = st.text_area(
                "Special Terms & Conditions",
                value=existing.get("special_terms", "") if existing else "",
                height=100,
                key="ct_special_{}".format(dept_select),
            )

        notes = st.text_area(
            "Additional Notes",
            value=existing.get("notes", "") if existing else "",
            height=80,
            key="ct_notes_{}".format(dept_select),
        )

        submitted = st.form_submit_button(
            "Save Contract for {}".format(dept_select),
            type="primary",
            use_container_width=True,
        )
        if submitted:
            db.upsert_contract_area(
                conn,
                department=dept_select,
                contract_type=ct,
                operator=operator.strip(),
                revenue_share_pct=rev_share,
                commission_structure=commission.strip() or None,
                contract_start=c_start.strip() or None,
                contract_end=c_end.strip() or None,
                renewal_date=c_renewal.strip() or None,
                operating_hours=op_hours.strip() or None,
                operating_days=op_days.strip() or None,
                meal_periods=meal_per.strip() or None,
                seating_capacity=seats,
                square_footage=sqft,
                key_contact_name=k_name.strip() or None,
                key_contact_phone=k_phone.strip() or None,
                key_contact_email=k_email.strip() or None,
                performance_kpis=kpis.strip() or None,
                special_terms=special.strip() or None,
                notes=notes.strip() or None,
                username=user["username"],
            )
            st.success("Contract for {} saved successfully!".format(dept_select))
            st.rerun()


def _render_readonly_contract(c):
    """Read-only contract card for non-admin users."""
    dept = c["department"]
    color = _dept_color(dept)
    icon = _dept_icon(dept)
    hours_html = (c.get("operating_hours") or "N/A").replace("\n", "<br>")

    card = (
        '<div style="background:#FFFFFF;border-left:4px solid {color};border-radius:8px;'
        'padding:1rem;margin-bottom:0.75rem;border:1px solid #E5E7EB;">'
        '<div style="font-weight:700;color:{color};font-size:1rem;margin-bottom:0.5rem;">'
        '{dept}</div>'
        '<div style="font-size:0.88rem;display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">'
        '<div><b>Type:</b> {ct}</div>'
        '<div><b>Operator:</b> {op}</div>'
        '<div><b>Days:</b> {days}</div>'
        '<div><b>Meals:</b> {meals}</div>'
        '</div>'
        '<div style="margin-top:0.5rem;font-size:0.85rem;"><b>Hours:</b><br>{hours}</div>'
        '</div>'
    ).format(
        color=color, dept=dept,
        ct=c.get("contract_type", "N/A"),
        op=c.get("operator", "N/A"),
        days=c.get("operating_days", "N/A"),
        meals=c.get("meal_periods", "N/A"),
        hours=hours_html,
    )
    st.markdown(card, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 3: KEY INFO (hours, emergency, policies)
# ═══════════════════════════════════════════════════════

def _render_key_info_tab(conn, user, user_depts):
    section_title("", "Key Information")

    cat_labels = list(_INFO_CATEGORY_MAP.keys())
    cat_filter = st.selectbox(
        "Filter by Category",
        cat_labels,
        key="keyinfo_cat_filter",
    )
    cat_val = _INFO_CATEGORY_MAP.get(cat_filter)

    dept_val = None
    if len(user_depts) > 1:
        dept_filter = st.selectbox(
            "Filter by Department",
            ["All Departments"] + list(user_depts),
            key="keyinfo_dept_filter",
        )
        dept_val = None if dept_filter == "All Departments" else dept_filter
    elif user_depts:
        dept_val = user_depts[0]

    entries = db.fetch_key_info(conn, category=cat_val, department=dept_val)

    if entries:
        cat_groups = {}
        for e in entries:
            c = e.get("category", "other")
            if c not in cat_groups:
                cat_groups[c] = []
            cat_groups[c].append(e)

        cat_display_order = ["hours", "emergency", "policy"]
        for cat in cat_display_order:
            if cat not in cat_groups:
                continue
            items = cat_groups[cat]

            if cat == "hours":
                _render_hours_section(items, conn, user)
            elif cat == "emergency":
                _render_emergency_section(items, conn, user)
            elif cat == "policy":
                _render_policy_section(items, conn, user)

        for cat, items in cat_groups.items():
            if cat not in cat_display_order:
                section_title("", "{} Information".format(cat.title()))
                for item in items:
                    _render_info_card(item, conn, user, border_color="#64748B")
    else:
        st.info("No key information entries found.")

    # Add Key Info form (admin/approver only)
    if _can_manage(user):
        mini_divider()
        section_title("", "Add Key Information")
        with st.form("add_keyinfo_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                ki_category = st.selectbox(
                    "Category *",
                    ["hours", "emergency", "policy"],
                    format_func=lambda x: {
                        "hours": "Hours",
                        "emergency": "Emergency Procedures",
                        "policy": "Policies"
                    }.get(x, x),
                    key="new_ki_category",
                )
                ki_title = st.text_input("Title *", key="new_ki_title")
                ki_dept = st.selectbox(
                    "Department",
                    ["All Departments"] + list(DEPARTMENTS),
                    key="new_ki_dept",
                )
            with col2:
                ki_content = st.text_area(
                    "Content *",
                    key="new_ki_content",
                    height=150,
                    help="Use line breaks to separate items",
                )
                ki_priority = st.selectbox(
                    "Priority",
                    [1, 2, 3],
                    format_func=lambda x: {
                        1: "1 - Normal",
                        2: "2 - High",
                        3: "3 - Critical"
                    }.get(x, str(x)),
                    key="new_ki_priority",
                )

            submitted = st.form_submit_button("Add Key Info", type="primary")
            if submitted:
                if not ki_title.strip() or not ki_content.strip():
                    st.error("Title and Content are required.")
                else:
                    dept_value = None if ki_dept == "All Departments" else ki_dept
                    db.upsert_key_info(
                        conn,
                        category=ki_category,
                        title=ki_title.strip(),
                        content=ki_content.strip(),
                        department=dept_value,
                        priority=ki_priority,
                        username=user["username"],
                    )
                    st.success("Key info '{}' added.".format(ki_title.strip()))
                    st.rerun()


# ─── Key Info Section Renderers ───

def _render_hours_section(items, conn, user):
    """Render operating hours cards."""
    section_title("", "Operating Hours")
    cols = st.columns(min(len(items), 3))
    for idx, item in enumerate(items):
        col_idx = idx % min(len(items), 3)
        with cols[col_idx]:
            dept_name = item.get("department") or "General"
            color = _dept_color(dept_name)
            content_lines = (item.get("content") or "").split("\n")
            lines_html = ""
            for line in content_lines:
                if line.strip():
                    lines_html += '<div style="padding:0.2rem 0;font-size:0.9rem;">{}</div>'.format(
                        line.strip()
                    )

            card_html = (
                '<div style="background:#FFFFFF;border-radius:10px;padding:1rem 1.25rem;'
                'box-shadow:0 1px 3px rgba(0,0,0,0.08);border:1px solid #E5E7EB;'
                'border-top:3px solid {color};margin-bottom:0.75rem;">'
                '<div style="font-weight:700;color:{color};font-size:0.95rem;'
                'margin-bottom:0.5rem;">{title}</div>'
                '{lines}'
                '</div>'
            ).format(color=color, title=item.get("title", ""), lines=lines_html)
            st.markdown(card_html, unsafe_allow_html=True)

            if _can_manage(user):
                del_key = "del_ki_{}".format(item["id"])
                if st.button("Delete", key=del_key, help="Delete"):
                    db.delete_key_info(conn, item["id"])
                    st.rerun()


def _render_emergency_section(items, conn, user):
    """Render emergency procedure cards with warning styling."""
    section_title("", "Emergency Procedures")
    for item in items:
        content_lines = (item.get("content") or "").split("\n")
        steps_html = ""
        for i, line in enumerate(content_lines):
            if line.strip():
                step_num = i + 1
                steps_html += (
                    '<div style="padding:0.3rem 0;display:flex;align-items:flex-start;gap:0.5rem;">'
                    '<span style="background:#DC3545;color:white;border-radius:50%;'
                    'min-width:22px;height:22px;display:flex;align-items:center;'
                    'justify-content:center;font-size:0.75rem;font-weight:700;">{num}</span>'
                    '<span style="font-size:0.9rem;">{text}</span>'
                    '</div>'
                ).format(num=step_num, text=line.strip())

        dept_label = item.get("department") or "All Departments"
        card_html = (
            '<div style="background:#FFF5F5;border:2px solid #DC3545;border-radius:10px;'
            'padding:1rem 1.25rem;margin-bottom:0.75rem;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;'
            'margin-bottom:0.5rem;">'
            '<span style="font-weight:700;color:#DC3545;font-size:1rem;">'
            '{title}</span>'
            '<span style="font-size:0.75rem;color:#64748B;">{dept}</span>'
            '</div>'
            '{steps}'
            '</div>'
        ).format(title=item.get("title", ""), dept=dept_label, steps=steps_html)
        st.markdown(card_html, unsafe_allow_html=True)

        if _can_manage(user):
            del_key = "del_ki_{}".format(item["id"])
            if st.button("Delete", key=del_key, help="Delete this procedure"):
                db.delete_key_info(conn, item["id"])
                st.rerun()


def _render_policy_section(items, conn, user):
    """Render policy cards."""
    section_title("", "Policies & Procedures")
    for item in items:
        _render_info_card(item, conn, user, border_color="#64748B")


def _render_info_card(item, conn, user, border_color="#64748B"):
    """Render a generic key info card."""
    content_lines = (item.get("content") or "").split("\n")
    lines_html = ""
    for line in content_lines:
        if line.strip():
            lines_html += (
                '<div style="padding:0.2rem 0;font-size:0.9rem;'
                'padding-left:0.75rem;border-left:2px solid #E5E7EB;">'
                '\u2022 {}</div>'.format(line.strip())
            )

    dept_label = item.get("department") or "All Departments"
    priority_val = item.get("priority", 0)
    priority_badge = ""
    if priority_val >= 2:
        priority_badge = (
            '<span style="background:#FFC107;color:#000;padding:0.1rem 0.4rem;'
            'border-radius:4px;font-size:0.7rem;font-weight:700;margin-left:0.5rem;">'
            'HIGH PRIORITY</span>'
        )

    card_html = (
        '<div style="background:#FFFFFF;border-left:4px solid {border};border-radius:8px;'
        'padding:0.75rem 1rem;margin-bottom:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.06);'
        'border-top:1px solid #E5E7EB;border-right:1px solid #E5E7EB;'
        'border-bottom:1px solid #E5E7EB;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        'margin-bottom:0.4rem;">'
        '<span style="font-weight:600;color:#1F2A44;font-size:0.95rem;">'
        '{title}{priority}</span>'
        '<span style="font-size:0.75rem;color:#64748B;">{dept}</span>'
        '</div>'
        '{lines}'
        '</div>'
    ).format(
        border=border_color,
        title=item.get("title", ""),
        priority=priority_badge,
        dept=dept_label,
        lines=lines_html,
    )
    st.markdown(card_html, unsafe_allow_html=True)

    if _can_manage(user):
        del_key = "del_ki_{}".format(item["id"])
        if st.button("Delete", key=del_key, help="Delete"):
            db.delete_key_info(conn, item["id"])
            st.rerun()
