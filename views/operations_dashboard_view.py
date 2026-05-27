"""
Clean Operations Dashboard — weekly close, forecast, allowable spend.
Combines consolidated financials, operational detail by lane,
daypart tracking, forecast, allowable spend, and YoY notes.
"""

from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEPARTMENTS
from calculations import sum_revenue_streams, fmt_dollar, fmt_pct
import db


# ─── Lane mapping ───
_RETAIL_DEPTS = ["Starbucks", "Qdoba", "Retail & Mac's Grill"]
_RESIDENTIAL_DEPTS = ["Board & Catering"]
_CATERING_DEPT = "Board & Catering"  # catering revenue lives in Board & Catering


# ═══════════════════════════════════════════════════
# Fiscal calendar
# ═══════════════════════════════════════════════════
FY26_START = date(2025, 7, 7)
FY25_START = date(2024, 7, 1)


def get_fiscal_week(d):
    """Return (fy_label, week_num) for date."""
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


# ═══════════════════════════════════════════════════
# Data fetchers
# ═══════════════════════════════════════════════════

def _fetch_dept_totals(conn, week_start, dept):
    """Get totals for a specific dept + week."""
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
    """Get consolidated totals across all depts."""
    totals = {"revenue": 0, "cos": 0, "labor_d": 0, "labor_h": 0, "covers": 0}
    for d in DEPARTMENTS:
        t = _fetch_dept_totals(conn, week_start, d)
        for k in ["revenue", "cos", "labor_d", "labor_h"]:
            totals[k] += t.get(k, 0) or 0

    # Covers = sum of door counts for the week
    door_rows = conn.execute(
        """SELECT COALESCE(SUM(count),0) FROM door_counts
           WHERE entry_date >= ? AND entry_date <= ?""",
        (week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchone()
    if door_rows:
        totals["covers"] = door_rows[0] or 0
    return totals


def _fetch_8wk_history(conn, dept_or_consolidated, ref_week, weeks=8):
    """Get 8-week history of revenue."""
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


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════

def _delta_arrow(this_val, last_val, is_pct=False, lower_is_better=False):
    """Generate small delta indicator for KPIs."""
    if last_val is None or last_val == 0:
        return "—", "#94A3B8"
    if is_pct:
        delta = this_val - last_val
        good = (delta < 0) if lower_is_better else (delta > 0)
        color = "#16A34A" if good else "#DC2626"
        arrow = "▲" if delta > 0 else "▼"
        return "{} {:+.1f} pp".format(arrow, delta), color
    else:
        pct = ((this_val - last_val) / last_val * 100) if last_val else 0
        good = (pct < 0) if lower_is_better else (pct > 0)
        color = "#16A34A" if good else "#DC2626"
        arrow = "▲" if pct > 0 else "▼"
        return "{} {:+.1f}% vs LY".format(arrow, pct), color


def _kpi_card(label, value, delta_text="", delta_color="#94A3B8",
              spark_data=None, spark_color="#1F2A44"):
    """Render a clean KPI card with optional sparkline."""
    spark_html = ""
    if spark_data and len(spark_data) > 1:
        # Build inline SVG sparkline
        max_val = max(spark_data) or 1
        min_val = min(spark_data)
        range_val = max_val - min_val or 1
        points = []
        for i, v in enumerate(spark_data):
            x = (i / (len(spark_data) - 1)) * 100
            y = 30 - ((v - min_val) / range_val * 25)
            points.append("{:.1f},{:.1f}".format(x, y))

        # Filled area path
        area_d = "M0,30 L{} L100,30 Z".format(" L".join(points))
        line_d = "M{}".format(" L".join(points))

        spark_html = (
            '<svg viewBox="0 0 100 30" preserveAspectRatio="none" '
            'style="width:100%;height:32px;margin-top:10px;display:block;">'
            '<path d="{a}" fill="{c}" opacity="0.10"/>'
            '<path d="{l}" stroke="{c}" stroke-width="1.4" fill="none" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
            '</svg>'
        ).format(a=area_d, l=line_d, c=spark_color)

    return (
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:10px;padding:18px 20px;height:100%;'
        'box-shadow:0 1px 2px rgba(0,0,0,0.03);">'
        '<div style="font-size:10px;font-weight:600;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.08em;">{label}</div>'
        '<div style="font-size:30px;font-weight:700;color:#1E293B;'
        'margin-top:6px;letter-spacing:-0.02em;line-height:1.1;">{value}</div>'
        '<div style="font-size:11px;font-weight:500;color:{dc};margin-top:4px;">'
        '{dt}</div>'
        '{sp}'
        '</div>'
    ).format(
        label=label, value=value, dt=delta_text, dc=delta_color, sp=spark_html
    )


def _section_panel_header(label, title, subtitle=""):
    """Render PANEL label + title."""
    sub = ""
    if subtitle:
        sub = (
            '<div style="font-size:13px;color:#64748B;margin-top:2px;">{}</div>'
        ).format(subtitle)
    st.markdown(
        '<div style="margin:32px 0 12px;">'
        '<div style="font-size:10px;font-weight:700;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.10em;">{label}</div>'
        '<div style="font-size:18px;font-weight:700;color:#1E293B;'
        'margin-top:4px;letter-spacing:-0.01em;">{title}</div>'
        '{sub}'
        '</div>'.format(label=label, title=title, sub=sub),
        unsafe_allow_html=True,
    )


def _allowable_progress_row(unit, forecast, allow_hrs_total, used_hrs,
                             allow_food_total, used_food, allow_hrs_dollars=0):
    """Single row of the allowable spend table."""
    # Hours usage %
    hrs_pct = (used_hrs / allow_hrs_total * 100) if allow_hrs_total > 0 else 0
    food_pct = (used_food / allow_food_total * 100) if allow_food_total > 0 else 0

    def _status_color(pct):
        if pct < 60:
            return "#16A34A"  # green
        elif pct < 90:
            return "#D97706"  # amber
        else:
            return "#DC2626"  # red

    h_color = _status_color(hrs_pct)
    f_color = _status_color(food_pct)
    h_dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'\
            'background:{};margin-right:6px;"></span>'.format(h_color)
    f_dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'\
            'background:{};margin-right:6px;"></span>'.format(f_color)

    return (
        '<tr style="border-bottom:1px solid #F1F5F9;">'
        '<td style="padding:14px 16px;font-size:13px;font-weight:500;color:#1E293B;">{unit}</td>'
        '<td style="padding:14px 16px;font-size:13px;color:#1E293B;text-align:right;">{fc}</td>'
        '<td style="padding:14px 16px;text-align:right;">'
        '<div style="font-size:13px;font-weight:600;color:#1E293B;">{ah_total:,.0f} hrs</div>'
        '<div style="font-size:11px;color:#94A3B8;margin-top:1px;">${ahd:,.0f} hourly</div>'
        '</td>'
        '<td style="padding:14px 16px;font-size:13px;color:#1E293B;">'
        '<div style="display:flex;align-items:center;">{hd}{used_h:,.0f} / {ah_total:,.0f} hrs ({hp:.0f}%)</div>'
        '<div style="background:#F1F5F9;height:4px;border-radius:2px;margin-top:6px;overflow:hidden;">'
        '<div style="height:100%;width:{hp_w:.0f}%;background:{hc};border-radius:2px;"></div>'
        '</div>'
        '</td>'
        '<td style="padding:14px 16px;font-size:13px;color:#1E293B;">'
        '<div style="display:flex;align-items:center;">{fd}${used_f:,.0f} / ${af_total:,.0f} ({fp:.0f}%)</div>'
        '<div style="background:#F1F5F9;height:4px;border-radius:2px;margin-top:6px;overflow:hidden;">'
        '<div style="height:100%;width:{fp_w:.0f}%;background:{fc};border-radius:2px;"></div>'
        '</div>'
        '</td>'
        '</tr>'
    ).format(
        unit=unit, fc=fmt_dollar(forecast),
        ah_total=allow_hrs_total, ahd=allow_hrs_dollars,
        hd=h_dot, used_h=used_hrs, hp=hrs_pct, hp_w=min(100, hrs_pct), hc=h_color,
        fd=f_dot, used_f=used_food, af_total=allow_food_total,
        fp=food_pct, fp_w=min(100, food_pct),
    )


# ═══════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════

def render(conn, user):
    """Main Operations Dashboard view."""
    # Header with action buttons
    header_col, action_col = st.columns([3, 2])
    with header_col:
        st.markdown(
            '<div style="margin:0 0 8px;">'
            '<div style="font-size:10px;font-weight:700;color:#94A3B8;'
            'text-transform:uppercase;letter-spacing:.10em;">Operations</div>'
            '<h1 style="font-size:28px;font-weight:700;color:#1E293B;'
            'margin:4px 0 4px;letter-spacing:-0.02em;">Operations Dashboard</h1>'
            '<div style="font-size:14px;color:#64748B;">'
            'Alma Dining — weekly close, forecast, and live allowable spend</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with action_col:
        st.markdown(
            '<div style="height:50px;"></div>',  # spacer
            unsafe_allow_html=True,
        )
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("🖨 Print / PDF", key="od_print",
                         use_container_width=True,
                         help="Use Cmd+P / Ctrl+P to save as PDF"):
                st.markdown(
                    '<script>window.print();</script>',
                    unsafe_allow_html=True,
                )
        with a2:
            send_clicked = st.button("📧 Email Digest", key="od_email",
                                      use_container_width=True,
                                      help="Send weekly summary via Gmail")
        with a3:
            if st.button("🔄 Refresh", key="od_refresh",
                         use_container_width=True,
                         help="Reload latest data"):
                st.cache_data.clear()
                st.rerun()

    # ═══════ Period selector ═══════
    if "od_week" not in st.session_state:
        st.session_state.od_week = db.get_week_start(date.today() - timedelta(weeks=1))

    fy, fw = get_fiscal_week(st.session_state.od_week)
    end = st.session_state.od_week + timedelta(days=6)

    c1, c2, c3 = st.columns([1.5, 4, 1.5])
    with c1:
        view_mode = st.radio(
            "View", ["Fiscal Week", "Calendar Week"],
            horizontal=True, key="od_mode", label_visibility="collapsed",
        )
    with c3:
        nav_a, nav_b = st.columns(2)
        with nav_a:
            if st.button("◀", key="od_prev", use_container_width=True):
                st.session_state.od_week -= timedelta(weeks=1)
                st.rerun()
        with nav_b:
            if st.button("▶", key="od_next", use_container_width=True):
                st.session_state.od_week += timedelta(weeks=1)
                st.rerun()
    with c2:
        st.markdown(
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            'border-radius:8px;padding:8px 14px;text-align:center;'
            'font-size:13px;font-weight:600;color:#1E293B;">'
            '{} W{} ({} – {})'
            '</div>'.format(
                fy, fw,
                st.session_state.od_week.strftime("%b %d"),
                end.strftime("%b %d, %Y")),
            unsafe_allow_html=True,
        )

    # ═══════ Sub-header: comparison context ═══════
    if view_mode == "Fiscal Week":
        prior_fy = "FY25" if fy == "FY26" else "FY24"
        last_year_week = fiscal_to_date(prior_fy, fw)
        comparison_text = "Comparing {} W{} against {} W{}".format(fy, fw, prior_fy, fw)
        if last_year_week:
            comparison_text += " ({} – {})".format(
                last_year_week.strftime("%b %d"),
                (last_year_week + timedelta(days=6)).strftime("%b %d, %Y")
            )
        comparison_text += " — academic-calendar-aligned, not date-aligned"
    else:
        last_year_week = st.session_state.od_week - timedelta(weeks=52)
        comparison_text = "Comparing against same calendar week last year ({})".format(
            last_year_week.strftime("%b %d, %Y")
        )

    st.markdown(
        '<div style="font-size:12px;color:#64748B;margin-top:8px;">{}</div>'.format(
            comparison_text
        ),
        unsafe_allow_html=True,
    )

    # ═══════ AI INSIGHTS PANEL ═══════
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    try:
        from ai_insights import render_insights_panel
        render_insights_panel(conn, st.session_state.od_week, last_year_week)
    except Exception as e:
        st.caption("AI insights unavailable: {}".format(str(e)[:100]))

    # ═══════ Email Digest Handler ═══════
    if send_clicked:
        try:
            from ai_insights import generate_insights
            from email_digest import _build_html_digest, send_digest

            with st.spinner("Building digest and sending..."):
                ly_iso = last_year_week.isoformat() if last_year_week else None
                ai_result = generate_insights(
                    "default",
                    st.session_state.od_week.isoformat(),
                    ly_iso,
                )
                ctx = ai_result.get("context", {})
                commentary = ai_result.get("commentary", "")
                html_body = _build_html_digest(ctx, commentary)

                user_email = user.get("email") or "dashboardmetz@gmail.com"
                subject = "Operations Dashboard — Week of {}".format(
                    st.session_state.od_week.isoformat())
                result = send_digest([user_email], subject, html_body)

            if result.get("success"):
                st.success("✓ Digest sent to {}".format(user_email))
            else:
                err = result.get("error", "Unknown error")
                st.error("Email failed: {}. Need 'gmail.send' scope.".format(err[:120]))
        except Exception as e:
            st.error("Email error: {}".format(str(e)[:200]))

    # ═══════ PANEL 1: Consolidated Financials ═══════
    _section_panel_header(
        "PANEL", "Consolidated Financials",
        "All three lanes — current fiscal week vs LY same fiscal week"
    )

    this_week = _fetch_consolidated(conn, st.session_state.od_week)
    last_week = _fetch_consolidated(conn, last_year_week) if last_year_week else this_week

    # Calculate %s
    rev = this_week["revenue"]
    fc_pct = (this_week["cos"] / rev * 100) if rev > 0 else 0
    lp_pct = (this_week["labor_d"] / rev * 100) if rev > 0 else 0
    covers = this_week["covers"]

    last_rev = last_week.get("revenue", 0)
    last_fc = (last_week["cos"] / last_rev * 100) if last_rev > 0 else 0
    last_lp = (last_week["labor_d"] / last_rev * 100) if last_rev > 0 else 0
    last_covers = last_week.get("covers", 0)

    # 8-week sparklines (consolidated)
    history = _fetch_8wk_history(conn, "_consolidated", st.session_state.od_week)
    rev_series = [h["revenue"] for h in history]

    rev_delta, rev_color = _delta_arrow(rev, last_rev)
    fc_delta, fc_color = _delta_arrow(fc_pct, last_fc, is_pct=True, lower_is_better=True)
    lp_delta, lp_color = _delta_arrow(lp_pct, last_lp, is_pct=True, lower_is_better=True)
    cv_delta, cv_color = _delta_arrow(covers, last_covers)

    cards = st.columns(4)
    with cards[0]:
        st.markdown(_kpi_card(
            "Revenue", fmt_dollar(rev), rev_delta, rev_color,
            spark_data=rev_series, spark_color="#1F2A44",
        ), unsafe_allow_html=True)
    with cards[1]:
        st.markdown(_kpi_card(
            "Food Cost %", "{:.1f}%".format(fc_pct), fc_delta, fc_color,
            spark_data=rev_series, spark_color="#C7A462",
        ), unsafe_allow_html=True)
    with cards[2]:
        st.markdown(_kpi_card(
            "Labor %", "{:.1f}%".format(lp_pct), lp_delta, lp_color,
            spark_data=rev_series, spark_color="#16A34A",
        ), unsafe_allow_html=True)
    with cards[3]:
        st.markdown(_kpi_card(
            "Covers", "{:,}".format(int(covers)), cv_delta, cv_color,
            spark_data=rev_series, spark_color="#3B82F6",
        ), unsafe_allow_html=True)

    # ─── Drill-down expander ───
    with st.expander("📊 Drill into details", expanded=False):
        _render_kpi_drilldown(conn, st.session_state.od_week, last_year_week)

    # ═══════ PANEL 2: Operational Detail ═══════
    _section_panel_header(
        "PANEL", "Operational Detail",
        "Each lane reads in op-statement language. Drill into sub-units below."
    )

    lane_tabs = st.tabs(["Retail", "Residential / Hamilton", "Catering"])

    def _render_lane(lane_depts, show_sub_units=True):
        """Render KPIs + sub-unit table for a lane."""
        lane_rev = sum(_fetch_dept_totals(conn, st.session_state.od_week, d).get("revenue", 0) for d in lane_depts)
        lane_cos = sum(_fetch_dept_totals(conn, st.session_state.od_week, d).get("cos", 0) for d in lane_depts)
        lane_lab = sum(_fetch_dept_totals(conn, st.session_state.od_week, d).get("labor_d", 0) for d in lane_depts)

        # Get target
        target_lp = 0
        target_fc = 0
        n = 0
        for d in lane_depts:
            t = _get_targets(conn, d)
            target_lp += t.get("target_labor_pct") or 0
            target_fc += t.get("target_food_cost_pct") or 0
            n += 1
        if n:
            target_lp /= n
            target_fc /= n

        lane_fc_pct = (lane_cos / lane_rev * 100) if lane_rev > 0 else 0
        lane_lp_pct = (lane_lab / lane_rev * 100) if lane_rev > 0 else 0

        # Get budget for vs target
        b_rev = 0
        for d in lane_depts:
            b = conn.execute(
                "SELECT revenue FROM budgets WHERE department=? AND week_start=?",
                (d, st.session_state.od_week.isoformat())
            ).fetchone()
            if b and b[0]:
                b_rev += b[0]

        rev_vs_b = ((lane_rev - b_rev) / b_rev * 100) if b_rev > 0 else 0

        # Estimate covers from door counts (only Hamilton)
        covers_lane = 0
        if "Board & Catering" in lane_depts:
            row = conn.execute(
                """SELECT COALESCE(SUM(count),0) FROM door_counts
                   WHERE entry_date >= ? AND entry_date <= ?""",
                (st.session_state.od_week.isoformat(),
                 (st.session_state.od_week + timedelta(days=6)).isoformat())
            ).fetchone()
            covers_lane = row[0] if row else 0

        ck = st.columns(4)
        with ck[0]:
            st.markdown(_kpi_card(
                "Revenue", fmt_dollar(lane_rev),
                "vs LY: {:+.1f}% • Target ${:,.0f}".format(rev_vs_b, b_rev) if b_rev else "",
                "#16A34A" if rev_vs_b >= 0 else "#DC2626"
            ), unsafe_allow_html=True)
        with ck[1]:
            st.markdown(_kpi_card(
                "Food Cost %", "{:.1f}%".format(lane_fc_pct),
                "Target {:.1f}%".format(target_fc) if target_fc else "",
                "#16A34A" if lane_fc_pct <= target_fc else "#DC2626"
            ), unsafe_allow_html=True)
        with ck[2]:
            st.markdown(_kpi_card(
                "Labor %", "{:.1f}%".format(lane_lp_pct),
                "Target {:.1f}%".format(target_lp) if target_lp else "",
                "#16A34A" if lane_lp_pct <= target_lp else "#DC2626"
            ), unsafe_allow_html=True)
        with ck[3]:
            label = "Covers" if covers_lane else "Avg Ticket"
            val = "{:,}".format(int(covers_lane)) if covers_lane else (
                "${:.2f}".format(lane_rev / max(1, covers_lane)) if covers_lane else "—"
            )
            st.markdown(_kpi_card(label, val, "", "#94A3B8"), unsafe_allow_html=True)

        # Sub-unit table
        if show_sub_units and len(lane_depts) > 1:
            st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)
            rows_html = []
            for d in lane_depts:
                t = _fetch_dept_totals(conn, st.session_state.od_week, d)
                d_rev = t.get("revenue", 0)
                d_cos = t.get("cos", 0)
                d_lab = t.get("labor_d", 0)
                d_fc = (d_cos / d_rev * 100) if d_rev > 0 else 0
                d_lp = (d_lab / d_rev * 100) if d_rev > 0 else 0
                rows_html.append(
                    '<tr style="border-bottom:1px solid #F1F5F9;">'
                    '<td style="padding:12px 16px;font-size:13px;color:#1E293B;font-weight:500;">{}</td>'
                    '<td style="padding:12px 16px;font-size:13px;color:#1E293B;text-align:right;">{}</td>'
                    '<td style="padding:12px 16px;font-size:13px;color:#1E293B;text-align:right;">{:.1f}%</td>'
                    '<td style="padding:12px 16px;font-size:13px;color:#1E293B;text-align:right;">{:.1f}%</td>'
                    '</tr>'.format(d, fmt_dollar(d_rev), d_fc, d_lp)
                )
            st.markdown(
                '<table style="width:100%;background:#FFFFFF;border:1px solid #E5E7EB;'
                'border-radius:8px;border-collapse:separate;border-spacing:0;'
                'overflow:hidden;margin-top:14px;">'
                '<thead><tr style="background:#F8FAFC;">'
                '<th style="padding:10px 16px;font-size:10px;color:#94A3B8;'
                'text-transform:uppercase;letter-spacing:.06em;text-align:left;font-weight:600;">SUB-UNIT</th>'
                '<th style="padding:10px 16px;font-size:10px;color:#94A3B8;'
                'text-transform:uppercase;letter-spacing:.06em;text-align:right;font-weight:600;">REVENUE</th>'
                '<th style="padding:10px 16px;font-size:10px;color:#94A3B8;'
                'text-transform:uppercase;letter-spacing:.06em;text-align:right;font-weight:600;">FC %</th>'
                '<th style="padding:10px 16px;font-size:10px;color:#94A3B8;'
                'text-transform:uppercase;letter-spacing:.06em;text-align:right;font-weight:600;">LABOR %</th>'
                '</tr></thead>'
                '<tbody>{}</tbody></table>'.format("".join(rows_html)),
                unsafe_allow_html=True,
            )

    with lane_tabs[0]:  # Retail
        _render_lane(_RETAIL_DEPTS, show_sub_units=True)
    with lane_tabs[1]:  # Residential
        _render_lane(["Board & Catering"], show_sub_units=False)
    with lane_tabs[2]:  # Catering (subset of Board & Catering catering revenue)
        _render_lane(["Board & Catering"], show_sub_units=False)

    # ═══════ PANEL 3: Daypart & Transaction Tracking ═══════
    _section_panel_header(
        "PANEL", "Daypart & Transaction Tracking",
        "Daily counts by location and meal period — current fiscal week"
    )

    _render_daypart_chart(conn, st.session_state.od_week)

    # ═══════ PANEL 4: Forecast ═══════
    next_fy, next_fw = get_fiscal_week(st.session_state.od_week + timedelta(weeks=1))
    _section_panel_header(
        "PANEL",
        "Forecast — Next Fiscal Week ({} W{})".format(next_fy, next_fw),
        "LY same-fiscal-week base, adjusted for 4-week velocity"
    )
    _render_forecast_panel(conn, st.session_state.od_week)

    # ═══════ PANEL 5: Allowable Spend Live ═══════
    _section_panel_header(
        "PANEL", "Allowable Spend & Hours — Live (Mid-Week)",
        "Avg variable hourly wage: $19.92/hr (salaried excluded). Source: ADP feed (weekly refresh)."
    )
    _render_allowable_spend_table(conn, st.session_state.od_week)

    # ═══════ PANEL 6: Notes Layer YoY ═══════
    _section_panel_header(
        "PANEL", "Notes Layer — This Week & Same Fiscal Week Last Year",
        "Institutional memory. Searchable. Pays compounding dividends in year 2+."
    )
    _render_notes_yoy(conn, st.session_state.od_week, last_year_week, fy, fw, prior_fy if view_mode == "Fiscal Week" else "LY")


# ═══════════════════════════════════════════════════
# Sub-render functions
# ═══════════════════════════════════════════════════

def _render_daypart_chart(conn, week_start):
    """Daily transaction counts by location/meal period."""
    days = [(week_start + timedelta(days=i)) for i in range(7)]
    day_labels = [d.strftime("%a") for d in days]

    # Fetch tender totals for these days, group by terminal+period
    rows = conn.execute(
        """SELECT report_date, terminal, service_period,
                  board_count + points_count + bonpts_count AS total
           FROM odyssey_tender_totals
           WHERE report_date >= ? AND report_date <= ?""",
        (week_start.isoformat(), (week_start + timedelta(days=6)).isoformat())
    ).fetchall() if _has_tender_table(conn) else []

    if not rows:
        st.markdown(
            '<div style="background:#F8FAFC;border:1px dashed #CBD5E1;'
            'border-radius:8px;padding:24px;text-align:center;color:#94A3B8;'
            'font-size:13px;">'
            'No tender/transaction data for this week.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame([dict(r) for r in rows])
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.strftime("%a")

    # Build series: (terminal, period) -> [day1, day2, ...]
    series_colors = {
        ("Hamilton 04", "Breakfast"): "#1F2A44",
        ("Hamilton 04", "Lunch"): "#3B82F6",
        ("Hamilton 04", "Dinner"): "#C7A462",
        ("Starbucks04 Epic", "Lunch"): "#16A34A",
        ("SIM - Loch Lomond", "Lunch"): "#EF4444",
        ("SIM - Qdoba", "Lunch"): "#D97706",
    }

    fig = go.Figure()
    for (term, period), color in series_colors.items():
        subset = df[(df["terminal"] == term) & (df["service_period"] == period)]
        if subset.empty:
            continue
        agg = subset.groupby("report_date")["total"].sum().reindex(day_labels, fill_value=0)
        # Friendly name
        fname = {
            "Hamilton 04": "Hamilton",
            "SIM - Loch Lomond": "Mac's",
            "SIM - Qdoba": "Qdoba",
            "Starbucks04 Epic": "Starbucks",
        }.get(term, term)
        label = "{} — {}".format(fname, period) if term == "Hamilton 04" else fname
        fig.add_trace(go.Scatter(
            x=day_labels, y=agg.values, name=label,
            mode="lines+markers", line=dict(color=color, width=2),
            marker=dict(size=6),
        ))

    fig.update_layout(
        height=320,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#64748B"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="rgba(148,163,184,0.10)", showline=False),
        yaxis=dict(gridcolor="rgba(148,163,184,0.10)", showline=False,
                   title=dict(text="Transactions / Covers", font=dict(size=11))),
        legend=dict(orientation="h", yanchor="top", y=-0.15,
                    xanchor="center", x=0.5, font=dict(size=10)),
    )

    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:10px;padding:18px;">',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_forecast_panel(conn, ref_week):
    """3 cards: Predicted Revenue, Allowable Food $, Allowable Labor Hours."""
    history = _fetch_8wk_history(conn, "_consolidated", ref_week, weeks=8)
    revs = [h["revenue"] for h in history if h["revenue"] > 0]

    if not revs:
        st.info("No historical data for forecast.")
        return

    if len(revs) >= 4:
        avg = sum(revs[-4:]) / 4
        recent = sum(revs[-2:]) / 2
        prior = sum(revs[-4:-2]) / 2
        velocity = (recent - prior) / 2
        forecast = max(0, avg + velocity)
        # Range = ±5%
        low = forecast * 0.95
        high = forecast * 1.05
    else:
        forecast = sum(revs) / len(revs) if revs else 0
        low = forecast * 0.95
        high = forecast * 1.05

    # Get consolidated targets (avg)
    target_fc = 32.0
    target_lp = 31.0
    avg_wage = 19.92
    n = 0
    for d in DEPARTMENTS:
        t = _get_targets(conn, d)
        target_fc += t.get("target_food_cost_pct") or 0
        target_lp += t.get("target_labor_pct") or 0
        if t.get("avg_hourly_wage"):
            avg_wage = t.get("avg_hourly_wage")
        n += 1
    if n:
        target_fc /= n
        target_lp /= n

    allow_food = forecast * (target_fc / 100)
    allow_labor_d = forecast * (target_lp / 100)
    allow_hours = allow_labor_d / avg_wage if avg_wage > 0 else 0

    # Last week's actual vs forecast (calibration)
    last_actual = revs[-1] if revs else 0
    if len(revs) >= 5:
        # what we WOULD have predicted last week using weeks before it
        prior_revs = revs[-5:-1]
        prior_avg = sum(prior_revs) / 4
        last_predicted = prior_avg
        calib_pct = ((last_actual - last_predicted) / last_predicted * 100) if last_predicted else 0
    else:
        last_predicted = 0
        calib_pct = 0

    cards = st.columns(3)
    with cards[0]:
        st.markdown(_kpi_card(
            "Predicted Revenue", fmt_dollar(forecast),
            "Range: {} – {}".format(fmt_dollar(low), fmt_dollar(high)),
            "#94A3B8"
        ), unsafe_allow_html=True)
    with cards[1]:
        st.markdown(_kpi_card(
            "Allowable Food $", fmt_dollar(allow_food),
            "at consolidated FC target {:.1f}%".format(target_fc),
            "#94A3B8"
        ), unsafe_allow_html=True)
    with cards[2]:
        st.markdown(_kpi_card(
            "Allowable Labor Hours", "{:,.0f}".format(allow_hours),
            "{} at ${:.2f}/hr avg variable wage".format(fmt_dollar(allow_labor_d), avg_wage),
            "#94A3B8"
        ), unsafe_allow_html=True)

    if last_predicted > 0:
        sign = "+" if calib_pct >= 0 else ""
        color = "#16A34A" if abs(calib_pct) < 3 else "#D97706"
        st.markdown(
            '<div style="font-size:12px;color:#64748B;margin-top:14px;'
            'padding:10px 14px;background:#F8FAFC;border-radius:6px;border:1px solid #E2E8F0;">'
            "Last week's calibration: predicted <b>{}</b>, actual <b>{}</b> "
            '(<span style="color:{};font-weight:600;">{}{:.2f}%</span>). '
            'Tracked weekly so the model can be tuned over time.'
            '</div>'.format(
                fmt_dollar(last_predicted), fmt_dollar(last_actual),
                color, sign, calib_pct
            ),
            unsafe_allow_html=True,
        )


def _render_allowable_spend_table(conn, week_start):
    """Live table: lane/unit, forecast, allowable, hours used, food $ used."""
    # For each dept, calculate forecast + allowable + actual usage
    ws = week_start.isoformat()

    rows_data = []
    for dept in DEPARTMENTS:
        # Forecast = 4-wk rolling avg
        history = _fetch_8wk_history(conn, dept, week_start, weeks=4)
        revs = [h["revenue"] for h in history if h["revenue"] > 0]
        forecast = sum(revs) / len(revs) if revs else 0

        # Targets
        t = _get_targets(conn, dept)
        target_lp = (t.get("target_labor_pct") or 30) / 100
        target_fc = (t.get("target_food_cost_pct") or 32) / 100
        wage = t.get("avg_hourly_wage") or 17
        salaries = t.get("salaries_dollars") or 0
        office = t.get("office_labor_dollars") or 0

        is_board = dept == "Board & Catering"
        allow_total = forecast * target_lp
        allow_hourly = max(0, allow_total - salaries - office) if is_board else allow_total
        allow_hrs = allow_hourly / wage if wage > 0 else 0
        allow_food = forecast * target_fc

        # Used so far (current week actuals)
        actual = _fetch_dept_totals(conn, week_start, dept)
        used_hrs = actual.get("labor_h", 0) or 0
        used_food = actual.get("cos", 0) or 0

        rows_data.append({
            "unit": dept,
            "forecast": forecast,
            "allow_hrs": allow_hrs,
            "allow_hourly_d": allow_hourly,
            "used_hrs": used_hrs,
            "allow_food": allow_food,
            "used_food": used_food,
        })

    rows_html = "".join(
        _allowable_progress_row(
            r["unit"], r["forecast"], r["allow_hrs"], r["used_hrs"],
            r["allow_food"], r["used_food"], r["allow_hourly_d"]
        )
        for r in rows_data
    )

    legend = (
        '<div style="margin-top:12px;font-size:11px;color:#94A3B8;'
        'display:flex;gap:18px;align-items:center;">'
        '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
        'background:#16A34A;margin-right:6px;vertical-align:middle;"></span>Within target</span>'
        '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
        'background:#D97706;margin-right:6px;vertical-align:middle;"></span>Watch (within 2pp / 60% used)</span>'
        '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
        'background:#DC2626;margin-right:6px;vertical-align:middle;"></span>Over budget — managers blocked from scheduling more hours / placing additional orders</span>'
        '</div>'
    )

    st.markdown(
        '<table style="width:100%;background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:10px;border-collapse:separate;border-spacing:0;overflow:hidden;">'
        '<thead><tr style="background:#F8FAFC;">'
        '<th style="padding:11px 16px;font-size:10px;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.06em;text-align:left;font-weight:600;">LANE / UNIT</th>'
        '<th style="padding:11px 16px;font-size:10px;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.06em;text-align:right;font-weight:600;">FORECAST REV</th>'
        '<th style="padding:11px 16px;font-size:10px;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.06em;text-align:right;font-weight:600;">ALLOWABLE</th>'
        '<th style="padding:11px 16px;font-size:10px;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.06em;text-align:left;font-weight:600;">HOURS USED</th>'
        '<th style="padding:11px 16px;font-size:10px;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.06em;text-align:left;font-weight:600;">FOOD $ USED</th>'
        '</tr></thead>'
        '<tbody>{}</tbody></table>{}'.format(rows_html, legend),
        unsafe_allow_html=True,
    )


def _render_notes_yoy(conn, this_week, last_year_week, fy, fw, prior_fy):
    """Side-by-side notes: this week vs same fiscal week last year."""
    # Fetch notes for both weeks
    this_notes = _fetch_notes_week(conn, this_week)
    last_notes = _fetch_notes_week(conn, last_year_week) if last_year_week else []

    c1, c2 = st.columns(2)

    def _render_notes_col(notes, title):
        st.markdown(
            '<div style="font-size:11px;font-weight:700;color:#94A3B8;'
            'text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">{}</div>'.format(title),
            unsafe_allow_html=True,
        )
        if not notes:
            st.markdown(
                '<div style="background:#F8FAFC;border:1px dashed #CBD5E1;'
                'border-radius:8px;padding:18px;text-align:center;color:#94A3B8;'
                'font-size:12px;">No notes recorded.</div>',
                unsafe_allow_html=True,
            )
            return
        for n in notes:
            day_label = n["date_label"]
            author = n.get("user", "Manager")
            note = n["note"]
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                'border-radius:8px;padding:12px 14px;margin-bottom:8px;">'
                '<div style="font-size:10px;font-weight:600;color:#94A3B8;'
                'text-transform:uppercase;letter-spacing:.06em;">{} — {} • {}</div>'
                '<div style="font-size:13px;color:#1E293B;margin-top:6px;line-height:1.4;">{}</div>'
                '</div>'.format(
                    "{} W{}".format(fy, fw), day_label, author, note),
                unsafe_allow_html=True,
            )

    with c1:
        _render_notes_col(this_notes, "{} W{} (Current)".format(fy, fw))
    with c2:
        _render_notes_col(last_notes, "{} W{} (Last Year, Same Fiscal Week)".format(prior_fy, fw))


def _fetch_notes_week(conn, week_start):
    """Fetch all daily notes for a 7-day window."""
    if week_start is None:
        return []
    end = (week_start + timedelta(days=6)).isoformat()
    start = week_start.isoformat()

    # Daily notes are stored in daily_notes table
    notes = []
    try:
        rows = conn.execute(
            """SELECT entry_date, category, notes, COALESCE(updated_by,'') as user
               FROM daily_notes
               WHERE entry_date >= ? AND entry_date <= ? AND notes != '' AND notes IS NOT NULL
               ORDER BY entry_date""",
            (start, end)
        ).fetchall()
        for r in rows:
            d = pd.to_datetime(r[0])
            notes.append({
                "date_label": "{} • {}".format(
                    d.strftime("%a").upper(),
                    (r[1] or "general").upper()),
                "note": r[2],
                "user": r[3],
            })
    except Exception:
        pass

    return notes[:8]  # Max 8 notes


def _has_tender_table(conn):
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='odyssey_tender_totals'"
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _render_kpi_drilldown(conn, week_start, last_year_week=None):
    """Drill-down view: daily breakdown across all KPIs for the week."""
    days = [(week_start + timedelta(days=i)) for i in range(7)]

    # Build daily rows
    rows = []
    for d in days:
        day_iso = d.isoformat()
        # Daily revenue from daily_sales
        try:
            rev_row = conn.execute(
                """SELECT
                      SUM(COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                          COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                          COALESCE(other_revenue,0)) AS revenue
                   FROM daily_sales WHERE entry_date = ?""",
                (day_iso,)
            ).fetchone()
            day_rev = rev_row[0] or 0 if rev_row else 0
        except Exception:
            day_rev = 0

        # Daily door counts
        try:
            door_row = conn.execute(
                "SELECT COALESCE(SUM(count),0) FROM door_counts WHERE entry_date = ?",
                (day_iso,)
            ).fetchone()
            day_covers = door_row[0] if door_row else 0
        except Exception:
            day_covers = 0

        # Daily tender (if available)
        try:
            tender_row = conn.execute(
                """SELECT COALESCE(SUM(board_count + points_count + bonpts_count),0)
                   FROM odyssey_tender_totals WHERE report_date = ?""",
                (day_iso,)
            ).fetchone()
            day_tender = tender_row[0] if tender_row else 0
        except Exception:
            day_tender = 0

        rows.append({
            "Day": d.strftime("%a %b %d"),
            "Revenue": "${:,.0f}".format(day_rev) if day_rev else "—",
            "Door Counts": "{:,}".format(int(day_covers)) if day_covers else "—",
            "Tender Trans.": "{:,}".format(int(day_tender)) if day_tender else "—",
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Per-department detail
    st.markdown(
        '<div style="font-size:11px;font-weight:600;color:#94A3B8;'
        'text-transform:uppercase;letter-spacing:.06em;margin:18px 0 8px;">'
        'BY DEPARTMENT — WEEK TOTALS</div>',
        unsafe_allow_html=True,
    )
    dept_rows = []
    for d in DEPARTMENTS:
        t = _fetch_dept_totals(conn, week_start, d)
        rev = t.get("revenue", 0) or 0
        cos = t.get("cos", 0) or 0
        lab_d = t.get("labor_d", 0) or 0
        lab_h = t.get("labor_h", 0) or 0
        fc_pct = (cos / rev * 100) if rev > 0 else 0
        lp_pct = (lab_d / rev * 100) if rev > 0 else 0
        dept_rows.append({
            "Department": d,
            "Revenue": "${:,.0f}".format(rev) if rev else "—",
            "COS $": "${:,.0f}".format(cos) if cos else "—",
            "FC %": "{:.1f}%".format(fc_pct) if rev > 0 else "—",
            "Labor $": "${:,.0f}".format(lab_d) if lab_d else "—",
            "Labor %": "{:.1f}%".format(lp_pct) if rev > 0 else "—",
            "Labor Hrs": "{:,.0f}".format(lab_h) if lab_h else "—",
        })
    st.dataframe(pd.DataFrame(dept_rows), use_container_width=True, hide_index=True)
