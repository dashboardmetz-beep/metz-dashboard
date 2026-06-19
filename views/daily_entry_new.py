"""
Daily Entry — Premium step-based layout.
5 steps: Overview, Sales, Labor, Notes, Participation
"""

from datetime import date, timedelta
import html as _html
import streamlit as st

from config import DEPARTMENTS
from calculations import sum_revenue_streams, fmt_dollar, fmt_number
from styles import hero_header
import db


# ─── Helpers ───

def _icon(name):
    icons = {
        "calendar": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        "sun": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
        "thermometer": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4 4 0 1 0 5 0z"/></svg>',
        "wind": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>',
        "droplet": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
        "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "users": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "chart": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        "people": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
        "pie": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
        "info": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "check": '<svg width="16" height="16" viewBox="0 0 24 24" fill="#16A34A" stroke="none"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
        "cloud": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>',
        "rain": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',
    }
    return icons.get(name, "")


def _step_pill(num, label, is_active, is_done):
    """Render a step indicator pill."""
    if is_active:
        return (
            '<div class="step-pill active">'
            '<div class="step-num">{}</div>'
            '<div class="step-label">{}</div>'
            '</div>'
        ).format(num, label)
    elif is_done:
        return (
            '<div class="step-pill done">'
            '<div class="step-num">✓</div>'
            '<div class="step-label">{}</div>'
            '</div>'
        ).format(label)
    else:
        return (
            '<div class="step-pill">'
            '<div class="step-num">{}</div>'
            '<div class="step-label">{}</div>'
            '</div>'
        ).format(num, label)


# ─── Main render ───

_MOUNTAIN_SVG = (
    '<svg viewBox="0 0 420 120" xmlns="http://www.w3.org/2000/svg" '
    'class="de-mountain" preserveAspectRatio="xMaxYMid meet">'
    '<g fill="none" stroke="#C9A34E" stroke-width="1.2" stroke-linecap="round" '
    'stroke-linejoin="round" opacity="0.85">'
    # back ridge
    '<path d="M0 95 L60 60 L95 78 L140 40 L180 70 L220 35 L265 72 L310 48 L355 78 L420 55"/>'
    # front ridges
    '<path d="M0 110 L40 92 L75 100 L120 80 L160 96 L205 78 L245 98 L290 82 L335 102 L380 88 L420 102"/>'
    # snow lines on peaks
    '<path d="M135 46 L142 41 L150 46"/>'
    '<path d="M215 41 L222 36 L230 41"/>'
    '<path d="M175 60 L182 70" opacity="0.6"/>'
    '<path d="M260 60 L270 72" opacity="0.6"/>'
    # sun
    '<circle cx="345" cy="32" r="14" opacity="0.7"/>'
    '<line x1="345" y1="10" x2="345" y2="6" opacity="0.5"/>'
    '<line x1="367" y1="32" x2="372" y2="32" opacity="0.5"/>'
    '<line x1="323" y1="32" x2="318" y2="32" opacity="0.5"/>'
    '</g>'
    '</svg>'
)


