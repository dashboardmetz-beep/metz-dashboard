"""
Flash Report — Premium financial summary layout.
KPI row + sub-tabs (Financial Summary, Operational Summary, etc.) + line-item table.
"""

from datetime import date, timedelta, datetime
import streamlit as st

from config import DEPARTMENTS
from calculations import fmt_dollar, fmt_pct
from styles import hero_header
import db


def _icon(name):
    icons = {
        "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "briefcase": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
        "percent": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>',
        "utensils": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
        "people": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
        "info": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "building": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/></svg>',
        "clock": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "cloud-up": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 16l-4-4-4 4"/><path d="M12 12v9"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/><polyline points="16 16 12 12 8 16"/></svg>',
        "cat_board": '<svg width="12" height="12" viewBox="0 0 24 24" fill="#16A34A"><circle cx="12" cy="12" r="8"/></svg>',
        "cat_flex": '<svg width="12" height="12" viewBox="0 0 24 24" fill="#8B5CF6"><circle cx="12" cy="12" r="8"/></svg>',
        "cat_catering": '<svg width="12" height="12" viewBox="0 0 24 24" fill="#F97316"><circle cx="12" cy="12" r="8"/></svg>',
        "cat_other": '<svg width="12" height="12" viewBox="0 0 24 24" fill="#3B82F6"><circle cx="12" cy="12" r="8"/></svg>',
        "chevron": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>',
    }
    return icons.get(name, "")


