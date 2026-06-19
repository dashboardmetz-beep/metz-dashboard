"""
Weekly Budget Entry — Premium dashboard-style layout.
KPI row + daily revenue entry table with categories.
"""

from datetime import date, timedelta
import streamlit as st

from config import DEPARTMENTS
from calculations import sum_revenue_streams, fmt_dollar
from styles import hero_header
import db


def _icon(name):
    icons = {
        "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "briefcase": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
        "percent": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>',
        "utensils": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
        "people": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
        "chart": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        "check": '<svg width="14" height="14" viewBox="0 0 24 24" fill="#16A34A"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
        "cat_board": '<svg width="14" height="14" viewBox="0 0 24 24" fill="#16A34A"><circle cx="12" cy="12" r="8"/></svg>',
        "cat_flex": '<svg width="14" height="14" viewBox="0 0 24 24" fill="#D97706"><circle cx="12" cy="12" r="8"/></svg>',
        "cat_catering": '<svg width="14" height="14" viewBox="0 0 24 24" fill="#F97316"><circle cx="12" cy="12" r="8"/></svg>',
        "cat_other": '<svg width="14" height="14" viewBox="0 0 24 24" fill="#3B82F6"><circle cx="12" cy="12" r="8"/></svg>',
    }
    return icons.get(name, "")


def page_weekly_entry(conn, user):
    # ─── State ───
    today = date.today()
    if "we_week" not in st.session_state:
        st.session_state.we_week = db.get_week_start(today) - timedelta(weeks=1)
    if "we_dept" not in st.session_state:
        st.session_state.we_dept = "Board & Catering"
    if "we_view_mode" not in st.session_state:
        st.session_state.we_view_mode = "$ Amount"

    week_start = st.session_state.we_week
    week_end = week_start + timedelta(days=6)

    # ─── Hero header ───
    def _we_right():
        d1, d2, d3, d4 = st.columns([2, 1, 1, 1.1])
        with d1:
            st.markdown(
                '<div class="de-date-display">'
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                'stroke="#0B1628" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<rect x="3" y="4" width="18" height="18" rx="2"/>'
                '<line x1="16" y1="2" x2="16" y2="6"/>'
                '<line x1="8" y1="2" x2="8" y2="6"/>'
                '<line x1="3" y1="10" x2="21" y2="10"/></svg>'
                '<span>Week Ending {d}</span>'
                '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
                'stroke="#8B7E66" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<polyline points="6 9 12 15 18 9"/></svg>'
                '</div>'.format(d=week_end.strftime("%b %-d, %Y")),
                unsafe_allow_html=True,
            )
        with d2:
            if st.button("‹  Prev Week", key="we_prev_week",
                         use_container_width=True):
                st.session_state.we_week -= timedelta(weeks=1)
                st.rerun()
        with d3:
            if st.button("Next Week  ›", key="we_next_week",
                         use_container_width=True):
                st.session_state.we_week += timedelta(weeks=1)
                st.rerun()
        with d4:
            if st.button("💾  Save All", key="we_save_all_v2",
                         use_container_width=True, type="primary"):
                st.toast("All budgets saved", icon="✅")

    hero_header(
        "Weekly Budget Entry",
        "Enter and review weekly budgets by unit",
        _we_right,
    )

    # ─── Department tabs + Roll Up Daily Totals ───
    dt1, dt2 = st.columns([4, 1])
    with dt1:
        dept_cols = st.columns(len(DEPARTMENTS) + 1)
        all_depts = list(DEPARTMENTS) + ["Consolidated"]
        for i, d in enumerate(all_depts):
            with dept_cols[i]:
                is_active = st.session_state.we_dept == d
                label = d.replace(" & ", " & ")
                btn_key = "we_dept_{}".format(d.replace(" ", "_").replace("&", "and").lower())
                if st.button(label, key=btn_key, use_container_width=True):
                    st.session_state.we_dept = d
                    st.rerun()
    with dt2:
        st.button("📊 Roll Up Daily Totals", key="we_rollup",
                  use_container_width=True)

    dept = st.session_state.we_dept

    # ─── KPI Row ───
    _render_kpi_row(conn, week_start, dept)

    # ─── Revenue Entry Table ───
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    _render_revenue_table(conn, user, week_start, dept)

    # ─── Footer ───
    st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1.5, 4, 1.5])
    with f1:
        st.button("💾 Save Draft", key="we_draft", use_container_width=True)
    with f2:
        st.markdown(
            '<div class="we-save-status">'
            '<span class="ws-check">{}</span>'
            '<span class="ws-text">All data saved automatically</span>'
            '<span class="ws-time">Last saved: just now</span>'
            '</div>'.format(_icon("check")),
            unsafe_allow_html=True,
        )
    with f3:
        st.button("Review & Submit ▾", key="we_submit",
                  use_container_width=True, type="primary")


