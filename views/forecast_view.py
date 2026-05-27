"""
Forecast & Allowable Spend Calculator.

For each department, calculates:
  - Forecast revenue (based on historical 4-week rolling average + recent velocity)
  - Allowable Labor $ = Forecast × Target Labor %
  - Allowable Labor Hours = (Allowable Labor $ - Salaries - Office Labor) / Avg Hourly Wage
  - Allowable Food $ = Forecast × Target Food Cost %
"""

from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEPARTMENTS
from styles import (
    page_header, dash_kpi_card, dash_section_header,
    dash_chart_start, dash_chart_end,
)
from calculations import sum_revenue_streams, fmt_dollar, fmt_pct, fmt_number
import db


# ─── Plotly theme ───
def _apply_theme(fig, height=320):
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#64748B"),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor="#1F2A44", font_color="#FFFFFF"),
        xaxis=dict(gridcolor="rgba(148,163,184,0.15)", showline=False),
        yaxis=dict(gridcolor="rgba(148,163,184,0.15)", showline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5, font=dict(size=11)),
    )
    return fig


def _init_forecast_tables(conn):
    """Add fields to targets table for forecast/allowable calculations."""
    # Add columns if they don't exist
    cols_to_add = [
        ("target_food_cost_pct", "REAL DEFAULT 30.0"),
        ("salaries_dollars", "REAL DEFAULT 0.0"),
        ("office_labor_dollars", "REAL DEFAULT 0.0"),
        ("avg_hourly_wage", "REAL DEFAULT 17.0"),
    ]
    for col, dtype in cols_to_add:
        try:
            conn.execute("ALTER TABLE targets ADD COLUMN {} {}".format(col, dtype))
        except Exception:
            pass  # Column already exists

    # Seed defaults if no rows
    existing = conn.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
    if existing == 0:
        defaults = [
            ("Board & Catering", 35.0, 12.0, 32.0, 5000.0, 1500.0, 17.0),
            ("Starbucks", 30.0, 10.0, 35.0, 0.0, 0.0, 16.0),
            ("Qdoba", 30.0, 10.0, 32.0, 0.0, 0.0, 16.0),
            ("Retail & Mac's Grill", 32.0, 11.0, 33.0, 0.0, 0.0, 16.5),
        ]
        for d, lp, splh, fc, sal, ofc, wage in defaults:
            conn.execute(
                """INSERT OR REPLACE INTO targets
                   (department, target_labor_pct, target_splh,
                    target_food_cost_pct, salaries_dollars,
                    office_labor_dollars, avg_hourly_wage)
                   VALUES (?,?,?,?,?,?,?)""",
                (d, lp, splh, fc, sal, ofc, wage),
            )
    conn.commit()


def _get_targets(conn, dept):
    """Get targets row for department."""
    row = conn.execute(
        "SELECT * FROM targets WHERE department = ?", (dept,)
    ).fetchone()
    if row:
        return dict(row)
    return {
        "target_labor_pct": 30.0,
        "target_splh": 10.0,
        "target_food_cost_pct": 32.0,
        "salaries_dollars": 0.0,
        "office_labor_dollars": 0.0,
        "avg_hourly_wage": 17.0,
    }


def _historical_revenue(conn, dept, weeks_back=8, ref_date=None):
    """Get historical revenue for past N weeks."""
    if ref_date is None:
        ref_date = date.today()
    start = (db.get_week_start(ref_date) - timedelta(weeks=weeks_back)).isoformat()
    end = db.get_week_start(ref_date).isoformat()

    rows = conn.execute(
        """SELECT week_start,
                  COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue,
                  COALESCE(cos_dollars,0) AS cos,
                  COALESCE(total_labor_dollars,0) AS labor_d,
                  COALESCE(total_labor_hours,0) AS labor_h
           FROM weekly_financials
           WHERE department = ? AND week_start < ? AND week_start >= ?
           ORDER BY week_start""",
        (dept, end, start)
    ).fetchall()
    return [dict(r) for r in rows]


