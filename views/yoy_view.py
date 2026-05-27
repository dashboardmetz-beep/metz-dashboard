"""
Year-over-Year View + Variance Flag System.
- Compare this week vs same week last year (calendar AND fiscal)
- Auto-detect threshold breaches and surface them as alerts
- 4-4-5 fiscal week calculator
"""

from datetime import date, timedelta, datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEPARTMENTS
from styles import (
    page_header, dash_kpi_card, dash_section_header,
    dash_chart_start, dash_chart_end,
)
from calculations import fmt_dollar, fmt_pct
import db


# ─── 4-4-5 Fiscal Calendar ───
# Each fiscal year has 4 quarters of 13 weeks (4-4-5 pattern)
# Adjust FISCAL_YEAR_START_DATE to match your actual fiscal year start
FISCAL_YEAR_START_2025 = date(2025, 7, 7)  # July 7, 2025 = FY26 Week 1
FISCAL_YEAR_START_2024 = date(2024, 7, 1)  # July 1, 2024 = FY25 Week 1


def get_fiscal_week(d):
    """Return (fiscal_year, fiscal_week_num) for a given date.
    FY26 starts 2025-07-07, FY25 starts 2024-07-01.
    """
    if d >= FISCAL_YEAR_START_2025:
        delta = (d - FISCAL_YEAR_START_2025).days
        week_num = (delta // 7) + 1
        return ("FY26", min(week_num, 53))
    elif d >= FISCAL_YEAR_START_2024:
        delta = (d - FISCAL_YEAR_START_2024).days
        week_num = (delta // 7) + 1
        return ("FY25", min(week_num, 53))
    return ("FY24", 1)


def fiscal_week_to_date(fy, week_num):
    """Convert fiscal week back to calendar date (week start)."""
    if fy == "FY26":
        return FISCAL_YEAR_START_2025 + timedelta(weeks=week_num - 1)
    elif fy == "FY25":
        return FISCAL_YEAR_START_2024 + timedelta(weeks=week_num - 1)
    return None


def _apply_theme(fig, height=320):
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#64748B"),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor="#1F2A44", font_color="#FFFFFF"),
        xaxis=dict(gridcolor="rgba(148,163,184,0.15)"),
        yaxis=dict(gridcolor="rgba(148,163,184,0.15)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5, font=dict(size=11)),
    )
    return fig


def _fetch_week_totals(conn, week_start, dept):
    """Get totals for a specific week + dept."""
    row = conn.execute(
        """SELECT COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue,
                  COALESCE(cos_dollars,0) AS cos,
                  COALESCE(total_labor_dollars,0) AS labor_d,
                  COALESCE(total_labor_hours,0) AS labor_h,
                  COALESCE(overtime_dollars,0) AS ot
           FROM weekly_financials
           WHERE department=? AND week_start=?""",
        (dept, week_start.isoformat() if isinstance(week_start, date) else week_start)
    ).fetchone()
    if row:
        return dict(row)
    return None


def render(conn, user):
    """Main YoY + Variance page."""
    page_header(
        "Year-over-Year & Alerts",
        "Compare to last year + variance flag alerts"
    )

    # ═══════ Department + Week Selector ═══════
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        dept = st.selectbox("Department", DEPARTMENTS, key="yoy_dept")
    with c2:
        view_mode = st.radio(
            "Compare by",
            ["Fiscal Week (4-4-5)", "Calendar Date"],
            key="yoy_mode", horizontal=True,
        )
    with c3:
        if "yoy_week" not in st.session_state:
            st.session_state.yoy_week = db.get_week_start(date.today() - timedelta(weeks=1))

    # Week navigation
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("◀ Prev", key="yoy_prev"):
            st.session_state.yoy_week -= timedelta(weeks=1)
            st.rerun()
    with nav3:
        if st.button("Next ▶", key="yoy_next"):
            st.session_state.yoy_week += timedelta(weeks=1)
            st.rerun()
    with nav2:
        this_week = st.session_state.yoy_week
        fy, fw = get_fiscal_week(this_week)
        end = this_week + timedelta(days=6)
        st.markdown(
            '<div style="text-align:center;padding:6px 0;">'
            '<div style="font-size:16px;font-weight:600;color:#1E293B;">'
            '{} – {}</div>'
            '<div style="font-size:11px;color:#94A3B8;margin-top:2px;">'
            '{} Week {}</div>'
            '</div>'.format(
                this_week.strftime("%b %d"),
                end.strftime("%b %d, %Y"), fy, fw),
            unsafe_allow_html=True,
        )

    # ═══════ Calculate comparison week ═══════
    if view_mode == "Fiscal Week (4-4-5)":
        # Same fiscal week, prior year
        prior_fy = "FY25" if fy == "FY26" else "FY24"
        last_year_week = fiscal_week_to_date(prior_fy, fw)
        comparison_label = "{} Week {}".format(prior_fy, fw)
    else:
        # Same calendar date, prior year (52 weeks back)
        last_year_week = this_week - timedelta(weeks=52)
        comparison_label = last_year_week.strftime("%b %d, %Y")

    # ═══════ Fetch data for both weeks ═══════
    this_data = _fetch_week_totals(conn, this_week, dept) or {
        "revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0, "ot": 0
    }
    last_data = _fetch_week_totals(conn, last_year_week, dept) if last_year_week else None

    # ═══════ KPI Comparison Cards ═══════
    dash_section_header(
        "This Week vs {}".format(comparison_label),
        "{} comparison".format(view_mode),
    )

    if not last_data:
        st.info("No data found for {}.".format(comparison_label))
        last_data = {"revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0, "ot": 0}

    metrics = [
        ("Revenue", "revenue", "$", "navy"),
        ("Cost of Sales", "cos", "$", "amber"),
        ("Labor $", "labor_d", "$", "blue"),
        ("Labor Hours", "labor_h", "", "gold"),
    ]

    cols = st.columns(len(metrics))
    for i, (label, key, unit, accent) in enumerate(metrics):
        this_val = this_data.get(key, 0) or 0
        last_val = last_data.get(key, 0) or 0
        delta = this_val - last_val
        pct_delta = (delta / last_val * 100) if last_val > 0 else 0

        with cols[i]:
            sign = "+" if delta >= 0 else ""
            if unit == "$":
                this_fmt = fmt_dollar(this_val)
                last_fmt = fmt_dollar(last_val)
                delta_fmt = "{}{}".format(sign, fmt_dollar(delta))
            else:
                this_fmt = "{:,.0f}".format(this_val)
                last_fmt = "{:,.0f}".format(last_val)
                delta_fmt = "{}{:,.0f}".format(sign, delta)

            color = "#16A34A" if delta >= 0 else "#EF4444"
            arrow = "▲" if delta >= 0 else "▼"

            st.markdown(
                '<div style="background:#FFF;border:1px solid #E5E7EB;'
                'border-radius:10px;padding:14px 16px;height:100%;">'
                '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                'letter-spacing:.06em;font-weight:600;">{}</div>'
                '<div style="font-size:22px;font-weight:700;color:#1E293B;'
                'margin-top:4px;">{}</div>'
                '<div style="font-size:11px;color:#94A3B8;margin-top:2px;">'
                'PY: {}</div>'
                '<div style="font-size:12px;font-weight:600;color:{};margin-top:6px;">'
                '{} {} ({:+.1f}%)</div>'
                '</div>'.format(
                    label, this_fmt, last_fmt, color, arrow,
                    delta_fmt, pct_delta),
                unsafe_allow_html=True,
            )

    # ═══════ Alert / Variance Flags ═══════
    st.markdown("")
    dash_section_header(
        "🚨 Variance Flags",
        "Auto-detected issues for this week",
    )

    flags = _detect_variance_flags(conn, this_week, dept, this_data)
    if not flags:
        st.markdown(
            '<div style="background:#F0FDF4;border:1px solid #16A34A40;'
            'border-radius:10px;padding:14px 18px;">'
            '<span style="color:#16A34A;font-weight:600;">✓ All clear</span> '
            '<span style="color:#64748B;">— No threshold breaches detected.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for flag in flags:
            color = {
                "critical": "#DC2626", "warning": "#D97706", "info": "#3B82F6"
            }.get(flag["severity"], "#64748B")
            bg = {
                "critical": "#FEF2F2", "warning": "#FEF3C7", "info": "#EFF6FF"
            }.get(flag["severity"], "#F8FAFC")
            icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(
                flag["severity"], "•")

            st.markdown(
                '<div style="background:{};border:1px solid {}30;'
                'border-left:3px solid {};border-radius:10px;'
                'padding:12px 16px;margin-bottom:8px;">'
                '<div style="display:flex;justify-content:space-between;align-items:start;">'
                '<div style="flex:1;">'
                '<div style="font-weight:600;color:#1E293B;font-size:14px;">'
                '{} {}</div>'
                '<div style="font-size:12px;color:#64748B;margin-top:4px;">{}</div>'
                '</div>'
                '<span style="font-size:10px;font-weight:700;color:{};'
                'text-transform:uppercase;letter-spacing:.06em;">{}</span>'
                '</div></div>'.format(
                    bg, color, color, icon, flag["title"],
                    flag["detail"], color, flag["severity"]),
                unsafe_allow_html=True,
            )

    # ═══════ Trend chart (8 weeks each year) ═══════
    if last_year_week:
        dash_section_header("8-Week Trend Comparison", "{} vs {}".format(fy, prior_fy if view_mode == "Fiscal Week (4-4-5)" else "Last Year"))

        # Fetch 8 weeks for both years
        this_history = []
        last_history = []
        for i in range(8):
            tw = this_week - timedelta(weeks=i)
            lw = last_year_week - timedelta(weeks=i)
            t_data = _fetch_week_totals(conn, tw, dept)
            l_data = _fetch_week_totals(conn, lw, dept)
            this_history.append({
                "week": tw.strftime("%b %d"),
                "revenue": t_data["revenue"] if t_data else 0,
            })
            last_history.append({
                "week": lw.strftime("%b %d"),
                "revenue": l_data["revenue"] if l_data else 0,
            })

        this_history.reverse()
        last_history.reverse()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[h["week"] for h in this_history],
            y=[h["revenue"] for h in this_history],
            name="This Year", mode="lines+markers",
            line=dict(color="#1F2A44", width=3),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=[h["week"] for h in this_history],  # Same x-axis (this year's weeks)
            y=[h["revenue"] for h in last_history],
            name="Last Year", mode="lines+markers",
            line=dict(color="#C7A462", width=2, dash="dash"),
            marker=dict(size=6),
        ))
        _apply_theme(fig, height=320)
        fig.update_yaxes(tickformat="$,.0f")
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})


