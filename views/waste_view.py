"""Waste Tracking — Daily Food Waste Logging & Analysis."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

import db
from config import DEPARTMENTS
from auth import get_user_departments
from styles import page_header, section_title, kpi_card, mini_divider, app_footer, event_reminders


_WASTE_CATEGORIES = [
    "Overproduction",
    "Expired / Spoiled",
    "Plate Waste",
    "Prep Trim / Scraps",
    "Damaged / Dropped",
    "Equipment Failure",
    "Cancelled Event",
    "Other",
]

_WASTE_REASONS = [
    "Forecast too high",
    "Poor rotation (FIFO)",
    "Menu change",
    "Low attendance",
    "Equipment malfunction",
    "Staff error",
    "Delivery issue",
    "Weather-related",
    "Event cancellation",
    "Other",
]

_MEAL_PERIODS = ["Breakfast", "Lunch", "Dinner", "Catering", "Other"]


def render(conn, user):
    page_header("Waste Tracking", "Food Waste Logging & Cost Analysis")
    event_reminders(conn)

    today = date.today()

    # Department
    user_depts = get_user_departments(user, DEPARTMENTS)
    if len(user_depts) == 1:
        dept = user_depts[0]
    else:
        dept = st.selectbox("Department", user_depts, key="waste_dept")

    tab_log, tab_today, tab_trends = st.tabs([
        "Log Waste", "Today's Log", "Trends & Analysis"
    ])

    with tab_log:
        _render_log_form(conn, user, today, dept)

    with tab_today:
        _render_daily_log(conn, today, dept)

    with tab_trends:
        _render_trends(conn, dept)



def _render_log_form(conn, user, today, dept):
    section_title("", "Log Food Waste")

    with st.form("waste_form_{}".format(dept)):
        c1, c2 = st.columns(2)
        with c1:
            log_date = st.date_input("Date", today, key="waste_date_{}".format(dept))
            category = st.selectbox("Waste Category", _WASTE_CATEGORIES, key="waste_cat_{}".format(dept))
            meal_period = st.selectbox("Meal Period", _MEAL_PERIODS, key="waste_meal_{}".format(dept))
        with c2:
            item_desc = st.text_input("Item Description", placeholder="e.g., Grilled chicken, pasta salad", key="waste_item_{}".format(dept))
            weight = st.number_input("Weight (lbs)", min_value=0.0, value=0.0, step=0.5, format="%.1f", key="waste_weight_{}".format(dept))
            cost = st.number_input("Estimated Cost ($)", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="waste_cost_{}".format(dept))

        reason = st.selectbox("Reason", _WASTE_REASONS, key="waste_reason_{}".format(dept))
        corrective = st.text_input("Corrective Action", placeholder="What will be done to prevent this?", key="waste_corrective_{}".format(dept))

        submitted = st.form_submit_button("Log Waste Entry", type="primary")
        if submitted:
            if not item_desc:
                st.error("Item description is required.")
            elif weight <= 0 and cost <= 0:
                st.error("Enter either weight or estimated cost (or both).")
            else:
                db.add_waste_log(
                    conn, log_date.isoformat(), dept,
                    category, item_desc, weight, cost,
                    reason, meal_period, corrective,
                    user["username"],
                )
                st.success("Waste logged: {} ({} lbs, ${:,.2f})".format(item_desc, weight, cost))
                st.rerun()


def _render_daily_log(conn, today, dept):
    section_title("", "Today's Waste Log \u2014 {} \u2014 {}".format(dept, today.strftime("%b %d, %Y")))

    logs = db.fetch_waste_logs(conn, today.isoformat(), dept)

    if not logs:
        st.info("No waste entries logged today for {}.".format(dept))
        return

    # Summary KPIs
    total_weight = sum(float(l.get("weight_lbs", 0) or 0) for l in logs)
    total_cost = sum(float(l.get("estimated_cost", 0) or 0) for l in logs)
    entry_count = len(logs)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Today's Entries", str(entry_count), "kpi-blue")
    with c2:
        kpi_card("Total Weight", "{:.1f} lbs".format(total_weight), "kpi-amber")
    with c3:
        kpi_card("Total Cost", "${:,.2f}".format(total_cost), "kpi-red")

    mini_divider()

    # Detail table
    log_df = pd.DataFrame(logs)
    display_cols = ["category", "item_description", "weight_lbs", "estimated_cost", "meal_period", "reason", "logged_by"]
    available = [c for c in display_cols if c in log_df.columns]
    log_df = log_df[available]
    rename_map = {
        "category": "Category",
        "item_description": "Item",
        "weight_lbs": "Weight (lbs)",
        "estimated_cost": "Cost ($)",
        "meal_period": "Meal",
        "reason": "Reason",
        "logged_by": "Logged By",
    }
    log_df.rename(columns=rename_map, inplace=True)
    fmt = {}
    if "Weight (lbs)" in log_df.columns:
        fmt["Weight (lbs)"] = "{:.1f}".format
    if "Cost ($)" in log_df.columns:
        fmt["Cost ($)"] = "${:,.2f}".format
    st.dataframe(log_df.style.format(fmt), use_container_width=True, hide_index=True)


def _render_trends(conn, dept):
    section_title("", "Waste Trends & Analysis")

    c1, c2 = st.columns(2)
    with c1:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2, format_func=lambda x: "Past {} days".format(x), key="waste_period")
    with c2:
        st.markdown("")  # spacer

    today = date.today()
    start = (today - timedelta(days=days_back)).isoformat()
    end = today.isoformat()

    # Summary by category
    summary = db.fetch_waste_summary(conn, start, end, dept)

    if not summary:
        st.info("No waste data for the selected period.")
        return

    total_weight = sum(float(s.get("total_weight", 0) or 0) for s in summary)
    total_cost = sum(float(s.get("total_cost", 0) or 0) for s in summary)
    total_entries = sum(int(s.get("entry_count", 0) or 0) for s in summary)
    daily_avg_cost = total_cost / days_back if days_back > 0 else 0

    # KPIs
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        kpi_card("Total Weight", "{:.1f} lbs".format(total_weight), "kpi-amber")
    with kc2:
        kpi_card("Total Cost", "${:,.2f}".format(total_cost), "kpi-red")
    with kc3:
        kpi_card("Entries", str(total_entries), "kpi-blue")
    with kc4:
        kpi_card("Daily Avg Cost", "${:,.2f}".format(daily_avg_cost), "kpi-green")

    mini_divider()

    # Charts
    sum_df = pd.DataFrame(summary)
    sum_df.rename(columns={
        "category": "Category",
        "total_weight": "Weight (lbs)",
        "total_cost": "Cost ($)",
        "entry_count": "Entries",
    }, inplace=True)

    ch1, ch2 = st.columns(2)
    with ch1:
        fig1 = px.pie(
            sum_df, names="Category", values="Cost ($)",
            title="Waste Cost by Category",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig1.update_layout(height=350)
        st.plotly_chart(fig1, use_container_width=True)
    with ch2:
        fig2 = px.bar(
            sum_df, x="Category", y="Weight (lbs)",
            title="Waste Weight by Category",
            color="Category",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Daily trend line
    mini_divider()
    all_logs = db.fetch_waste_logs_range(conn, start, end, dept)
    if all_logs:
        trend_df = pd.DataFrame(all_logs)
        daily = trend_df.groupby("log_date", as_index=False).agg({
            "weight_lbs": "sum",
            "estimated_cost": "sum",
        })
        daily.rename(columns={
            "log_date": "Date",
            "weight_lbs": "Weight (lbs)",
            "estimated_cost": "Cost ($)",
        }, inplace=True)

        fig3 = px.line(
            daily, x="Date", y="Cost ($)",
            title="Daily Waste Cost Trend",
            markers=True,
        )
        fig3.update_traces(line_color="#DC3545")
        fig3.update_layout(height=350)
        st.plotly_chart(fig3, use_container_width=True)

    # Category breakdown table
    mini_divider()
    section_title("", "Category Breakdown")
    fmt = {}
    if "Weight (lbs)" in sum_df.columns:
        fmt["Weight (lbs)"] = "{:.1f}".format
    if "Cost ($)" in sum_df.columns:
        fmt["Cost ($)"] = "${:,.2f}".format
    st.dataframe(sum_df.style.format(fmt), use_container_width=True, hide_index=True)
