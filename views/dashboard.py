"""
Page 4: Enhanced Dashboard
Daily/weekly toggle, KPI cards, charts for sales trends, labor comparison,
meal plan, food cost, POS data, weather flags, budget status, comments, export.
"""

from datetime import date, timedelta
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import DEPARTMENTS
from calculations import (
    calc_labor_pct, calc_splh, calc_cos_pct,
    sum_revenue_streams, variance,
    fmt_pct, fmt_dollar, fmt_number,
)
from styles import (
    page_header, section_title, kpi_card, mini_divider, app_footer,
    event_reminders, chart_card_start, chart_card_end,
    dash_kpi_card, dash_metric_card, dash_section_header,
    dash_chart_start, dash_chart_end, dash_progress_card,
    dash_dept_status_row,
)
import db


# ─── Plotly theme helper ───

_PLOTLY_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#64748B"),
    title_text="",
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(fixedrange=True),
    yaxis=dict(fixedrange=True),
    hoverlabel=dict(
        bgcolor="#1F2A44",
        font_size=12,
        font_family="Inter, sans-serif",
        font_color="#FFFFFF",
        bordercolor="#C7A462",
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=11, color="#64748B"),
    ),
)

# Locked chart color palette
_CHART_NAVY = "#1F2A44"
_CHART_GOLD = "#C7A462"
_CHART_GREEN = "#16A34A"
_CHART_RED = "#DC2626"
_DEPT_COLORS = {
    "Board & Catering": "#1F2A44",
    "Starbucks": "#C7A462",
    "Qdoba": "#3B82F6",
    "Retail & Mac's Grill": "#16A34A",
}


def _apply_theme(fig, height=340):
    """Apply the consistent Plotly theme to a figure."""
    fig.update_layout(**_PLOTLY_THEME)
    fig.update_layout(height=height, bargap=0.3, title_text="")
    fig.update_xaxes(showgrid=False, showline=False,
                     tickfont=dict(size=11, color="#94A3B8"))
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.03)", gridwidth=1,
                     showline=False,
                     tickfont=dict(size=11, color="#94A3B8"))
    fig.update_traces(marker_line_width=0, marker=dict(cornerradius=4),
                      selector=dict(type="bar"))
    return fig


def _render_revenue_donut(dept_data):
    """Render a donut chart showing revenue breakdown by department."""
    labels = []
    values = []
    colors = []
    for d in dept_data:
        if d["revenue"] > 0:
            labels.append(d["department"])
            values.append(d["revenue"])
            colors.append(_DEPT_COLORS.get(d["department"], "#94A3B8"))

    if not values:
        st.caption("No revenue data available.")
        return

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=11, family="Inter, sans-serif"),
        hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.0f}<br>Share: %{percent}<extra></extra>",
        sort=False,
    )])
    fig.update_layout(
        showlegend=False,
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13, color="#64748B"),
        hoverlabel=dict(
            bgcolor="#1F2A44", font_size=12,
            font_family="Inter, sans-serif", font_color="#FFFFFF",
            bordercolor="#C7A462",
        ),
        annotations=[dict(
            text="Revenue<br>Split",
            x=0.5, y=0.5, font_size=14, font_color="#1E293B",
            font_family="Inter, sans-serif", showarrow=False,
        )],
    )
    st.plotly_chart(fig, use_container_width=True)


def page_dashboard(conn, user):
    subsection = st.session_state.get("current_subsection", "Overview")

    if subsection == "Operations Overview":
        page_header("Operations Overview", "Location-level KPIs, gauges & action flags")
        # Week navigation
        if "ops_week" not in st.session_state:
            st.session_state.ops_week = db.get_week_start(date.today())
        target_od = st.session_state.ops_week + timedelta(days=6)
        if st.session_state.get("ops_date") != target_od:
            st.session_state.ops_date = target_od
        nav1, nav2, nav3 = st.columns([1, 3, 1])
        with nav1:
            if st.button("\u25c0 Prev Week", key="ops_prev"):
                st.session_state.ops_week -= timedelta(weeks=1)
                st.rerun()
        with nav3:
            if st.button("Next Week \u25b6", key="ops_next"):
                st.session_state.ops_week += timedelta(weeks=1)
                st.rerun()
        with nav2:
            picked = st.date_input("Week Ending", key="ops_date")
            new_wk = db.get_week_start(picked)
            if new_wk != st.session_state.ops_week:
                st.session_state.ops_week = new_wk
                st.rerun()
        _render_operations_overview(st.session_state.ops_week)
        return

    if subsection == "Accounts Receivable":
        page_header("Accounts Receivable", "Alma College — AR Aging & Collections")
        _render_ar_section(conn, user)
        return

    if subsection == "Meal Plan Tracker":
        page_header("Meal Plan Tracker", "Alma College — Budget vs Actual Revenue")
        _render_meal_plan_tracker(conn, user)
        return

    if subsection == "Digital Meal Counts":
        page_header("Digital Meal Counts", "Board — Daily counts by meal service")
        _render_digital_meal_counts(conn)
        return

    if subsection == "Tender Totals":
        page_header("Tender Totals", "Daily tender by terminal — Hamilton, Loch Lomond, Qdoba, Starbucks")
        _render_tender_totals(conn)
        return

    # ── Default: Overview ──
    page_header("Performance Dashboard", "Real-time operational insights")
    event_reminders(conn)

    # ─── Daily / Weekly Toggle ───
    view_mode = st.radio("View Mode", ["Weekly", "Daily"], horizontal=True, key="dash_mode")

    today = date.today()

    if view_mode == "Weekly":
        _render_weekly_dashboard(conn, user, today)
    else:
        _render_daily_dashboard(conn, user, today)


# ═══════════════════════════════════════════════════════
# Architect-style card wrappers
# ═══════════════════════════════════════════════════════


def _arch_card_open(title="", subtitle=""):
    """Open an Architect-style white card with optional title."""
    title_html = ""
    if title:
        title_html = (
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
            '<div>'
            '<span style="font-size:15px;font-weight:700;color:#1A1A18;font-family:Inter,sans-serif;">{}</span>'
        ).format(title)
        if subtitle:
            title_html += '<div style="font-size:11px;color:#8B8A84;margin-top:2px;">{}</div>'.format(subtitle)
        title_html += '</div></div>'
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E8E7E3;border-radius:14px;'
        'padding:20px 22px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        '{}'.format(title_html),
        unsafe_allow_html=True,
    )


def _arch_card_close():
    """Close an Architect-style card."""
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# WEEKLY DASHBOARD
# ═══════════════════════════════════════════════════════