def _forecast_next_week(history):
    """Forecast next week using 4-week rolling avg + velocity adjustment."""
    if not history:
        return {"revenue": 0, "method": "no data"}

    revs = [r["revenue"] for r in history if r["revenue"]]
    if not revs:
        return {"revenue": 0, "method": "no revenue"}

    if len(revs) >= 4:
        # 4-week rolling average
        avg = sum(revs[-4:]) / 4
        # Velocity: avg of last 2 vs avg of weeks 3-4 ago
        recent = sum(revs[-2:]) / 2
        prior = sum(revs[-4:-2]) / 2 if len(revs) >= 4 else recent
        velocity = (recent - prior) / 2 if prior else 0
        forecast = max(0, avg + velocity)
        return {
            "revenue": forecast,
            "method": "4-wk avg + velocity",
            "avg": avg,
            "velocity": velocity,
            "weeks_used": 4,
        }
    else:
        avg = sum(revs) / len(revs)
        return {
            "revenue": avg,
            "method": "{}-wk avg".format(len(revs)),
            "avg": avg,
            "velocity": 0,
            "weeks_used": len(revs),
        }


def render(conn, user):
    """Main forecast page."""
    _init_forecast_tables(conn)
    page_header(
        "Forecast & Allowable Spend",
        "Predict next week + calculate labor and food ceilings"
    )

    # Department selector
    dept = st.selectbox("Department", DEPARTMENTS, key="fc_dept")
    is_board = dept == "Board & Catering"

    # Get targets and history
    targets = _get_targets(conn, dept)
    history = _historical_revenue(conn, dept, weeks_back=8)
    forecast = _forecast_next_week(history)

    # ═══════ Targets Configuration ═══════
    with st.expander("⚙️ Adjust Targets", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_lp = st.number_input(
                "Target Labor %", min_value=0.0, max_value=100.0, step=0.5,
                value=float(targets["target_labor_pct"]),
                key="t_labor_pct",
            )
            new_fc = st.number_input(
                "Target Food Cost %", min_value=0.0, max_value=100.0, step=0.5,
                value=float(targets.get("target_food_cost_pct") or 32.0),
                key="t_fc_pct",
            )
        with c2:
            new_wage = st.number_input(
                "Avg Hourly Wage ($)", min_value=0.0, step=0.50,
                value=float(targets.get("avg_hourly_wage") or 17.0),
                key="t_wage",
            )
            new_splh = st.number_input(
                "Target SPLH", min_value=0.0, step=0.5,
                value=float(targets.get("target_splh") or 10.0),
                key="t_splh",
            )
        with c3:
            if is_board:
                new_sal = st.number_input(
                    "Salaries $/wk", min_value=0.0, step=100.0,
                    value=float(targets.get("salaries_dollars") or 0.0),
                    key="t_sal",
                )
                new_ofc = st.number_input(
                    "Office Labor $/wk", min_value=0.0, step=100.0,
                    value=float(targets.get("office_labor_dollars") or 0.0),
                    key="t_ofc",
                )
            else:
                new_sal = 0.0
                new_ofc = 0.0
                st.caption("Retail: no salaried/office subtraction")

        if st.button("Save Targets", key="t_save"):
            conn.execute(
                """INSERT OR REPLACE INTO targets
                   (department, target_labor_pct, target_splh,
                    target_food_cost_pct, salaries_dollars,
                    office_labor_dollars, avg_hourly_wage)
                   VALUES (?,?,?,?,?,?,?)""",
                (dept, new_lp, new_splh, new_fc, new_sal, new_ofc, new_wage),
            )
            conn.commit()
            st.success("Targets saved.")
            st.rerun()

    # Use latest values
    target_labor_pct = float(targets["target_labor_pct"]) / 100
    target_fc_pct = float(targets.get("target_food_cost_pct") or 32) / 100
    salaries = float(targets.get("salaries_dollars") or 0)
    office_labor = float(targets.get("office_labor_dollars") or 0)
    avg_wage = float(targets.get("avg_hourly_wage") or 17)

    # ═══════ Forecast ═══════
    forecast_rev = forecast["revenue"]

    dash_section_header(
        "Next Week Forecast",
        "{} — {}".format(dept, forecast["method"]),
    )

    # Allow manager override
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            '<div style="background:#FFF;border:1px solid #E5E7EB;'
            'border-left:3px solid #C7A462;border-radius:10px;padding:14px 18px;'
            'display:flex;justify-content:space-between;align-items:center;">'
            '<div>'
            '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
            'letter-spacing:.08em;font-weight:600;">Forecast Revenue</div>'
            '<div style="font-size:28px;font-weight:700;color:#1E293B;'
            'margin-top:4px;">{}</div>'
            '<div style="font-size:11px;color:#94A3B8;margin-top:2px;">'
            'Based on {} weeks of history</div>'
            '</div></div>'.format(
                fmt_dollar(forecast_rev),
                forecast.get("weeks_used", 0)),
            unsafe_allow_html=True,
        )
    with c2:
        override = st.number_input(
            "Override ($)", min_value=0.0, step=100.0,
            value=float(forecast_rev),
            key="fc_override",
        )
        if abs(override - forecast_rev) > 0.01:
            forecast_rev = override

    # ═══════ Allowable Spend ═══════
    st.markdown("")
    dash_section_header(
        "Allowable Spend",
        "Hard ceilings based on forecast × targets",
    )

    # Calculations
    allowable_labor_dollars = forecast_rev * target_labor_pct
    allowable_food_dollars = forecast_rev * target_fc_pct

    if is_board:
        allowable_hourly = max(0, allowable_labor_dollars - salaries - office_labor)
    else:
        allowable_hourly = allowable_labor_dollars

    allowable_hours = allowable_hourly / avg_wage if avg_wage > 0 else 0

    # 4-card display
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        dash_kpi_card(
            "Total Labor $", fmt_dollar(allowable_labor_dollars),
            change="{:.1f}% of revenue".format(target_labor_pct * 100),
            accent="navy",
        )
    with k2:
        dash_kpi_card(
            "Hourly Labor $", fmt_dollar(allowable_hourly),
            change="After salaries & office" if is_board else "All variable",
            accent="blue",
        )
    with k3:
        dash_kpi_card(
            "Allowable Hours", "{:.0f}".format(allowable_hours),
            change="@ ${:.2f}/hr avg".format(avg_wage),
            accent="gold",
        )
    with k4:
        dash_kpi_card(
            "Food $ Ceiling", fmt_dollar(allowable_food_dollars),
            change="{:.1f}% of revenue".format(target_fc_pct * 100),
            accent="green",
        )

    # ═══════ Math breakdown ═══════
    with st.expander("📐 See the math"):
        st.markdown("""
**Forecast Revenue** = `{rev}`

**Total Allowable Labor $** = Forecast × Target Labor %
= `{rev}` × `{lp}%` = **`{tot_lab}`**
""".format(
            rev=fmt_dollar(forecast_rev),
            lp=target_labor_pct * 100,
            tot_lab=fmt_dollar(allowable_labor_dollars),
        ))

        if is_board:
            st.markdown("""
**Allowable Hourly Labor $** = Total Labor − Salaries − Office Labor
= `{tot}` − `{sal}` − `{ofc}` = **`{hourly}`**
""".format(
                tot=fmt_dollar(allowable_labor_dollars),
                sal=fmt_dollar(salaries),
                ofc=fmt_dollar(office_labor),
                hourly=fmt_dollar(allowable_hourly),
            ))

        st.markdown("""
**Allowable Hours** = Hourly $ ÷ Avg Wage
= `{h}` ÷ `${w:.2f}` = **`{hrs:.0f} hrs`**

**Allowable Food $** = Forecast × Target FC %
= `{rev}` × `{fc}%` = **`{food}`**
""".format(
            h=fmt_dollar(allowable_hourly),
            w=avg_wage,
            hrs=allowable_hours,
            rev=fmt_dollar(forecast_rev),
            fc=target_fc_pct * 100,
            food=fmt_dollar(allowable_food_dollars),
        ))

    # ═══════ Historical chart ═══════
    if history:
        dash_chart_start("8-Week Revenue History", "With forecast")
        df = pd.DataFrame(history)
        df["week_label"] = pd.to_datetime(df["week_start"]).dt.strftime("%b %d")

        next_week = (date.today() + timedelta(days=7)).strftime("%b %d (forecast)")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["week_label"], y=df["revenue"],
            name="Actual Revenue", marker_color="#1F2A44",
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
        ))
        # Forecast bar
        fig.add_trace(go.Bar(
            x=[next_week], y=[forecast_rev],
            name="Forecast", marker_color="#1F2A44",
            marker_pattern_shape="/",
            hovertemplate="<b>Forecast</b><br>$%{y:,.0f}<extra></extra>",
        ))

        # Trendline (rolling avg)
        if len(df) >= 3:
            rolling = df["revenue"].rolling(window=3, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=df["week_label"], y=rolling,
                name="3-wk avg trend", mode="lines",
                line=dict(color="#C7A462", width=2, dash="dot"),
            ))

        _apply_theme(fig, height=300)
        fig.update_yaxes(tickformat="$,.0f")
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})
        dash_chart_end()
    else:
        st.info("No historical data yet for {}. Add weekly financials to enable forecasting.".format(dept))

    # ═══════ Variance check vs current week budget ═══════
    current_week = db.get_week_start(date.today())
    current_budget = conn.execute(
        "SELECT * FROM budgets WHERE department=? AND week_start=?",
        (dept, current_week.isoformat())
    ).fetchone()

    if current_budget:
        cb = dict(current_budget)
        b_rev = cb.get("revenue") or 0
        b_lab_d = cb.get("labor_dollars") or 0
        b_lab_h = cb.get("labor_hours") or 0

        if b_rev > 0:
            dash_section_header(
                "Current Week Comparison",
                "Allowable vs Budgeted ({})".format(current_week.isoformat())
            )

            v_lab = b_lab_d - allowable_labor_dollars
            v_hrs = b_lab_h - allowable_hours

            c1, c2 = st.columns(2)
            with c1:
                color = "#16A34A" if v_lab <= 0 else "#EF4444"
                arrow = "▼" if v_lab <= 0 else "▲"
                st.markdown(
                    '<div style="background:#FFF;border:1px solid #E5E7EB;'
                    'border-radius:10px;padding:14px 18px;">'
                    '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    'letter-spacing:.08em;font-weight:600;">Labor $ vs Allowable</div>'
                    '<div style="display:flex;justify-content:space-between;'
                    'align-items:center;margin-top:6px;">'
                    '<span style="font-size:22px;font-weight:700;color:#1E293B;">{}</span>'
                    '<span style="font-size:14px;font-weight:600;color:{};">{}{}</span>'
                    '</div></div>'.format(
                        fmt_dollar(b_lab_d), color, arrow, fmt_dollar(abs(v_lab))),
                    unsafe_allow_html=True,
                )
            with c2:
                color = "#16A34A" if v_hrs <= 0 else "#EF4444"
                arrow = "▼" if v_hrs <= 0 else "▲"
                st.markdown(
                    '<div style="background:#FFF;border:1px solid #E5E7EB;'
                    'border-radius:10px;padding:14px 18px;">'
                    '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    'letter-spacing:.08em;font-weight:600;">Hours vs Allowable</div>'
                    '<div style="display:flex;justify-content:space-between;'
                    'align-items:center;margin-top:6px;">'
                    '<span style="font-size:22px;font-weight:700;color:#1E293B;">{:.0f}</span>'
                    '<span style="font-size:14px;font-weight:600;color:{};">{}{:.0f}</span>'
                    '</div></div>'.format(
                        b_lab_h, color, arrow, abs(v_hrs)),
                    unsafe_allow_html=True,
                )
