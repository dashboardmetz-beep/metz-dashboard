"""
Forecast & Allowable Spend — Premium layout.
KPI row + Adjust Targets + Allowable Spend cards + math reveal.
"""

from datetime import date, timedelta
import streamlit as st

from config import DEPARTMENTS
from calculations import fmt_dollar
from styles import hero_header
import db


def _icon(name):
    icons = {
        "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "users": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "utensils": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
        "clock": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "calc": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="10" y2="10"/><line x1="13" y1="10" x2="15" y2="10"/><line x1="8" y1="14" x2="10" y2="14"/><line x1="13" y1="14" x2="15" y2="14"/><line x1="8" y1="18" x2="10" y2="18"/><line x1="13" y1="18" x2="15" y2="18"/></svg>',
        "info": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "building": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/></svg>',
        "clk": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "cloud-up": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/><polyline points="16 16 12 12 8 16"/><path d="M12 12v9"/></svg>',
        "gear": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B5246" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
        "chevron-r": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>',
    }
    return icons.get(name, "")


def _init_tables(conn):
    cols = [
        ("target_food_cost_pct", "REAL DEFAULT 30.0"),
        ("salaries_dollars", "REAL DEFAULT 0.0"),
        ("office_labor_dollars", "REAL DEFAULT 0.0"),
        ("avg_hourly_wage", "REAL DEFAULT 17.0"),
    ]
    for col, dtype in cols:
        try:
            conn.execute("ALTER TABLE targets ADD COLUMN {} {}".format(col, dtype))
        except Exception:
            pass
    conn.commit()


def _get_targets(conn, dept):
    row = conn.execute(
        "SELECT * FROM targets WHERE department=?", (dept,)
    ).fetchone()
    return dict(row) if row else {
        "target_labor_pct": 30.0, "target_splh": 10.0,
        "target_food_cost_pct": 30.0, "salaries_dollars": 0,
        "office_labor_dollars": 0, "avg_hourly_wage": 17.0,
    }


def _historical(conn, dept, weeks=8, ref=None):
    if ref is None:
        ref = date.today()
    start = (db.get_week_start(ref) - timedelta(weeks=weeks)).isoformat()
    end = db.get_week_start(ref).isoformat()
    rows = conn.execute(
        """SELECT week_start,
                  COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                  COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                  COALESCE(other_revenue,0) AS revenue
           FROM weekly_financials
           WHERE department=? AND week_start < ? AND week_start >= ?
           ORDER BY week_start""",
        (dept, end, start)
    ).fetchall()
    return [dict(r) for r in rows]


def _forecast(history):
    revs = [r["revenue"] for r in history if r.get("revenue")]
    if not revs:
        return {"revenue": 0, "weeks": 0}
    if len(revs) >= 4:
        avg = sum(revs[-4:]) / 4
        recent = sum(revs[-2:]) / 2
        prior = sum(revs[-4:-2]) / 2
        velocity = (recent - prior) / 2 if prior else 0
        return {"revenue": max(0, avg + velocity), "weeks": len(revs)}
    return {"revenue": sum(revs) / len(revs), "weeks": len(revs)}