def _render_weekly_dashboard(conn, user, today):
    # Week navigation
    if "dash_week" not in st.session_state:
        st.session_state.dash_week = db.get_week_start(today) - timedelta(weeks=1)
    target_dd = st.session_state.dash_week + timedelta(days=6)
    if st.session_state.get("dash_date") != target_dd:
        st.session_state.dash_date = target_dd

    col_prev, col_date, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("\u25c0 Prev Week", key="dash_prev"):
            st.session_state.dash_week -= timedelta(weeks=1)
            st.rerun()
    with col_next:
        if st.button("Next Week \u25b6", key="dash_next"):
            st.session_state.dash_week += timedelta(weeks=1)
            st.rerun()
    with col_date:
        picked = st.date_input("Week Ending", key="dash_date")
        new_week = db.get_week_start(picked)
        if new_week != st.session_state.dash_week:
            st.session_state.dash_week = new_week
            st.rerun()

    week_start = st.session_state.dash_week.isoformat()

    # ─── Gather department data ───
    dept_data = []
    for dept in DEPARTMENTS:
        b = db.fetch_budget(conn, week_start, dept)
        fin = db.fetch_weekly_financials(conn, week_start, dept)
        _pnl_keys = ["gross_profit", "total_payroll", "tax_fringe",
                     "after_prime_costs", "pace", "non_cont_expenses",
                     "insurance", "profit_fee", "royalties", "net_income",
                     "management_fees"]
        if fin:
            total_rev = sum_revenue_streams(
                fin.get("board_revenue", 0), fin.get("retail_revenue", 0),
                fin.get("flex_revenue", 0), fin.get("catering_revenue", 0),
                fin.get("other_revenue", 0),
            )
            row = {
                "department": dept,
                "revenue": total_rev,
                "labor_dollars": fin.get("total_labor_dollars", 0) or 0,
                "labor_hours": fin.get("total_labor_hours", 0) or 0,
                "cos_dollars": fin.get("cos_dollars", 0) or 0,
                "overtime": fin.get("overtime_dollars", 0) or 0,
                "direct_expenses": fin.get("direct_expenses", 0) or 0,
                "status": b["status"] if b else "Draft",
            }
            for pk in _pnl_keys:
                row[pk] = fin.get(pk, 0) or 0
            dept_data.append(row)
        elif b:
            row = {
                "department": dept,
                "revenue": b.get("revenue", 0) or 0,
                "labor_dollars": b.get("labor_dollars", 0) or 0,
                "labor_hours": b.get("labor_hours", 0) or 0,
                "cos_dollars": 0, "overtime": 0, "direct_expenses": 0,
                "status": b["status"],
            }
            for pk in _pnl_keys:
                row[pk] = 0
            dept_data.append(row)
        else:
            row = {
                "department": dept,
                "revenue": 0, "labor_dollars": 0, "labor_hours": 0,
                "cos_dollars": 0, "overtime": 0, "direct_expenses": 0,
                "status": "Draft",
            }
            for pk in _pnl_keys:
                row[pk] = 0
            dept_data.append(row)

    df = pd.DataFrame(dept_data)
    total_rev = df["revenue"].sum()
    total_lab = df["labor_dollars"].sum()
    total_hrs = df["labor_hours"].sum()
    total_cos = df["cos_dollars"].sum()
    total_ot = df["overtime"].sum()
    total_de = df["direct_expenses"].sum()
    total_labor_pct = calc_labor_pct(total_lab, total_rev)
    total_splh = calc_splh(total_rev, total_hrs)
    total_cos_pct = calc_cos_pct(total_cos, total_rev)

    # Count statuses for badge
    approved_count = sum(1 for d in dept_data if d["status"] == "Approved")

    # ─── Fetch Last Year data for KPI deltas ───
    ly_total_rev = 0
    ly_total_lab = 0
    ly_total_hrs = 0
    ly_total_cos = 0
    has_ly = False
    for dept in DEPARTMENTS:
        ly = db.fetch_ly_actuals(conn, week_start, dept)
        if ly:
            has_ly = True
            ly_total_rev += ly["revenue"] or 0
            ly_total_lab += ly["labor_dollars"] or 0
            ly_total_hrs += ly["labor_hours"] or 0

    # Compute changes vs LY
    rev_pct = None
    lab_pct_change = None
    lp_diff = None
    splh_diff = None
    if has_ly:
        _rev_d, rev_pct = variance(total_rev, ly_total_rev)
        _lab_d, lab_pct_change = variance(total_lab, ly_total_lab)
        ly_labor_pct = calc_labor_pct(ly_total_lab, ly_total_rev)
        ly_splh = calc_splh(ly_total_rev, ly_total_hrs)
        if total_labor_pct is not None and ly_labor_pct is not None:
            lp_diff = total_labor_pct - ly_labor_pct
        if total_splh is not None and ly_splh is not None:
            splh_diff = total_splh - ly_splh

    # ─── Helper for inline change badges ───
    def _change_html(val, fmt_fn, suffix="", invert=False):
        """Return colored +/- badge HTML. invert=True means lower is better."""
        if val is None:
            return ""
        positive = val >= 0
        good = (not positive) if invert else positive
        color = "#16A34A" if good else "#E24B4A"
        bg = "#F0FDF4" if good else "#FEF2F2"
        arrow = "\u25b2" if positive else "\u25bc"
        sign = "+" if positive else ""
        text = "{}{}{}{}".format(arrow, " ", sign, fmt_fn(val))
        if suffix:
            text += " " + suffix
        return (
            '<span style="display:inline-block;font-size:12px;font-weight:600;'
            'color:{};background:{};padding:2px 8px;border-radius:10px;'
            'margin-left:6px;">{}</span>'.format(color, bg, text)
        )

    # ═══════════════════════════════════════════════════════
    # ROW 1 — Hero KPI Cards (4 across, Architect style)
    # ═══════════════════════════════════════════════════════
    _kpi_card_css = """
    <style>
    .arch-kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }
    .arch-kpi {
        background: #fff; border: 1px solid #E8E7E3; border-radius: 12px;
        padding: 18px 20px; display: flex; flex-direction: column; gap: 4px;
        position: relative; overflow: hidden;
    }
    .arch-kpi::after {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    }
    .arch-kpi.green::after { background: linear-gradient(90deg, #16A34A, #22C55E); }
    .arch-kpi.red::after { background: linear-gradient(90deg, #DC2626, #EF4444); }
    .arch-kpi.amber::after { background: linear-gradient(90deg, #D97706, #F59E0B); }
    .arch-kpi.blue::after { background: linear-gradient(90deg, #2563EB, #3B82F6); }
    .arch-kpi-label { font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: #8B8A84; }
    .arch-kpi-val { font-size: 28px; font-weight: 700; color: #1A1A18; line-height: 1.1; display: flex; align-items: center; gap: 4px; }
    .arch-kpi-badge {
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600; min-width: 28px; height: 28px;
        border-radius: 50%; margin-left: auto;
    }

    .arch-metric-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }
    .arch-metric {
        background: #fff; border: 1px solid #E8E7E3; border-radius: 10px;
        padding: 14px 16px; display: flex; justify-content: space-between; align-items: center;
    }
    .arch-metric-label { font-size: 11px; color: #8B8A84; }
    .arch-metric-val { font-size: 18px; font-weight: 700; }
    .arch-metric-change { font-size: 11px; font-weight: 600; }

    .arch-section-title { font-size: 15px; font-weight: 600; color: #1A1A18; margin: 20px 0 10px; }
    .arch-section-sub { font-size: 12px; color: #8B8A84; margin-left: 8px; }

    .arch-target-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }
    .arch-target {
        background: #fff; border: 1px solid #E8E7E3; border-radius: 10px;
        padding: 14px 16px; display: flex; flex-direction: column; gap: 6px;
    }
    .arch-target-top { display: flex; justify-content: space-between; align-items: center; }
    .arch-target-pct { font-size: 18px; font-weight: 700; color: #1A1A18; }
    .arch-target-bar { height: 5px; background: #ECEAE3; border-radius: 3px; overflow: hidden; }
    .arch-target-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
    .arch-target-label { font-size: 10px; color: #8B8A84; }
    </style>
    """
    st.markdown(_kpi_card_css, unsafe_allow_html=True)

    # Build the 4 KPI cards
    rev_badge = _change_html(rev_pct, fmt_pct)
    lab_badge = _change_html(lab_pct_change, fmt_pct, invert=True)
    cos_badge_text = fmt_pct(total_cos_pct) if total_cos_pct is not None else "--"
    splh_badge = _change_html(splh_diff, fmt_dollar)

    kpi_html = '<div class="arch-kpi-row">'

    # Revenue
    kpi_html += '''<div class="arch-kpi green">
        <div class="arch-kpi-label">TOTAL REVENUE</div>
        <div class="arch-kpi-val">{}{}</div>
    </div>'''.format(fmt_dollar(total_rev), rev_badge)

    # Labor
    kpi_html += '''<div class="arch-kpi red">
        <div class="arch-kpi-label">TOTAL LABOR</div>
        <div class="arch-kpi-val">{}{}<span class="arch-kpi-badge" style="background:#FEF2F2;color:#EF4444;">{}</span></div>
    </div>'''.format(
        fmt_dollar(total_lab), lab_badge,
        fmt_pct(total_labor_pct) if total_labor_pct is not None else "--",
    )

    # Cost of Sales
    kpi_html += '''<div class="arch-kpi amber">
        <div class="arch-kpi-label">COST OF SALES</div>
        <div class="arch-kpi-val">{}<span class="arch-kpi-badge" style="background:#FEF3C7;color:#D97706;">{}</span></div>
    </div>'''.format(fmt_dollar(total_cos), cos_badge_text)

    # SPLH
    kpi_html += '''<div class="arch-kpi blue">
        <div class="arch-kpi-label">SPLH</div>
        <div class="arch-kpi-val">{}{}<span class="arch-kpi-badge" style="background:#EFF6FF;color:#3B82F6;">{}/{}</span></div>
    </div>'''.format(
        fmt_dollar(total_splh), splh_badge,
        approved_count, len(DEPARTMENTS),
    )

    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # ROW 2 — Secondary Metrics (4 compact cards)
    # ═══════════════════════════════════════════════════════
    lp_badge = _change_html(lp_diff, lambda v: "{:.1f} pts".format(v), invert=True)
    ot_color = "#E24B4A" if total_ot > 0 else "#1A1A18"
    metric_html = '<div class="arch-metric-row">'
    metric_html += '''<div class="arch-metric">
        <div><div class="arch-metric-label">Labor %</div>
        <div class="arch-metric-val" style="color:#1A1A18">{}</div></div>
        <div class="arch-metric-change">{}</div>
    </div>'''.format(fmt_pct(total_labor_pct), lp_badge)

    metric_html += '''<div class="arch-metric">
        <div><div class="arch-metric-label">Total Hours</div>
        <div class="arch-metric-val" style="color:#3B82F6">{}</div></div>
    </div>'''.format(fmt_number(total_hrs))

    metric_html += '''<div class="arch-metric">
        <div><div class="arch-metric-label">Overtime</div>
        <div class="arch-metric-val" style="color:{}">{}</div></div>
    </div>'''.format(ot_color, fmt_dollar(total_ot))

    metric_html += '''<div class="arch-metric">
        <div><div class="arch-metric-label">Direct Expenses</div>
        <div class="arch-metric-val" style="color:#D97706">{}</div></div>
    </div>'''.format(fmt_dollar(total_de))

    metric_html += '</div>'
    st.markdown(metric_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # ROW 3 — Weekly Revenue Trend (combo bar+line) + Revenue Donut
    # ═══════════════════════════════════════════════════════
    chart_data = []
    for d in dept_data:
        lp = calc_labor_pct(d["labor_dollars"], d["revenue"])
        sp = calc_splh(d["revenue"], d["labor_hours"])
        chart_data.append({
            "Department": d["department"],
            "Revenue": d["revenue"],
            "SPLH": sp if sp is not None else 0,
            "Labor %": lp if lp is not None else 0,
        })
    chart_df = pd.DataFrame(chart_data)

    # ── Build 8-week revenue history for combo chart ──
    _week_history = []
    for w in range(7, -1, -1):
        wk_date = st.session_state.dash_week - timedelta(weeks=w)
        wk_label = (wk_date + timedelta(days=6)).strftime("%b %d")
        wk_total = 0
        for dept in DEPARTMENTS:
            fin = db.fetch_weekly_financials(conn, wk_date.isoformat(), dept)
            rev = 0
            if fin:
                rev = sum_revenue_streams(
                    fin.get("board_revenue", 0), fin.get("retail_revenue", 0),
                    fin.get("flex_revenue", 0), fin.get("catering_revenue", 0),
                    fin.get("other_revenue", 0),
                )
            _week_history.append({
                "Week": wk_label, "Department": dept, "Revenue": rev,
            })
            wk_total += rev

    r3l, r3r = st.columns([3, 2])
    with r3l:
        _arch_card_open("Revenue Trend", "Past 8 weeks by department")
        hist_df = pd.DataFrame(_week_history)
        # Stacked bar by department
        fig = go.Figure()
        _dept_order = list(DEPARTMENTS)
        for dept in _dept_order:
            ddf = hist_df[hist_df["Department"] == dept]
            fig.add_trace(go.Bar(
                name=dept, x=ddf["Week"], y=ddf["Revenue"],
                marker_color=_DEPT_COLORS.get(dept, "#94A3B8"),
                hovertemplate="<b>%{{x}}</b><br>{}: $%{{y:,.0f}}<extra></extra>".format(dept),
            ))
        # Total line on secondary axis
        week_totals = hist_df.groupby("Week", sort=False)["Revenue"].sum().reset_index()
        fig.add_trace(go.Scatter(
            name="Total", x=week_totals["Week"], y=week_totals["Revenue"],
            mode="lines+markers", yaxis="y2",
            line=dict(color="#16A34A", width=3),
            marker=dict(size=7, color="#16A34A"),
            hovertemplate="<b>%{x}</b><br>Total: $%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            barmode="stack", showlegend=True, height=380,
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                        tickfont=dict(size=11, color="#16A34A"),
                        tickformat="$,.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="center", x=0.5, font=dict(size=10)),
        )
        _apply_theme(fig, height=380)
        fig.update_xaxes(tickfont=dict(size=11))
        fig.update_yaxes(tickformat="$,.0f", tickfont=dict(size=11))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        _arch_card_close()

    with r3r:
        _arch_card_open("Revenue Split", "Share by department")
        # Architect-style donut with centered total
        labels = []
        values = []
        colors = []
        for d in dept_data:
            if d["revenue"] > 0:
                labels.append(d["department"])
                values.append(d["revenue"])
                colors.append(_DEPT_COLORS.get(d["department"], "#94A3B8"))
        if values:
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values, hole=0.65,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=3)),
                textinfo="percent", textposition="outside",
                textfont=dict(size=12, family="Inter, sans-serif", color="#64748B"),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                sort=False,
            )])
            total_fmt = "${:,.0f}".format(total_rev) if total_rev < 1000000 else "${:,.0f}".format(total_rev)
            fig.update_layout(
                showlegend=True, height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                            xanchor="center", x=0.5, font=dict(size=10, color="#64748B")),
                annotations=[dict(
                    text="<b>{}</b><br><span style='font-size:11px;color:#8B8A84'>Total Revenue</span>".format(total_fmt),
                    x=0.5, y=0.5, font_size=22, font_color="#1A1A18",
                    font_family="Inter, sans-serif", showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No revenue data available.")
        _arch_card_close()

    # ═══════════════════════════════════════════════════════
    # ROW 4 — Department Revenue Cards
    # ═══════════════════════════════════════════════════════
    _DEPT_ACCENT = {
        "Board & Catering": "#1F2A44",
        "Starbucks": "#C7A462",
        "Qdoba": "#3B82F6",
        "Retail & Mac's Grill": "#16A34A",
    }
    dept_metric_html = '<div class="arch-metric-row">'
    for d in dept_data:
        rev_pct_dept = (d["revenue"] / total_rev * 100) if total_rev > 0 else 0
        color = _DEPT_ACCENT.get(d["department"], "#3B82F6")
        # Fetch LY for each dept to show change badge
        ly_dept = db.fetch_ly_actuals(conn, week_start, d["department"])
        ly_rev = ly_dept["revenue"] if ly_dept and ly_dept.get("revenue") else None
        dept_change = ""
        if ly_rev and ly_rev > 0:
            pct_ch = ((d["revenue"] - ly_rev) / ly_rev) * 100
            ch_color = "#16A34A" if pct_ch >= 0 else "#E24B4A"
            ch_arrow = "\u25b2" if pct_ch >= 0 else "\u25bc"
            ch_sign = "+" if pct_ch >= 0 else ""
            dept_change = '<span style="font-size:11px;font-weight:600;color:{}">{} {}{:.1f}%</span>'.format(
                ch_color, ch_arrow, ch_sign, pct_ch)
        dept_metric_html += '''<div class="arch-metric">
            <div><div class="arch-metric-label">{}</div>
            <div class="arch-metric-val" style="color:{}">{}</div></div>
            <div style="text-align:right"><div style="font-size:12px;font-weight:600;color:{}">{:.0f}%</div>{}</div>
        </div>'''.format(d["department"], color, fmt_dollar(d["revenue"]), color, rev_pct_dept, dept_change)
    dept_metric_html += '</div>'
    st.markdown(dept_metric_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # ROW 5 — Target Section (budget utilization progress bars)
    # ═══════════════════════════════════════════════════════
    st.markdown(
        '<div class="arch-section-title">Target Section'
        '<span class="arch-section-sub">Budget utilization</span></div>',
        unsafe_allow_html=True,
    )

    _TARGET_COLORS = {
        "Board & Catering": "#1F2A44",
        "Starbucks": "#C7A462",
        "Qdoba": "#3B82F6",
        "Retail & Mac's Grill": "#16A34A",
    }
    target_html = '<div class="arch-target-row">'
    for d in dept_data:
        b = db.fetch_budget(conn, week_start, d["department"])
        budget_rev = b.get("revenue", 0) if b else 0
        if budget_rev and budget_rev > 0:
            pct_of_budget = min((d["revenue"] / budget_rev) * 100, 150)
            bar_w = min(pct_of_budget, 100)
        else:
            pct_of_budget = 0
            bar_w = 0
        color = _TARGET_COLORS.get(d["department"], "#3B82F6")
        pct_color = "#16A34A" if pct_of_budget >= 95 else ("#D97706" if pct_of_budget >= 80 else "#DC2626")
        target_html += '''<div class="arch-target">
            <div class="arch-target-top">
                <span class="arch-target-pct" style="color:{}">{:.0f}%</span>
                <span style="font-size:10px;color:#8B8A84">{} / {}</span>
            </div>
            <div class="arch-target-bar">
                <div class="arch-target-fill" style="width:{:.0f}%;background:{}"></div>
            </div>
            <div class="arch-target-label">{}</div>
        </div>'''.format(pct_color, pct_of_budget, fmt_dollar(d["revenue"]),
                         fmt_dollar(budget_rev) if budget_rev else "--", bar_w, color,
                         d["department"])
    target_html += '</div>'
    st.markdown(target_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # ROW 6 — Revenue by Dept Bar + Labor % by Dept Bar
    # ═══════════════════════════════════════════════════════
    r4l, r4r = st.columns(2)
    with r4l:
        _arch_card_open("Revenue by Department", "Current week breakdown")
        fig = go.Figure()
        for _, row in chart_df.iterrows():
            fig.add_trace(go.Bar(
                x=[row["Department"]], y=[row["Revenue"]],
                name=row["Department"],
                marker_color=_DEPT_COLORS.get(row["Department"], "#94A3B8"),
                text=["${:,.0f}".format(row["Revenue"])],
                textposition="outside",
                hovertemplate="<b>{}</b><br>Revenue: ${:,.0f}<extra></extra>".format(
                    row["Department"], row["Revenue"]),
                showlegend=False,
            ))
        fig.update_layout(height=320, bargap=0.35)
        _apply_theme(fig, height=320)
        fig.update_xaxes(tickfont=dict(size=10))
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        _arch_card_close()
    with r4r:
        _arch_card_open("Labor % by Department", "Labor as % of revenue")
        fig = go.Figure()
        for _, row in chart_df.iterrows():
            bar_color = "#DC2626" if row["Labor %"] > 40 else ("#D97706" if row["Labor %"] > 35 else _DEPT_COLORS.get(row["Department"], "#94A3B8"))
            fig.add_trace(go.Bar(
                x=[row["Department"]], y=[row["Labor %"]],
                name=row["Department"],
                marker_color=bar_color,
                text=["{:.1f}%".format(row["Labor %"])],
                textposition="outside",
                hovertemplate="<b>{}</b><br>Labor: {:.1f}%<extra></extra>".format(
                    row["Department"], row["Labor %"]),
                showlegend=False,
            ))
        # Add target line at 35%
        fig.add_hline(y=35, line_dash="dash", line_color="#DC2626", line_width=1,
                      annotation_text="Target 35%", annotation_position="top right",
                      annotation_font_size=10, annotation_font_color="#DC2626")
        fig.update_layout(height=320, bargap=0.35)
        _apply_theme(fig, height=320)
        fig.update_xaxes(tickfont=dict(size=10))
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        _arch_card_close()

    # ═══════════════════════════════════════════════════════
    # ROW 7 — Scheduled vs Actual Labor + Food Cost Trend
    # ═══════════════════════════════════════════════════════
    r6l, r6r = st.columns(2)
    with r6l:
        _arch_card_open("Scheduled vs Actual Labor", "Weekly comparison by department")
        _render_labor_comparison(conn, today)
        _arch_card_close()
    with r6r:
        _arch_card_open("Food Cost Tracking", "Past 8 weeks trend")
        _render_food_cost_chart(conn, st.session_state.dash_week, dept_data)
        _arch_card_close()

    # ═══════════════════════════════════════════════════════
    # ROW 7.5 — P&L Summary
    # ═══════════════════════════════════════════════════════
    _render_pnl_section(dept_data, total_rev)

    # ═══════════════════════════════════════════════════════
    # ROW 8 — Meal Plan + Door Counts
    # ═══════════════════════════════════════════════════════
    r7l, r7r = st.columns(2)
    with r7l:
        _arch_card_open("Meal Plan Participation", "Past 14 days")
        _render_meal_plan_chart(conn, today)
        _arch_card_close()
    with r7r:
        _arch_card_open("Door Counts", "Board & Catering — past 14 days")
        _render_door_counts_chart(conn, today)
        _arch_card_close()

    # ═══════════════════════════════════════════════════════
    # ROW 9 — Meal Exchange
    # ═══════════════════════════════════════════════════════
    _arch_card_open("Meal Exchange", "Qdoba & Retail — past 14 days")
    _render_meal_exchange_chart(conn, today)
    _arch_card_close()

    # ═══════════════════════════════════════════════════════
    # ROW 10 — Budget Status + Open Comments
    # ═══════════════════════════════════════════════════════
    st.markdown(
        '<div class="arch-section-title">Status & Activity</div>',
        unsafe_allow_html=True,
    )

    r9l, r9r = st.columns(2)
    with r9l:
        _arch_card_open("Budget Status")
        for d in dept_data:
            dash_dept_status_row(
                d["department"],
                d["status"],
                dept_color=_DEPT_COLORS.get(d["department"], "#1F2A44"),
            )
        _arch_card_close()
    with r9r:
        _arch_card_open("Open Comments")
        any_open = False
        for dept in DEPARTMENTS:
            comments = db.fetch_comments(conn, week_start, dept, open_only=True)
            if comments:
                any_open = True
                st.markdown(
                    '<div style="font-size:12px;font-weight:600;color:#1F2A44;'
                    'margin:8px 0 4px;border-left:3px solid {};padding-left:8px;">{}</div>'.format(
                        _DEPT_COLORS.get(dept, "#1F2A44"), dept),
                    unsafe_allow_html=True,
                )
                for c in comments:
                    st.markdown(
                        '<div style="font-size:12px;color:#64748B;padding:4px 0 4px 11px;">'
                        '<strong style="color:#1E293B">[{}]</strong> {}: {} '
                        '<span style="color:#94A3B8;font-size:11px;">— {}</span>'
                        '</div>'.format(
                            c["field"], c["reason_code"],
                            c["comment_text"], c["created_by"],
                        ),
                        unsafe_allow_html=True,
                    )
        if not any_open:
            st.caption("No open comments for this week.")
        _arch_card_close()

    # ─── Split Transactions (collapsed) ───
    with st.expander("Split Transactions Summary (Past 7 Days)", expanded=False):
        _render_split_transactions_table(conn, today)

    # ─── Export ───
    _render_export_section(conn, today)



# ═══════════════════════════════════════════════════════
# DAILY DASHBOARD
# ═══════════════════════════════════════════════════════


def _render_daily_dashboard(conn, user, today):
    # Date navigation
    if "dash_day" not in st.session_state:
        st.session_state.dash_day = today

    col_prev, col_date, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("\u25c0 Prev Day", key="dashd_prev"):
            st.session_state.dash_day -= timedelta(days=1)
            st.rerun()
    with col_next:
        if st.button("Next Day \u25b6", key="dashd_next"):
            st.session_state.dash_day += timedelta(days=1)
            st.rerun()
    with col_date:
        picked = st.date_input("Date", st.session_state.dash_day, key="dashd_date")
        if picked != st.session_state.dash_day:
            st.session_state.dash_day = picked
            st.rerun()

    entry_date = st.session_state.dash_day.isoformat()
    st.caption(st.session_state.dash_day.strftime("%A, %B %d, %Y"))

    # ─── Weather Flag ───
    weather = db.fetch_daily_weather(conn, entry_date)
    if weather:
        if weather.get("weather_affected_staffing"):
            st.warning("Weather Alert: {} - {}".format(
                weather["condition"], weather.get("notes", "")))
        else:
            st.info("Weather: {}".format(weather["condition"]))

    # ─── Daily KPIs ───
    dash_section_header("Daily Summary", st.session_state.dash_day.strftime("%A, %B %d, %Y"))
    total_rev = 0
    total_hrs = 0
    daily_rows = []
    for dept in DEPARTMENTS:
        sales = db.fetch_daily_sales(conn, entry_date, dept)
        labor = db.fetch_daily_labor(conn, entry_date, dept)
        if sales:
            rev = sum_revenue_streams(
                sales.get("board_revenue", 0), sales.get("retail_revenue", 0),
                sales.get("flex_revenue", 0), sales.get("catering_revenue", 0),
                sales.get("other_revenue", 0),
            )
        else:
            rev = 0
        hrs = labor["labor_hours"] if labor else 0
        total_rev += rev
        total_hrs += hrs
        daily_rows.append({
            "Department": dept,
            "Board": sales.get("board_revenue", 0) if sales else 0,
            "Retail": sales.get("retail_revenue", 0) if sales else 0,
            "Flex": sales.get("flex_revenue", 0) if sales else 0,
            "Catering": sales.get("catering_revenue", 0) if sales else 0,
            "Other": sales.get("other_revenue", 0) if sales else 0,
            "Total Revenue": rev,
            "Labor Hrs": hrs,
        })

    splh = calc_splh(total_rev, total_hrs)
    k1, k2, k3 = st.columns(3)
    with k1:
        dash_kpi_card("Total Revenue", fmt_dollar(total_rev), accent="green",
                       badge_text=str(len(DEPARTMENTS)), badge_bg="#F0FDF4", badge_color="#16A34A")
    with k2:
        dash_kpi_card("Total Labor Hours", fmt_number(total_hrs), accent="blue",
                       badge_text="", badge_bg="#EFF6FF", badge_color="#3B82F6")
    with k3:
        dash_kpi_card("SPLH", fmt_dollar(splh), accent="amber",
                       badge_text="", badge_bg="#FEF3C7", badge_color="#D97706")

    # ─── Daily summary table ───
    if daily_rows:
        ddf = pd.DataFrame(daily_rows)
        dollar_cols = ["Board", "Retail", "Flex", "Catering", "Other", "Total Revenue"]
        fmt_dict = {}
        for c in dollar_cols:
            fmt_dict[c] = "${:,.0f}".format
        fmt_dict["Labor Hrs"] = "{:.1f}".format
        st.dataframe(ddf.style.format(fmt_dict), use_container_width=True, hide_index=True)

    # ─── Daily Door Counts – Board & Catering ───
    dash_section_header("Door Counts", "Board & Catering")
    _render_daily_door_counts(conn, entry_date)

    # ─── Daily Meal Exchange – Qdoba & Retail & Mac's Grill ───
    dash_section_header("Meal Exchange", "Qdoba & Retail & Mac's Grill")
    _render_daily_meal_exchange(conn, entry_date)

    # ─── Daily Meal Plan Participation – Board & Catering ───
    dash_section_header("Meal Plan Participation", "Board & Catering")
    _render_daily_meal_plan(conn, entry_date)

    # ─── Daily Sales Trend ───
    dash_chart_start("Sales Trend", "Past 14 days")
    _render_daily_sales_trend(conn, st.session_state.dash_day)
    dash_chart_end()



# ═══════════════════════════════════════════════════════
# SHARED CHART HELPERS
# ═══════════════════════════════════════════════════════


def _render_daily_sales_trend(conn, reference_date):
    """Render daily sales trend chart for past 14 days."""
    start_date = (reference_date - timedelta(days=13)).isoformat()
    end_date = reference_date.isoformat()

    all_sales = db.fetch_daily_sales_range(conn, start_date, end_date)

    if not all_sales:
        st.caption("No daily sales data available for chart.")
        return

    chart_rows = []
    for s in all_sales:
        rev = sum_revenue_streams(
            s.get("board_revenue", 0), s.get("retail_revenue", 0),
            s.get("flex_revenue", 0), s.get("catering_revenue", 0),
            s.get("other_revenue", 0),
        )
        chart_rows.append({
            "Date": s["entry_date"],
            "Department": s["department"],
            "Revenue": rev,
        })

    if not chart_rows:
        st.caption("No daily sales data available for chart.")
        return

    trend_df = pd.DataFrame(chart_rows)

    # Check for weather-affected days
    weather_dates = []
    for i in range(14):
        d = (reference_date - timedelta(days=13 - i)).isoformat()
        w = db.fetch_daily_weather(conn, d)
        if w and w.get("weather_affected_staffing"):
            weather_dates.append(d)

    fig = px.line(trend_df, x="Date", y="Revenue", color="Department",
                  markers=True, color_discrete_map=_DEPT_COLORS)
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
    )
    fig.update_layout(height=400)
    _apply_theme(fig)
    fig.update_traces(marker=dict(size=6), line=dict(width=2.5))
    fig.update_xaxes(tickformat="%b %d", tickangle=-45)

    # Add weather flags as vertical lines
    for wd in weather_dates:
        fig.add_vline(x=wd, line_dash="dash", line_color="orange",
                      annotation_text="Weather", annotation_position="top left")

    st.plotly_chart(fig, use_container_width=True)


def _render_labor_comparison(conn, reference_date):
    """Render scheduled vs actual labor hours for past 7 days."""
    start_date = (reference_date - timedelta(days=6)).isoformat()
    end_date = reference_date.isoformat()

    schedule_data = db.fetch_labor_schedule_range(conn, start_date, end_date)

    if not schedule_data:
        st.caption("No labor schedule data available. Import ADP data or enter manually.")
        return

    chart_rows = []
    for s in schedule_data:
        chart_rows.append({
            "Date": s["entry_date"],
            "Department": s["department"],
            "Scheduled": s.get("scheduled_hours", 0) or 0,
            "Actual": s.get("actual_hours", 0) or 0,
        })

    if not chart_rows:
        st.caption("No labor schedule data available.")
        return

    labor_df = pd.DataFrame(chart_rows)

    # Aggregate by department
    dept_agg = labor_df.groupby("Department").agg({
        "Scheduled": "sum",
        "Actual": "sum",
    }).reset_index()

    fig = go.Figure(data=[
        go.Bar(
            name="Scheduled", x=dept_agg["Department"], y=dept_agg["Scheduled"],
            marker_color=_CHART_NAVY,
            hovertemplate="<b>%{x}</b><br>Scheduled: %{y:.1f} hrs<extra></extra>",
            texttemplate="%{y:.0f}", textposition="outside",
        ),
        go.Bar(
            name="Actual", x=dept_agg["Department"], y=dept_agg["Actual"],
            marker_color=_CHART_GOLD,
            hovertemplate="<b>%{x}</b><br>Actual: %{y:.1f} hrs<extra></extra>",
            texttemplate="%{y:.0f}", textposition="outside",
        ),
    ])
    fig.update_layout(barmode="group", height=350)
    _apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# NEW CHART SECTIONS – WEEKLY
# ═══════════════════════════════════════════════════════


def _render_pnl_section(dept_data, total_rev):
    """Render a P&L summary section from CTUIT-imported data."""
    # Aggregate P&L across all departments
    total_cos = sum(d.get("cos_dollars", 0) for d in dept_data)
    total_gp = sum(d.get("gross_profit", 0) for d in dept_data)
    total_payroll = sum(d.get("total_payroll", 0) for d in dept_data)
    total_labor = sum(d.get("labor_dollars", 0) for d in dept_data)
    total_tf = sum(d.get("tax_fringe", 0) for d in dept_data)
    total_apc = sum(d.get("after_prime_costs", 0) for d in dept_data)
    total_de = sum(d.get("direct_expenses", 0) for d in dept_data)
    total_pace_val = sum(d.get("pace", 0) for d in dept_data)
    total_nc = sum(d.get("non_cont_expenses", 0) for d in dept_data)
    total_ni = sum(d.get("net_income", 0) for d in dept_data)
    total_ins = sum(d.get("insurance", 0) for d in dept_data)
    total_pf = sum(d.get("profit_fee", 0) for d in dept_data)
    total_roy = sum(d.get("royalties", 0) for d in dept_data)

    # Only show if we have at least some P&L data (gross_profit or net_income)
    has_pnl = total_gp != 0 or total_ni != 0 or total_apc != 0
    if not has_pnl:
        return

    dash_section_header("Profit & Loss Summary", "From CTUIT Ops Statement")

    # ROW 1: Key P&L metrics
    pl1, pl2, pl3, pl4 = st.columns(4)
    with pl1:
        gp_pct = (total_gp / total_rev * 100) if total_rev > 0 else 0
        dash_kpi_card(
            "Gross Profit", fmt_dollar(total_gp),
            change="{:.1f}% margin".format(gp_pct), accent="green",
            badge_text=fmt_pct(gp_pct),
            badge_bg="#F0FDF4", badge_color="#16A34A",
        )
    with pl2:
        dash_kpi_card(
            "Total Payroll", fmt_dollar(total_payroll),
            change="Labor + Tax & Fringe", accent="red",
            badge_text="{:.1f}%".format(total_payroll / total_rev * 100) if total_rev > 0 else "--",
            badge_bg="#FEF2F2", badge_color="#EF4444",
        )
    with pl3:
        dash_kpi_card(
            "PACE", fmt_dollar(total_pace_val),
            change="After controllable exp.", accent="blue",
            badge_text="{:.1f}%".format(total_pace_val / total_rev * 100) if total_rev > 0 else "--",
            badge_bg="#EFF6FF", badge_color="#3B82F6",
        )
    with pl4:
        ni_color = "green" if total_ni >= 0 else "red"
        dash_kpi_card(
            "Net Income", fmt_dollar(total_ni),
            change="{:.1f}% of revenue".format(total_ni / total_rev * 100) if total_rev > 0 else "",
            accent=ni_color,
            badge_text="{:.1f}%".format(total_ni / total_rev * 100) if total_rev > 0 else "--",
            badge_bg="#F0FDF4" if total_ni >= 0 else "#FEF2F2",
            badge_color="#16A34A" if total_ni >= 0 else "#EF4444",
        )

    # ROW 2: Waterfall-style P&L breakdown by department
    pnl_chart_data = []
    for d in dept_data:
        dept_name = d["department"]
        if d.get("gross_profit", 0) != 0 or d.get("net_income", 0) != 0:
            pnl_chart_data.append({
                "Department": dept_name,
                "Gross Profit": d.get("gross_profit", 0),
                "After Prime": d.get("after_prime_costs", 0),
                "PACE": d.get("pace", 0),
                "Net Income": d.get("net_income", 0),
            })

    if pnl_chart_data:
        pnl_df = pd.DataFrame(pnl_chart_data)
        r_left, r_right = st.columns(2)
        with r_left:
            dash_chart_start("P&L by Department", "Key profit metrics")
            fig = go.Figure()
            for metric, color in [("Gross Profit", "#16A34A"), ("PACE", "#3B82F6"),
                                  ("Net Income", "#C7A462")]:
                fig.add_trace(go.Bar(
                    name=metric, x=pnl_df["Department"], y=pnl_df[metric],
                    marker_color=color,
                    texttemplate="$%{{y:,.0f}}",
                    textposition="outside",
                    hovertemplate="<b>%{{x}}</b><br>{}: $%{{y:,.0f}}<extra></extra>".format(metric),
                ))
            fig.update_layout(barmode="group", showlegend=True, height=380)
            _apply_theme(fig)
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
            dash_chart_end()

        with r_right:
            dash_chart_start("Expense Breakdown", "Non-controllable details")
            # Show breakdown of non-controllable expenses
            nc_data = []
            for d in dept_data:
                dept_name = d["department"]
                ins_val = d.get("insurance", 0)
                pf_val = d.get("profit_fee", 0)
                roy_val = d.get("royalties", 0)
                if ins_val > 0 or pf_val > 0 or roy_val > 0:
                    nc_data.append({"Department": dept_name, "Insurance": ins_val,
                                    "Profit Fee": pf_val, "Royalties": roy_val})
            if nc_data:
                nc_df = pd.DataFrame(nc_data)
                fig2 = go.Figure()
                for metric, color in [("Insurance", "#94A3B8"), ("Profit Fee", "#D97706"),
                                      ("Royalties", "#7C3AED")]:
                    fig2.add_trace(go.Bar(
                        name=metric, x=nc_df["Department"], y=nc_df[metric],
                        marker_color=color,
                        hovertemplate="<b>%{{x}}</b><br>{}: $%{{y:,.0f}}<extra></extra>".format(metric),
                    ))
                fig2.update_layout(barmode="stack", showlegend=True, height=380)
                _apply_theme(fig2)
                fig2.update_xaxes(visible=False)
                fig2.update_yaxes(visible=False)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.caption("No non-controllable expense data available.")
            dash_chart_end()

    # ROW 3: Compact P&L detail metrics
    det1, det2, det3, det4 = st.columns(4)
    with det1:
        dash_metric_card("Tax & Fringe", fmt_dollar(total_tf), value_color="#64748B")
    with det2:
        dash_metric_card("After Prime Costs", fmt_dollar(total_apc), value_color="#1E293B")
    with det3:
        dash_metric_card("Controllable Exp.", fmt_dollar(total_de), value_color="#D97706")
    with det4:
        dash_metric_card("Non-Cont. Exp.", fmt_dollar(total_nc), value_color="#7C3AED")


def _render_food_cost_chart(conn, week_start, dept_data):
    """Render food cost tracking as grouped bar + food cost % overlay.

    Shows invoice_total per department as bars, with food cost %
    as colored badges when weekly financials are available.
    """
    end_date = week_start.isoformat()
    start_date = (week_start - timedelta(weeks=7)).isoformat()

    food_cost_rows = db.fetch_food_cost_range(conn, start_date, end_date)

    if not food_cost_rows:
        st.caption("No food cost data available for the past 8 weeks.")
        return

    fc_df = pd.DataFrame(food_cost_rows)
    # Filter out "Consolidated" if present
    fc_df = fc_df[~fc_df["department"].str.contains("Consolidated", case=False, na=False)]

    if fc_df.empty:
        st.caption("No food cost data available.")
        return

    # ── Grouped bar chart by week and department ──
    fc_df["week_label"] = pd.to_datetime(fc_df["week_start"]).dt.strftime("%b %d")

    fig = go.Figure()
    for dept in DEPARTMENTS:
        ddf = fc_df[fc_df["department"] == dept]
        if not ddf.empty:
            fig.add_trace(go.Bar(
                name=dept,
                x=ddf["week_label"],
                y=ddf["invoice_total"],
                marker_color=_DEPT_COLORS.get(dept, "#94A3B8"),
                text=["${:,.0f}".format(v) for v in ddf["invoice_total"]],
                textposition="outside",
                textfont=dict(size=9),
                hovertemplate="<b>{}</b><br>%{{x}}<br>Invoice: $%{{y:,.0f}}<extra></extra>".format(dept),
            ))

    fig.update_layout(
        barmode="group", height=280, bargap=0.25, bargroupgap=0.1,
        xaxis_title="", yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5, font=dict(size=9)),
    )
    _apply_theme(fig, height=280)
    fig.update_yaxes(tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Food cost % summary as inline HTML badges ──
    unique_weeks = sorted(fc_df["week_start"].unique())
    pct_rows = []
    for wk in unique_weeks:
        for dept_row in fc_df[fc_df["week_start"] == wk].to_dict("records"):
            dept_name = dept_row.get("department", "")
            inv_total = dept_row.get("invoice_total", 0) or 0
            fin = db.fetch_weekly_financials(conn, wk, dept_name)
            if fin:
                rev = sum_revenue_streams(
                    fin.get("board_revenue", 0), fin.get("retail_revenue", 0),
                    fin.get("flex_revenue", 0), fin.get("catering_revenue", 0),
                    fin.get("other_revenue", 0),
                )
                if rev and rev > 0:
                    pct_rows.append({
                        "Department": dept_name,
                        "Food Cost %": round((inv_total / rev) * 100, 1),
                    })

    if pct_rows:
        # Show latest week's food cost % as inline badges
        pct_html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">'
        for row in pct_rows:
            pct_val = row["Food Cost %"]
            color = "#DC2626" if pct_val > 40 else ("#D97706" if pct_val > 35 else "#16A34A")
            bg = "#FEF2F2" if pct_val > 40 else ("#FEF3C7" if pct_val > 35 else "#F0FDF4")
            dept_short = row["Department"].replace("Retail & Mac's Grill", "Retail").replace("Board & Catering", "Board")
            pct_html += (
                '<div style="background:{};border-radius:8px;padding:6px 12px;'
                'display:flex;align-items:center;gap:6px;">'
                '<span style="font-size:10px;color:#64748B;">{}</span>'
                '<span style="font-size:13px;font-weight:700;color:{};">{:.1f}%</span>'
                '</div>'
            ).format(bg, dept_short, color, pct_val)
        pct_html += '</div>'
        st.markdown(pct_html, unsafe_allow_html=True)


def _render_meal_plan_chart(conn, reference_date):
    """Render meal plan participation chart for past 14 days.

    Two-line chart: resident enrolled vs meals_used, and
    commuter enrolled vs meals_used.
    """
    start_date = (reference_date - timedelta(days=13)).isoformat()
    end_date = reference_date.isoformat()

    meal_rows = db.fetch_meal_plan_range(conn, start_date, end_date)

    if not meal_rows:
        st.caption("No meal plan data available for the past 14 days.")
        return

    mp_df = pd.DataFrame(meal_rows)

    # Separate resident and commuter plan types
    chart_rows = []
    for _, row in mp_df.iterrows():
        plan = row.get("plan_type", "")
        enrolled = row.get("enrolled_count", 0) or 0
        used = row.get("meals_used", 0) or 0
        entry = row.get("entry_date", "")
        chart_rows.append({
            "Date": entry,
            "Metric": "{} - Enrolled".format(plan),
            "Count": enrolled,
        })
        chart_rows.append({
            "Date": entry,
            "Metric": "{} - Meals Used".format(plan),
            "Count": used,
        })

    if not chart_rows:
        st.caption("No meal plan data available for the past 14 days.")
        return

    chart_df = pd.DataFrame(chart_rows)

    fig = px.line(
        chart_df,
        x="Date",
        y="Count",
        color="Metric",
        markers=True,
    )
    fig.update_layout(height=400)
    _apply_theme(fig)
    fig.update_traces(marker=dict(size=6), line=dict(width=2.5))
    fig.update_xaxes(tickformat="%b %d", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def _render_meal_exchange_chart(conn, reference_date):
    """Render meal exchange chart for Qdoba & Retail & Mac's Grill (past 14 days)."""
    start_date = (reference_date - timedelta(days=13)).isoformat()
    end_date = reference_date.isoformat()

    mx_rows = db.fetch_meal_exchange_range(conn, start_date, end_date)

    if not mx_rows:
        st.caption("No meal exchange data available for the past 14 days.")
        return

    mx_df = pd.DataFrame(mx_rows)
    # Filter to only Qdoba and Retail & Mac's Grill
    mx_df = mx_df[mx_df["department"].isin(["Qdoba", "Retail & Mac's Grill"])]

    if mx_df.empty:
        st.caption("No meal exchange data available for Qdoba or Retail & Mac's Grill.")
        return

    mx_df.rename(columns={
        "entry_date": "Date",
        "department": "Department",
        "dollar_amount": "Dollar Amount",
        "exchange_count": "Exchanges",
    }, inplace=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            mx_df, x="Date", y="Exchanges", color="Department",
            title="Daily Meal Exchange Count", barmode="group",
        )
        fig.update_layout(height=350)
        _apply_theme(fig)
        fig.update_xaxes(tickformat="%b %d", tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.bar(
            mx_df, x="Date", y="Dollar Amount", color="Department",
            title="Daily Meal Exchange Dollars", barmode="group",
        )
        fig2.update_layout(height=350)
        _apply_theme(fig2)
        fig2.update_xaxes(tickformat="%b %d", tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)


def _render_daily_meal_exchange(conn, entry_date):
    """Render meal exchange summary for Qdoba & Retail & Mac's Grill for a single day."""
    has_data = False
    rows = []
    for dept in ["Qdoba", "Retail & Mac's Grill"]:
        mx = db.fetch_meal_exchange(conn, entry_date, dept)
        if mx:
            has_data = True
            rows.append({
                "Department": dept,
                "Exchange Count": int(mx.get("exchange_count", 0)),
                "Dollar Amount": float(mx.get("dollar_amount", 0.0)),
            })
        else:
            rows.append({
                "Department": dept,
                "Exchange Count": 0,
                "Dollar Amount": 0.0,
            })

    if not has_data:
        st.caption("No meal exchange data available for Qdoba or Retail & Mac's Grill on this date.")
        return

    mx_df = pd.DataFrame(rows)
    fmt_dict = {
        "Exchange Count": "{:,.0f}".format,
        "Dollar Amount": "${:,.2f}".format,
    }
    st.dataframe(mx_df.style.format(fmt_dict), use_container_width=True, hide_index=True)


def _render_door_counts_chart(conn, reference_date):
    """Render door counts bar chart by meal period for past 14 days.

    Shows breakfast/lunch/dinner door counts for Board & Catering only.
    """
    start_date = (reference_date - timedelta(days=13)).isoformat()
    end_date = reference_date.isoformat()

    door_rows = db.fetch_door_counts_range(conn, start_date, end_date, department="Board & Catering")

    if not door_rows:
        st.caption("No door count data available for the past 14 days.")
        return

    dc_df = pd.DataFrame(door_rows)
    dc_df.rename(columns={
        "entry_date": "Date",
        "meal_period": "Meal Period",
        "count": "Count",
    }, inplace=True)

    # Capitalize meal period for display
    dc_df["Meal Period"] = dc_df["Meal Period"].str.title()

    color_map = {"Breakfast": "#E85D04", "Lunch": "#2E3A59", "Dinner": "#0077B6"}
    fig = px.bar(
        dc_df,
        x="Date",
        y="Count",
        color="Meal Period",
        barmode="stack",
        color_discrete_map=color_map,
        category_orders={"Meal Period": ["Breakfast", "Lunch", "Dinner"]},
    )
    fig.update_layout(height=400)
    _apply_theme(fig)
    fig.update_xaxes(tickformat="%b %d", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def _render_split_transactions_table(conn, reference_date):
    """Render split transactions summary table for past 7 days."""
    start_date = (reference_date - timedelta(days=6)).isoformat()
    end_date = reference_date.isoformat()

    split_rows = db.fetch_split_transactions_range(conn, start_date, end_date)

    if not split_rows:
        st.caption("No split transaction data available for the past 7 days.")
        return

    st_df = pd.DataFrame(split_rows)

    # Select and order the display columns
    display_cols = [
        "transaction_date", "department", "transaction_id",
        "tender_type_1", "amount_1",
        "tender_type_2", "amount_2",
        "tender_type_3", "amount_3",
        "total_amount",
    ]
    # Keep only columns that exist in the data
    available_cols = [c for c in display_cols if c in st_df.columns]
    st_df = st_df[available_cols]

    # Format dollar columns
    dollar_cols = ["amount_1", "amount_2", "amount_3", "total_amount"]
    fmt_dict = {}
    for c in dollar_cols:
        if c in st_df.columns:
            fmt_dict[c] = "${:,.2f}".format

    st.dataframe(st_df.style.format(fmt_dict), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# NEW CHART SECTIONS – DAILY
# ═══════════════════════════════════════════════════════


def _render_daily_door_counts(conn, entry_date):
    """Render door count by meal period for Board & Catering for a single day."""
    counts = db.fetch_door_counts(conn, entry_date, "Board & Catering")
    if not counts:
        st.caption("No door count data available for Board & Catering on this date.")
        return

    door_map = {}
    for r in counts:
        door_map[r.get("meal_period", "total")] = int(r.get("count", 0) or 0)

    total = sum(door_map.values())
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Breakfast", "{:,.0f}".format(door_map.get("breakfast", 0)))
    with c2:
        st.metric("Lunch", "{:,.0f}".format(door_map.get("lunch", 0)))
    with c3:
        st.metric("Dinner", "{:,.0f}".format(door_map.get("dinner", 0)))
    with c4:
        st.metric("Total", "{:,.0f}".format(total))


def _render_daily_meal_plan(conn, entry_date):
    """Render meal plan participation for a single day."""
    meal_rows = db.fetch_meal_plan_for_date(conn, entry_date)

    if not meal_rows:
        st.caption("No meal plan data available for this date.")
        return

    mp_df = pd.DataFrame(meal_rows)
    display_cols = ["plan_type", "enrolled_count", "meals_used"]
    available_cols = [c for c in display_cols if c in mp_df.columns]
    mp_df = mp_df[available_cols]

    rename_map = {}
    if "plan_type" in mp_df.columns:
        rename_map["plan_type"] = "Plan Type"
    if "enrolled_count" in mp_df.columns:
        rename_map["enrolled_count"] = "Enrolled"
    if "meals_used" in mp_df.columns:
        rename_map["meals_used"] = "Meals Used"
    mp_df.rename(columns=rename_map, inplace=True)

    fmt_dict = {}
    if "Enrolled" in mp_df.columns:
        fmt_dict["Enrolled"] = "{:,.0f}".format
    if "Meals Used" in mp_df.columns:
        fmt_dict["Meals Used"] = "{:,.0f}".format

    st.dataframe(mp_df.style.format(fmt_dict), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# OPERATIONS OVERVIEW SECTION
# ═══════════════════════════════════════════════════════

def _render_operations_overview(week_start=None):
    """Render the interactive Operations Overview dashboard.

    Embeds a self-contained HTML/CSS/JS dashboard with location-level
    KPIs, canvas gauges, flags, and an edit-actuals form.
    Data is pulled from DB for the selected week.
    """
    import json
    import streamlit.components.v1 as components
    from config import DEPARTMENTS

    conn = db.get_conn()

    if week_start is None:
        week_start = db.get_week_start(date.today())
    week_iso = week_start.isoformat()
    week_end = week_start + timedelta(days=6)
    week_label = week_end.strftime("%-m/%-d/%y")
    fiscal_period = week_start.month
    week_number = week_start.isocalendar()[1]
    period_label = "Week {} &middot; P{}".format(week_number, fiscal_period)

    # ── Location config: map dept → display info ──
    _LOC_CONFIG = [
        {"dept": "Board & Catering", "name": "Hamilton Commons",
         "owner": "Dan \u00b7 Residential Lead", "type": "residential"},
        {"dept": "Starbucks", "name": "Starbucks #29348",
         "owner": "Heather Louis \u00b7 Retail Mgr", "type": "retail"},
        {"dept": "Retail & Mac's Grill", "name": "Mac's / Loch Lomond",
         "owner": "Heather Louis \u00b7 Retail Mgr", "type": "retail"},
        {"dept": "Qdoba", "name": "Qdoba",
         "owner": "Heather Louis \u00b7 Retail Mgr", "type": "retail"},
    ]

    locs = []
    for idx, cfg in enumerate(_LOC_CONFIG):
        dept = cfg["dept"]
        fin = db.fetch_weekly_financials(conn, week_iso, dept)
        bgt = db.fetch_budget(conn, week_iso, dept)
        ly = db.fetch_ly_actuals(conn, week_iso, dept)

        # Actuals
        if fin:
            rev = sum_revenue_streams(
                fin.get("board_revenue", 0), fin.get("retail_revenue", 0),
                fin.get("flex_revenue", 0), fin.get("catering_revenue", 0),
                fin.get("other_revenue", 0),
            )
            lab = fin.get("total_labor_dollars", 0) or 0
            hrs = fin.get("total_labor_hours", 0) or 0
            cos = fin.get("cos_dollars", 0) or 0
            ot = fin.get("overtime_dollars", 0) or 0
            de = fin.get("direct_expenses", 0) or 0
        else:
            rev = lab = hrs = cos = ot = de = 0

        # Budget targets
        bgt_rev = (bgt.get("revenue", 0) or 0) if bgt else 0
        bgt_lab = (bgt.get("labor_dollars", 0) or 0) if bgt else 0
        bgt_hrs = (bgt.get("labor_hours", 0) or 0) if bgt else 0

        # Last year
        ly_rev = (ly["revenue"] or 0) if ly else 0
        ly_lab = (ly["labor_dollars"] or 0) if ly else 0

        # Derived metrics
        labor_pct = (lab / rev * 100) if rev > 0 else 0
        food_cost_pct = (cos / rev * 100) if rev > 0 else 0
        splh = (rev / hrs) if hrs > 0 else 0

        # Target labor %
        tgt_labor_pct = (bgt_lab / bgt_rev * 100) if bgt_rev > 0 else 35.0

        # Trend vs LY
        rev_trend = ""
        if ly_rev > 0:
            pct_chg = (rev - ly_rev) / ly_rev * 100
            rev_trend = "{}{:.1f}%".format("+" if pct_chg >= 0 else "", pct_chg)
        lab_trend = ""
        if ly_lab > 0:
            pct_chg = (lab - ly_lab) / ly_lab * 100
            lab_trend = "{}{:.1f}%".format("+" if pct_chg >= 0 else "", pct_chg)

        # Status logic
        red_count = 0
        if bgt_rev > 0 and rev < bgt_rev * 0.90:
            red_count += 1
        if labor_pct > tgt_labor_pct * 1.05:
            red_count += 1
        if food_cost_pct > 38:
            red_count += 1
        status = "critical" if red_count >= 2 else ("watch" if red_count == 1 else "ok")

        # Flags
        flags = []
        if bgt_rev > 0:
            if rev >= bgt_rev:
                flags.append({"t": "ok", "msg": "Revenue on/above budget ({})".format(fmt_dollar(bgt_rev))})
            elif rev >= bgt_rev * 0.90:
                flags.append({"t": "warn", "msg": "Revenue {:.1f}% below budget".format((1 - rev / bgt_rev) * 100)})
            else:
                flags.append({"t": "bad", "msg": "Revenue {:.1f}% below budget — action needed".format((1 - rev / bgt_rev) * 100)})
        if labor_pct > tgt_labor_pct * 1.05:
            flags.append({"t": "bad", "msg": "Labor {:.1f}% — {:.1f} pts over target".format(labor_pct, labor_pct - tgt_labor_pct)})
        elif labor_pct > tgt_labor_pct:
            flags.append({"t": "warn", "msg": "Labor {:.1f}% — slightly above {:.1f}% target".format(labor_pct, tgt_labor_pct)})
        else:
            flags.append({"t": "ok", "msg": "Labor {:.1f}% — within target".format(labor_pct)})
        if ot > 0:
            flags.append({"t": "warn", "msg": "Overtime: {} this week".format(fmt_dollar(ot))})
        if not fin and not bgt:
            flags.append({"t": "neu", "msg": "No data entered for this week"})

        loc = {
            "id": idx,
            "name": cfg["name"],
            "owner": cfg["owner"],
            "type": cfg["type"],
            "status": status,
            "kpis": [
                {"label": "net sales", "val": round(rev, 2), "target": round(bgt_rev, 2) if bgt_rev > 0 else round(rev * 1.05, 2),
                 "unit": "$", "higherBad": False, "trend": rev_trend},
                {"label": "food cost %", "val": round(food_cost_pct, 1), "target": 36.5,
                 "unit": "%", "higherBad": True, "trend": ""},
                {"label": "labor %", "val": round(labor_pct, 1), "target": round(tgt_labor_pct, 1),
                 "unit": "%", "higherBad": True, "trend": lab_trend},
            ],
            "gauges": [
                {"label": "SPLH", "val": round(splh, 2), "min": 0, "max": round(splh * 2, 2) if splh > 0 else 30,
                 "target": round(bgt_rev / bgt_hrs, 2) if bgt_hrs > 0 else 15, "higherBad": False},
                {"label": "labor hours", "val": round(hrs, 1), "min": 0, "max": round(bgt_hrs * 1.5, 0) if bgt_hrs > 0 else 200,
                 "target": round(bgt_hrs, 0) if bgt_hrs > 0 else 100, "higherBad": True},
                {"label": "overtime $", "val": round(ot, 2), "min": 0, "max": 500,
                 "target": 0, "higherBad": True},
                {"label": "labor dollars", "val": round(lab, 2), "min": 0,
                 "max": round(bgt_lab * 1.5, 0) if bgt_lab > 0 else round(lab * 1.5, 0) if lab > 0 else 5000,
                 "target": round(bgt_lab, 0) if bgt_lab > 0 else 0, "higherBad": True},
                {"label": "COS dollars", "val": round(cos, 2), "min": 0,
                 "max": round(rev * 0.6, 0) if rev > 0 else 5000,
                 "target": round(rev * 0.365, 0) if rev > 0 else 0, "higherBad": True},
                {"label": "direct expenses", "val": round(de, 2), "min": 0, "max": 2000,
                 "target": 0, "higherBad": True},
            ],
            "flags": flags,
        }
        locs.append(loc)

    # Build the HTML with live data injected
    locs_json = json.dumps(locs)
    html_code = _get_ops_dashboard_html_template(locs_json, week_label, period_label)
    components.html(html_code, height=860, scrolling=True)


def _get_ops_dashboard_html_template(locs_json, week_label, period_label):
    """Return the full HTML for the Operations Overview dashboard with live data."""
    return ('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #ffffff; --bg2: #f5f4f0; --bg3: #eceae3;
    --text: #1a1a18; --text2: #6b6a64; --text3: #9c9a92;
    --border: rgba(0,0,0,0.10); --border2: rgba(0,0,0,0.18);
    --green: #639922; --green-bg: #eaf3de; --green-txt: #27500a;
    --amber: #EF9F27; --amber-bg: #faeeda; --amber-txt: #633806;
    --red: #E24B4A; --red-bg: #fcebeb; --red-txt: #791f1f;
    --blue-bg: #e6f1fb; --blue-txt: #0c447c;
    --radius: 8px; --radius-lg: 12px;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg3); color: var(--text);
    font-size: 14px; line-height: 1.5; margin: 0;
  }
  .app { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
  .topbar {
    background: var(--bg); border-bottom: 0.5px solid var(--border);
    padding: 10px 20px; display: flex; align-items: center;
    justify-content: space-between; flex-shrink: 0; gap: 12px; flex-wrap: wrap;
  }
  .topbar-left { display: flex; flex-direction: column; gap: 1px; }
  .topbar-title { font-size: 14px; font-weight: 600; color: var(--text); }
  .topbar-sub { font-size: 11px; color: var(--text2); }
  .topbar-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .period-badge {
    font-size: 11px; font-weight: 500;
    background: var(--blue-bg); color: var(--blue-txt);
    border-radius: 10px; padding: 3px 10px;
  }
  select, input[type=text] {
    font-size: 12px; padding: 5px 10px; border-radius: var(--radius);
    border: 0.5px solid var(--border2); background: var(--bg2); color: var(--text);
    cursor: pointer; outline: none;
  }
  .edit-btn {
    font-size: 11px; font-weight: 500; padding: 5px 12px;
    border-radius: var(--radius); border: 0.5px solid var(--border2);
    background: var(--bg2); color: var(--text2);
    cursor: pointer; transition: background .15s, color .15s;
  }
  .edit-btn:hover { background: var(--bg3); color: var(--text); }
  .edit-btn.active { background: var(--blue-bg); color: var(--blue-txt); border-color: transparent; }
  .body { display: flex; flex: 1; overflow: hidden; }
  .sidebar {
    width: 220px; flex-shrink: 0; background: var(--bg);
    border-right: 0.5px solid var(--border);
    display: flex; flex-direction: column; overflow-y: auto;
  }
  .sidebar-label {
    font-size: 9px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
    color: var(--text3); padding: 14px 14px 6px;
  }
  .loc-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 14px; cursor: pointer;
    border-left: 2px solid transparent;
    transition: background .1s, border-color .1s;
  }
  .loc-item:hover { background: var(--bg2); }
  .loc-item.selected { background: var(--bg2); border-left-color: #378add; }
  .loc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .loc-info { flex: 1; min-width: 0; }
  .loc-name { font-size: 12px; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .loc-owner { font-size: 10px; color: var(--text3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .mini-gauges { display: flex; gap: 3px; flex-shrink: 0; }
  .main { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 14px; }
  .detail-header {
    background: var(--bg); border: 0.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 14px 16px;
    display: flex; align-items: center; justify-content: space-between;
    gap: 12px; flex-wrap: wrap;
  }
  .detail-name { font-size: 16px; font-weight: 600; color: var(--text); }
  .detail-owner { font-size: 11px; color: var(--text2); margin-top: 2px; }
  .status-pill { font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 12px; white-space: nowrap; }
  .section-label {
    font-size: 9px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
    color: var(--text3); margin-bottom: 8px;
  }
  .kpi-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 10px; }
  .kpi-card {
    background: var(--bg); border: 0.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 12px 14px;
    display: flex; flex-direction: column; gap: 6px;
  }
  .kpi-top { display: flex; align-items: center; justify-content: space-between; }
  .kpi-lbl { font-size: 10px; color: var(--text2); }
  .kpi-trend { font-size: 11px; font-weight: 600; }
  .kpi-val { font-size: 26px; font-weight: 700; color: var(--text); line-height: 1; }
  .kpi-bar-bg { height: 4px; background: var(--bg3); border-radius: 2px; overflow: hidden; }
  .kpi-bar-fill { height: 100%; border-radius: 2px; transition: width .4s ease; }
  .kpi-target { font-size: 9px; color: var(--text3); }
  .gauge-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 10px; }
  .gauge-card {
    background: var(--bg); border: 0.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 10px 12px;
    display: flex; flex-direction: column; align-items: center; gap: 4px;
  }
  .gauge-val { font-size: 15px; font-weight: 600; color: var(--text); }
  .gauge-lbl { font-size: 10px; color: var(--text2); text-align: center; }
  .gauge-tgt { font-size: 9px; color: var(--text3); }
  .flags-card {
    background: var(--bg); border: 0.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 12px 14px;
    display: flex; flex-direction: column; gap: 6px;
  }
  .flag { display: flex; align-items: flex-start; gap: 8px; font-size: 12px; color: var(--text2); }
  .fdot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
  .edit-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; }
  .edit-card {
    background: var(--bg2); border: 0.5px solid var(--border);
    border-radius: var(--radius); padding: 10px 12px;
    display: flex; flex-direction: column; gap: 4px;
  }
  .edit-lbl { font-size: 10px; color: var(--text2); }
  .edit-row { display: flex; align-items: center; gap: 6px; }
  .edit-inp {
    flex: 1; font-size: 13px; font-weight: 500; color: var(--text);
    background: var(--bg); border: 0.5px solid var(--border2);
    border-radius: 4px; padding: 4px 8px; outline: none;
  }
  .edit-inp:focus { border-color: #378add; }
  .edit-unit { font-size: 11px; color: var(--text3); }
  .save-btn {
    font-size: 12px; font-weight: 600; padding: 8px 20px;
    border-radius: var(--radius); border: none;
    background: #378add; color: #fff; cursor: pointer; transition: background .15s;
  }
  .save-btn:hover { background: #185fa5; }
</style>
</head>
<body>
<div class="app">
  <div class="topbar">
    <div class="topbar-left">
      <div class="topbar-title">Alma College Dining — Operations Dashboard</div>
      <div class="topbar-sub">Metz Culinary Management &middot; GM: Micah Braman</div>
    </div>
    <div class="topbar-right">
      <select id="period-sel" onchange="setPeriod(this.value)">
        <option value="wk">Week of ''' + week_label + '''</option>
        <option value="ptd">Period to date</option>
        <option value="ytd">Year to date</option>
      </select>
      <span class="period-badge" id="period-badge">''' + period_label + '''</span>
      <button class="edit-btn" id="edit-btn" onclick="toggleEdit()">Edit actuals</button>
    </div>
  </div>
  <div class="body">
    <div class="sidebar">
      <div class="sidebar-label">All locations</div>
      <div id="sidebar-list"></div>
    </div>
    <div class="main" id="main-panel"></div>
  </div>
</div>
<script>
const _RAW=''' + locs_json + ''';
function _autoFmt(unit){if(unit==="%")return v=>v.toFixed(1)+"%";if(unit==="$")return v=>"$"+v.toLocaleString(undefined,{minimumFractionDigits:0,maximumFractionDigits:0});return v=>v.toLocaleString();}
function _gaugeFmt(label){if(label.includes("$")||label.includes("dollar")||label.includes("overtime"))return v=>"$"+v.toLocaleString(undefined,{minimumFractionDigits:0,maximumFractionDigits:0});if(label.includes("%"))return v=>v.toFixed(1)+"%";if(label.includes("hour"))return v=>v.toFixed(1)+" hrs";return v=>v.toLocaleString();}
const LOCS=_RAW.map(l=>{l.kpis.forEach(k=>{k.fmt=_autoFmt(k.unit);});l.gauges.forEach(g=>{g.fmt=_gaugeFmt(g.label);});return l;});
let selected=0,editMode=false;
function metricColor(v,t,h){const r=v/t;if(h){if(r>1.05)return{bar:"#E24B4A",trend:"#E24B4A"};if(r>1)return{bar:"#EF9F27",trend:"#EF9F27"};return{bar:"#639922",trend:"#639922"};}else{if(r<.9)return{bar:"#E24B4A",trend:"#E24B4A"};if(r<.96)return{bar:"#EF9F27",trend:"#EF9F27"};return{bar:"#639922",trend:"#639922"};}}
function gaugeColor(v,mn,mx,t,h){const p=(v-mn)/(mx-mn),tp=(t-mn)/(mx-mn);if(h){if(p>tp*1.05)return{arc:"#E24B4A",needle:"#A32D2D"};if(p>tp)return{arc:"#EF9F27",needle:"#854F0B"};return{arc:"#639922",needle:"#27500A"};}else{if(p<tp*.88)return{arc:"#E24B4A",needle:"#A32D2D"};if(p<tp*.95)return{arc:"#EF9F27",needle:"#854F0B"};return{arc:"#639922",needle:"#27500A"};}}
function statusColor(s){return s==="ok"?"#639922":s==="watch"?"#EF9F27":"#E24B4A";}
function statusPill(s){const m={ok:{bg:"var(--green-bg)",color:"var(--green-txt)",label:"on track"},watch:{bg:"var(--amber-bg)",color:"var(--amber-txt)",label:"watch"},critical:{bg:"var(--red-bg)",color:"var(--red-txt)",label:"critical"}};return m[s]||m.watch;}
function dotColor(t){return t==="ok"?"#639922":t==="warn"?"#EF9F27":t==="bad"?"#E24B4A":"var(--border2)";}
function trendColor(t,h){if(!t)return"var(--text3)";const u=t[0]==="+";return(h&&u)||(!h&&!u)?"#E24B4A":"#639922";}
function drawMini(c,v,mn,mx,t,h){const d=devicePixelRatio||1,S=28;c.width=S*d;c.height=S*d;c.style.width=S+"px";c.style.height=S+"px";const x=c.getContext("2d");x.scale(d,d);const cx=S/2,cy=S*.64,r=S*.37,sA=Math.PI*1.1,eA=Math.PI*1.9,rng=eA-sA;x.lineCap="round";x.beginPath();x.arc(cx,cy,r,sA,eA);x.strokeStyle="rgba(0,0,0,0.09)";x.lineWidth=r*.24;x.stroke();const p=Math.max(0,Math.min(1,(v-mn)/(mx-mn))),col=gaugeColor(v,mn,mx,t,h);x.beginPath();x.arc(cx,cy,r,sA,sA+p*rng);x.strokeStyle=col.arc;x.lineWidth=r*.24;x.stroke();const nA=sA+p*rng;x.beginPath();x.moveTo(cx,cy);x.lineTo(cx+Math.cos(nA)*r*.7,cy+Math.sin(nA)*r*.7);x.strokeStyle=col.needle;x.lineWidth=r*.1;x.stroke();x.beginPath();x.arc(cx,cy,r*.14,0,Math.PI*2);x.fillStyle="#bbb";x.fill();}
function drawFull(c,v,mn,mx,t,h){const d=devicePixelRatio||1,W=c.parentElement.clientWidth||140,H=Math.round(W*.58);c.width=W*d;c.height=H*d;c.style.width="100%";c.style.height=H+"px";const x=c.getContext("2d");x.scale(d,d);const cx=W/2,cy=H*.82,r=Math.min(W,H*1.7)*.39,sA=Math.PI*1.1,eA=Math.PI*1.9,rng=eA-sA;x.lineCap="round";x.beginPath();x.arc(cx,cy,r,sA,eA);x.strokeStyle="rgba(0,0,0,0.08)";x.lineWidth=r*.18;x.stroke();const p=Math.max(0,Math.min(1,(v-mn)/(mx-mn))),col=gaugeColor(v,mn,mx,t,h);x.beginPath();x.arc(cx,cy,r,sA,sA+p*rng);x.strokeStyle=col.arc;x.lineWidth=r*.18;x.stroke();const tp=Math.max(0,Math.min(1,(t-mn)/(mx-mn))),tA=sA+tp*rng;x.beginPath();x.arc(cx+Math.cos(tA)*r,cy+Math.sin(tA)*r,r*.055,0,Math.PI*2);x.fillStyle="#555";x.fill();for(let i=0;i<=8;i++){const a=sA+(i/8)*rng;x.beginPath();x.moveTo(cx+Math.cos(a)*r*.74,cy+Math.sin(a)*r*.74);x.lineTo(cx+Math.cos(a)*r*.84,cy+Math.sin(a)*r*.84);x.strokeStyle="rgba(0,0,0,0.15)";x.lineWidth=i%4===0?1.5:.8;x.stroke();}const nA=sA+p*rng;x.beginPath();x.moveTo(cx,cy);x.lineTo(cx+Math.cos(nA)*r*.7,cy+Math.sin(nA)*r*.7);x.strokeStyle=col.needle;x.lineWidth=r*.055;x.stroke();x.beginPath();x.arc(cx,cy,r*.1,0,Math.PI*2);x.fillStyle="#ccc";x.fill();}
function buildSidebar(){document.getElementById("sidebar-list").innerHTML=LOCS.map(l=>'<div class="loc-item'+(l.id===selected?" selected":"")+'" onclick="selectLoc('+l.id+')"><span class="loc-dot" style="background:'+statusColor(l.status)+'"></span><div class="loc-info"><div class="loc-name">'+l.name+'</div><div class="loc-owner">'+l.owner+'</div></div><div class="mini-gauges">'+l.kpis.map((_,i)=>'<canvas id="mg-'+l.id+'-'+i+'"></canvas>').join("")+'</div></div>').join("");}
function renderMiniGauges(){LOCS.forEach(l=>{l.kpis.forEach((k,i)=>{const c=document.getElementById("mg-"+l.id+"-"+i);if(!c)return;const mn=k.unit==="%"?0:k.target*.4,mx=k.unit==="%"?(k.label.includes("food")||k.label.includes("labor")?55:100):k.target*1.6;drawMini(c,k.val,mn,mx,k.target,k.higherBad);});});}
function buildDetail(){const l=LOCS[selected],sp=statusPill(l.status);const kH=l.kpis.map(k=>{const c=metricColor(k.val,k.target,k.higherBad),bp=Math.min(100,Math.abs(k.val/k.target*100)).toFixed(0),tc=trendColor(k.trend,k.higherBad);return'<div class="kpi-card"><div class="kpi-top"><span class="kpi-lbl">'+k.label+'</span><span class="kpi-trend" style="color:'+tc+'">'+(k.trend||"")+'</span></div><div class="kpi-val">'+k.fmt(k.val)+'</div><div class="kpi-bar-bg"><div class="kpi-bar-fill" style="width:'+bp+'%;background:'+c.bar+'"></div></div><div class="kpi-target">target: '+k.fmt(k.target)+'</div></div>';}).join("");const gH=l.gauges.map((g,i)=>'<div class="gauge-card"><canvas id="fg-'+l.id+'-'+i+'" style="width:100%;display:block"></canvas><div class="gauge-val">'+g.fmt(g.val)+'</div><div class="gauge-lbl">'+g.label+'</div><div class="gauge-tgt">target: '+g.fmt(g.target)+'</div></div>').join("");const fH=l.flags.map(f=>'<div class="flag"><span class="fdot" style="background:'+dotColor(f.t)+'"></span><span>'+f.msg+'</span></div>').join("");document.getElementById("main-panel").innerHTML='<div class="detail-header"><div><div class="detail-name">'+l.name+'</div><div class="detail-owner">'+l.owner+'</div></div><span class="status-pill" style="background:'+sp.bg+';color:'+sp.color+'">'+sp.label+'</span></div><div><div class="section-label">Tier-1 KPIs — vs target</div><div class="kpi-grid">'+kH+'</div></div><div><div class="section-label">Operational gauges</div><div class="gauge-grid">'+gH+'</div></div><div class="flags-card"><div class="section-label" style="margin-bottom:4px">Flags &amp; actions</div>'+fH+'</div><div id="edit-section" style="display:'+(editMode?"block":"none")+'"><div class="section-label">Edit actuals — '+l.name+'</div>'+buildEditForm(l)+'</div>';requestAnimationFrame(()=>{l.gauges.forEach((g,i)=>{const c=document.getElementById("fg-"+l.id+"-"+i);if(c)drawFull(c,g.val,g.min,g.max,g.target,g.higherBad);});});}
function buildEditForm(l){const a=[...l.kpis.map((k,i)=>({key:"kpi-"+i,label:k.label,val:k.val,unit:k.unit})),...l.gauges.map((g,i)=>({key:"gauge-"+i,label:g.label,val:g.val,unit:g.unit||""}))];return'<div class="edit-grid">'+a.map(m=>'<div class="edit-card"><div class="edit-lbl">'+m.label+'</div><div class="edit-row"><input class="edit-inp" id="ei-'+l.id+'-'+m.key+'" type="number" step="0.1" value="'+m.val+'"><span class="edit-unit">'+m.unit+'</span></div></div>').join("")+'</div><div style="margin-top:12px;display:flex;gap:8px;align-items:center"><button class="save-btn" onclick="saveActuals('+l.id+')">Save actuals</button><span id="save-msg-'+l.id+'" style="font-size:11px;color:var(--green-txt);display:none">Saved!</span></div>';}
function saveActuals(id){const l=LOCS[id];l.kpis.forEach((k,i)=>{const e=document.getElementById("ei-"+id+"-kpi-"+i);if(e)k.val=parseFloat(e.value)||k.val;});l.gauges.forEach((g,i)=>{const e=document.getElementById("ei-"+id+"-gauge-"+i);if(e)g.val=parseFloat(e.value)||g.val;});const r=l.kpis.filter(k=>{const x=k.val/k.target;return k.higherBad?x>1.05:x<.9;}).length;l.status=r>=2?"critical":r===1?"watch":"ok";buildSidebar();renderMiniGauges();buildDetail();const m=document.getElementById("save-msg-"+id);if(m){m.style.display="inline";setTimeout(()=>{m.style.display="none";},2000);}}
function selectLoc(i){selected=i;buildSidebar();renderMiniGauges();buildDetail();}
function toggleEdit(){editMode=!editMode;const b=document.getElementById("edit-btn");b.classList.toggle("active",editMode);b.textContent=editMode?"Done editing":"Edit actuals";const e=document.getElementById("edit-section");if(e)e.style.display=editMode?"block":"none";}
function setPeriod(v){const l={wk:"''' + period_label + '''",ptd:"Period to date",ytd:"Year to date"};document.getElementById("period-badge").textContent=l[v]||"";}
buildSidebar();buildDetail();requestAnimationFrame(renderMiniGauges);
window.addEventListener("resize",()=>{renderMiniGauges();const l=LOCS[selected];l.gauges.forEach((g,i)=>{const c=document.getElementById("fg-"+l.id+"-"+i);if(c)drawFull(c,g.val,g.min,g.max,g.target,g.higherBad);});});
</script>
</body>
</html>''')


# ═══════════════════════════════════════════════════════
# ACCOUNTS RECEIVABLE SECTION
# ═══════════════════════════════════════════════════════

def _render_ar_section(conn, user):
    """Render Accounts Receivable — manual input + dashboard from DB."""
    from styles import empty_state

    username = user.get("username", "") if user else ""

    # ── Add / Edit Invoice Form ──
    with st.expander("Add / Edit Invoice", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            inv_num = st.text_input("Invoice Number", key="ar_inv_num")
            due_dt = st.date_input("Due Date", value=date.today(), key="ar_due_date")
        with c2:
            total_val = st.number_input("Total ($)", min_value=0.0, format="%.2f", key="ar_total")
            current_val = st.number_input("Current ($)", min_value=0.0, format="%.2f", key="ar_current")

        d1, d2, d3 = st.columns(3)
        with d1:
            d_0_30 = st.number_input("0-30 Days ($)", min_value=0.0, format="%.2f", key="ar_0_30")
            d_31_60 = st.number_input("31-60 Days ($)", min_value=0.0, format="%.2f", key="ar_31_60")
        with d2:
            d_61_90 = st.number_input("61-90 Days ($)", min_value=0.0, format="%.2f", key="ar_61_90")
            d_91_120 = st.number_input("91-120 Days ($)", min_value=0.0, format="%.2f", key="ar_91_120")
        with d3:
            d_121_150 = st.number_input("121-150 Days ($)", min_value=0.0, format="%.2f", key="ar_121_150")
            d_151_plus = st.number_input("151+ Days ($)", min_value=0.0, format="%.2f", key="ar_151_plus")

        if st.button("Save Invoice", key="ar_save", type="primary", use_container_width=True):
            if not inv_num.strip():
                st.warning("Please enter an invoice number.")
            else:
                db.upsert_ar_invoice(
                    conn, inv_num.strip(), due_dt.isoformat(), total_val, current_val,
                    d_0_30, d_31_60, d_61_90, d_91_120, d_121_150, d_151_plus, username,
                )
                st.success("Invoice {} saved.".format(inv_num.strip()))
                st.rerun()

    # ── Load data from DB ──
    rows = db.fetch_ar_invoices(conn)

    if not rows:
        empty_state(
            "No AR invoices yet",
            "Use the form above to add invoice data.",
        )
        return

    alma = pd.DataFrame(rows)

    # ── KPIs ──
    total_unpaid = alma["total"].sum()
    total_current = alma["current_amount"].sum()
    total_overdue = total_unpaid - total_current
    overdue_0_30 = alma["days_0_30"].sum()
    overdue_31_60 = alma["days_31_60"].sum()
    overdue_61_90 = alma["days_61_90"].sum()
    overdue_91_plus = alma["days_91_120"].sum() + alma["days_121_150"].sum() + alma["days_151_plus"].sum()
    overdue_30_plus = overdue_31_60 + overdue_61_90 + overdue_91_plus
    num_invoices = len(alma)
    num_overdue = len(alma[alma["total"] - alma["current_amount"] > 0])

    dash_section_header("Alma College — Accounts Receivable", "{} invoices".format(num_invoices))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card(
            "Total Unpaid", fmt_dollar(total_unpaid),
            change="{} invoices".format(num_invoices), accent="blue",
            badge_text=str(num_invoices), badge_bg="#EFF6FF", badge_color="#3B82F6",
        )
    with k2:
        dash_kpi_card(
            "Current", fmt_dollar(total_current),
            change="{:.0f}% of total".format(
                total_current / total_unpaid * 100) if total_unpaid else "",
            accent="green",
            badge_text="{:.0f}%".format(
                total_current / total_unpaid * 100) if total_unpaid else "0%",
            badge_bg="#F0FDF4", badge_color="#16A34A",
        )
    with k3:
        dash_kpi_card(
            "Overdue", fmt_dollar(total_overdue),
            change="{} overdue invoices".format(num_overdue), accent="amber",
            badge_text="{:.0f}%".format(
                total_overdue / total_unpaid * 100) if total_unpaid else "0%",
            badge_bg="#FEF3C7", badge_color="#D97706",
        )
    with k4:
        dash_kpi_card(
            "Overdue 30+ Days", fmt_dollar(overdue_30_plus),
            accent="red",
            badge_text="{:.0f}%".format(
                overdue_30_plus / total_unpaid * 100) if total_unpaid else "0%",
            badge_bg="#FEF2F2", badge_color="#EF4444",
        )

    # ── Charts Row ──
    r1, r2 = st.columns([3, 2])

    with r1:
        dash_chart_start("AR Aging Breakdown", "Amount by aging bucket")
        buckets = ["Current", "0-30 Days", "31-60 Days", "61-90 Days", "91+ Days"]
        values = [total_current, overdue_0_30, overdue_31_60, overdue_61_90, overdue_91_plus]
        colors = ["#3B82F6", "#16A34A", "#F59E0B", "#EF4444", "#7C3AED"]

        fig = go.Figure(data=[go.Bar(
            x=buckets, y=values, marker_color=colors,
            texttemplate="$%{y:,.0f}", textposition="outside",
            hovertemplate="<b>%{x}</b><br>Amount: $%{y:,.0f}<extra></extra>",
        )])
        fig.update_layout(showlegend=False, height=380)
        _apply_theme(fig, height=380)
        fig.update_xaxes(tickfont=dict(size=12, color="#1E293B", family="Inter, sans-serif"), showgrid=False)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True)
        dash_chart_end()

    with r2:
        dash_chart_start("Aging Distribution", "Share by bucket")
        pie_labels, pie_values, pie_colors_list = [], [], []
        for lbl, val, clr in zip(buckets, values, colors):
            if val > 0:
                pie_labels.append(lbl)
                pie_values.append(val)
                pie_colors_list.append(clr)
        if pie_values:
            fig2 = go.Figure(data=[go.Pie(
                labels=pie_labels, values=pie_values, hole=0.55,
                marker=dict(colors=pie_colors_list, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent", textposition="outside",
                textfont=dict(size=10, family="Inter, sans-serif"),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                sort=False,
            )])
            fig2.update_layout(
                showlegend=False, height=380,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=13, color="#64748B"),
                hoverlabel=dict(bgcolor="#1F2A44", font_size=12,
                                font_family="Inter, sans-serif", font_color="#FFFFFF",
                                bordercolor="#C7A462"),
                annotations=[dict(text="Aging<br>Split", x=0.5, y=0.5, font_size=14,
                                   font_color="#1E293B", font_family="Inter, sans-serif",
                                   showarrow=False)],
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No aging data to display.")
        dash_chart_end()

    # ── Invoice Detail Table with Delete ──
    dash_chart_start("Invoice Details", "All invoices — click delete to remove")

    detail = alma[["id", "invoice_number", "due_date", "total", "current_amount",
                    "days_0_30", "days_31_60", "days_61_90", "days_91_120",
                    "days_121_150", "days_151_plus"]].copy()
    detail.columns = [
        "ID", "Invoice #", "Due Date", "Total", "Current", "0-30 Days",
        "31-60 Days", "61-90 Days", "91-120 Days", "121-150 Days", "151+ Days",
    ]
    detail = detail.sort_values("Total", ascending=False)

    dollar_cols = ["Total", "Current", "0-30 Days", "31-60 Days",
                   "61-90 Days", "91-120 Days", "121-150 Days", "151+ Days"]
    fmt_dict = {c: "${:,.2f}".format for c in dollar_cols}

    def _highlight_overdue(val):
        if isinstance(val, (int, float)) and val > 0:
            return "color: #DC2626; font-weight: 600;"
        return ""

    display = detail.drop(columns=["ID"])
    styled = display.style.format(fmt_dict).map(
        _highlight_overdue,
        subset=["31-60 Days", "61-90 Days", "91-120 Days", "121-150 Days", "151+ Days"],
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

    # Delete by invoice number
    with st.popover("Delete an invoice"):
        inv_ids = detail[["ID", "Invoice #"]].values.tolist()
        if inv_ids:
            options = {"{} (ID: {})".format(inv, iid): iid for iid, inv in inv_ids}
            selected = st.selectbox("Select invoice to delete", list(options.keys()), key="ar_del_select")
            if st.button("Delete", key="ar_del_btn", type="primary"):
                db.delete_ar_invoice(conn, options[selected])
                st.success("Deleted.")
                st.rerun()

    dash_chart_end()


# ═══════════════════════════════════════════════════════
# MEAL PLAN TRACKER SECTION
# ═══════════════════════════════════════════════════════


def _parse_meal_plan_excel(file_bytes, sheet_name="4068 - Alma"):
    """Parse the Meal Plan Tracker Excel for Alma College.

    Returns list of dicts ready for DB insert, or None on failure.
    Each dict: {semester, section, plan_name, budgeted_daily_rate, actual_daily_rate,
                flex_amount, budgeted_plans, actual_plans, budgeted_revenue,
                actual_revenue, budgeted_flex, actual_flex}
    """
    from io import BytesIO
    try:
        xl = pd.ExcelFile(BytesIO(file_bytes))
        if sheet_name not in xl.sheet_names:
            # Try partial match
            matches = [s for s in xl.sheet_names if "Alma" in s or "4068" in s]
            if matches:
                sheet_name = matches[0]
            else:
                return None
        df = pd.read_excel(xl, sheet_name, header=None)
    except Exception:
        return None

    rows = []

    def _safe_float(v, default=0.0):
        try:
            if pd.isna(v):
                return default
            return float(v)
        except (ValueError, TypeError):
            return default

    def _safe_int(v, default=0):
        try:
            if pd.isna(v):
                return default
            return int(float(v))
        except (ValueError, TypeError):
            return default

    # The sheet has two halves — Fall (rows ~0-54) and Spring (rows ~55-108)
    # Each half has: Resident plans, Commuter plans, Additional Flex
    # Detect semester boundaries by looking for "Board Days" in column 1
    semester_starts = []
    for i in range(len(df)):
        val = df.iloc[i, 1]
        if pd.notna(val) and str(val).strip() == "Board Days":
            semester_starts.append(i)

    semester_labels = ["Fall", "Spring"]

    for sem_idx, start_row in enumerate(semester_starts):
        semester = semester_labels[sem_idx] if sem_idx < len(semester_labels) else "Semester {}".format(sem_idx + 1)

        # Find section headers within this semester block
        end_row = semester_starts[sem_idx + 1] if sem_idx + 1 < len(semester_starts) else len(df)

        current_section = None
        for i in range(start_row, end_row):
            label = df.iloc[i, 1]
            if pd.isna(label):
                continue
            label_str = str(label).strip()

            # Detect section headers
            if label_str == "Resident Meal Plan":
                current_section = "Resident"
                continue
            if label_str == "Commuter Meal Plan":
                current_section = "Commuter"
                continue
            if label_str == "Additional Flex Sales":
                current_section = "Additional Flex"
                continue

            # Skip header rows and summary rows
            if label_str in ("Board Days", "Budgeted Daily Rate", "Budgeted Rate",
                             "Flex $ Amount", ""):
                continue

            # Parse plan rows
            if current_section in ("Resident", "Commuter"):
                plan_name = label_str
                if "Plan" not in plan_name and "Block" not in plan_name and "Meals" not in plan_name:
                    continue
                rows.append({
                    "semester": semester,
                    "section": current_section,
                    "plan_name": plan_name,
                    "budgeted_daily_rate": _safe_float(df.iloc[i, 2]),
                    "actual_daily_rate": _safe_float(df.iloc[i, 3]),
                    "flex_amount": _safe_float(df.iloc[i, 4]),
                    "budgeted_plans": _safe_int(df.iloc[i, 5]),
                    "actual_plans": _safe_int(df.iloc[i, 6]),
                    "budgeted_revenue": _safe_float(df.iloc[i, 7]),
                    "actual_revenue": _safe_float(df.iloc[i, 8]),
                    "budgeted_flex": _safe_float(df.iloc[i, 10]),
                    "actual_flex": _safe_float(df.iloc[i, 11]),
                })
            elif current_section == "Additional Flex":
                plan_name = label_str
                if plan_name in ("", "NaN") or plan_name.startswith("#"):
                    continue
                rows.append({
                    "semester": semester,
                    "section": "Additional Flex",
                    "plan_name": plan_name,
                    "budgeted_daily_rate": 0,
                    "actual_daily_rate": 0,
                    "flex_amount": _safe_float(df.iloc[i, 2]),
                    "budgeted_plans": _safe_int(df.iloc[i, 3]),
                    "actual_plans": _safe_int(df.iloc[i, 4]),
                    "budgeted_revenue": _safe_float(df.iloc[i, 5]),
                    "actual_revenue": _safe_float(df.iloc[i, 6]),
                    "budgeted_flex": 0,
                    "actual_flex": 0,
                })

    return rows if rows else None


def _render_meal_plan_tracker(conn, user):
    """Render Meal Plan Tracker — upload Excel or view from DB."""
    from styles import empty_state

    username = user.get("username", "") if user else ""

    # ── Upload ──
    uploaded = st.file_uploader(
        "Upload Meal Plan Tracker (.xlsx)",
        type=["xlsx", "xls"],
        key="mpt_upload",
        help="Upload the Meal Plan Tracker Excel. Alma College data will be extracted automatically.",
    )

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        parsed = _parse_meal_plan_excel(file_bytes)
        if parsed:
            # Determine semesters in parsed data
            semesters = list(set(r["semester"] for r in parsed))
            for sem in semesters:
                db.clear_meal_plan_tracker(conn, sem)
            for r in parsed:
                db.upsert_meal_plan_row(
                    conn, r["semester"], r["section"], r["plan_name"],
                    r["budgeted_daily_rate"], r["actual_daily_rate"], r["flex_amount"],
                    r["budgeted_plans"], r["actual_plans"],
                    r["budgeted_revenue"], r["actual_revenue"],
                    r["budgeted_flex"], r["actual_flex"], username,
                )
            st.success("Imported {} plan rows for {}.".format(len(parsed), ", ".join(semesters)))
            st.rerun()
        else:
            st.error("Could not find Alma College data in this file.")

    # ── Load from DB ──
    semesters = db.fetch_meal_plan_tracker_semesters(conn)
    if not semesters:
        empty_state(
            "No meal plan data yet",
            "Upload your Meal Plan Tracker Excel above to get started.",
        )
        return

    # Semester selector
    selected_sem = st.radio("Semester", semesters, horizontal=True, key="mpt_sem")
    rows = db.fetch_meal_plan_tracker(conn, selected_sem)

    if not rows:
        empty_state("No data for this semester.")
        return

    mpt_df = pd.DataFrame(rows)

    # ── KPIs ──
    total_budgeted_rev = mpt_df["budgeted_revenue"].sum() + mpt_df["budgeted_flex"].sum()
    total_actual_rev = mpt_df["actual_revenue"].sum() + mpt_df["actual_flex"].sum()
    total_variance = total_actual_rev - total_budgeted_rev
    total_budgeted_plans = mpt_df["budgeted_plans"].sum()
    total_actual_plans = mpt_df["actual_plans"].sum()
    plans_variance = total_actual_plans - total_budgeted_plans

    var_pct = (total_variance / total_budgeted_rev * 100) if total_budgeted_rev else 0
    var_sign = "+" if total_variance >= 0 else ""

    dash_section_header(
        "Alma College — {} Meal Plans".format(selected_sem),
        "{} plan types".format(len(mpt_df)),
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card(
            "Budgeted Revenue", fmt_dollar(total_budgeted_rev),
            accent="blue",
            badge_text=str(len(mpt_df)), badge_bg="#EFF6FF", badge_color="#3B82F6",
        )
    with k2:
        dash_kpi_card(
            "Actual Revenue", fmt_dollar(total_actual_rev),
            accent="green" if total_actual_rev >= total_budgeted_rev else "red",
            badge_text="{}{:.1f}%".format(var_sign, var_pct),
            badge_bg="#F0FDF4" if total_variance >= 0 else "#FEF2F2",
            badge_color="#16A34A" if total_variance >= 0 else "#EF4444",
        )
    with k3:
        dash_kpi_card(
            "Variance", "{}{}".format(var_sign, fmt_dollar(total_variance)),
            change="{}{:.1f}% vs budget".format(var_sign, var_pct),
            accent="green" if total_variance >= 0 else "red",
        )
    with k4:
        plan_sign = "+" if plans_variance >= 0 else ""
        dash_kpi_card(
            "Total Plans", "{:,}".format(total_actual_plans),
            change="{}{:,} vs budget ({:,})".format(plan_sign, plans_variance, total_budgeted_plans),
            accent="purple",
            badge_text="{}{:,}".format(plan_sign, plans_variance),
            badge_bg="#F5F3FF" if plans_variance >= 0 else "#FEF2F2",
            badge_color="#7C3AED" if plans_variance >= 0 else "#EF4444",
        )

    # ── Charts ──
    r1, r2 = st.columns([3, 2])

    with r1:
        dash_chart_start("Budget vs Actual by Plan", "Revenue comparison")
        # Group by section for cleaner chart
        chart_data = mpt_df[mpt_df["budgeted_revenue"] > 0].copy()
        if not chart_data.empty:
            chart_data["short_name"] = chart_data["plan_name"].str[:20]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=chart_data["short_name"], x=chart_data["budgeted_revenue"],
                name="Budget", orientation="h", marker_color="#1F2A44",
                hovertemplate="<b>%{y}</b><br>Budget: $%{x:,.0f}<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                y=chart_data["short_name"], x=chart_data["actual_revenue"],
                name="Actual", orientation="h", marker_color="#C7A462",
                hovertemplate="<b>%{y}</b><br>Actual: $%{x:,.0f}<extra></extra>",
            ))
            fig.update_layout(barmode="group", height=420, showlegend=True)
            _apply_theme(fig, height=420)
            fig.update_xaxes(visible=False)
            fig.update_yaxes(
                tickfont=dict(size=11, color="#1E293B"),
                showgrid=False, autorange="reversed",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No revenue data to chart.")
        dash_chart_end()

    with r2:
        dash_chart_start("Revenue Split", "By section")
        section_totals = mpt_df.groupby("section").agg(
            actual=("actual_revenue", "sum"),
            flex=("actual_flex", "sum"),
        ).reset_index()
        section_totals["total"] = section_totals["actual"] + section_totals["flex"]
        section_totals = section_totals[section_totals["total"] > 0]

        if not section_totals.empty:
            pie_colors = ["#1F2A44", "#3B82F6", "#C7A462", "#16A34A"]
            fig2 = go.Figure(data=[go.Pie(
                labels=section_totals["section"],
                values=section_totals["total"],
                hole=0.55,
                marker=dict(colors=pie_colors[:len(section_totals)],
                            line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                textposition="outside",
                textfont=dict(size=10, family="Inter, sans-serif"),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                sort=False,
            )])
            fig2.update_layout(
                showlegend=False, height=420,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=13, color="#64748B"),
                hoverlabel=dict(bgcolor="#1F2A44", font_size=12,
                                font_family="Inter, sans-serif", font_color="#FFFFFF",
                                bordercolor="#C7A462"),
                annotations=[dict(text="Revenue<br>Split", x=0.5, y=0.5, font_size=14,
                                   font_color="#1E293B", font_family="Inter, sans-serif",
                                   showarrow=False)],
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No data to chart.")
        dash_chart_end()

    # ── Enrollment chart ──
    enroll_data = mpt_df[mpt_df["budgeted_plans"] > 0].copy()
    if not enroll_data.empty:
        dash_chart_start("Plan Enrollment", "Budgeted vs Actual count")
        enroll_data["short_name"] = enroll_data["plan_name"].str[:20]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=enroll_data["short_name"], y=enroll_data["budgeted_plans"],
            name="Budgeted", marker_color="#1F2A44",
            texttemplate="%{y}", textposition="outside",
            hovertemplate="<b>%{x}</b><br>Budgeted: %{y}<extra></extra>",
        ))
        fig3.add_trace(go.Bar(
            x=enroll_data["short_name"], y=enroll_data["actual_plans"],
            name="Actual", marker_color="#C7A462",
            texttemplate="%{y}", textposition="outside",
            hovertemplate="<b>%{x}</b><br>Actual: %{y}<extra></extra>",
        ))
        fig3.update_layout(barmode="group", height=380, showlegend=True)
        _apply_theme(fig3, height=380)
        fig3.update_xaxes(tickfont=dict(size=10, color="#1E293B"), tickangle=-30)
        fig3.update_yaxes(visible=False)
        st.plotly_chart(fig3, use_container_width=True)
        dash_chart_end()

    # ── Detail Table ──
    dash_chart_start("Plan Details", "All plans — editable in DB")

    detail = mpt_df[["section", "plan_name", "budgeted_plans", "actual_plans",
                      "budgeted_revenue", "actual_revenue",
                      "budgeted_flex", "actual_flex"]].copy()
    detail["revenue_variance"] = detail["actual_revenue"] - detail["budgeted_revenue"]
    detail["flex_variance"] = detail["actual_flex"] - detail["budgeted_flex"]
    detail.columns = [
        "Section", "Plan", "Bud. Plans", "Act. Plans",
        "Bud. Revenue", "Act. Revenue", "Bud. Flex", "Act. Flex",
        "Rev. Variance", "Flex Variance",
    ]

    dollar_cols = ["Bud. Revenue", "Act. Revenue", "Bud. Flex", "Act. Flex",
                   "Rev. Variance", "Flex Variance"]
    fmt_dict = {c: "${:,.0f}".format for c in dollar_cols}
    fmt_dict["Bud. Plans"] = "{:,}".format
    fmt_dict["Act. Plans"] = "{:,}".format

    def _color_variance(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: #16A34A; font-weight: 600;"
            elif val < 0:
                return "color: #DC2626; font-weight: 600;"
        return ""

    styled = detail.style.format(fmt_dict).map(
        _color_variance, subset=["Rev. Variance", "Flex Variance"],
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)
    dash_chart_end()


# ═══════════════════════════════════════════════════════
# DIGITAL MEAL COUNTS
# ═══════════════════════════════════════════════════════


def _render_digital_meal_counts(conn):
    """Render Digital Meal Counts — Board (Hamilton Commons)."""
    from meal_counts_parser import get_weekly_summary, get_daily_detail

    weeks = get_weekly_summary(conn, location="Board")
    if not weeks:
        st.caption("No meal count data imported yet. Upload the Digital Meal Counts Excel in Data Import.")
        return

    # Week navigation — Prev / label / Next
    if "mc_week_idx" not in st.session_state:
        st.session_state.mc_week_idx = len(weeks) - 1

    idx = st.session_state.mc_week_idx
    idx = max(0, min(idx, len(weeks) - 1))

    col_prev, col_label, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀ Prev Week", key="mc_prev", disabled=(idx == 0)):
            st.session_state.mc_week_idx = idx - 1
            st.rerun()
    with col_next:
        if st.button("Next Week ▶", key="mc_next", disabled=(idx >= len(weeks) - 1)):
            st.session_state.mc_week_idx = idx + 1
            st.rerun()
    with col_label:
        sel = weeks[idx]
        from datetime import datetime as _dt
        try:
            ws = _dt.strptime(sel["week_start"], "%Y-%m-%d")
            we = _dt.strptime(sel["week_end"], "%Y-%m-%d")
            label = "{} — {}".format(ws.strftime("%b %d"), we.strftime("%b %d, %Y"))
        except Exception:
            label = "{} → {}".format(sel["week_start"], sel["week_end"])
        st.markdown(
            '<div style="text-align:center;padding:8px 0;">'
            '<div style="font-size:18px;font-weight:700;color:#1E293B;">{}</div>'
            '<div style="font-size:12px;color:#94A3B8;margin-top:2px;">{}</div>'
            '</div>'.format(label, sel["sheet_name"]),
            unsafe_allow_html=True,
        )

    sel = weeks[idx]

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card("Total Meals", "{:,}".format(sel["total"]), accent="navy")
    with k2:
        dash_kpi_card("Breakfast", "{:,}".format(sel["breakfast"]), accent="green")
    with k3:
        dash_kpi_card("Lunch", "{:,}".format(sel["lunch"]), accent="gold")
    with k4:
        dash_kpi_card("Dinner", "{:,}".format(sel["dinner"]), accent="blue")

    # Daily detail table
    daily = get_daily_detail(conn, sel["week_start"], sel["week_end"])
    if daily:
        st.markdown(
            '<div style="font-size:14px;font-weight:600;color:#1E293B;'
            'margin:16px 0 8px;">Daily Breakdown</div>',
            unsafe_allow_html=True,
        )
        table_data = []
        for d in daily:
            table_data.append({
                "Date": d["date"],
                "Day": d["day_name"],
                "Breakfast": d["total_breakfast"],
                "Lunch": d["total_lunch"],
                "Dinner": d["total_dinner"],
                "Total": d["total_day"],
                "Admission": d["admission"],
                "Special": d["special_groups"],
                "Weather": d["weather"],
            })
        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
        )

        # Chart — stacked bar by meal service
        dash_chart_start("Meals by Service", "Breakfast / Lunch / Dinner")
        chart_df = pd.DataFrame(table_data)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_df["Date"], y=chart_df["Breakfast"],
            name="Breakfast", marker_color="#16A34A",
        ))
        fig.add_trace(go.Bar(
            x=chart_df["Date"], y=chart_df["Lunch"],
            name="Lunch", marker_color="#C7A462",
        ))
        fig.add_trace(go.Bar(
            x=chart_df["Date"], y=chart_df["Dinner"],
            name="Dinner", marker_color="#1F2A44",
        ))
        fig.update_layout(barmode="stack", height=320)
        _apply_theme(fig, height=320)
        fig.update_xaxes(tickformat="%a %b %d")
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
        dash_chart_end()

    # Weekly trend chart (all weeks)
    if len(weeks) > 1:
        dash_chart_start("Weekly Trend", "Total meals over time")
        trend_df = pd.DataFrame(weeks)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=trend_df["week_start"], y=trend_df["breakfast"],
            name="Breakfast", marker_color="#16A34A",
        ))
        fig.add_trace(go.Bar(
            x=trend_df["week_start"], y=trend_df["lunch"],
            name="Lunch", marker_color="#C7A462",
        ))
        fig.add_trace(go.Bar(
            x=trend_df["week_start"], y=trend_df["dinner"],
            name="Dinner", marker_color="#1F2A44",
        ))
        fig.add_trace(go.Scatter(
            x=trend_df["week_start"], y=trend_df["total"],
            name="Total", mode="lines+markers",
            line=dict(color="#3B82F6", width=2),
            marker=dict(size=6),
        ))
        fig.update_layout(barmode="stack", height=320)
        _apply_theme(fig, height=320)
        fig.update_xaxes(tickformat="%b %d")
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
        dash_chart_end()


# ═══════════════════════════════════════════════════════
# TENDER TOTALS
# ═══════════════════════════════════════════════════════


_TERMINAL_COLORS = {
    "Hamilton 04": "#1F2A44",
    "SIM - Loch Lomond": "#16A34A",
    "SIM - Qdoba": "#3B82F6",
    "Starbucks04 Epic": "#C7A462",
}


def _render_tender_totals(conn):
    """Render Tender Totals by Terminal — daily view."""
    # Ensure tables exist
    from odyssey_parser import init_odyssey_tables
    init_odyssey_tables(conn)

    # Fetch all available report dates
    dates = conn.execute(
        """SELECT DISTINCT report_date FROM odyssey_tender_totals
           ORDER BY report_date DESC"""
    ).fetchall()

    if not dates:
        st.caption("No tender totals data yet. Reports auto-import from Gmail when they arrive.")
        return

    date_list = [d[0] for d in dates]

    # Date selector with Prev/Next nav
    if "tt_date_idx" not in st.session_state:
        st.session_state.tt_date_idx = 0

    idx = max(0, min(st.session_state.tt_date_idx, len(date_list) - 1))
    selected_date = date_list[idx]

    c_prev, c_mid, c_next = st.columns([1, 4, 1])
    with c_prev:
        if st.button("◀ Prev Day", key="tt_prev", disabled=(idx >= len(date_list) - 1)):
            st.session_state.tt_date_idx = idx + 1
            st.rerun()
    with c_next:
        if st.button("Next Day ▶", key="tt_next", disabled=(idx == 0)):
            st.session_state.tt_date_idx = idx - 1
            st.rerun()
    with c_mid:
        from datetime import datetime as _dt
        try:
            d_obj = _dt.strptime(selected_date, "%Y-%m-%d")
            label = d_obj.strftime("%A, %B %d, %Y")
        except Exception:
            label = selected_date
        st.markdown(
            '<div style="text-align:center;padding:8px 0;">'
            '<div style="font-size:18px;font-weight:700;color:#1E293B;">{}</div>'
            '<div style="font-size:11px;color:#94A3B8;margin-top:2px;'
            'text-transform:uppercase;letter-spacing:.08em;">Report Date</div>'
            '</div>'.format(label),
            unsafe_allow_html=True,
        )

    # Fetch data for selected date
    rows = conn.execute(
        """SELECT terminal, service_period, board_count, points_count, bonpts_count
           FROM odyssey_tender_totals
           WHERE report_date = ?
           ORDER BY terminal, service_period""",
        (selected_date,)
    ).fetchall()

    if not rows:
        st.caption("No data for this date.")
        return

    # Aggregate totals
    total_board = sum(r["board_count"] for r in rows)
    total_points = sum(r["points_count"] for r in rows)
    total_bonpts = sum(r["bonpts_count"] for r in rows)
    grand_total = total_board + total_points + total_bonpts

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card("Total Transactions", "{:,}".format(grand_total), accent="navy")
    with k2:
        dash_kpi_card("Board", "{:,}".format(total_board), accent="gold")
    with k3:
        dash_kpi_card("Points", "{:,}".format(total_points), accent="blue")
    with k4:
        dash_kpi_card("Bonus Points", "{:,}".format(total_bonpts), accent="green")

    # Terminal breakdown
    terminals_set = sorted(set(r["terminal"] for r in rows))
    terminal_cols = st.columns(len(terminals_set))

    for i, term in enumerate(terminals_set):
        term_rows = [r for r in rows if r["terminal"] == term]
        term_board = sum(r["board_count"] for r in term_rows)
        term_points = sum(r["points_count"] for r in term_rows)
        term_bonpts = sum(r["bonpts_count"] for r in term_rows)
        term_total = term_board + term_points + term_bonpts
        color = _TERMINAL_COLORS.get(term, "#64748B")

        with terminal_cols[i]:
            st.markdown(
                '<div style="background:#fff;border:1px solid #E5E7EB;'
                'border-left:3px solid {};border-radius:10px;padding:14px 16px;'
                'height:100%;">'
                '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                'letter-spacing:.08em;font-weight:600;margin-bottom:6px;">{}</div>'
                '<div style="font-size:22px;font-weight:700;color:#1E293B;'
                'margin-bottom:4px;">{:,}</div>'
                '<div style="font-size:11px;color:#94A3B8;">'
                'B: <b>{:,}</b> · P: <b>{:,}</b> · BP: <b>{:,}</b></div>'
                '</div>'.format(color, term, term_total,
                                term_board, term_points, term_bonpts),
                unsafe_allow_html=True,
            )

    # Table
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:#1E293B;'
        'margin:20px 0 8px;">Breakdown by Service Period</div>',
        unsafe_allow_html=True,
    )
    df = pd.DataFrame([dict(r) for r in rows])
    df["total"] = df["board_count"] + df["points_count"] + df["bonpts_count"]
    display = df[[
        "terminal", "service_period", "board_count",
        "points_count", "bonpts_count", "total"
    ]].copy()
    display.columns = ["Terminal", "Service Period", "Board", "Points", "Bonus Pts", "Total"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    # Chart — stacked bar by terminal
    dash_chart_start("Transactions by Terminal", "Board / Points / Bonus Points")
    fig = go.Figure()
    term_agg = df.groupby("terminal").agg({
        "board_count": "sum", "points_count": "sum", "bonpts_count": "sum"
    }).reset_index()
    fig.add_trace(go.Bar(
        x=term_agg["terminal"], y=term_agg["board_count"],
        name="Board", marker_color="#1F2A44",
    ))
    fig.add_trace(go.Bar(
        x=term_agg["terminal"], y=term_agg["points_count"],
        name="Points", marker_color="#3B82F6",
    ))
    fig.add_trace(go.Bar(
        x=term_agg["terminal"], y=term_agg["bonpts_count"],
        name="Bonus Points", marker_color="#16A34A",
    ))
    fig.update_layout(barmode="stack", height=320)
    _apply_theme(fig, height=320)
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False})
    dash_chart_end()

    # Multi-day trend if we have > 1 day of data
    if len(date_list) > 1:
        trend_rows = conn.execute(
            """SELECT report_date,
                      SUM(board_count) as board,
                      SUM(points_count) as points,
                      SUM(bonpts_count) as bonpts
               FROM odyssey_tender_totals
               GROUP BY report_date
               ORDER BY report_date"""
        ).fetchall()
        trend_df = pd.DataFrame([dict(r) for r in trend_rows])
        trend_df["total"] = trend_df["board"] + trend_df["points"] + trend_df["bonpts"]

        dash_chart_start("Daily Trend", "All available days")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=trend_df["report_date"], y=trend_df["board"],
            name="Board", marker_color="#1F2A44",
        ))
        fig.add_trace(go.Bar(
            x=trend_df["report_date"], y=trend_df["points"],
            name="Points", marker_color="#3B82F6",
        ))
        fig.add_trace(go.Bar(
            x=trend_df["report_date"], y=trend_df["bonpts"],
            name="Bonus Points", marker_color="#16A34A",
        ))
        fig.add_trace(go.Scatter(
            x=trend_df["report_date"], y=trend_df["total"],
            name="Total", mode="lines+markers",
            line=dict(color="#EF4444", width=2),
            marker=dict(size=6),
        ))
        fig.update_layout(barmode="stack", height=320)
        _apply_theme(fig, height=320)
        fig.update_xaxes(tickformat="%b %d")
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
        dash_chart_end()


# ═══════════════════════════════════════════════════════
# EXPORT SECTION
# ═══════════════════════════════════════════════════════


def _render_export_section(conn, today):
    """Render export options."""
    dash_section_header("Export Data", "Download reports as CSV")

    export_type = st.selectbox("Export Type", [
        "Approved Budgets",
        "Weekly Financials",
        "Daily Sales",
        "Food Cost",
        "Meal Plan",
    ], key="dash_export_type")

    ex1, ex2 = st.columns(2)
    with ex1:
        export_start = st.date_input("From", db.get_week_start(today) - timedelta(weeks=4), key="exp_start")
    with ex2:
        export_end = st.date_input("To", today, key="exp_end")

    if st.button("Export CSV", key="dash_export_btn"):
        if export_type == "Approved Budgets":
            start_str = db.get_week_start(export_start).isoformat()
            end_str = db.get_week_start(export_end).isoformat()
            rows = conn.execute(
                """SELECT week_start, department, revenue, labor_dollars, labor_hours,
                          status, version, submitted_by, submitted_at, approved_by, approved_at
                   FROM budgets
                   WHERE status='Approved' AND week_start>=? AND week_start<=?
                   ORDER BY week_start, department""",
                (start_str, end_str),
            ).fetchall()
            if rows:
                export_df = pd.DataFrame([dict(r) for r in rows])
                csv = export_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "approved_budgets.csv", "text/csv",
                                   key="dl_budgets")
            else:
                st.warning("No approved budgets in selected range.")

        elif export_type == "Weekly Financials":
            start_str = db.get_week_start(export_start).isoformat()
            end_str = db.get_week_start(export_end).isoformat()
            rows = conn.execute(
                """SELECT * FROM weekly_financials
                   WHERE week_start>=? AND week_start<=?
                   ORDER BY week_start, department""",
                (start_str, end_str),
            ).fetchall()
            if rows:
                export_df = pd.DataFrame([dict(r) for r in rows])
                csv = export_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "weekly_financials.csv", "text/csv",
                                   key="dl_wfin")
            else:
                st.warning("No weekly financial data in selected range.")

        elif export_type == "Daily Sales":
            start_str = export_start.isoformat()
            end_str = export_end.isoformat()
            all_sales = db.fetch_daily_sales_range(conn, start_str, end_str)
            if all_sales:
                export_df = pd.DataFrame(all_sales)
                csv = export_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "daily_sales.csv", "text/csv",
                                   key="dl_dsales")
            else:
                st.warning("No daily sales data in selected range.")

        elif export_type == "Food Cost":
            start_str = export_start.isoformat()
            end_str = export_end.isoformat()
            food_rows = db.fetch_food_cost_range(conn, start_str, end_str)
            if food_rows:
                export_df = pd.DataFrame(food_rows)
                csv = export_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "food_cost.csv", "text/csv",
                                   key="dl_foodcost")
            else:
                st.warning("No food cost data in selected range.")

        elif export_type == "Meal Plan":
            start_str = export_start.isoformat()
            end_str = export_end.isoformat()
            meal_rows = db.fetch_meal_plan_range(conn, start_str, end_str)
            if meal_rows:
                export_df = pd.DataFrame(meal_rows)
                csv = export_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "meal_plan.csv", "text/csv",
                                   key="dl_mealplan")
            else:
                st.warning("No meal plan data in selected range.")