def page_flash_report(conn, user):
    # ─── State ───
    today = date.today()
    if "fr_week" not in st.session_state:
        st.session_state.fr_week = db.get_week_start(today) - timedelta(weeks=1)
    if "fr_dept" not in st.session_state:
        st.session_state.fr_dept = "Consolidated"
    if "fr_subtab" not in st.session_state:
        st.session_state.fr_subtab = "Financial Summary"

    week_start = st.session_state.fr_week
    week_end = week_start + timedelta(days=6)
    dept = st.session_state.fr_dept

    # ─── Hero header ───
    def _fr_right():
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
            if st.button("‹  Prev Week", key="fr_prev_week",
                         use_container_width=True):
                st.session_state.fr_week -= timedelta(weeks=1)
                st.rerun()
        with d3:
            if st.button("Next Week  ›", key="fr_next_week",
                         use_container_width=True):
                st.session_state.fr_week += timedelta(weeks=1)
                st.rerun()
        with d4:
            if st.button("💾  Save All", key="fr_save_all_v2",
                         use_container_width=True, type="primary"):
                st.toast("Saved", icon="✅")

    hero_header(
        "Flash Report",
        "Weekly financial and operational performance summary",
        _fr_right,
    )

    # ─── Info bar ───
    last_updated = conn.execute(
        """SELECT MAX(updated_at) FROM weekly_financials WHERE week_start=?""",
        (week_start.isoformat(),)
    ).fetchone()
    last_str = last_updated[0] if last_updated and last_updated[0] else "—"

    imported = conn.execute(
        """SELECT MAX(imported_at) FROM odyssey_import_log
           WHERE report_date >= ? AND report_date <= ?""",
        (week_start.isoformat(), week_end.isoformat())
    ).fetchone()
    imported_str = imported[0] if imported and imported[0] else None

    info_html = (
        '<div class="fr-info-bar">'
        '<div class="fr-info-item">{bld}<span class="fii-label">Department:</span>'
        '<span class="fii-value"><b>{dept}</b></span></div>'
        '<div class="fr-info-item">{clk}<span class="fii-label">Last Updated:</span>'
        '<span class="fii-value">{last}</span></div>'
    ).format(
        bld=_icon("building"), clk=_icon("clock"),
        dept=dept, last=last_str,
    )
    if imported_str:
        info_html += (
            '<div class="fr-info-item" style="margin-left:auto;">'
            '<span class="fr-badge-imported">Imported</span>'
            '{c}<span class="fii-value">{i}</span></div>'
        ).format(c=_icon("cloud-up"), i=imported_str)
    info_html += '</div>'
    st.markdown(info_html, unsafe_allow_html=True)

    # ─── KPI Row ───
    _render_kpi_row(conn, week_start, dept)

    # ─── Sub-tabs ───
    st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
    subtabs = ["Financial Summary", "Operational Summary",
               "Revenue Breakdown", "Labor Summary", "Variance Analysis"]
    tcols = st.columns(len(subtabs))
    for i, st_name in enumerate(subtabs):
        with tcols[i]:
            is_active = st.session_state.fr_subtab == st_name
            btn_type = "primary" if is_active else "secondary"
            if st.button(st_name, key="fr_subtab_{}".format(i),
                         use_container_width=True, type=btn_type):
                st.session_state.fr_subtab = st_name
                st.rerun()

    st.markdown('<div class="fr-subtab-divider"></div>', unsafe_allow_html=True)

    # ─── Content based on subtab ───
    if st.session_state.fr_subtab == "Financial Summary":
        _render_financial_summary(conn, week_start, dept)
    elif st.session_state.fr_subtab == "Operational Summary":
        _render_operational_summary(conn, week_start, dept)
    elif st.session_state.fr_subtab == "Revenue Breakdown":
        _render_revenue_breakdown(conn, week_start, dept)
    elif st.session_state.fr_subtab == "Labor Summary":
        _render_labor_summary(conn, week_start, dept)
    elif st.session_state.fr_subtab == "Variance Analysis":
        _render_variance_analysis(conn, week_start, dept)

    # ─── Footer ───
    st.markdown('<div style="margin-top:18px;"></div>', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([1, 4, 1.5])
    with fc1:
        st.button("💾 Save Draft", key="fr_save_draft", use_container_width=True)
    with fc3:
        st.button("✓ Review & Submit ▾", key="fr_submit",
                  use_container_width=True, type="primary")


def _fetch_kpis(conn, week_start, dept):
    """Fetch totals for KPI cards."""
    if dept == "Consolidated":
        row = conn.execute(
            """SELECT
                  COALESCE(SUM(board_revenue),0) + COALESCE(SUM(retail_revenue),0) +
                  COALESCE(SUM(flex_revenue),0) + COALESCE(SUM(catering_revenue),0) +
                  COALESCE(SUM(other_revenue),0) AS revenue,
                  COALESCE(SUM(cos_dollars),0) +
                  COALESCE(SUM(total_labor_dollars),0) +
                  COALESCE(SUM(direct_expenses),0) AS expenses,
                  COALESCE(SUM(cos_dollars),0) AS cos,
                  COALESCE(SUM(total_labor_dollars),0) AS labor_d
               FROM weekly_financials WHERE week_start=?""",
            (week_start.isoformat(),)
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT
                  COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue,
                  COALESCE(cos_dollars,0) +
                  COALESCE(total_labor_dollars,0) +
                  COALESCE(direct_expenses,0) AS expenses,
                  COALESCE(cos_dollars,0) AS cos,
                  COALESCE(total_labor_dollars,0) AS labor_d
               FROM weekly_financials WHERE week_start=? AND department=?""",
            (week_start.isoformat(), dept)
        ).fetchone()
    return dict(row) if row else {"revenue": 0, "expenses": 0, "cos": 0, "labor_d": 0}


def _render_kpi_row(conn, week_start, dept):
    """Top 5 KPI cards."""
    this_wk = _fetch_kpis(conn, week_start, dept)
    last_wk = _fetch_kpis(conn, week_start - timedelta(weeks=1), dept)

    revenue = this_wk["revenue"]
    expenses = this_wk["expenses"]
    labor_pct = (this_wk["labor_d"] / revenue * 100) if revenue > 0 else 0
    fc_pct = (this_wk["cos"] / revenue * 100) if revenue > 0 else 0
    last_labor_pct = (last_wk["labor_d"] / last_wk["revenue"] * 100) if last_wk["revenue"] > 0 else 0
    last_fc_pct = (last_wk["cos"] / last_wk["revenue"] * 100) if last_wk["revenue"] > 0 else 0

    rev_delta = ((revenue - last_wk["revenue"]) / last_wk["revenue"] * 100) if last_wk["revenue"] > 0 else 0
    exp_delta = ((expenses - last_wk["expenses"]) / last_wk["expenses"] * 100) if last_wk["expenses"] > 0 else 0

    covers_row = conn.execute(
        "SELECT COALESCE(SUM(count),0) FROM door_counts WHERE entry_date >= ? AND entry_date <= ?",
        (week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchone()
    covers = (covers_row[0] or 0) if covers_row else 0
    last_covers_row = conn.execute(
        "SELECT COALESCE(SUM(count),0) FROM door_counts WHERE entry_date >= ? AND entry_date <= ?",
        ((week_start - timedelta(weeks=1)).isoformat(),
         (week_start - timedelta(days=1)).isoformat())
    ).fetchone()
    last_covers = (last_covers_row[0] or 0) if last_covers_row else 0
    cov_delta = ((covers - last_covers) / last_covers * 100) if last_covers > 0 else 0

    cards = st.columns(5)
    metrics = [
        ("Total Revenue", "${:,.2f}".format(revenue), rev_delta, "%", "dollar", "#ECFDF5", False),
        ("Total Expenses", "${:,.2f}".format(expenses), exp_delta, "%", "briefcase", "#EFF6FF", True),
        ("Labor %", "{:.1f}%".format(labor_pct), labor_pct - last_labor_pct, "pts", "percent", "#F5F3FF", True),
        ("Food Cost %", "{:.1f}%".format(fc_pct), fc_pct - last_fc_pct, "pts", "utensils", "#FFFBEB", True),
        ("Covers", "{:,}".format(int(covers)), cov_delta, "%", "people", "#F0F9FF", False),
    ]
    for i, (label, value, delta, unit, icon, bg, invert) in enumerate(metrics):
        with cards[i]:
            is_positive = delta >= 0
            if invert:
                color = "#DC2626" if is_positive else "#16A34A"
            else:
                color = "#16A34A" if is_positive else "#DC2626"
            arrow = "▲" if is_positive else "▼"
            delta_str = "{:.1f} {}".format(abs(delta), unit)
            st.markdown(
                '<div class="fr-kpi">'
                '<div class="fr-kpi-row">'
                '<div class="fr-kpi-icon" style="background:{bg};">{icon}</div>'
                '<div class="fr-kpi-meta">'
                '<div class="fr-kpi-label">{label}</div>'
                '<div class="fr-kpi-value">{value}</div>'
                '<div class="fr-kpi-delta">'
                '<span style="color:{c};font-weight:600;">{a} {d}</span> '
                '<span style="color:#94A3B8;">vs Last Week</span></div>'
                '</div></div></div>'.format(
                    bg=bg, icon=_icon(icon), label=label, value=value,
                    c=color, a=arrow, d=delta_str,
                ),
                unsafe_allow_html=True,
            )


def _fetch_dept_breakdown(conn, week_start, dept):
    """Get revenue breakdown by category for actual/budget/projection."""
    # Actuals from weekly_financials
    if dept == "Consolidated":
        row = conn.execute(
            """SELECT
                  COALESCE(SUM(board_revenue),0) AS board,
                  COALESCE(SUM(flex_revenue),0) AS flex,
                  COALESCE(SUM(catering_revenue),0) AS catering,
                  COALESCE(SUM(other_revenue),0) AS other,
                  COALESCE(SUM(retail_revenue),0) AS retail
               FROM weekly_financials WHERE week_start=?""",
            (week_start.isoformat(),)
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT
                  COALESCE(board_revenue,0) AS board,
                  COALESCE(flex_revenue,0) AS flex,
                  COALESCE(catering_revenue,0) AS catering,
                  COALESCE(other_revenue,0) AS other,
                  COALESCE(retail_revenue,0) AS retail
               FROM weekly_financials WHERE week_start=? AND department=?""",
            (week_start.isoformat(), dept)
        ).fetchone()
    actual = dict(row) if row else {"board": 0, "flex": 0, "catering": 0, "other": 0, "retail": 0}

    # Budget (estimate as 95% of actual or from budgets table)
    if dept == "Consolidated":
        budget_row = conn.execute(
            """SELECT COALESCE(SUM(revenue),0) FROM budgets WHERE week_start=?""",
            (week_start.isoformat(),)
        ).fetchone()
    else:
        budget_row = conn.execute(
            """SELECT COALESCE(revenue,0) FROM budgets WHERE week_start=? AND department=?""",
            (week_start.isoformat(), dept)
        ).fetchone()
    budget_total = (budget_row[0] or 0) if budget_row else 0
    actual_total = sum(actual.values())
    ratio = budget_total / actual_total if actual_total else 1
    budget = {k: v * ratio for k, v in actual.items()}

    # Projection (assume between budget and actual)
    projection = {k: (b + a) / 2 for k, b in budget.items() for a in [actual.get(k, 0)]}
    projection = {k: (budget[k] + actual[k]) / 2 for k in actual}

    return actual, budget, projection


def _render_financial_summary(conn, week_start, dept):
    """Main Financial Summary table."""
    actual, budget, projection = _fetch_dept_breakdown(conn, week_start, dept)

    categories = [
        ("Board", "board", "cat_board"),
        ("Flex", "flex", "cat_flex"),
        ("Catering", "catering", "cat_catering"),
        ("Other", "other", "cat_other"),
    ]

    rows_html = ""
    # REVENUE section header
    rows_html += (
        '<tr class="t-section-header">'
        '<td colspan="6" class="t-section">REVENUE</td>'
        '</tr>'
    )
    total_budget = 0
    total_proj = 0
    total_actual = 0
    for cat_label, key, icon_name in categories:
        b = budget.get(key, 0) or 0
        p = projection.get(key, 0) or 0
        a = actual.get(key, 0) or 0
        v_b = a - b
        v_p = a - p
        v_b_pct = (v_b / b * 100) if b > 0 else 0
        v_p_pct = (v_p / p * 100) if p > 0 else 0

        total_budget += b
        total_proj += p
        total_actual += a

        v_b_color = "#16A34A" if v_b >= 0 else "#DC2626"
        v_p_color = "#16A34A" if v_p >= 0 else "#DC2626"
        v_b_arrow = "↑" if v_b >= 0 else "↓"
        v_p_arrow = "↑" if v_p >= 0 else "↓"

        rows_html += (
            '<tr>'
            '<td class="t-li"><div class="t-li-label">{ico}<span>{name}</span></div></td>'
            '<td class="t-num">${b:,.2f}</td>'
            '<td class="t-num">${p:,.2f}</td>'
            '<td class="t-num">${a:,.2f}</td>'
            '<td class="t-num" style="color:{vbc};">{vba} ${vb:,.0f} ({vbp:.1f}%)</td>'
            '<td class="t-num" style="color:{vpc};">{vpa} ${vp:,.0f} ({vpp:.1f}%)</td>'
            '</tr>'.format(
                ico=_icon(icon_name), name=cat_label,
                b=b, p=p, a=a,
                vb=abs(v_b), vbc=v_b_color, vba=v_b_arrow, vbp=v_b_pct,
                vp=abs(v_p), vpc=v_p_color, vpa=v_p_arrow, vpp=v_p_pct,
            )
        )

    # TOTAL row
    t_vb = total_actual - total_budget
    t_vp = total_actual - total_proj
    t_vb_pct = (t_vb / total_budget * 100) if total_budget > 0 else 0
    t_vp_pct = (t_vp / total_proj * 100) if total_proj > 0 else 0
    rows_html += (
        '<tr class="t-total-row">'
        '<td class="t-li"><b>TOTAL REVENUE</b></td>'
        '<td class="t-num"><b>${:,.2f}</b></td>'
        '<td class="t-num"><b>${:,.2f}</b></td>'
        '<td class="t-num"><b>${:,.2f}</b></td>'
        '<td class="t-num" style="color:{};"><b>{} ${:,.0f} ({:.1f}%)</b></td>'
        '<td class="t-num" style="color:{};"><b>{} ${:,.0f} ({:.1f}%)</b></td>'
        '</tr>'.format(
            total_budget, total_proj, total_actual,
            "#16A34A" if t_vb >= 0 else "#DC2626",
            "↑" if t_vb >= 0 else "↓", abs(t_vb), t_vb_pct,
            "#16A34A" if t_vp >= 0 else "#DC2626",
            "↑" if t_vp >= 0 else "↓", abs(t_vp), t_vp_pct,
        )
    )

    st.markdown(
        '<div class="fr-card">'
        '<div class="fr-card-header">'
        '<span class="fr-card-title">Financial Summary</span>{info}'
        '</div>'
        '<table class="fr-summary-table">'
        '<thead><tr>'
        '<th class="t-li">LINE ITEM</th>'
        '<th class="t-num">BUDGET</th>'
        '<th class="t-num">PROJECTION</th>'
        '<th class="t-num">ACTUAL</th>'
        '<th class="t-num">VAR BUDGET</th>'
        '<th class="t-num">VAR PROJ</th>'
        '</tr></thead>'
        '<tbody>{rows}</tbody>'
        '</table>'
        '</div>'.format(info=_icon("info"), rows=rows_html),
        unsafe_allow_html=True,
    )

    # Cost of Sales collapsible row
    kpis = _fetch_kpis(conn, week_start, dept)
    cos = kpis["cos"]
    labor_d = kpis["labor_d"]
    revenue = kpis["revenue"]
    cos_pct = (cos / revenue * 100) if revenue > 0 else 0
    labor_pct = (labor_d / revenue * 100) if revenue > 0 else 0

    st.markdown(
        '<div class="fr-collapsible">'
        '<div class="fr-collapsible-row">'
        '<span class="fr-card-title">Cost of Sales</span>{info}'
        '<div class="fr-collapsible-meta">'
        '<span><span class="fii-label">Actual:</span> <b>${a:,.2f}</b></span>'
        '<span><span class="fii-label">COS %:</span> <b>{p:.1f}%</b></span>'
        '{chev}</div></div></div>'
        '<div class="fr-collapsible">'
        '<div class="fr-collapsible-row">'
        '<span class="fr-card-title">Labor</span>{info2}'
        '<div class="fr-collapsible-meta">'
        '<span><span class="fii-label">Actual:</span> <b>${la:,.2f}</b></span>'
        '<span><span class="fii-label">Labor %:</span> <b>{lp:.1f}%</b></span>'
        '{chev2}</div></div></div>'.format(
            info=_icon("info"), a=cos, p=cos_pct, chev=_icon("chevron"),
            info2=_icon("info"), la=labor_d, lp=labor_pct, chev2=_icon("chevron"),
        ),
        unsafe_allow_html=True,
    )


def _render_operational_summary(conn, week_start, dept):
    st.info("Operational Summary — coming soon. Shift logs, weather impact, staffing variance.")


def _render_revenue_breakdown(conn, week_start, dept):
    actual, _, _ = _fetch_dept_breakdown(conn, week_start, dept)
    st.markdown(
        '<div class="fr-card"><div class="fr-card-header">'
        '<span class="fr-card-title">Revenue by Category</span></div>',
        unsafe_allow_html=True,
    )
    total = sum(actual.values()) or 1
    rows_html = ""
    for k, v in actual.items():
        pct = v / total * 100
        rows_html += (
            '<tr><td class="t-li">{}</td>'
            '<td class="t-num">${:,.2f}</td>'
            '<td class="t-num">{:.1f}%</td></tr>'.format(k.title(), v, pct)
        )
    st.markdown(
        '<table class="fr-summary-table">'
        '<thead><tr><th class="t-li">CATEGORY</th>'
        '<th class="t-num">REVENUE</th>'
        '<th class="t-num">% OF TOTAL</th></tr></thead>'
        '<tbody>{}</tbody></table></div>'.format(rows_html),
        unsafe_allow_html=True,
    )


def _render_labor_summary(conn, week_start, dept):
    st.info("Labor Summary — detailed labor breakdown coming soon.")


def _render_variance_analysis(conn, week_start, dept):
    st.info("Variance Analysis — coming soon.")