def render(conn, user):
    _init_tables(conn)

    today = date.today()
    if "fc_week" not in st.session_state:
        st.session_state.fc_week = db.get_week_start(today)
    if "fc_dept" not in st.session_state:
        st.session_state.fc_dept = "Board & Catering"

    week_start = st.session_state.fc_week
    week_end = week_start + timedelta(days=6)
    dept = st.session_state.fc_dept

    # ─── Hero header ───
    def _fc_right():
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
            if st.button("‹  Prev Week", key="fc_prev_week",
                         use_container_width=True):
                st.session_state.fc_week -= timedelta(weeks=1)
                st.rerun()
        with d3:
            if st.button("Next Week  ›", key="fc_next_week",
                         use_container_width=True):
                st.session_state.fc_week += timedelta(weeks=1)
                st.rerun()
        with d4:
            if st.button("💾  Save Forecast", key="fc_save_v2",
                         use_container_width=True, type="primary"):
                st.toast("Forecast saved", icon="✅")

    hero_header(
        "Forecast & Allowable Spend",
        "Predict next week + calculate labor and food ceilings",
        _fc_right,
    )

    # ─── Info bar ───
    info_html = (
        '<div class="fr-info-bar">'
        '<div class="fr-info-item">{bld}<span class="fii-label">Department:</span>'
        '<span class="fii-value"><b>{dept}</b></span></div>'
        '<div class="fr-info-item">{clk}<span class="fii-label">Last Updated:</span>'
        '<span class="fii-value">—</span></div>'
        '</div>'.format(bld=_icon("building"), clk=_icon("clk"), dept=dept)
    )
    st.markdown(info_html, unsafe_allow_html=True)

    # Department selector
    new_dept = st.selectbox("Department", DEPARTMENTS,
                             index=DEPARTMENTS.index(dept) if dept in DEPARTMENTS else 0,
                             key="fc_dept_sel")
    if new_dept != dept:
        st.session_state.fc_dept = new_dept
        st.rerun()
    dept = new_dept

    # ─── Calculations ───
    targets = _get_targets(conn, dept)
    history = _historical(conn, dept, weeks=8)
    forecast = _forecast(history)
    forecast_rev = forecast["revenue"]
    is_board = dept == "Board & Catering"

    target_lp = (targets.get("target_labor_pct") or 30) / 100
    target_fc = (targets.get("target_food_cost_pct") or 30) / 100
    wage = targets.get("avg_hourly_wage") or 17.0
    salaries = targets.get("salaries_dollars") or 0
    office = targets.get("office_labor_dollars") or 0

    total_labor_d = forecast_rev * target_lp
    hourly_labor_d = max(0, total_labor_d - salaries - office) if is_board else total_labor_d
    allow_hours = hourly_labor_d / wage if wage > 0 else 0
    food_ceiling = forecast_rev * target_fc

    # ─── 5 KPI cards ───
    cards = st.columns(5)
    metrics = [
        ("Forecast Revenue", "${:,.2f}".format(forecast_rev),
         "Based on {} weeks of history".format(forecast["weeks"]),
         "dollar", "#ECFDF5"),
        ("Total Labor $", "${:,.2f}".format(total_labor_d),
         "{:.1f}% of revenue".format(target_lp * 100),
         "users", "#F5F3FF"),
        ("Food $ Ceiling", "${:,.2f}".format(food_ceiling),
         "{:.1f}% of revenue".format(target_fc * 100),
         "utensils", "#FFFBEB"),
        ("Allowable Hours", "{:,.0f}".format(allow_hours),
         "@ ${:.2f}/hr avg".format(wage),
         "clock", "#F0F9FF"),
        ("Hourly Labor $", "${:,.2f}".format(hourly_labor_d),
         "After salaries & office" if is_board else "All variable",
         "calc", "#EFF6FF"),
    ]
    for i, (label, value, sub, icon, bg) in enumerate(metrics):
        with cards[i]:
            st.markdown(
                '<div class="fc-kpi">'
                '<div class="fc-kpi-row">'
                '<div class="fc-kpi-icon" style="background:{bg};">{icon}</div>'
                '<div class="fc-kpi-meta">'
                '<div class="fc-kpi-label">{label}</div>'
                '<div class="fc-kpi-value">{value}</div>'
                '<div class="fc-kpi-sub">{sub}</div>'
                '</div></div></div>'.format(
                    bg=bg, icon=_icon(icon), label=label, value=value, sub=sub,
                ),
                unsafe_allow_html=True,
            )

    # ─── Adjust Targets section ───
    st.markdown(
        '<div class="fc-targets-row">'
        '<div class="fc-targets-left">'
        '<span class="fc-targets-chev">▾</span>{gear}<b>Adjust Targets</b>'
        '<span class="fc-targets-sub">Set labor %, food cost % and hourly rate assumptions</span>'
        '</div></div>'.format(gear=_icon("gear")),
        unsafe_allow_html=True,
    )

    with st.expander("Edit targets", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_lp = st.number_input("Target Labor %", min_value=0.0, max_value=100.0,
                                      step=0.5, value=float(targets["target_labor_pct"] or 30),
                                      key="fc_t_lp")
            new_fc = st.number_input("Target Food Cost %", min_value=0.0, max_value=100.0,
                                      step=0.5, value=float(targets.get("target_food_cost_pct") or 30),
                                      key="fc_t_fc")
        with c2:
            new_wage = st.number_input("Avg Hourly Wage ($)", min_value=0.0, step=0.5,
                                        value=float(wage), key="fc_t_wage")
            new_splh = st.number_input("Target SPLH", min_value=0.0, step=0.5,
                                        value=float(targets.get("target_splh") or 10),
                                        key="fc_t_splh")
        with c3:
            if is_board:
                new_sal = st.number_input("Salaries $/wk", min_value=0.0, step=100.0,
                                           value=float(salaries), key="fc_t_sal")
                new_ofc = st.number_input("Office Labor $/wk", min_value=0.0, step=100.0,
                                           value=float(office), key="fc_t_ofc")
            else:
                new_sal = 0
                new_ofc = 0
                st.caption("Retail — no salaried/office subtraction")

        if st.button("Save Targets", key="fc_t_save", type="primary"):
            conn.execute(
                """INSERT OR REPLACE INTO targets
                   (department, target_labor_pct, target_splh,
                    target_food_cost_pct, salaries_dollars,
                    office_labor_dollars, avg_hourly_wage)
                   VALUES (?,?,?,?,?,?,?)""",
                (dept, new_lp, new_splh, new_fc, new_sal, new_ofc, new_wage),
            )
            conn.commit()
            st.success("Saved.")
            st.rerun()

    # ─── Allowable Spend section ───
    st.markdown(
        '<div class="fc-section-header">'
        '<div><span class="fc-section-title">Allowable Spend {info}</span></div>'
        '<span class="fc-section-meta">Hard ceilings based on forecast × targets</span>'
        '</div>'.format(info=_icon("info")),
        unsafe_allow_html=True,
    )

    a1, a2, a3, a4 = st.columns(4)
    spend_cards = [
        ("Total Labor $", "${:,.2f}".format(total_labor_d),
         "{:.1f}% of forecasted revenue".format(target_lp * 100), "#8B5CF6"),
        ("Hourly Labor $", "${:,.2f}".format(hourly_labor_d),
         "After salaries & office allocation" if is_board else "All variable", "#3B82F6"),
        ("Allowable Hours", "{:,.0f}".format(allow_hours),
         "@ ${:.2f}/hr average".format(wage), "#0EA5E9"),
        ("Food $ Ceiling", "${:,.2f}".format(food_ceiling),
         "{:.1f}% of forecasted revenue".format(target_fc * 100), "#D97706"),
    ]
    for i, (label, value, sub, color) in enumerate(spend_cards):
        col = [a1, a2, a3, a4][i]
        with col:
            st.markdown(
                '<div class="fc-spend-card">'
                '<div class="fc-spend-label" style="color:{c};">{label}</div>'
                '<div class="fc-spend-value">{value}</div>'
                '<div class="fc-spend-sub">{sub}</div>'
                '</div>'.format(c=color, label=label, value=value, sub=sub),
                unsafe_allow_html=True,
            )

    # ─── See the math expander ───
    with st.expander("📐 See the math — View how allowable amounts are calculated"):
        st.markdown("""
**Forecast Revenue** = `${rev:,.2f}` (based on rolling 4-wk avg + velocity)

**Total Allowable Labor $** = Forecast × Target Labor %
= `${rev:,.2f}` × `{lp:.1f}%` = **`${tot:,.2f}`**
""".format(rev=forecast_rev, lp=target_lp * 100, tot=total_labor_d))
        if is_board:
            st.markdown("""
**Hourly Labor $** = Total Labor − Salaries − Office Labor
= `${tot:,.2f}` − `${s:,.2f}` − `${o:,.2f}` = **`${h:,.2f}`**
""".format(tot=total_labor_d, s=salaries, o=office, h=hourly_labor_d))
        st.markdown("""
**Allowable Hours** = Hourly $ ÷ Avg Wage
= `${h:,.2f}` ÷ `${w:.2f}` = **`{hrs:.0f} hrs`**

**Food $ Ceiling** = Forecast × Target FC %
= `${rev:,.2f}` × `{fc:.1f}%` = **`${food:,.2f}`**
""".format(h=hourly_labor_d, w=wage, hrs=allow_hours,
            rev=forecast_rev, fc=target_fc * 100, food=food_ceiling))

    # ─── No data banner ───
    if not history:
        st.markdown(
            '<div class="fc-banner">'
            '<div class="fc-banner-text">'
            '<b>No historical data yet for {}.</b><br>'
            '<span>Add weekly financials to enable more accurate forecasting.</span>'
            '</div>'
            '<div class="fc-banner-action">📊 Add Weekly Financials</div>'
            '</div>'.format(dept),
            unsafe_allow_html=True,
        )

    # ─── Footer ───
    st.markdown(
        '<div class="fc-footer-note">ℹ Forecasts are projections only. '
        'Actual results may vary.</div>',
        unsafe_allow_html=True,
    )