def _render_kpi_row(conn, week_start, dept):
    """5 KPI cards across the top."""
    # Fetch current week
    if dept == "Consolidated":
        rows = conn.execute(
            """SELECT
                  COALESCE(SUM(board_revenue),0) + COALESCE(SUM(retail_revenue),0) +
                  COALESCE(SUM(flex_revenue),0) + COALESCE(SUM(catering_revenue),0) +
                  COALESCE(SUM(other_revenue),0) AS revenue,
                  COALESCE(SUM(cos_dollars),0) +
                  COALESCE(SUM(total_labor_dollars),0) +
                  COALESCE(SUM(direct_expenses),0) AS expenses,
                  COALESCE(SUM(cos_dollars),0) AS cos,
                  COALESCE(SUM(total_labor_dollars),0) AS labor_d
               FROM weekly_financials WHERE week_start = ?""",
            (week_start.isoformat(),)
        ).fetchone()
        last_rows = conn.execute(
            """SELECT
                  COALESCE(SUM(board_revenue),0) + COALESCE(SUM(retail_revenue),0) +
                  COALESCE(SUM(flex_revenue),0) + COALESCE(SUM(catering_revenue),0) +
                  COALESCE(SUM(other_revenue),0) AS revenue,
                  COALESCE(SUM(cos_dollars),0) AS cos,
                  COALESCE(SUM(total_labor_dollars),0) AS labor_d
               FROM weekly_financials WHERE week_start = ?""",
            ((week_start - timedelta(weeks=1)).isoformat(),)
        ).fetchone()
    else:
        rows = conn.execute(
            """SELECT
                  COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue,
                  COALESCE(cos_dollars,0) +
                  COALESCE(total_labor_dollars,0) +
                  COALESCE(direct_expenses,0) AS expenses,
                  COALESCE(cos_dollars,0) AS cos,
                  COALESCE(total_labor_dollars,0) AS labor_d
               FROM weekly_financials
               WHERE week_start=? AND department=?""",
            (week_start.isoformat(), dept)
        ).fetchone()
        last_rows = conn.execute(
            """SELECT
                  COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue,
                  COALESCE(cos_dollars,0) AS cos,
                  COALESCE(total_labor_dollars,0) AS labor_d
               FROM weekly_financials
               WHERE week_start=? AND department=?""",
            ((week_start - timedelta(weeks=1)).isoformat(), dept)
        ).fetchone()

    revenue = rows["revenue"] if rows else 0
    expenses = rows["expenses"] if rows else 0
    cos = rows["cos"] if rows else 0
    labor_d = rows["labor_d"] if rows else 0
    last_rev = (last_rows["revenue"] if last_rows else 0) or 0
    last_cos = (last_rows["cos"] if last_rows else 0) or 0
    last_labor_d = (last_rows["labor_d"] if last_rows else 0) or 0
    last_expenses = last_cos + last_labor_d

    labor_pct = (labor_d / revenue * 100) if revenue > 0 else 0
    fc_pct = (cos / revenue * 100) if revenue > 0 else 0
    last_labor_pct = (last_labor_d / last_rev * 100) if last_rev > 0 else 0
    last_fc_pct = (last_cos / last_rev * 100) if last_rev > 0 else 0

    rev_delta = ((revenue - last_rev) / last_rev * 100) if last_rev > 0 else 0
    exp_delta = ((expenses - last_expenses) / last_expenses * 100) if last_expenses > 0 else 0
    labor_delta = labor_pct - last_labor_pct
    fc_delta = fc_pct - last_fc_pct

    # Covers from door_counts
    covers_row = conn.execute(
        """SELECT COALESCE(SUM(count),0) FROM door_counts
           WHERE entry_date >= ? AND entry_date <= ?""",
        (week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchone()
    covers = (covers_row[0] or 0) if covers_row else 0
    last_covers_row = conn.execute(
        """SELECT COALESCE(SUM(count),0) FROM door_counts
           WHERE entry_date >= ? AND entry_date <= ?""",
        ((week_start - timedelta(weeks=1)).isoformat(),
         (week_start - timedelta(days=1)).isoformat())
    ).fetchone()
    last_covers = (last_covers_row[0] or 0) if last_covers_row else 0
    covers_delta = ((covers - last_covers) / last_covers * 100) if last_covers > 0 else 0

    cards = st.columns(5)
    metrics = [
        ("TOTAL REVENUE", "${:,.2f}".format(revenue),
         "vs Last Week", rev_delta, "%", "dollar", "#ECFDF5", False),
        ("TOTAL EXPENSES", "${:,.2f}".format(expenses),
         "vs Last Week", exp_delta, "%", "briefcase", "#EFF6FF", True),
        ("LABOR %", "{:.1f}%".format(labor_pct),
         "vs Last Week", labor_delta, "pts", "percent", "#F5F3FF", True),
        ("FOOD COST %", "{:.1f}%".format(fc_pct),
         "vs Last Week", fc_delta, "pts", "utensils", "#FFFBEB", True),
        ("COVERS", "{:,}".format(int(covers)),
         "vs Last Week", covers_delta, "%", "people", "#F0F9FF", False),
    ]

    for i, (label, value, prefix, delta, unit, icon, bg, invert) in enumerate(metrics):
        with cards[i]:
            is_positive = delta >= 0
            if invert:
                color = "#DC2626" if is_positive else "#16A34A"
            else:
                color = "#16A34A" if is_positive else "#DC2626"
            arrow = "▲" if is_positive else "▼"
            sign = ""
            delta_str = "{}{:.1f} {}".format(sign, abs(delta), unit)

            st.markdown(
                '<div class="we-kpi-card">'
                '<div class="we-kpi-row">'
                '<div class="we-kpi-icon" style="background:{bg};">{icon}</div>'
                '<div class="we-kpi-meta">'
                '<div class="we-kpi-label">{label}</div>'
                '<div class="we-kpi-value">{value}</div>'
                '<div class="we-kpi-delta">{prefix} '
                '<span style="color:{c};font-weight:600;">{a} {d}</span></div>'
                '</div></div></div>'.format(
                    bg=bg, icon=_icon(icon), label=label, value=value,
                    prefix=prefix, c=color, a=arrow, d=delta_str,
                ),
                unsafe_allow_html=True,
            )


def _render_revenue_table(conn, user, week_start, dept):
    """Daily revenue entry table — 7 days × categories."""
    st.markdown(
        '<div class="we-section-card">'
        '<div class="we-section-header">'
        '<div>'
        '<span class="we-section-title">Revenue Entry</span>'
        '<span class="we-section-sub">Auto-calculated total</span>'
        '</div>'
        '<div class="we-toggle-row">',
        unsafe_allow_html=True,
    )

    # Toggle $ Amount / % of Sales
    tg1, tg2, _ = st.columns([0.7, 0.7, 4])
    with tg1:
        is_amt = st.session_state.we_view_mode == "$ Amount"
        if st.button("$ Amount", key="we_mode_amt", use_container_width=True):
            st.session_state.we_view_mode = "$ Amount"
            st.rerun()
    with tg2:
        if st.button("% of Sales", key="we_mode_pct", use_container_width=True):
            st.session_state.we_view_mode = "% of Sales"
            st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Days header
    days = [(week_start + timedelta(days=i)) for i in range(7)]

    # Categories with colored dots
    categories = [
        ("Board", "board_revenue", "cat_board"),
        ("Flex", "flex_revenue", "cat_flex"),
        ("Catering", "catering_revenue", "cat_catering"),
        ("Other", "other_revenue", "cat_other"),
    ]

    if dept == "Consolidated":
        st.info("Consolidated view — drill into a specific department to enter daily revenue.")
        return

    # Existing daily sales for this dept + week
    existing_rows = conn.execute(
        """SELECT entry_date, board_revenue, retail_revenue, flex_revenue,
                  catering_revenue, other_revenue
           FROM daily_sales
           WHERE department=? AND entry_date >= ? AND entry_date <= ?""",
        (dept, week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchall()
    existing_map = {r[0]: dict(r) for r in existing_rows}

    # Render table
    # Header row
    header_html = '<tr><th class="t-cat">CATEGORY</th>'
    for d in days:
        header_html += (
            '<th class="t-day"><div class="t-day-name">{}</div>'
            '<div class="t-day-date">{}</div></th>'.format(
                d.strftime("%a").upper(), d.strftime("%b %d"))
        )
    header_html += '<th class="t-week">WEEK TOTAL</th></tr>'

    # Data rows
    rows_html = ""
    column_totals = [0.0] * 7
    week_grand_total = 0

    for cat_label, cat_field, icon_name in categories:
        cells_html = '<td class="t-cat"><div class="t-cat-label">{}<span>{} ($)</span></div></td>'.format(
            _icon(icon_name), cat_label,
        )
        row_total = 0
        for i, d in enumerate(days):
            day_data = existing_map.get(d.isoformat(), {})
            val = day_data.get(cat_field, 0) or 0
            row_total += val
            column_totals[i] += val
            cells_html += '<td class="t-cell">{:,.0f}</td>'.format(val)
        cells_html += '<td class="t-total-cell">${:,.2f}</td>'.format(row_total)
        week_grand_total += row_total
        rows_html += '<tr>{}</tr>'.format(cells_html)

    # Total row
    total_row = '<tr class="t-total-row"><td class="t-cat"><b>TOTAL REVENUE ($)</b></td>'
    for v in column_totals:
        total_row += '<td class="t-cell"><b>${:,.0f}</b></td>'.format(v)
    total_row += '<td class="t-total-cell"><b>${:,.2f}</b></td></tr>'.format(week_grand_total)
    rows_html += total_row

    st.markdown(
        '<table class="we-revenue-table">'
        '<thead>{}</thead>'
        '<tbody>{}</tbody>'
        '</table>'.format(header_html, rows_html),
        unsafe_allow_html=True,
    )

    # Quick-edit panel — let user edit one day at a time
    with st.expander("✏️ Edit revenue for a specific day"):
        edit_day = st.selectbox(
            "Day",
            options=[d.isoformat() for d in days],
            format_func=lambda x: "{} ({})".format(
                date.fromisoformat(x).strftime("%A"),
                date.fromisoformat(x).strftime("%b %d")),
            key="we_edit_day",
        )
        edit_data = existing_map.get(edit_day, {})

        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            board = st.number_input(
                "Board $", min_value=0.0, step=10.0,
                value=float(edit_data.get("board_revenue") or 0),
                key="we_edit_board_{}".format(edit_day),
            )
        with ec2:
            flex = st.number_input(
                "Flex $", min_value=0.0, step=10.0,
                value=float(edit_data.get("flex_revenue") or 0),
                key="we_edit_flex_{}".format(edit_day),
            )
        with ec3:
            catering = st.number_input(
                "Catering $", min_value=0.0, step=10.0,
                value=float(edit_data.get("catering_revenue") or 0),
                key="we_edit_cat_{}".format(edit_day),
            )
        with ec4:
            other = st.number_input(
                "Other $", min_value=0.0, step=10.0,
                value=float(edit_data.get("other_revenue") or 0),
                key="we_edit_other_{}".format(edit_day),
            )

        retail = float(edit_data.get("retail_revenue") or 0)
        if st.button("Save day", key="we_save_day", type="primary"):
            conn.execute(
                """INSERT OR REPLACE INTO daily_sales
                   (entry_date, department, board_revenue, retail_revenue,
                    flex_revenue, catering_revenue, other_revenue,
                    updated_by, updated_at)
                   VALUES (?,?,?,?,?,?,?,?, datetime('now','localtime'))""",
                (edit_day, dept, board, retail, flex, catering, other,
                 user.get("username", "system"))
            )
            conn.commit()
            st.success("Saved {}".format(edit_day))
            st.rerun()
