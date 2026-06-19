"""
Operations Dashboard — premium corporate layout.
Matches reference: KPI row with icon cards, revenue chart, alerts panel,
executive summary, and allowable spend table.
"""

from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import html as _html

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


# ─── Data fetchers ───

def _fetch_dept_totals(conn, week_start, dept):
    row = conn.execute(
        """SELECT
              COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
              COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
              COALESCE(other_revenue,0) AS revenue,
              COALESCE(cos_dollars,0) AS cos,
              COALESCE(total_labor_dollars,0) AS labor_d,
              COALESCE(total_labor_hours,0) AS labor_h
           FROM weekly_financials
           WHERE department=? AND week_start=?""",
        (dept, week_start.isoformat() if isinstance(week_start, date) else week_start)
    ).fetchone()
    if row:
        return dict(row)
    return {"revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0}


def _fetch_consolidated(conn, week_start):
    totals = {"revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0, "covers": 0}
    for d in DEPARTMENTS:
        t = _fetch_dept_totals(conn, week_start, d)
        for k in ["revenue", "cos", "labor_d", "labor_h"]:
            totals[k] += t.get(k, 0) or 0

    door_rows = conn.execute(
        """SELECT COALESCE(SUM(count),0) FROM door_counts
           WHERE entry_date >= ? AND entry_date <= ?""",
        (week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchone()
    if door_rows:
        totals["covers"] = door_rows[0] or 0
    return totals


def _fetch_8wk_history(conn, dept_or_consolidated, ref_week, weeks=8):
    history = []
    for i in range(weeks - 1, -1, -1):
        wk = ref_week - timedelta(weeks=i)
        if dept_or_consolidated == "_consolidated":
            t = _fetch_consolidated(conn, wk)
        else:
            t = _fetch_dept_totals(conn, wk, dept_or_consolidated)
        history.append({
            "week": wk.strftime("%b %d"),
            "revenue": t.get("revenue", 0) or 0,
        })
    return history


def _get_targets(conn, dept):
    row = conn.execute(
        "SELECT * FROM targets WHERE department=?", (dept,)
    ).fetchone()
    return dict(row) if row else {}


def _consolidated_budget(conn, week_start):
    """Get consolidated budget across all depts."""
    rows = conn.execute(
        """SELECT COALESCE(SUM(revenue),0) AS revenue,
                  COALESCE(SUM(labor_dollars),0) AS labor_d,
                  COALESCE(SUM(labor_hours),0) AS labor_h
           FROM budgets WHERE week_start=?""",
        (week_start.isoformat(),)
    ).fetchone()
    return dict(rows) if rows else {"revenue": 0, "labor_d": 0, "labor_h": 0}


# ─── Render: KPI Card with icon ───

def _icon_svg(name):
    icons = {
        "dollar": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "users": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "utensils": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
        "trending": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
        "people": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
    }
    return icons.get(name, icons["dollar"])


def _kpi_card_premium(label, value, delta_pct=None, delta_color="green",
                       budget_text="", icon="dollar", icon_color="#16A34A",
                       icon_bg="#ECFDF5", invert_color=False):
    """Premium KPI card with icon circle, big number, delta, budget reference."""
    delta_html = ""
    if delta_pct is not None:
        is_positive = delta_pct >= 0
        if invert_color:
            color = "#DC2626" if is_positive else "#16A34A"
        else:
            color = "#16A34A" if is_positive else "#DC2626"
        arrow = "▲" if is_positive else "▼"
        sign = "+" if is_positive else ""
        delta_html = (
            '<div class="kpi-delta" style="color:{c};">'
            '{a} {s}{v} vs LY</div>'
        ).format(c=color, a=arrow, s=sign, v=delta_pct)

    budget_html = ""
    if budget_text:
        budget_html = (
            '<div class="kpi-budget">{}</div>'.format(budget_text)
        )

    return (
        '<div class="kpi-premium">'
        '<div class="kpi-row">'
        '<div class="kpi-icon-circle" style="background:{ibg};color:{ic};">{icon}</div>'
        '<div class="kpi-meta">'
        '<div class="kpi-label-sm">{label}</div>'
        '<div class="kpi-value-big">{value}</div>'
        '{delta}{budget}'
        '</div></div></div>'
    ).format(
        ibg=icon_bg, ic=icon_color, icon=_icon_svg(icon),
        label=label, value=value, delta=delta_html, budget=budget_html,
    )


def _alert_card(title, detail, level="warning", time_ago="just now"):
    """Single alert row."""
    config = {
        "critical": ("#DC2626", "#FEF2F2", "●"),
        "warning": ("#D97706", "#FFFBEB", "●"),
        "success": ("#16A34A", "#ECFDF5", "●"),
    }
    color, bg, dot = config.get(level, config["warning"])
    return (
        '<div class="alert-row">'
        '<div class="alert-dot" style="background:{bg};color:{c};">{dot}</div>'
        '<div class="alert-body">'
        '<div class="alert-title">{title}</div>'
        '<div class="alert-detail">{detail}</div>'
        '</div>'
        '<div class="alert-time">{time}</div>'
        '</div>'
    ).format(bg=bg, c=color, dot=dot, title=_html.escape(title),
             detail=_html.escape(detail), time=time_ago)


def _spend_row(unit, forecast_rev, allow_hrs, allow_rate, used_hrs,
                labor_pct, used_food, food_pct, allow_food):
    """Single row in Allowable Spend table."""
    used_pct = (used_hrs / allow_hrs * 100) if allow_hrs > 0 else 0
    used_food_pct = (used_food / allow_food * 100) if allow_food > 0 else 0
    over_hrs = used_pct > 100
    over_food = used_food_pct > 100

    hr_color = "#DC2626" if over_hrs else "#16A34A"
    food_color = "#DC2626" if over_food else "#16A34A"

    return (
        '<tr>'
        '<td class="t-unit">{unit}</td>'
        '<td class="t-num">{fc}</td>'
        '<td class="t-allow">'
        '<div class="t-allow-main">{ah:,.0f} hrs</div>'
        '<div class="t-allow-sub">${ar:.2f}/hr</div>'
        '</td>'
        '<td class="t-used">'
        '<div class="t-used-row">{uh:,.0f} hrs '
        '<span class="t-pct" style="color:{hc};">● ({up:.0f}%)</span></div>'
        '</td>'
        '<td class="t-num">{lp:.1f}%</td>'
        '<td class="t-num">${uf:,.0f} <span class="t-pct" style="color:{fc2};">●</span></td>'
        '<td class="t-num">{fp:.1f}%</td>'
        '</tr>'
    ).format(
        unit=unit, fc="${:,.0f}".format(forecast_rev),
        ah=allow_hrs, ar=allow_rate,
        uh=used_hrs, up=used_pct, hc=hr_color,
        lp=labor_pct, uf=used_food, fc2=food_color, fp=food_pct,
    )


# ─── Main render ───

def render(conn, user):
    """Main premium Operations Dashboard."""
    sync_clicked = False
    email_clicked = False

    def _ops_right():
        nonlocal sync_clicked, email_clicked
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            sync_clicked = st.button("🔄  Sync CTUIT", key="ops_sync",
                                     use_container_width=True)
        with a2:
            st.button("🖨  Print / PDF", key="ops_print",
                      use_container_width=True,
                      help="Use Cmd+P to save as PDF")
        with a3:
            email_clicked = st.button("✉  Email Digest", key="ops_email",
                                      use_container_width=True)
        with a4:
            if st.button("⟳  Refresh", key="ops_refresh",
                         use_container_width=True, type="primary"):
                st.cache_data.clear()
                st.rerun()

    hero_header(
        "Operations Dashboard",
        "Alma Dining — weekly close, forecast, and live allowable spend",
        _ops_right,
        left_ratio=4, right_ratio=6,
    )

    # ─── Period selector card ───
    if "od_week" not in st.session_state:
        st.session_state.od_week = db.get_week_start(date.today() - timedelta(weeks=1))

    fy, fw = get_fiscal_week(st.session_state.od_week)
    end = st.session_state.od_week + timedelta(days=6)

    p_col1, p_col2, p_col3 = st.columns([1.4, 4, 1])
    with p_col1:
        view_mode = st.radio(
            "Period",
            ["Fiscal Week", "Calendar Week"],
            key="od_mode", label_visibility="collapsed",
        )
    with p_col2:
        nav_l, nav_c, nav_r = st.columns([1, 5, 1])
        with nav_l:
            if st.button("◀", key="od_prev", use_container_width=True):
                st.session_state.od_week -= timedelta(weeks=1)
                st.rerun()
        with nav_c:
            st.markdown(
                '<div class="period-display">{} W{} '
                '<span style="color:#94A3B8;font-weight:400;">'
                '({} – {})</span></div>'.format(
                    fy, fw,
                    st.session_state.od_week.strftime("%b %d"),
                    end.strftime("%b %d, %Y")),
                unsafe_allow_html=True,
            )
        with nav_r:
            if st.button("▶", key="od_next", use_container_width=True):
                st.session_state.od_week += timedelta(weeks=1)
                st.rerun()
    with p_col3:
        pass

    # Comparison line
    if view_mode == "Fiscal Week":
        prior_fy = "FY25" if fy == "FY26" else "FY24"
        last_year_week = fiscal_to_date(prior_fy, fw)
        if last_year_week:
            cmp_text = "Comparing {} W{} vs {} W{} ({} – {})".format(
                fy, fw, prior_fy, fw,
                last_year_week.strftime("%b %d"),
                (last_year_week + timedelta(days=6)).strftime("%b %d, %Y"))
        else:
            cmp_text = "No prior-year week available"
    else:
        last_year_week = st.session_state.od_week - timedelta(weeks=52)
        cmp_text = "Comparing against {}".format(last_year_week.strftime("%b %d, %Y"))

    st.markdown(
        '<div class="period-compare">{}</div>'.format(cmp_text),
        unsafe_allow_html=True,
    )

    # ─── KPI Row ───
    this_week = _fetch_consolidated(conn, st.session_state.od_week)
    last_week = _fetch_consolidated(conn, last_year_week) if last_year_week else this_week
    budget = _consolidated_budget(conn, st.session_state.od_week)

    rev = this_week["revenue"]
    fc_pct = (this_week["cos"] / rev * 100) if rev > 0 else 0
    lp_pct = (this_week["labor_d"] / rev * 100) if rev > 0 else 0
    prime_pct = fc_pct + lp_pct
    covers = this_week["covers"]

    last_rev = last_week.get("revenue", 0)
    last_fc = (last_week["cos"] / last_rev * 100) if last_rev > 0 else 0
    last_lp = (last_week["labor_d"] / last_rev * 100) if last_rev > 0 else 0
    last_prime = last_fc + last_lp
    last_covers = last_week.get("covers", 0)

    rev_delta = round(((rev - last_rev) / last_rev * 100), 1) if last_rev > 0 else None
    fc_delta = round((fc_pct - last_fc), 1) if last_fc > 0 else None
    lp_delta = round((lp_pct - last_lp), 1) if last_lp > 0 else None
    prime_delta = round((prime_pct - last_prime), 1) if last_prime > 0 else None
    covers_delta = round(((covers - last_covers) / last_covers * 100), 1) if last_covers > 0 else None

    k = st.columns(5)
    with k[0]:
        st.markdown(_kpi_card_premium(
            "REVENUE", "${:,.0f}".format(rev),
            delta_pct=rev_delta,
            budget_text="Budget: ${:,.0f}".format(budget.get("revenue", 0)) if budget.get("revenue") else "",
            icon="dollar", icon_color="#16A34A", icon_bg="#ECFDF5",
        ), unsafe_allow_html=True)
    with k[1]:
        st.markdown(_kpi_card_premium(
            "LABOR %", "{:.1f}%".format(lp_pct),
            delta_pct=lp_delta,
            budget_text="Budget: 30.0%",
            icon="users", icon_color="#8B5CF6", icon_bg="#F5F3FF",
            invert_color=True,
        ), unsafe_allow_html=True)
    with k[2]:
        st.markdown(_kpi_card_premium(
            "FOOD COST %", "{:.1f}%".format(fc_pct),
            delta_pct=fc_delta,
            budget_text="Budget: 29.5%",
            icon="utensils", icon_color="#D97706", icon_bg="#FFFBEB",
            invert_color=True,
        ), unsafe_allow_html=True)
    with k[3]:
        st.markdown(_kpi_card_premium(
            "PRIME COST %", "{:.1f}%".format(prime_pct),
            delta_pct=prime_delta,
            budget_text="Budget: 59.0%",
            icon="trending", icon_color="#7C3AED", icon_bg="#F5F3FF",
            invert_color=True,
        ), unsafe_allow_html=True)
    with k[4]:
        st.markdown(_kpi_card_premium(
            "COVERS", "{:,}".format(int(covers)),
            delta_pct=covers_delta,
            budget_text="Budget: {:,}".format(int(budget.get("revenue", 0)/40) if budget.get("revenue") else 0),
            icon="people", icon_color="#3B82F6", icon_bg="#EFF6FF",
        ), unsafe_allow_html=True)

    # ─── Main row: Revenue chart + Alerts ───
    m1, m2 = st.columns([3, 2])

    with m1:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-header">'
            '<div class="panel-title">Revenue — Actual vs Budget vs Last Year</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        _render_revenue_chart(conn, st.session_state.od_week, last_year_week)
        st.markdown('</div>', unsafe_allow_html=True)

    with m2:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-header">'
            '<div class="panel-title">Alerts & Notifications</div>'
            '<a href="#" class="panel-link">View All</a>'
            '</div>'
            '<div class="alert-list">',
            unsafe_allow_html=True,
        )
        alerts = _build_alerts(conn, st.session_state.od_week, this_week)
        for a in alerts:
            st.markdown(_alert_card(**a), unsafe_allow_html=True)
        if not alerts:
            st.markdown(
                _alert_card(
                    "All key metrics within target range",
                    "No threshold breaches detected this week",
                    level="success", time_ago="now"),
                unsafe_allow_html=True,
            )
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ─── Bottom row: Executive Summary + Allowable Spend Table ───
    b1, b2 = st.columns([2, 3])

    with b1:
        _render_executive_summary(conn, st.session_state.od_week, last_year_week)

    with b2:
        _render_allowable_spend_panel(conn, st.session_state.od_week)

    # ─── Action handlers ───
    if sync_clicked:
        with st.spinner("Syncing CTUIT data..."):
            try:
                from ctuit_import import auto_import_ctuit
                results = auto_import_ctuit(
                    conn, user.get("username", "system"), download_from_gmail=True
                )
                count = sum(r.get("records", 0) for r in results if r.get("success"))
                st.success("Synced {} records from CTUIT.".format(count))
            except Exception as e:
                st.error("Sync error: {}".format(str(e)[:200]))

    if email_clicked:
        try:
            from ai_insights import generate_insights
            from email_digest import _build_html_digest, send_digest
            with st.spinner("Building digest..."):
                ly_iso = last_year_week.isoformat() if last_year_week else None
                ai = generate_insights("default", st.session_state.od_week.isoformat(), ly_iso)
                html = _build_html_digest(ai.get("context", {}), ai.get("commentary", ""))
                email = user.get("email") or "dashboardmetz@gmail.com"
                res = send_digest(
                    [email],
                    "Operations Dashboard — {}".format(st.session_state.od_week.isoformat()),
                    html
                )
            if res.get("success"):
                st.success("Digest sent to {}".format(email))
            else:
                st.error("Email failed: {}".format(res.get("error", "unknown")))
        except Exception as e:
            st.error("Email error: {}".format(str(e)[:200]))


def _render_revenue_chart(conn, week_start, last_year_week):
    """Daily revenue line chart: Actual vs Budget vs Last Year (Sun-Sat)."""
    days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    week_dates = [(week_start + timedelta(days=i)) for i in range(7)]

    # Daily actuals from daily_sales table
    actual = []
    for d in week_dates:
        try:
            row = conn.execute(
                """SELECT SUM(COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                              COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                              COALESCE(other_revenue,0)) AS rev
                   FROM daily_sales WHERE entry_date = ?""",
                (d.isoformat(),)
            ).fetchone()
            actual.append((row[0] or 0) if row else 0)
        except Exception:
            actual.append(0)

    # Budget = weekly budget / 7 spread evenly
    budget_row = conn.execute(
        "SELECT COALESCE(SUM(revenue),0) FROM budgets WHERE week_start=?",
        (week_start.isoformat(),)
    ).fetchone()
    weekly_budget = (budget_row[0] or 0) if budget_row else 0
    budget = [weekly_budget / 7] * 7 if weekly_budget else [0] * 7

    # Last year daily
    last_year = []
    if last_year_week:
        for i in range(7):
            d = last_year_week + timedelta(days=i)
            try:
                row = conn.execute(
                    """SELECT SUM(COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                                  COALESCE(other_revenue,0)) AS rev
                       FROM daily_sales WHERE entry_date = ?""",
                    (d.isoformat(),)
                ).fetchone()
                last_year.append((row[0] or 0) if row else 0)
            except Exception:
                last_year.append(0)
    else:
        last_year = [0] * 7

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days_of_week, y=actual, name="Actual",
        mode="lines+markers",
        line=dict(color="#0B1929", width=2.5),
        marker=dict(size=7, color="#0B1929"),
    ))
    fig.add_trace(go.Scatter(
        x=days_of_week, y=budget, name="Budget",
        mode="lines+markers",
        line=dict(color="#B8965A", width=2, dash="dot"),
        marker=dict(size=6, color="#B8965A"),
    ))
    fig.add_trace(go.Scatter(
        x=days_of_week, y=last_year, name="Last Year",
        mode="lines+markers",
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        marker=dict(size=5, color="#94A3B8"),
    ))

    fig.update_layout(
        height=320,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#64748B"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="rgba(148,163,184,0.08)", showline=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(148,163,184,0.10)", showline=False,
                   tickformat="$,.0f", zeroline=False),
        legend=dict(orientation="h", yanchor="top", y=1.10,
                    xanchor="left", x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#0B1929", font_color="#FFFFFF"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _build_alerts(conn, week_start, this_week_data):
    """Build alert list from variance flags."""
    alerts = []
    rev = this_week_data.get("revenue", 0) or 0

    for dept in DEPARTMENTS:
        t = _fetch_dept_totals(conn, week_start, dept)
        d_rev = t.get("revenue", 0) or 0
        if d_rev <= 0:
            continue
        targets = _get_targets(conn, dept)
        target_lp = targets.get("target_labor_pct") or 30
        target_fc = targets.get("target_food_cost_pct") or 32

        actual_lp = (t.get("labor_d", 0) / d_rev * 100) if d_rev > 0 else 0
        actual_fc = (t.get("cos", 0) / d_rev * 100) if d_rev > 0 else 0

        if actual_lp > target_lp + 2:
            alerts.append({
                "title": "{} labor is over target".format(dept),
                "detail": "Labor % is {:.1f} pts above budget".format(
                    actual_lp - target_lp),
                "level": "critical" if actual_lp > target_lp + 4 else "warning",
                "time_ago": "2h ago",
            })
        if actual_fc > target_fc + 2:
            alerts.append({
                "title": "{} food cost above plan".format(dept),
                "detail": "Food cost % is {:.1f} pts above budget".format(
                    actual_fc - target_fc),
                "level": "warning",
                "time_ago": "3h ago",
            })

    return alerts[:4]  # cap at 4


def _render_executive_summary(conn, week_start, last_year_week):
    """Executive Summary box — AI commentary if available, else heuristic."""
    summary_lines = []

    this_week = _fetch_consolidated(conn, week_start)
    last_week = _fetch_consolidated(conn, last_year_week) if last_year_week else None
    budget = _consolidated_budget(conn, week_start)

    rev = this_week["revenue"]
    b_rev = budget.get("revenue", 0)
    last_rev = last_week.get("revenue", 0) if last_week else 0

    # Revenue commentary
    if rev > 0 and b_rev > 0:
        rev_vs_budget = ((rev - b_rev) / b_rev * 100)
        rev_vs_ly = ((rev - last_rev) / last_rev * 100) if last_rev > 0 else 0
        rev_text = "Revenue is tracking {:+.1f}% vs budget".format(rev_vs_budget)
        if last_rev > 0:
            rev_text += " and {:+.1f}% vs last year".format(rev_vs_ly)
        rev_text += "."
        summary_lines.append(("trending", rev_text,
                              "Strong performance across all units." if rev_vs_budget > 0
                              else "Investigate underperforming units."))

    # Labor commentary
    if rev > 0:
        lp_pct = (this_week["labor_d"] / rev * 100)
        last_lp = (last_week["labor_d"] / last_rev * 100) if last_week and last_rev > 0 else lp_pct
        delta = lp_pct - last_lp
        if abs(delta) >= 0.3:
            text = "Labor costs {} {:.1f} pts vs last year.".format(
                "improved" if delta < 0 else "increased", abs(delta))
            sub = "Scheduling efficiency driving results." if delta < 0 else "Review scheduling vs forecast."
            summary_lines.append(("users", text, sub))

    # Food cost commentary
    if rev > 0:
        fc_pct = (this_week["cos"] / rev * 100)
        last_fc = (last_week["cos"] / last_rev * 100) if last_week and last_rev > 0 else fc_pct
        delta = fc_pct - last_fc
        if abs(delta) >= 0.3:
            text = "Food cost variance driven by departmental mix."
            sub = "Review portioning and waste controls." if delta > 0 else "Sourcing improvements paying off."
            summary_lines.append(("utensils", text, sub))

    items_html = ""
    for icon, text, sub in summary_lines:
        items_html += (
            '<div class="es-row">'
            '<div class="es-icon">{}</div>'
            '<div class="es-text">'
            '<div class="es-main">{}</div>'
            '<div class="es-sub">{}</div>'
            '</div></div>'
        ).format(_icon_svg(icon), _html.escape(text), _html.escape(sub))

    if not items_html:
        items_html = (
            '<div class="es-row">'
            '<div class="es-text">'
            '<div class="es-main">No commentary available</div>'
            '<div class="es-sub">Add weekly financials to enable insights.</div>'
            '</div></div>'
        )

    st.markdown(
        '<div class="panel-card">'
        '<div class="panel-header">'
        '<div class="panel-title-row">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="#B8965A">'
        '<path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z"/>'
        '</svg>'
        '<span class="panel-title">Executive Summary</span>'
        '<span class="ai-badge">AI-generated</span>'
        '</div></div>'
        '<div class="es-list">{}</div>'
        '<a href="#" class="panel-link">View full commentary →</a>'
        '</div>'.format(items_html),
        unsafe_allow_html=True,
    )


def _render_allowable_spend_panel(conn, week_start):
    """Allowable Spend & Hours table with tabs."""
    st.markdown(
        '<div class="panel-card">'
        '<div class="spend-tabs">'
        '<span class="spend-tab active">Allowable Spend & Hours</span>'
        '<span class="spend-tab">Labor</span>'
        '<span class="spend-tab">Food Cost</span>'
        '<span class="spend-tab">Covers</span>'
        '<span class="spend-tab">Forecast</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    rows_html = ""
    total_forecast = 0
    total_allow_hrs = 0
    total_used_hrs = 0
    total_used_food = 0
    total_allow_food = 0

    for dept in DEPARTMENTS:
        # 4-week rolling avg as forecast
        history = _fetch_8wk_history(conn, dept, week_start, weeks=4)
        revs = [h["revenue"] for h in history if h["revenue"] > 0]
        forecast_rev = sum(revs) / len(revs) if revs else 0

        targets = _get_targets(conn, dept)
        target_lp = (targets.get("target_labor_pct") or 30) / 100
        target_fc = (targets.get("target_food_cost_pct") or 32) / 100
        wage = targets.get("avg_hourly_wage") or 19.92
        salaries = targets.get("salaries_dollars") or 0
        office = targets.get("office_labor_dollars") or 0

        is_board = dept == "Board & Catering"
        allow_total = forecast_rev * target_lp
        allow_hourly = max(0, allow_total - salaries - office) if is_board else allow_total
        allow_hrs = allow_hourly / wage if wage > 0 else 0
        allow_food = forecast_rev * target_fc

        actual = _fetch_dept_totals(conn, week_start, dept)
        used_hrs = actual.get("labor_h", 0) or 0
        used_food = actual.get("cos", 0) or 0
        a_rev = actual.get("revenue", 0) or 0
        labor_pct = (actual.get("labor_d", 0) / a_rev * 100) if a_rev > 0 else 0
        food_pct = (used_food / a_rev * 100) if a_rev > 0 else 0

        rows_html += _spend_row(
            dept, forecast_rev, allow_hrs, wage,
            used_hrs, labor_pct, used_food, food_pct, allow_food
        )

        total_forecast += forecast_rev
        total_allow_hrs += allow_hrs
        total_used_hrs += used_hrs
        total_used_food += used_food
        total_allow_food += allow_food

    total_used_pct = (total_used_hrs / total_allow_hrs * 100) if total_allow_hrs > 0 else 0
    total_color = "#DC2626" if total_used_pct > 100 else "#16A34A"

    # Total row
    rows_html += (
        '<tr class="t-total">'
        '<td class="t-unit"><b>Total / Average</b></td>'
        '<td class="t-num"><b>${:,.0f}</b></td>'
        '<td class="t-allow"><div class="t-allow-main"><b>{:,.0f} hrs</b></div></td>'
        '<td class="t-used">'
        '<div class="t-used-row"><b>{:,.0f} hrs</b> '
        '<span class="t-pct" style="color:{}">({:.1f}%)</span></div>'
        '</td>'
        '<td class="t-num">—</td>'
        '<td class="t-num"><b>${:,.0f}</b></td>'
        '<td class="t-num">—</td>'
        '</tr>'.format(
            total_forecast, total_allow_hrs,
            total_used_hrs, total_color, total_used_pct,
            total_used_food)
    )

    st.markdown(
        '<table class="spend-table">'
        '<thead><tr>'
        '<th class="t-unit">LANE / UNIT</th>'
        '<th class="t-num">FORECAST REV</th>'
        '<th>ALLOWABLE</th>'
        '<th>HOURS USED</th>'
        '<th class="t-num">LABOR %</th>'
        '<th class="t-num">FOOD $ USED</th>'
        '<th class="t-num">FOOD %</th>'
        '</tr></thead>'
        '<tbody>{}</tbody>'
        '</table></div>'.format(rows_html),
        unsafe_allow_html=True,
    )
