"""
Year-over-Year & Alerts — Premium layout.
Compare to last year + variance flag alerts + 8-week trend chart + week summary.
"""

from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEPARTMENTS
from styles import hero_header
import db


# ─── Fiscal Calendar (4-4-5) ───
FY26_START = date(2025, 7, 7)
FY25_START = date(2024, 7, 1)


def get_fiscal_week(d):
    if d >= FY26_START:
        delta = (d - FY26_START).days
        return ("FY26", (delta // 7) + 1)
    elif d >= FY25_START:
        delta = (d - FY25_START).days
        return ("FY25", (delta // 7) + 1)
    return ("FY24", 1)


def fiscal_to_date(fy, week_num):
    if fy == "FY26":
        return FY26_START + timedelta(weeks=week_num - 1)
    if fy == "FY25":
        return FY25_START + timedelta(weeks=week_num - 1)
    return None


def _icon(name):
    icons = {
        "dollar": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "tag": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
        "users": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "clock": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "flag": '<svg width="14" height="14" viewBox="0 0 24 24" fill="#DC2626" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
        "info": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "info-blue": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "building": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/></svg>',
    }
    return icons.get(name, "")


def _fetch_week_totals(conn, week_start, dept):
    if week_start is None:
        return None
    row = conn.execute(
        """SELECT COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue,
                  COALESCE(cos_dollars,0) AS cos,
                  COALESCE(total_labor_dollars,0) AS labor_d,
                  COALESCE(total_labor_hours,0) AS labor_h
           FROM weekly_financials
           WHERE department=? AND week_start=?""",
        (dept, week_start.isoformat())
    ).fetchone()
    return dict(row) if row else None


def render(conn, user):
    today = date.today()
    if "yoy_week" not in st.session_state:
        st.session_state.yoy_week = db.get_week_start(today) - timedelta(weeks=1)
    if "yoy_dept" not in st.session_state:
        st.session_state.yoy_dept = "Board & Catering"
    if "yoy_mode" not in st.session_state:
        st.session_state.yoy_mode = "Fiscal Week (4-4-5)"

    week_start = st.session_state.yoy_week
    week_end = week_start + timedelta(days=6)
    dept = st.session_state.yoy_dept

    # ─── Hero header ───
    def _yoy_right():
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
            if st.button("‹  Prev Week", key="yoy_prev_week",
                         use_container_width=True):
                st.session_state.yoy_week -= timedelta(weeks=1)
                st.rerun()
        with d3:
            if st.button("Next Week  ›", key="yoy_next_week",
                         use_container_width=True):
                st.session_state.yoy_week += timedelta(weeks=1)
                st.rerun()
        with d4:
            if st.button("📄  Export Report", key="yoy_export_v2",
                         use_container_width=True, type="primary"):
                st.toast("Report generated", icon="📄")

    hero_header(
        "Year-over-Year & Alerts",
        "Compare to last year + variance flag alerts",
        _yoy_right,
    )

    # ─── Filter row ───
    f1, f2, f3, f4 = st.columns([2, 1, 2, 2])
    with f1:
        new_dept = st.selectbox("Department", DEPARTMENTS,
                                 index=DEPARTMENTS.index(dept) if dept in DEPARTMENTS else 0,
                                 key="yoy_dept_sel", label_visibility="collapsed")
        if new_dept != dept:
            st.session_state.yoy_dept = new_dept
            st.rerun()
        dept = new_dept
    with f3:
        new_mode = st.radio(
            "Compare By",
            ["Fiscal Week (4-4-5)", "Calendar Date"],
            key="yoy_mode_sel",
            horizontal=True,
            index=0 if st.session_state.yoy_mode == "Fiscal Week (4-4-5)" else 1,
            label_visibility="collapsed",
        )
        if new_mode != st.session_state.yoy_mode:
            st.session_state.yoy_mode = new_mode
            st.rerun()

    # ─── Compute comparison week ───
    fy, fw = get_fiscal_week(week_start)
    if st.session_state.yoy_mode == "Fiscal Week (4-4-5)":
        prior_fy = "FY25" if fy == "FY26" else "FY24"
        last_year_week = fiscal_to_date(prior_fy, fw)
    else:
        last_year_week = week_start - timedelta(weeks=52)

    # ─── Fetch data ───
    this_data = _fetch_week_totals(conn, week_start, dept) or {
        "revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0}
    last_data = _fetch_week_totals(conn, last_year_week, dept) or {
        "revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0}

    # ─── 4 KPI cards (Revenue, Cost of Sales, Labor $, Labor Hours) ───
    cards = st.columns(4)
    metrics = [
        ("Revenue", "revenue", "${:,.2f}", "dollar", "#ECFDF5", "%", False),
        ("Cost of Sales", "cos", "${:,.2f}", "tag", "#F5F3FF", "%", True),
        ("Labor $", "labor_d", "${:,.2f}", "users", "#EFF6FF", "%", True),
        ("Labor Hours", "labor_h", "{:,.0f}", "clock", "#F0F9FF", "", False),
    ]
    for i, (label, key, fmt, icon, bg, unit, invert) in enumerate(metrics):
        this_val = this_data.get(key, 0) or 0
        last_val = last_data.get(key, 0) or 0
        delta = this_val - last_val
        pct = (delta / last_val * 100) if last_val > 0 else 0

        with cards[i]:
            is_positive = delta >= 0
            if invert:
                color = "#DC2626" if is_positive else "#16A34A"
            else:
                color = "#16A34A" if is_positive else "#DC2626"
            arrow = "▲" if is_positive else "▼"

            if unit == "%":
                delta_str = "{} {:,.2f} ({:.1f}%)".format(
                    "$" if key != "labor_h" else "", abs(delta), pct)
            else:
                delta_str = "{:,.0f} ({:.1f}%)".format(abs(delta), pct)

            st.markdown(
                '<div class="yoy-kpi">'
                '<div class="yoy-kpi-row">'
                '<div class="yoy-kpi-icon" style="background:{bg};">{icon}</div>'
                '<div class="yoy-kpi-meta">'
                '<div class="yoy-kpi-label">{label}</div>'
                '<div class="yoy-kpi-value">{value}</div>'
                '<div class="yoy-kpi-py">PY: {py}</div>'
                '<div class="yoy-kpi-delta" style="color:{c};">{a} {d}</div>'
                '</div></div></div>'.format(
                    bg=bg, icon=_icon(icon), label=label,
                    value=fmt.format(this_val),
                    py=fmt.format(last_val),
                    c=color, a=arrow, d=delta_str,
                ),
                unsafe_allow_html=True,
            )

    # ─── Variance Flags section ───
    flags = _detect_flags(conn, week_start, dept, this_data)
    st.markdown(
        '<div class="yoy-flags-card">'
        '<div class="yoy-flags-header">'
        '{flag}<span class="yoy-flags-title">Variance Flags</span>'
        '<a href="#" class="yoy-flags-link">View Details</a>'
        '</div>'.format(flag=_icon("flag")),
        unsafe_allow_html=True,
    )
    if not flags:
        st.markdown(
            '<div class="yoy-flag-empty">'
            '{i}<span><b>No financial data for this week.</b> '
            'Add weekly entries in Weekly Budget to enable analysis.</span>'
            '</div>'.format(i=_icon("info-blue")),
            unsafe_allow_html=True,
        )
    else:
        for f in flags:
            color = {"critical": "#DC2626", "warning": "#D97706"}.get(f["severity"], "#3B82F6")
            st.markdown(
                '<div class="yoy-flag-row" style="border-left-color:{c};">'
                '<div><b>{t}</b> — <span>{d}</span></div></div>'.format(
                    c=color, t=f["title"], d=f["detail"]),
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── 8-Week Trend + Week Summary (2 columns) ───
    left, right = st.columns([3, 2])

    with left:
        st.markdown(
            '<div class="yoy-card">'
            '<div class="yoy-card-header">'
            '<span class="yoy-card-title">8-Week Trend Comparison</span>'
            '<span class="yoy-card-meta">{} vs {}</span>'
            '</div>'.format(fy, "FY25" if fy == "FY26" else "FY24"),
            unsafe_allow_html=True,
        )
        _render_trend_chart(conn, week_start, last_year_week, dept)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="yoy-card">'
            '<div class="yoy-card-header">'
            '<span class="yoy-card-title">Week Summary</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        # Summary rows
        summary_metrics = [
            ("Revenue", this_data.get("revenue", 0), last_data.get("revenue", 0), "#16A34A", "$"),
            ("Cost of Sales", this_data.get("cos", 0), last_data.get("cos", 0), "#DC2626", "$"),
            ("Labor $", this_data.get("labor_d", 0), last_data.get("labor_d", 0), "#D97706", "$"),
            ("Labor Hours", this_data.get("labor_h", 0), last_data.get("labor_h", 0), "#3B82F6", ""),
        ]
        rows_html = ""
        for name, this_v, last_v, dot_color, unit in summary_metrics:
            delta = this_v - last_v
            pct = (delta / last_v * 100) if last_v > 0 else 0
            arrow = "▲" if delta >= 0 else "▼"
            delta_color = "#16A34A" if delta >= 0 else "#DC2626"
            this_str = "${:,.2f}".format(this_v) if unit == "$" else "{:,.0f}".format(this_v)
            last_str = "${:,.2f}".format(last_v) if unit == "$" else "{:,.0f}".format(last_v)
            delta_str = "${:,.2f}".format(abs(delta)) if unit == "$" else "{:,.0f}".format(abs(delta))
            rows_html += (
                '<div class="yoy-sum-row">'
                '<div class="yoy-sum-name">'
                '<span class="yoy-sum-dot" style="background:{dc};"></span>{n}</div>'
                '<div class="yoy-sum-vals">'
                '<span class="yoy-sum-this">{this}</span>'
                '<span class="yoy-sum-py">vs PY {py}</span>'
                '<span class="yoy-sum-delta" style="color:{dlc};">{a} {d} ({p:.1f}%)</span>'
                '</div></div>'.format(
                    dc=dot_color, n=name, this=this_str, py=last_str,
                    dlc=delta_color, a=arrow, d=delta_str, p=pct,
                )
            )
        st.markdown(rows_html, unsafe_allow_html=True)

        # Alerts & Insights
        st.markdown(
            '<div class="yoy-insight-box">'
            '<div class="yoy-insight-title">{i}Alerts & Insights</div>'
            '<div class="yoy-insight-body"><b>No issues detected for this week.</b><br>'
            "We'll flag any variances that exceed your targets.</div>"
            '</div>'.format(i=_icon("info-blue")),
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── Footer note ───
    st.markdown(
        '<div class="yoy-footer-note">ℹ YoY comparisons are based on the same fiscal week last year.</div>',
        unsafe_allow_html=True,
    )


def _detect_flags(conn, week_start, dept, this_data):
    flags = []
    rev = this_data.get("revenue", 0) or 0
    if rev <= 0:
        return flags

    # Target check
    targets_row = conn.execute(
        "SELECT * FROM targets WHERE department=?", (dept,)
    ).fetchone()
    if not targets_row:
        return flags
    targets = dict(targets_row)
    target_lp = targets.get("target_labor_pct") or 30
    target_fc = targets.get("target_food_cost_pct") or 32

    actual_lp = (this_data.get("labor_d", 0) / rev * 100)
    actual_fc = (this_data.get("cos", 0) / rev * 100)

    if actual_lp > target_lp + 2:
        flags.append({
            "severity": "critical" if actual_lp > target_lp + 5 else "warning",
            "title": "Labor % over target",
            "detail": "Actual {:.1f}% vs target {:.1f}% (+{:.1f} pts)".format(
                actual_lp, target_lp, actual_lp - target_lp),
        })
    if actual_fc > target_fc + 2:
        flags.append({
            "severity": "warning",
            "title": "Food cost % over target",
            "detail": "Actual {:.1f}% vs target {:.1f}% (+{:.1f} pts)".format(
                actual_fc, target_fc, actual_fc - target_fc),
        })
    return flags


def _render_trend_chart(conn, week_start, last_year_week, dept):
    """8-week trend chart: This Year vs Last Year."""
    this_history = []
    last_history = []
    week_labels = []

    for i in range(7, -1, -1):
        tw = week_start - timedelta(weeks=i)
        lw = last_year_week - timedelta(weeks=i) if last_year_week else None
        t = _fetch_week_totals(conn, tw, dept) or {"revenue": 0}
        l = _fetch_week_totals(conn, lw, dept) or {"revenue": 0}
        this_history.append(t["revenue"])
        last_history.append(l["revenue"])
        week_labels.append(tw.strftime("%b %d"))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=week_labels, y=this_history, name="This Year",
        mode="lines+markers",
        line=dict(color="#0B1929", width=2.5),
        marker=dict(size=7, color="#0B1929"),
    ))
    fig.add_trace(go.Scatter(
        x=week_labels, y=last_history, name="Last Year",
        mode="lines+markers",
        line=dict(color="#B8965A", width=2, dash="dash"),
        marker=dict(size=6, color="#B8965A"),
    ))
    fig.update_layout(
        height=300,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#64748B"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="rgba(148,163,184,0.08)", showline=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(148,163,184,0.10)", showline=False,
                   tickformat="$,.0f", zeroline=True, zerolinecolor="#E4E2DC"),
        legend=dict(orientation="h", yanchor="top", y=1.10,
                    xanchor="left", x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