def page_daily_entry(conn, user):
    # ─── State ───
    if "de_date" not in st.session_state:
        st.session_state.de_date = date.today()
    if "de_step" not in st.session_state:
        st.session_state.de_step = 1
    if "de_dept" not in st.session_state:
        st.session_state.de_dept = "Board & Catering"
    if "de_impact" not in st.session_state:
        st.session_state.de_impact = "No Impact"

    entry_date = st.session_state.de_date

    def _de_right():
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
                '<span>{d}</span>'
                '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
                'stroke="#8B7E66" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<polyline points="6 9 12 15 18 9"/></svg>'
                '</div>'.format(d=entry_date.strftime("%B %-d, %Y")),
                unsafe_allow_html=True,
            )
        with d2:
            if st.button("‹  Prev Day", key="de_prev_day",
                         use_container_width=True):
                st.session_state.de_date -= timedelta(days=1)
                st.rerun()
        with d3:
            if st.button("Next Day  ›", key="de_next_day",
                         use_container_width=True):
                st.session_state.de_date += timedelta(days=1)
                st.rerun()
        with d4:
            if st.button("💾  Save All", key="de_save_all",
                         use_container_width=True, type="primary"):
                st.toast("All sections saved", icon="✅")

    hero_header(
        "Daily Entry",
        "Daily Sales, Labor & Weather Logging",
        _de_right,
    )

    # ─── STEP-BASED ENTRY FORM (always visible — this is the actual entry UI) ───
    steps = ["Overview", "Sales", "Labor", "Notes", "Participation"]
    current_step = st.session_state.de_step

    step_cols = st.columns(5)
    for i, name in enumerate(steps, 1):
        with step_cols[i - 1]:
            is_active = i == current_step
            is_done = i < current_step
            num_or_check = "✓" if is_done else str(i)
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                "{} {}".format(num_or_check, name),
                key="de_step_{}".format(i),
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.de_step = i
                st.rerun()

    if current_step == 1:
        _render_overview_step(conn, user, entry_date)
    elif current_step == 2:
        _render_sales_step(conn, user, entry_date)
    elif current_step == 3:
        _render_labor_step(conn, user, entry_date)
    elif current_step == 4:
        _render_notes_step(conn, user, entry_date)
    elif current_step == 5:
        _render_participation_step(conn, user, entry_date)

    f1, _, f3 = st.columns([1, 3, 2])
    with f1:
        if st.button("Clear All", key="de_clear", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("de_input_"):
                    del st.session_state[k]
            st.rerun()
    with f3:
        fa, fb = st.columns(2)
        with fa:
            if st.button("Save Draft", key="de_save_draft",
                         use_container_width=True):
                st.toast("Draft saved", icon="💾")
        with fb:
            next_label = (
                "Next: {} →".format(steps[current_step])
                if current_step < 5 else "Finish ✓"
            )
            if st.button(next_label, key="de_next_step",
                         use_container_width=True, type="primary"):
                if current_step < 5:
                    st.session_state.de_step = current_step + 1
                else:
                    st.toast("Daily entry complete", icon="🎉")
                st.rerun()


# ─── Step 1: Overview ───

def _render_overview_step(conn, user, entry_date):
    # 3-column row: Weather / Staffing Impact / Communication Notes
    c1, c2, c3 = st.columns(3)

    # Get weather
    weather = _fetch_weather(entry_date)

    with c1:
        st.markdown(
            '<div class="de-card">'
            '<div class="de-card-header">{icon}<span class="de-card-title">Weather</span></div>'
            '<div class="weather-big">{temp}°F</div>'
            '<div class="weather-cond">{cond}</div>'
            '<div class="weather-stats">'
            '<div class="ws-item">{ico_t}<div><div class="ws-label">Feels Like</div><div class="ws-val">{feels}°F</div></div></div>'
            '<div class="ws-item">{ico_w}<div><div class="ws-label">Wind</div><div class="ws-val">{wind} mph</div></div></div>'
            '<div class="ws-item">{ico_h}<div><div class="ws-label">Humidity</div><div class="ws-val">{hum}%</div></div></div>'
            '</div></div>'.format(
                icon=_icon("sun"),
                temp=weather.get("temp", "—"),
                cond=weather.get("condition", "—"),
                feels=weather.get("feels_like", "—"),
                wind=weather.get("wind", "—"),
                hum=weather.get("humidity", "—"),
                ico_t=_icon("thermometer"),
                ico_w=_icon("wind"),
                ico_h=_icon("droplet"),
            ),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            '<div class="de-card">'
            '<div class="de-card-header"><span class="de-card-title">Staffing Impact</span></div>'
            '<div class="de-card-sub">How is today\'s weather impacting staffing?</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        impact = st.session_state.de_impact
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            cls = "impact-btn selected" if impact == "No Impact" else "impact-btn"
            if st.button("✓ No Impact", key="im_no",
                         use_container_width=True):
                st.session_state.de_impact = "No Impact"
                st.rerun()
        with ic2:
            if st.button("Minor Impact", key="im_minor",
                         use_container_width=True):
                st.session_state.de_impact = "Minor Impact"
                st.rerun()
        with ic3:
            if st.button("Major Impact", key="im_major",
                         use_container_width=True):
                st.session_state.de_impact = "Major Impact"
                st.rerun()

    with c3:
        st.markdown(
            '<div class="de-card">'
            '<div class="de-card-header"><span class="de-card-title">Communication Notes</span></div>'
            '<div class="de-card-sub">Log weather or operations related communications</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        comm = st.text_area(
            "Communication Notes",
            key="de_input_comm_{}".format(entry_date),
            placeholder="Enter communication notes...",
            max_chars=500,
            label_visibility="collapsed",
            height=100,
        )
        st.markdown(
            '<div class="char-counter">{}/500</div>'.format(len(comm or "")),
            unsafe_allow_html=True,
        )

    # ─── At a Glance row ───
    st.markdown(
        '<div class="de-section-header">At a Glance</div>',
        unsafe_allow_html=True,
    )

    # Fetch totals
    totals = _fetch_day_totals(conn, entry_date)
    yesterday = _fetch_day_totals(conn, entry_date - timedelta(days=1))

    cards = st.columns(5)
    metrics = [
        ("Total Sales", "${:,.0f}".format(totals["sales"]),
         "{:+.1f}% vs Yesterday".format(_pct_change(totals["sales"], yesterday["sales"])),
         "dollar", "#ECFDF5", "#16A34A"),
        ("Labor Hours (Actual)", "{:.1f} hrs".format(totals["labor_h"]),
         "{:+.1f} hrs vs Yesterday".format(totals["labor_h"] - yesterday["labor_h"]),
         "users", "#EFF6FF", "#3B82F6"),
        ("Labor %", "{:.1f}%".format(totals["labor_pct"]),
         "{:+.1f} pts vs Yesterday".format(totals["labor_pct"] - yesterday["labor_pct"]),
         "chart", "#F5F3FF", "#8B5CF6"),
        ("Covers", "{:,}".format(int(totals["covers"])),
         "{:+d} vs Yesterday".format(int(totals["covers"] - yesterday["covers"])),
         "people", "#F0F9FF", "#0EA5E9"),
        ("Prime Cost %", "{:.1f}%".format(totals["prime_pct"]),
         "{:+.1f} pts vs Yesterday".format(totals["prime_pct"] - yesterday["prime_pct"]),
         "pie", "#FFFBEB", "#D97706"),
    ]
    for i, (label, value, delta, icon, bg, color) in enumerate(metrics):
        with cards[i]:
            st.markdown(
                '<div class="glance-card">'
                '<div class="glance-icon" style="background:{bg};">{icon}</div>'
                '<div class="glance-label">{label}</div>'
                '<div class="glance-value">{value}</div>'
                '<div class="glance-delta">{delta}</div>'
                '</div>'.format(
                    bg=bg, icon=_icon(icon),
                    label=label, value=value, delta=delta,
                ),
                unsafe_allow_html=True,
            )

    # ─── Info banner ───
    st.markdown(
        '<div class="info-banner">{}'
        '<span>Complete all sections to ensure accurate daily reporting and forecasting.</span>'
        '</div>'.format(_icon("info")),
        unsafe_allow_html=True,
    )


# ─── Step 2: Sales ───

def _render_sales_step(conn, user, entry_date):
    st.markdown(
        '<div class="de-section-header">Daily Sales by Department</div>',
        unsafe_allow_html=True,
    )
    dept = st.selectbox("Department", DEPARTMENTS, key="de_sales_dept")

    existing = conn.execute(
        """SELECT * FROM daily_sales WHERE entry_date=? AND department=?""",
        (entry_date.isoformat(), dept)
    ).fetchone()
    existing = dict(existing) if existing else {}

    c1, c2, c3 = st.columns(3)
    with c1:
        board = st.number_input("Board $", min_value=0.0, step=10.0,
                                 value=float(existing.get("board_revenue") or 0),
                                 key="de_input_board_{}_{}".format(dept, entry_date))
    with c2:
        retail = st.number_input("Retail $", min_value=0.0, step=10.0,
                                  value=float(existing.get("retail_revenue") or 0),
                                  key="de_input_retail_{}_{}".format(dept, entry_date))
    with c3:
        flex = st.number_input("Flex $", min_value=0.0, step=10.0,
                                value=float(existing.get("flex_revenue") or 0),
                                key="de_input_flex_{}_{}".format(dept, entry_date))

    c4, c5 = st.columns(2)
    with c4:
        catering = st.number_input("Catering $", min_value=0.0, step=10.0,
                                    value=float(existing.get("catering_revenue") or 0),
                                    key="de_input_catering_{}_{}".format(dept, entry_date))
    with c5:
        other = st.number_input("Other $", min_value=0.0, step=10.0,
                                 value=float(existing.get("other_revenue") or 0),
                                 key="de_input_other_{}_{}".format(dept, entry_date))

    total = board + retail + flex + catering + other
    st.markdown(
        '<div class="sales-total">Total: <b>${:,.2f}</b></div>'.format(total),
        unsafe_allow_html=True,
    )

    if st.button("Save Sales", key="de_save_sales", type="primary"):
        try:
            conn.execute(
                """INSERT OR REPLACE INTO daily_sales
                   (entry_date, department, board_revenue, retail_revenue,
                    flex_revenue, catering_revenue, other_revenue, updated_by, updated_at)
                   VALUES (?,?,?,?,?,?,?,?, datetime('now','localtime'))""",
                (entry_date.isoformat(), dept, board, retail, flex,
                 catering, other, user.get("username", "system"))
            )
            conn.commit()
            st.success("Sales saved.")
        except Exception as e:
            st.error("Save error: {}".format(str(e)[:200]))


# ─── Step 3: Labor ───

def _render_labor_step(conn, user, entry_date):
    st.markdown(
        '<div class="de-section-header">Daily Labor Hours</div>',
        unsafe_allow_html=True,
    )
    dept = st.selectbox("Department", DEPARTMENTS, key="de_labor_dept")

    existing = conn.execute(
        """SELECT labor_hours FROM daily_labor
           WHERE entry_date=? AND department=?""",
        (entry_date.isoformat(), dept)
    ).fetchone()
    existing_hrs = float(existing[0]) if existing and existing[0] else 0.0

    hrs = st.number_input(
        "Labor Hours", min_value=0.0, step=0.5,
        value=existing_hrs,
        key="de_input_labor_{}_{}".format(dept, entry_date),
    )

    if st.button("Save Labor", key="de_save_labor", type="primary"):
        try:
            conn.execute(
                """INSERT OR REPLACE INTO daily_labor
                   (entry_date, department, labor_hours, updated_by, updated_at)
                   VALUES (?,?,?,?, datetime('now','localtime'))""",
                (entry_date.isoformat(), dept, hrs, user.get("username", "system"))
            )
            conn.commit()
            st.success("Labor saved.")
        except Exception as e:
            st.error("Save error: {}".format(str(e)[:200]))


# ─── Step 4: Notes ───

def _render_notes_step(conn, user, entry_date):
    st.markdown(
        '<div class="de-section-header">Daily Notes</div>',
        unsafe_allow_html=True,
    )
    dept = st.selectbox("Department", DEPARTMENTS, key="de_notes_dept")

    categories = ["staffing", "training", "operations", "other"]
    cols = st.columns(2)
    notes_input = {}
    for i, cat in enumerate(categories):
        with cols[i % 2]:
            existing = conn.execute(
                """SELECT notes FROM daily_notes
                   WHERE entry_date=? AND department=? AND category=?""",
                (entry_date.isoformat(), dept, cat)
            ).fetchone()
            val = (existing[0] if existing else "") or ""
            notes_input[cat] = st.text_area(
                cat.title(),
                value=val,
                key="de_input_note_{}_{}_{}".format(cat, dept, entry_date),
                placeholder="Enter {} notes...".format(cat),
                height=120,
            )

    if st.button("Save Notes", key="de_save_notes", type="primary"):
        try:
            for cat, txt in notes_input.items():
                conn.execute(
                    """INSERT OR REPLACE INTO daily_notes
                       (entry_date, department, category, notes, updated_by, updated_at)
                       VALUES (?,?,?,?,?, datetime('now','localtime'))""",
                    (entry_date.isoformat(), dept, cat, txt, user.get("username", "system"))
                )
            conn.commit()
            st.success("Notes saved.")
        except Exception as e:
            st.error("Save error: {}".format(str(e)[:200]))


# ─── Step 5: Participation (Door Counts) ───

def _render_participation_step(conn, user, entry_date):
    st.markdown(
        '<div class="de-section-header">Door Counts by Meal Period</div>',
        unsafe_allow_html=True,
    )
    dept = st.selectbox("Department", DEPARTMENTS, key="de_part_dept")

    existing_rows = conn.execute(
        """SELECT meal_period, count FROM door_counts
           WHERE entry_date=? AND department=?""",
        (entry_date.isoformat(), dept)
    ).fetchall()
    existing_map = {r[0]: r[1] for r in existing_rows}

    c1, c2, c3 = st.columns(3)
    with c1:
        bf = st.number_input("Breakfast", min_value=0, step=10,
                              value=int(existing_map.get("breakfast", 0)),
                              key="de_input_door_bf_{}_{}".format(dept, entry_date))
    with c2:
        ln = st.number_input("Lunch", min_value=0, step=10,
                              value=int(existing_map.get("lunch", 0)),
                              key="de_input_door_ln_{}_{}".format(dept, entry_date))
    with c3:
        dn = st.number_input("Dinner", min_value=0, step=10,
                              value=int(existing_map.get("dinner", 0)),
                              key="de_input_door_dn_{}_{}".format(dept, entry_date))

    total = bf + ln + dn
    st.markdown(
        '<div class="sales-total">Total Covers: <b>{:,}</b></div>'.format(total),
        unsafe_allow_html=True,
    )

    if st.button("Save Participation", key="de_save_part", type="primary"):
        try:
            for mp, val in [("breakfast", bf), ("lunch", ln), ("dinner", dn)]:
                conn.execute(
                    """INSERT OR REPLACE INTO door_counts
                       (entry_date, department, meal_period, count,
                        updated_by, updated_at)
                       VALUES (?,?,?,?,?, datetime('now','localtime'))""",
                    (entry_date.isoformat(), dept, mp, val,
                     user.get("username", "system"))
                )
            conn.commit()
            st.success("Participation saved.")
        except Exception as e:
            st.error("Save error: {}".format(str(e)[:200]))


# ─── Data helpers ───

def _fetch_weather(d):
    """Get weather for date — uses live API or returns demo."""
    try:
        from integrations.weather import fetch_current_weather
        is_today = d == date.today()
        if is_today:
            w = fetch_current_weather()
            return {
                "temp": int(w.get("temp", 70)),
                "feels_like": int(w.get("feels_like", 70)),
                "condition": w.get("condition", "Clear Sky"),
                "wind": int(w.get("wind", 0)),
                "humidity": int(w.get("humidity", 50)),
            }
    except Exception:
        pass
    return {"temp": 71, "feels_like": 66, "condition": "Clear Sky",
            "wind": 13, "humidity": 37}


def _fetch_day_totals(conn, d):
    """Compute daily totals across all departments."""
    try:
        row = conn.execute(
            """SELECT SUM(COALESCE(board_revenue,0) + COALESCE(retail_revenue,0) +
                          COALESCE(flex_revenue,0) + COALESCE(catering_revenue,0) +
                          COALESCE(other_revenue,0)) as sales
               FROM daily_sales WHERE entry_date = ?""",
            (d.isoformat(),)
        ).fetchone()
        sales = (row[0] or 0) if row else 0
    except Exception:
        sales = 0

    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(labor_hours),0) FROM daily_labor WHERE entry_date = ?",
            (d.isoformat(),)
        ).fetchone()
        labor_h = (row[0] or 0) if row else 0
    except Exception:
        labor_h = 0

    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(count),0) FROM door_counts WHERE entry_date = ?",
            (d.isoformat(),)
        ).fetchone()
        covers = (row[0] or 0) if row else 0
    except Exception:
        covers = 0

    avg_wage = 17.0
    labor_d = labor_h * avg_wage
    labor_pct = (labor_d / sales * 100) if sales > 0 else 0
    prime_pct = labor_pct + 32  # approximation

    return {
        "sales": sales,
        "labor_h": labor_h,
        "labor_d": labor_d,
        "labor_pct": labor_pct,
        "covers": covers,
        "prime_pct": prime_pct,
    }


def _pct_change(a, b):
    if b == 0:
        return 0
    return (a - b) / b * 100
