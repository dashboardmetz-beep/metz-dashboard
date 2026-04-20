"""
Page 1: Daily Entry
Daily sales (5 revenue streams) + labor hours + live weather for Alma, MI +
staffing communication + daily notes (staffing/scheduling, training, other) +
door counts + meal plan participation.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from config import DEPARTMENTS, WEATHER_CONDITIONS, REVENUE_STREAM_LABELS, DAILY_NOTE_CATEGORIES
from calculations import sum_revenue_streams, fmt_dollar, fmt_number
from auth import can_edit_daily, get_user_departments
from styles import page_header, section_title, mini_divider, app_footer, event_reminders
import db


def _odyssey_table_exists(conn):
    """Check if odyssey_tender_totals table exists."""
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='odyssey_tender_totals'"
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _render_live_weather(selected_date):
    """Show live weather for Alma, MI and staffing impact advisory."""
    try:
        from integrations.weather import fetch_current_weather, fetch_daily_forecast

        is_today = selected_date == date.today()

        if is_today:
            wx = fetch_current_weather()
            if wx:
                section_title("", "Live Weather — Alma, Michigan")
                wc1, wc2, wc3, wc4, wc5 = st.columns(5)
                with wc1:
                    st.metric("Condition", wx["description"])
                with wc2:
                    st.metric("Temperature", "{}\u00b0F".format(
                        int(wx["temperature_f"]) if wx["temperature_f"] is not None else "N/A"))
                with wc3:
                    st.metric("Feels Like", "{}\u00b0F".format(
                        int(wx["feels_like_f"]) if wx["feels_like_f"] is not None else "N/A"))
                with wc4:
                    st.metric("Wind", "{} mph".format(
                        int(wx["wind_mph"]) if wx["wind_mph"] is not None else "N/A"))
                with wc5:
                    st.metric("Humidity", "{}%".format(
                        int(wx["humidity_pct"]) if wx["humidity_pct"] is not None else "N/A"))

                # Staffing impact advisory
                if wx["may_affect_staffing"]:
                    st.error(
                        "**Staffing Advisory:** {} conditions may affect employee commutes "
                        "and staffing levels. Consider contacting team members.".format(wx["description"])
                    )
                return wx
            else:
                st.caption("Unable to fetch live weather data.")
                return None
        else:
            # Show forecast for the selected date
            fx = fetch_daily_forecast(selected_date)
            if fx:
                section_title("", "Weather Forecast — Alma, Michigan")
                wc1, wc2, wc3, wc4 = st.columns(4)
                with wc1:
                    st.metric("Forecast", fx["description"])
                with wc2:
                    high = int(fx["high_f"]) if fx["high_f"] is not None else "N/A"
                    low = int(fx["low_f"]) if fx["low_f"] is not None else "N/A"
                    st.metric("High / Low", "{}\u00b0 / {}\u00b0F".format(high, low))
                with wc3:
                    precip = fx["precipitation_in"] if fx["precipitation_in"] is not None else 0
                    st.metric("Precipitation", '{}" '.format(round(precip, 2)))
                with wc4:
                    wind = int(fx["wind_max_mph"]) if fx["wind_max_mph"] is not None else "N/A"
                    st.metric("Max Wind", "{} mph".format(wind))

                if fx["may_affect_staffing"]:
                    st.error(
                        "**Staffing Advisory:** {} expected. "
                        "Plan for potential staffing impact.".format(fx["description"])
                    )
                return fx
            else:
                st.caption("No forecast available for this date.")
                return None
    except ImportError:
        st.caption("Weather module not available.")
        return None
    except Exception as e:
        st.caption("Weather unavailable: {}".format(str(e)))
        return None


def page_daily_entry(conn, user):
    today = date.today()
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = today

    page_header("Daily Entry", "Daily Sales, Labor & Weather Logging")
    event_reminders(conn)

    # ─── Date Navigation ───

    col_prev, col_date, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("\u25c0 Prev Day"):
            st.session_state.selected_date -= timedelta(days=1)
            st.rerun()
    with col_next:
        if st.button("Next Day \u25b6"):
            st.session_state.selected_date += timedelta(days=1)
            st.rerun()
    with col_date:
        picked = st.date_input("Date", st.session_state.selected_date)
        if picked != st.session_state.selected_date:
            st.session_state.selected_date = picked
            st.rerun()

    entry_date = st.session_state.selected_date.isoformat()
    day_name = st.session_state.selected_date.strftime("%A, %B %d, %Y")
    st.caption(day_name)

    # ─── Live Weather for Alma, MI ───
    mini_divider()
    live_wx = _render_live_weather(st.session_state.selected_date)

    # ─── Weather & Staffing Communication Log ───
    mini_divider()
    section_title("", "Weather & Staffing Communication")
    weather = db.fetch_daily_weather(conn, entry_date)

    # Auto-suggest condition from live weather if no saved entry
    default_condition = "Clear"
    default_affected = False
    default_notes = ""

    if weather:
        default_condition = weather["condition"]
        default_affected = bool(weather["weather_affected_staffing"])
        default_notes = weather["notes"] if weather["notes"] else ""
    elif live_wx:
        default_condition = live_wx.get("condition", "Clear")
        default_affected = live_wx.get("may_affect_staffing", False)
        if default_affected:
            default_notes = "Auto-detected: {} conditions".format(live_wx.get("description", ""))

    wcol1, wcol2 = st.columns([2, 3])
    with wcol1:
        condition_idx = WEATHER_CONDITIONS.index(default_condition) if default_condition in WEATHER_CONDITIONS else 0
        w_condition = st.selectbox("Logged Condition", WEATHER_CONDITIONS, index=condition_idx, key="w_cond")
        w_affected = st.checkbox("Weather affected staffing",
                                 value=default_affected,
                                 key="w_affected")
    with wcol2:
        w_notes = st.text_area("Communication Notes",
                               value=default_notes,
                               height=100,
                               placeholder="Log weather-related staffing communications here...\n"
                                           "e.g., 'Called in 2 extra staff due to snow. "
                                           "Notified team via group text at 6am.'",
                               key="w_notes")

    if st.button("Save Weather & Communication Log", key="save_weather"):
        db.upsert_daily_weather(conn, entry_date, w_condition, w_affected, w_notes, user["username"])
        st.success("Weather & communication log saved.")
        st.rerun()

    if w_affected:
        st.warning("Weather-affected staffing flagged for this date.")

    # ─── Today's Calendar Events ───
    day_events = db.fetch_dining_impact_events(conn, entry_date, entry_date)
    if day_events:
        for ev in day_events:
            impact = ev.get("dining_impact", "")
            st.info("**{}** {}".format(
                ev["title"],
                "\u2014 *{}*".format(impact) if impact else "",
            ))

    # ─── Department Selection ───
    mini_divider()
    user_depts = get_user_departments(user, DEPARTMENTS)
    if len(user_depts) == 1:
        dept = user_depts[0]
        st.markdown("**Department:** {}".format(dept))
    else:
        dept = st.selectbox("Department", user_depts, key="daily_dept")

    editable = can_edit_daily(user, dept)

    # ─── Sales Entry ───
    section_title("", "Daily Sales - {}".format(dept))

    sales = db.fetch_daily_sales(conn, entry_date, dept)
    board_rev = float(sales["board_revenue"]) if sales else 0.0
    retail_rev = float(sales["retail_revenue"]) if sales else 0.0
    flex_rev = float(sales["flex_revenue"]) if sales else 0.0
    catering_rev = float(sales["catering_revenue"]) if sales else 0.0
    other_rev = float(sales["other_revenue"]) if sales else 0.0

    if editable:
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1:
            board_rev = st.number_input("Board ($)", value=board_rev, min_value=0.0,
                                        step=50.0, format="%.2f", key="ds_board")
        with sc2:
            retail_rev = st.number_input("Retail ($)", value=retail_rev, min_value=0.0,
                                         step=50.0, format="%.2f", key="ds_retail")
        with sc3:
            flex_rev = st.number_input("Flex ($)", value=flex_rev, min_value=0.0,
                                       step=50.0, format="%.2f", key="ds_flex")
        with sc4:
            catering_rev = st.number_input("Catering ($)", value=catering_rev, min_value=0.0,
                                            step=50.0, format="%.2f", key="ds_catering")
        with sc5:
            other_rev = st.number_input("Other ($)", value=other_rev, min_value=0.0,
                                         step=50.0, format="%.2f", key="ds_other")
    else:
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1:
            st.metric("Board", fmt_dollar(board_rev))
        with sc2:
            st.metric("Retail", fmt_dollar(retail_rev))
        with sc3:
            st.metric("Flex", fmt_dollar(flex_rev))
        with sc4:
            st.metric("Catering", fmt_dollar(catering_rev))
        with sc5:
            st.metric("Other", fmt_dollar(other_rev))

    total_rev = sum_revenue_streams(board_rev, retail_rev, flex_rev, catering_rev, other_rev)
    st.metric("Total Revenue", fmt_dollar(total_rev))

    if editable:
        if st.button("Save Sales", use_container_width=True, key="save_sales"):
            db.upsert_daily_sales(conn, entry_date, dept, board_rev, retail_rev,
                                  flex_rev, catering_rev, other_rev, user["username"])
            st.success("Sales saved.")
            st.rerun()

    # ─── Labor Entry ───
    mini_divider()
    section_title("", "Daily Labor - {}".format(dept))

    labor = db.fetch_daily_labor(conn, entry_date, dept)
    labor_hours = float(labor["labor_hours"]) if labor else 0.0

    # Show ADP scheduled if available
    schedule = db.fetch_labor_schedule(conn, entry_date, dept)

    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        if editable:
            labor_hours = st.number_input("Actual Labor Hours", value=labor_hours,
                                          min_value=0.0, step=1.0, format="%.1f",
                                          key="dl_hours")
        else:
            st.metric("Actual Hours", fmt_number(labor_hours))
    with lc2:
        if schedule:
            st.metric("Scheduled (ADP)", fmt_number(float(schedule["scheduled_hours"])))
        else:
            st.metric("Scheduled (ADP)", "N/A")
    with lc3:
        if schedule and labor_hours > 0:
            var_hrs = labor_hours - float(schedule["scheduled_hours"])
            delta_color = "normal" if var_hrs <= 0 else "inverse"
            st.metric("Variance", fmt_number(var_hrs),
                      "{} hrs".format(fmt_number(var_hrs)), delta_color=delta_color)
        else:
            st.metric("Variance", "N/A")

    if editable:
        if st.button("Save Labor", use_container_width=True, key="save_labor"):
            db.upsert_daily_labor(conn, entry_date, dept, labor_hours, user["username"])
            st.success("Labor hours saved.")
            st.rerun()

    # ─── Daily Notes: Staffing & Scheduling, Training, Other ───
    mini_divider()
    section_title("", "Daily Notes")

    existing_notes = db.fetch_daily_notes(conn, entry_date, dept)

    note_cols = st.columns(len(DAILY_NOTE_CATEGORIES))
    note_values = {}
    for idx, cat in enumerate(DAILY_NOTE_CATEGORIES):
        with note_cols[idx]:
            note_values[cat] = st.text_area(
                cat,
                value=existing_notes.get(cat, ""),
                height=100,
                placeholder="Enter {} notes...".format(cat.lower()),
                key="note_{}".format(cat.replace(" ", "_").replace("&", "and")),
            )

    if editable:
        if st.button("Save Daily Notes", key="save_notes"):
            for cat, text in note_values.items():
                db.upsert_daily_note(conn, entry_date, dept, cat, text, user["username"])
            st.success("Daily notes saved.")
            st.rerun()

    # ─── Door Counts by Meal Period (Board & Catering, weekdays only) ───
    if dept == "Board & Catering":
        mini_divider()
        section_title("", "Door Counts by Meal Period")

        existing_doors = db.fetch_door_counts(conn, entry_date, dept)
        door_map = {}
        for d in existing_doors:
            door_map[d["meal_period"]] = int(d["count"])

        meal_periods = ["breakfast", "lunch", "dinner"]

        # ─── Check for auto-fill from Tender Totals (Hamilton 04) ───
        tender_rows = conn.execute(
            """SELECT service_period, board_count FROM odyssey_tender_totals
               WHERE report_date = ? AND terminal = 'Hamilton 04'""",
            (entry_date,)
        ).fetchall() if _odyssey_table_exists(conn) else []

        tender_map = {}
        for r in tender_rows:
            period = r[0].lower() if r[0] else ""
            tender_map[period] = r[1]

        # If tender data exists and door counts are empty, use tender values as default
        if tender_map and not door_map:
            for mp in meal_periods:
                if mp in tender_map:
                    door_map[mp] = tender_map[mp]

        if editable:
            if tender_map:
                st.info(
                    "📊 Tender data available for {} from Hamilton 04: "
                    "B={:,}, L={:,}, D={:,}".format(
                        entry_date,
                        tender_map.get("breakfast", 0),
                        tender_map.get("lunch", 0),
                        tender_map.get("dinner", 0),
                    )
                )
                if st.button("Auto-fill from Tender Totals", key="tender_autofill"):
                    for mp in meal_periods:
                        if mp in tender_map:
                            db.upsert_door_count(
                                conn, entry_date, dept, mp,
                                tender_map[mp], user["username"],
                            )
                    # Clear session state so widgets re-read from DB
                    for mp in meal_periods:
                        st.session_state.pop("door_" + mp, None)
                    st.success("Door counts filled from Tender Totals.")
                    st.rerun()

            # Use unique keys per date so values refresh when date changes
            date_suffix = str(entry_date).replace("-", "")
            bf_key = "door_breakfast_{}".format(date_suffix)
            ln_key = "door_lunch_{}".format(date_suffix)
            dn_key = "door_dinner_{}".format(date_suffix)

            # Initialize session state with door_map values if not set
            if bf_key not in st.session_state:
                st.session_state[bf_key] = door_map.get("breakfast", 0)
            if ln_key not in st.session_state:
                st.session_state[ln_key] = door_map.get("lunch", 0)
            if dn_key not in st.session_state:
                st.session_state[dn_key] = door_map.get("dinner", 0)

            dc1, dc2, dc3 = st.columns(3)
            door_vals = {}
            with dc1:
                door_vals["breakfast"] = st.number_input(
                    "Breakfast", min_value=0, step=10, key=bf_key,
                )
            with dc2:
                door_vals["lunch"] = st.number_input(
                    "Lunch", min_value=0, step=10, key=ln_key,
                )
            with dc3:
                door_vals["dinner"] = st.number_input(
                    "Dinner", min_value=0, step=10, key=dn_key,
                )
            total_door = sum(door_vals.values())
            st.markdown("**Total Door Count: {:,}**".format(total_door))

            if st.button("Save Door Counts", key="save_doors"):
                for mp in meal_periods:
                    db.upsert_door_count(
                        conn, entry_date, dept, mp,
                        door_vals[mp], user["username"],
                    )
                st.success("Door counts saved.")
                st.rerun()
        else:
            dc1, dc2, dc3, dc4 = st.columns(4)
            with dc1:
                st.metric("Breakfast", fmt_number(door_map.get("breakfast", 0), 0))
            with dc2:
                st.metric("Lunch", fmt_number(door_map.get("lunch", 0), 0))
            with dc3:
                st.metric("Dinner", fmt_number(door_map.get("dinner", 0), 0))
            with dc4:
                total_door = sum(door_map.get(mp, 0) for mp in meal_periods)
                st.metric("Total", fmt_number(total_door, 0))

    # ─── Meal Plan Participation (Board & Catering only) ───
    if dept == "Board & Catering":
        mini_divider()
        section_title("", "Meal Plan Participation - {}".format(dept))

        meal_plans = db.fetch_meal_plan_for_date(conn, entry_date)
        meal_dict = {m["plan_type"]: m for m in meal_plans}

        mp1, mp2 = st.columns(2)
        with mp1:
            st.markdown("**Resident Plan**")
            res_data = meal_dict.get("resident", {})
            if editable:
                res_enrolled = st.number_input(
                    "Enrolled (Resident)",
                    value=int(res_data.get("enrolled_count", 0)),
                    min_value=0, step=1, key="mp_res_enr",
                )
                res_used = st.number_input(
                    "Meals Used (Resident)",
                    value=int(res_data.get("meals_used", 0)),
                    min_value=0, step=1, key="mp_res_used",
                )
            else:
                res_enrolled = int(res_data.get("enrolled_count", 0))
                res_used = int(res_data.get("meals_used", 0))
                st.metric("Enrolled", res_enrolled)
                st.metric("Meals Used", res_used)

        with mp2:
            st.markdown("**Commuter Plan**")
            com_data = meal_dict.get("commuter", {})
            if editable:
                com_enrolled = st.number_input(
                    "Enrolled (Commuter)",
                    value=int(com_data.get("enrolled_count", 0)),
                    min_value=0, step=1, key="mp_com_enr",
                )
                com_used = st.number_input(
                    "Meals Used (Commuter)",
                    value=int(com_data.get("meals_used", 0)),
                    min_value=0, step=1, key="mp_com_used",
                )
            else:
                com_enrolled = int(com_data.get("enrolled_count", 0))
                com_used = int(com_data.get("meals_used", 0))
                st.metric("Enrolled", com_enrolled)
                st.metric("Meals Used", com_used)

        if editable:
            if st.button("Save Meal Plan Data", key="save_meal"):
                db.upsert_meal_plan(conn, entry_date, "resident", res_enrolled, res_used, 0, user["username"])
                db.upsert_meal_plan(conn, entry_date, "commuter", com_enrolled, com_used, 0, user["username"])
                st.success("Meal plan data saved.")
                st.rerun()

    # ─── Meal Exchange (Qdoba & Retail & Mac's Grill only) ───
    if dept in ("Qdoba", "Retail & Mac's Grill"):
        mini_divider()
        section_title("", "Meal Exchange - {}".format(dept))

        mx_data = db.fetch_meal_exchange(conn, entry_date, dept)
        mx_count = int(mx_data.get("exchange_count", 0)) if mx_data else 0
        mx_dollars = float(mx_data.get("dollar_amount", 0.0)) if mx_data else 0.0

        if editable:
            mx1, mx2 = st.columns(2)
            with mx1:
                new_mx_count = st.number_input(
                    "Exchange Count",
                    value=mx_count,
                    min_value=0,
                    step=1,
                    key="mx_count",
                )
            with mx2:
                new_mx_dollars = st.number_input(
                    "Dollar Amount ($)",
                    value=mx_dollars,
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="mx_dollars",
                )
            if st.button("Save Meal Exchange", key="save_mx"):
                db.upsert_meal_exchange(conn, entry_date, dept, new_mx_count, new_mx_dollars, user["username"])
                st.success("Meal exchange data saved.")
                st.rerun()
        else:
            mx1, mx2 = st.columns(2)
            with mx1:
                st.metric("Exchange Count", "{:,}".format(mx_count))
            with mx2:
                st.metric("Dollar Amount", "${:,.2f}".format(mx_dollars))

    # ─── Daily Summary (all departments) ───
    mini_divider()
    section_title("", "Daily Summary - All Departments")

    summary_rows = []
    for d in DEPARTMENTS:
        s = db.fetch_daily_sales(conn, entry_date, d)
        l = db.fetch_daily_labor(conn, entry_date, d)
        if s:
            t = sum_revenue_streams(
                s["board_revenue"], s["retail_revenue"], s["flex_revenue"],
                s["catering_revenue"], s["other_revenue"]
            )
            summary_rows.append({
                "Department": d,
                "Board": s["board_revenue"] or 0,
                "Retail": s["retail_revenue"] or 0,
                "Flex": s["flex_revenue"] or 0,
                "Catering": s["catering_revenue"] or 0,
                "Other": s["other_revenue"] or 0,
                "Total Revenue": t,
                "Labor Hrs": float(l["labor_hours"]) if l else 0,
            })
        else:
            summary_rows.append({
                "Department": d,
                "Board": 0, "Retail": 0, "Flex": 0, "Catering": 0, "Other": 0,
                "Total Revenue": 0,
                "Labor Hrs": float(l["labor_hours"]) if l else 0,
            })

    df = pd.DataFrame(summary_rows)

    # Format dollar columns
    dollar_cols = ["Board", "Retail", "Flex", "Catering", "Other", "Total Revenue"]
    fmt_dict = {}
    for c in dollar_cols:
        fmt_dict[c] = "${:,.0f}".format
    fmt_dict["Labor Hrs"] = "{:.1f}".format

    st.dataframe(
        df.style.format(fmt_dict),
        use_container_width=True,
        hide_index=True,
    )

    # ─── Weather Communication History ───
    if weather and weather.get("weather_affected_staffing"):
        st.info("**Weather Flag:** {} - {}".format(
            weather["condition"],
            weather.get("notes", "No notes")
        ))

    # ─── Week Weather Outlook ───
    if st.session_state.selected_date == today:
        with st.expander("7-Day Weather Outlook — Alma, MI"):
            try:
                from integrations.weather import fetch_week_forecast
                forecasts = fetch_week_forecast(today)
                if forecasts:
                    forecast_rows = []
                    for f in forecasts:
                        row = {
                            "Date": f["date"],
                            "Condition": f["description"],
                            "High": "{}\u00b0F".format(int(f["high_f"])) if f["high_f"] is not None else "N/A",
                            "Low": "{}\u00b0F".format(int(f["low_f"])) if f["low_f"] is not None else "N/A",
                            "Precip": '{}"'.format(round(f["precipitation_in"], 2)) if f["precipitation_in"] is not None else "0\"",
                            "Wind": "{} mph".format(int(f["wind_max_mph"])) if f["wind_max_mph"] is not None else "N/A",
                            "Staffing Risk": "Yes" if f["may_affect_staffing"] else "No",
                        }
                        forecast_rows.append(row)
                    fdf = pd.DataFrame(forecast_rows)
                    st.dataframe(fdf, use_container_width=True, hide_index=True)

                    # Highlight risky days
                    risky = [f for f in forecasts if f["may_affect_staffing"]]
                    if risky:
                        st.warning(
                            "**Heads up:** {} day(s) this week may affect staffing: {}".format(
                                len(risky),
                                ", ".join(["{} ({})".format(f["date"], f["description"]) for f in risky])
                            )
                        )
                else:
                    st.caption("Could not fetch forecast data.")
            except Exception as e:
                st.caption("Forecast unavailable: {}".format(str(e)))