def _detect_variance_flags(conn, week_start, dept, this_data):
    """Auto-detect variance issues. Returns list of flag dicts."""
    flags = []
    revenue = this_data.get("revenue", 0) or 0
    cos = this_data.get("cos", 0) or 0
    labor_d = this_data.get("labor_d", 0) or 0
    ot = this_data.get("ot", 0) or 0

    # Get targets
    targets_row = conn.execute(
        "SELECT * FROM targets WHERE department=?", (dept,)
    ).fetchone()
    targets = dict(targets_row) if targets_row else {}
    target_lp = targets.get("target_labor_pct", 30) or 30
    target_fc = targets.get("target_food_cost_pct", 32) or 32

    # Get budget for this week
    budget = conn.execute(
        "SELECT * FROM budgets WHERE department=? AND week_start=?",
        (dept, week_start.isoformat())
    ).fetchone()

    # Flag 1: Revenue vs budget
    if budget and budget["revenue"] and revenue > 0:
        b_rev = budget["revenue"] or 0
        var_pct = ((revenue - b_rev) / b_rev * 100) if b_rev > 0 else 0
        if abs(var_pct) >= 10:
            flags.append({
                "severity": "critical" if abs(var_pct) >= 15 else "warning",
                "title": "Revenue {} vs Budget".format(
                    "↑ over" if var_pct > 0 else "↓ under"),
                "detail": "Actual ${:,.0f} vs budget ${:,.0f} ({:+.1f}%)".format(
                    revenue, b_rev, var_pct),
            })

    # Flag 2: Labor % over target
    if revenue > 0:
        actual_lp = (labor_d / revenue * 100) if revenue > 0 else 0
        if actual_lp > target_lp + 2:
            flags.append({
                "severity": "critical" if actual_lp > target_lp + 5 else "warning",
                "title": "Labor % over target",
                "detail": "Actual {:.1f}% vs target {:.1f}% (+{:.1f} pts)".format(
                    actual_lp, target_lp, actual_lp - target_lp),
            })

    # Flag 3: Food cost % over target
    if revenue > 0 and cos > 0:
        actual_fc = (cos / revenue * 100) if revenue > 0 else 0
        if actual_fc > target_fc + 2:
            flags.append({
                "severity": "critical" if actual_fc > target_fc + 5 else "warning",
                "title": "Food cost % over target",
                "detail": "Actual {:.1f}% vs target {:.1f}% (+{:.1f} pts)".format(
                    actual_fc, target_fc, actual_fc - target_fc),
            })

    # Flag 4: Overtime spike
    if labor_d > 0 and ot > 0:
        ot_pct = (ot / labor_d * 100) if labor_d > 0 else 0
        if ot_pct > 8:
            flags.append({
                "severity": "warning",
                "title": "High overtime",
                "detail": "OT is {:.1f}% of total labor (${:,.0f})".format(ot_pct, ot),
            })

    # Flag 5: No data entered
    if revenue == 0 and labor_d == 0:
        flags.append({
            "severity": "info",
            "title": "No financial data for this week",
            "detail": "Add weekly entries in Weekly Budget to enable analysis.",
        })

    return flags
