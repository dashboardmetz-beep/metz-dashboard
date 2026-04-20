"""
Page 2: Weekly Budget Entry
Sub-section routing: each sidebar sub-section renders as its own clean isolated view.
"""

import os
import re
import subprocess
from datetime import date, timedelta

import streamlit as st
import pandas as pd

from config import (
    DEPARTMENTS, FIELDS, REASON_CODES, STATUS_COLORS, OPERATION_COST_CATEGORIES,
    UPLOAD_DIR, ALLOWED_ATTACHMENT_EXTENSIONS, ALLOWED_IMPORT_EXTENSIONS,
    MAX_FILE_SIZE_MB, BUDGET_IMPORT_COLUMNS,
    CTUIT_REPORT_GROUP_MAP, CTUIT_SALES_MAP, CTUIT_SUMMARY_MAP, CTUIT_LABOR_DETAIL,
    CTUIT_NON_CONT_DETAIL, CTUIT_DETAIL_MAP, CTUIT_DETAIL_SECTIONS,
    INVOICE_DAY_COLUMNS, INVOICE_DAY_LABELS, INVOICE_EXCEL_SECTION_MAP,
    INVOICE_TRACKER_FILE,
)
from calculations import (
    calc_labor_pct, calc_splh, calc_cos_pct, calc_cpm, calc_mplh,
    calc_food_cost, sum_revenue_streams, variance, fmt_pct, fmt_dollar, fmt_number,
)
from auth import (
    can_edit_budget, can_approve_budget, can_return_budget,
    can_unlock_budget,
)
from styles import (
    page_header, section_title, status_badge, mini_divider, event_reminders,
    budget_summary_metric, budget_kpi_row, budget_save_start, budget_save_end,
)
import db


# ─── Value helpers ──────────────────────────────────────────────


def _ds(dept):
    """Short department suffix for unique widget keys across tabs."""
    return dept.replace(" ", "").replace("&", "")[:4].lower()


def _fval(source, key, rollup=None, fallback=0.0):
    """Get a float value from rollup (priority) or source dict."""
    if rollup and key in rollup:
        val = rollup[key]
        return float(val) if val is not None else fallback
    if source:
        val = source.get(key, fallback)
        if val is None:
            return fallback
        return float(val)
    return fallback


def _build_fin_update(fin, overrides):
    """Build a full weekly_financials dict preserving existing values with overrides."""
    base = {
        "board_revenue": _fval(fin, "board_revenue"),
        "retail_revenue": _fval(fin, "retail_revenue"),
        "flex_revenue": _fval(fin, "flex_revenue"),
        "catering_revenue": _fval(fin, "catering_revenue"),
        "other_revenue": _fval(fin, "other_revenue"),
        "cos_dollars": _fval(fin, "cos_dollars"),
        "total_labor_dollars": _fval(fin, "total_labor_dollars"),
        "total_labor_hours": _fval(fin, "total_labor_hours"),
        "overtime_dollars": _fval(fin, "overtime_dollars"),
        "direct_expenses": _fval(fin, "direct_expenses"),
        "gross_profit": _fval(fin, "gross_profit"),
        "total_payroll": _fval(fin, "total_payroll"),
        "tax_fringe": _fval(fin, "tax_fringe"),
        "after_prime_costs": _fval(fin, "after_prime_costs"),
        "pace": _fval(fin, "pace"),
        "non_cont_expenses": _fval(fin, "non_cont_expenses"),
        "insurance": _fval(fin, "insurance"),
        "profit_fee": _fval(fin, "profit_fee"),
        "royalties": _fval(fin, "royalties"),
        "net_income": _fval(fin, "net_income"),
        "management_fees": _fval(fin, "management_fees"),
    }
    base.update(overrides)
    return base


def _get_total_revenue(fin):
    """Calculate total revenue from saved financials."""
    return sum_revenue_streams(
        _fval(fin, "board_revenue"),
        _fval(fin, "retail_revenue"),
        _fval(fin, "flex_revenue"),
        _fval(fin, "catering_revenue"),
        _fval(fin, "other_revenue"),
    )


# ─── Main entry point ──────────────────────────────────────────


def page_weekly_entry(conn, user):
    # ─── Week Navigation (init before header) ───
    today = date.today()
    if "selected_week" not in st.session_state:
        # Default to latest week with data, or last week
        latest = conn.execute(
            "SELECT MAX(week_start) FROM weekly_financials"
        ).fetchone()
        if latest and latest[0]:
            st.session_state.selected_week = date.fromisoformat(latest[0])
        else:
            st.session_state.selected_week = db.get_week_start(today) - timedelta(weeks=1)
    # Sync wb_date with selected_week BEFORE widget renders
    target_date = st.session_state.selected_week + timedelta(days=6)
    if st.session_state.get("wb_date") != target_date:
        st.session_state.wb_date = target_date

    week_end_display = target_date.strftime("%B %d, %Y")
    page_header("Weekly Budget Entry", "Week Ending {}".format(week_end_display))
    event_reminders(conn)

    col_prev, col_date, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("\u25c0 Prev Week"):
            st.session_state.selected_week -= timedelta(weeks=1)
            st.rerun()
    with col_next:
        if st.button("Next Week \u25b6"):
            st.session_state.selected_week += timedelta(weeks=1)
            st.rerun()
    with col_date:
        picked = st.date_input("Week Ending", key="wb_date")
        new_week = db.get_week_start(picked)
        if new_week != st.session_state.selected_week:
            st.session_state.selected_week = new_week
            st.rerun()

    week_start = st.session_state.selected_week.isoformat()

    # ─── Department Tabs ───
    tab_labels = DEPARTMENTS + ["Consolidated"]

    # Editors can only see their own department + Consolidated
    if user["role"] == "editor":
        tab_labels = [user["department"], "Consolidated"]

    tabs = st.tabs(tab_labels)

    for tab_idx, tab in enumerate(tabs):
        dept = tab_labels[tab_idx]
        with tab:
            if dept == "Consolidated":
                _render_consolidated(conn, user, week_start)
            else:
                _render_department_tab(conn, user, week_start, dept)


# ═══════════════════════════════════════════════════════════════
#  Single-department tab (editable)
# ═══════════════════════════════════════════════════════════════


def _render_department_tab(conn, user, week_start, dept):
    """Render the full entry view for one department."""
    budget = db.fetch_budget(conn, week_start, dept)
    status = budget["status"] if budget else "Draft"
    fin = db.fetch_weekly_financials(conn, week_start, dept)

    # Status badge
    st.markdown(status_badge(status), unsafe_allow_html=True)
    if budget and budget.get("updated_at"):
        st.caption("Last updated: {} by {}".format(
            budget["updated_at"], budget.get("updated_by", "\u2014")))

    mini_divider()

    # Permission logic
    editable = can_edit_budget(user, status)

    # Roll Up
    rollup = None
    rollup_key = "_rollup_{}".format(dept.replace(" ", "_").replace("&", ""))
    if editable:
        if st.button("Roll Up Daily Totals", key="rollup_{}".format(dept.replace(" ", "_")),
                      help="Sum daily sales + labor for this week"):
            rollup_data = db.rollup_daily_to_weekly(conn, week_start, dept)
            st.session_state[rollup_key] = rollup_data
            st.success("Daily totals rolled up. Review and save.")
    rollup = st.session_state.pop(rollup_key, None)

    # Sub-section Dispatch — include week in key so values refresh per week
    dk = "{}_{}".format(_ds(dept), week_start.replace("-", ""))
    active_sub = st.session_state.get("current_subsection", "Revenue")

    if active_sub == "Revenue":
        _render_revenue(conn, user, week_start, dept, editable, fin, rollup, dk)
    elif active_sub == "Food Cost":
        _render_food_cost(conn, user, week_start, dept, editable, fin, rollup, dk)
    elif active_sub == "Labor":
        _render_labor(conn, user, week_start, dept, editable, fin, rollup, dk)
    elif active_sub == "Invoice Tracker":
        _render_invoice_tracker(conn, user, week_start, dept, editable, fin, dk)
    elif active_sub == "Financials & Costs":
        _render_financials_and_costs(conn, user, week_start, dept, editable, fin, rollup, dk)
    elif active_sub == "Targets":
        _render_targets(conn, user, week_start, dept, fin, dk)
    elif active_sub == "Reports":
        _render_reports(conn, user, week_start, dept, editable, fin, dk)
    elif active_sub == "CTUIT Import":
        _render_ctuit_import(conn, user, week_start, dept, editable, fin, dk)
    else:
        _render_revenue(conn, user, week_start, dept, editable, fin, rollup, dk)

    # Workflow Actions
    _render_workflow_actions(conn, user, week_start, dept, status, editable, budget, fin, dk)


# ═══════════════════════════════════════════════════════════════
#  Consolidated tab (read-only aggregate)
# ═══════════════════════════════════════════════════════════════


def _render_consolidated(conn, user, week_start):
    """Render a read-only consolidated view across all departments."""
    section_title("", "Consolidated Summary")

    # ─── Gather data for all departments ───
    all_fin = []
    all_food = []
    all_ops = []
    statuses = []
    for dept in DEPARTMENTS:
        budget = db.fetch_budget(conn, week_start, dept)
        fin = db.fetch_weekly_financials(conn, week_start, dept)
        food = db.fetch_food_cost(conn, week_start, dept)
        ops = db.fetch_weekly_operational(conn, week_start, dept)
        all_fin.append((dept, fin))
        all_food.append((dept, food))
        all_ops.append((dept, ops))
        statuses.append((dept, budget["status"] if budget else "Draft"))

    # ─── Status Overview ───
    for dept, s in statuses:
        badge = STATUS_COLORS.get(s, "\u26aa")
        st.markdown("{} **{}**: {}".format(badge, dept, s))

    mini_divider()

    # ─── Consolidated Revenue ───
    section_title("", "Revenue")
    total_board = 0.0
    total_retail = 0.0
    total_flex = 0.0
    total_catering = 0.0
    total_other = 0.0
    for dept, fin in all_fin:
        total_board += _fval(fin, "board_revenue")
        total_retail += _fval(fin, "retail_revenue")
        total_flex += _fval(fin, "flex_revenue")
        total_catering += _fval(fin, "catering_revenue")
        total_other += _fval(fin, "other_revenue")
    grand_revenue = total_board + total_retail + total_flex + total_catering + total_other

    budget_kpi_row([
        ("Board", fmt_dollar(total_board), "blue"),
        ("Retail", fmt_dollar(total_retail), "purple"),
        ("Flex", fmt_dollar(total_flex), "teal"),
        ("Catering", fmt_dollar(total_catering), "amber"),
        ("Other", fmt_dollar(total_other), "green"),
    ])
    budget_summary_metric("TOTAL REVENUE", fmt_dollar(grand_revenue))

    mini_divider()

    # ─── Consolidated Labor ───
    section_title("", "Labor")
    total_labor_d = 0.0
    total_labor_h = 0.0
    for dept, fin in all_fin:
        total_labor_d += _fval(fin, "total_labor_dollars")
        total_labor_h += _fval(fin, "total_labor_hours")
    labor_pct = calc_labor_pct(total_labor_d, grand_revenue)
    splh = calc_splh(grand_revenue, total_labor_h)

    budget_kpi_row([
        ("Total Labor ($)", fmt_dollar(total_labor_d), "red"),
        ("Total Hours", fmt_number(total_labor_h), "blue"),
        ("Labor %", fmt_pct(labor_pct), "amber"),
        ("SPLH", fmt_dollar(splh), "green"),
    ])

    mini_divider()

    # ─── Consolidated Food Cost ───
    section_title("", "Food Cost")
    total_cos = 0.0
    for dept, fin in all_fin:
        total_cos += _fval(fin, "cos_dollars")
    cos_pct = calc_cos_pct(total_cos, grand_revenue)

    budget_kpi_row([
        ("COS ($)", fmt_dollar(total_cos), "amber"),
        ("COS (%)", fmt_pct(cos_pct), "amber"),
    ])

    mini_divider()

    # ─── Consolidated Other Financials ───
    section_title("", "Other Financials")
    total_ot = 0.0
    total_de = 0.0
    for dept, fin in all_fin:
        total_ot += _fval(fin, "overtime_dollars")
        total_de += _fval(fin, "direct_expenses")

    budget_kpi_row([
        ("Overtime", fmt_dollar(total_ot), "red"),
        ("Direct Expenses", fmt_dollar(total_de), "blue"),
    ])

    mini_divider()

    # ─── Per-Department Breakdown Table ───
    section_title("", "Department Breakdown")
    header_cols = st.columns([2, 1, 1, 1, 1, 1])
    with header_cols[0]:
        st.markdown("**Department**")
    with header_cols[1]:
        st.markdown("**Revenue**")
    with header_cols[2]:
        st.markdown("**Labor $**")
    with header_cols[3]:
        st.markdown("**Labor %**")
    with header_cols[4]:
        st.markdown("**SPLH**")
    with header_cols[5]:
        st.markdown("**COS %**")

    for dept, fin in all_fin:
        rev = _get_total_revenue(fin)
        lab_d = _fval(fin, "total_labor_dollars")
        lab_h = _fval(fin, "total_labor_hours")
        cos_d = _fval(fin, "cos_dollars")
        lp = calc_labor_pct(lab_d, rev)
        sp = calc_splh(rev, lab_h)
        cp = calc_cos_pct(cos_d, rev)

        row_cols = st.columns([2, 1, 1, 1, 1, 1])
        with row_cols[0]:
            st.markdown(dept)
        with row_cols[1]:
            st.markdown(fmt_dollar(rev))
        with row_cols[2]:
            st.markdown(fmt_dollar(lab_d))
        with row_cols[3]:
            st.markdown(fmt_pct(lp))
        with row_cols[4]:
            st.markdown(fmt_dollar(sp))
        with row_cols[5]:
            st.markdown(fmt_pct(cp))

    # Totals row
    row_cols = st.columns([2, 1, 1, 1, 1, 1])
    with row_cols[0]:
        st.markdown("**TOTAL**")
    with row_cols[1]:
        st.markdown("**{}**".format(fmt_dollar(grand_revenue)))
    with row_cols[2]:
        st.markdown("**{}**".format(fmt_dollar(total_labor_d)))
    with row_cols[3]:
        st.markdown("**{}**".format(fmt_pct(labor_pct)))
    with row_cols[4]:
        st.markdown("**{}**".format(fmt_dollar(splh)))
    with row_cols[5]:
        st.markdown("**{}**".format(fmt_pct(cos_pct)))


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Revenue
# ═══════════════════════════════════════════════════════════════


def _render_revenue(conn, user, week_start, dept, editable, fin, rollup, dk=""):
    section_title("", "Revenue")

    # Board & Catering: no Retail field
    # Starbucks, Qdoba, Retail & Mac's Grill: no Board field
    is_board_dept = (dept == "Board & Catering")
    show_board = is_board_dept
    show_retail = not is_board_dept

    if editable:
        # Build fields list based on department
        fields = []
        if show_board:
            fields.append(("Board ($)", "board_revenue", "wf_board_"))
        if show_retail:
            fields.append(("Retail ($)", "retail_revenue", "wf_retail_"))
        fields.append(("Flex ($)", "flex_revenue", "wf_flex_"))
        fields.append(("Catering ($)", "catering_revenue", "wf_catering_"))
        fields.append(("Other ($)", "other_revenue", "wf_other_"))

        cols = st.columns(len(fields))
        rev_values = {}
        for col, (label, db_key, key_prefix) in zip(cols, fields):
            with col:
                # Use rollup value if available, otherwise use saved DB value
                widget_key = "{}{}".format(key_prefix, dk)
                default_val = _fval(fin, db_key, rollup)
                # Force widget to use the DB/rollup value by updating session state
                if widget_key not in st.session_state or rollup:
                    st.session_state[widget_key] = default_val
                rev_values[db_key] = st.number_input(label,
                                                      min_value=0.0, step=100.0, format="%.2f",
                                                      key=widget_key)

        # Zero out hidden fields so totals stay correct
        board_rev = rev_values.get("board_revenue", 0.0)
        retail_rev = rev_values.get("retail_revenue", 0.0)
        flex_rev = rev_values.get("flex_revenue", 0.0)
        catering_rev = rev_values.get("catering_revenue", 0.0)
        other_rev = rev_values.get("other_revenue", 0.0)

        total_revenue = sum_revenue_streams(board_rev, retail_rev, flex_rev, catering_rev, other_rev)
        budget_summary_metric("TOTAL REVENUE", fmt_dollar(total_revenue))

        # premium button styling applied globally via CSS
        if st.button("Save Revenue", key="save_revenue_{}".format(dk), use_container_width=True):
            fin_data = _build_fin_update(fin, {
                "board_revenue": board_rev,
                "retail_revenue": retail_rev,
                "flex_revenue": flex_rev,
                "catering_revenue": catering_rev,
                "other_revenue": other_rev,
            })
            db.upsert_weekly_financials(conn, week_start, dept, fin_data, user["username"])
            st.success("Revenue saved.")
            st.rerun()
        # end premium button
    else:
        board_rev = _fval(fin, "board_revenue")
        retail_rev = _fval(fin, "retail_revenue")
        flex_rev = _fval(fin, "flex_revenue")
        catering_rev = _fval(fin, "catering_revenue")
        other_rev = _fval(fin, "other_revenue")

        kpi_items = []
        if show_board:
            kpi_items.append(("Board", fmt_dollar(board_rev), "blue"))
        if show_retail:
            kpi_items.append(("Retail", fmt_dollar(retail_rev), "purple"))
        kpi_items.append(("Flex", fmt_dollar(flex_rev), "teal"))
        kpi_items.append(("Catering", fmt_dollar(catering_rev), "amber"))
        kpi_items.append(("Other", fmt_dollar(other_rev), "green"))
        budget_kpi_row(kpi_items)

        total_revenue = sum_revenue_streams(board_rev, retail_rev, flex_rev, catering_rev, other_rev)
        budget_summary_metric("TOTAL REVENUE", fmt_dollar(total_revenue))


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Food Cost
# ═══════════════════════════════════════════════════════════════


def _render_food_cost(conn, user, week_start, dept, editable, fin, rollup, dk=""):
    section_title("", "Food Cost")
    food = db.fetch_food_cost(conn, week_start, dept)
    total_revenue = _get_total_revenue(fin)

    if editable:
        fc1, fc2 = st.columns(2)
        with fc1:
            cos_val = st.number_input("Total Food Cost ($)",
                                      value=float(food["invoice_total"]) if food else 0.0,
                                      min_value=0.0, step=50.0, format="%.2f", key="fc_total_{}".format(dk))
        with fc2:
            fc_notes = st.text_input("Food Cost Notes",
                                     value=(food["notes"] or "") if food else "",
                                     key="fc_notes_{}".format(dk))
    else:
        cos_val = float(food["invoice_total"]) if food else 0.0
        fc_notes = (food["notes"] or "") if food else ""
        fc1, fc2 = st.columns(2)
        with fc1:
            st.metric("Food Cost ($)", fmt_dollar(cos_val))
        with fc2:
            st.metric("Notes", fc_notes or "—")

    cos_pct = calc_cos_pct(cos_val, total_revenue)

    # Get resident meals from operational data for CPM
    ops = db.fetch_weekly_operational(conn, week_start, dept)
    resident_meals = _fval(ops, "students_resident_plan")
    cpm = calc_cpm(cos_val, resident_meals)

    budget_kpi_row([
        ("COS ($)", fmt_dollar(cos_val), "amber"),
        ("COS (%)", fmt_pct(cos_pct), "amber"),
        ("CPM (Res)", fmt_dollar(cpm), "blue"),
    ])

    if editable:
        # premium button styling applied globally via CSS
        if st.button("Save Food Cost", key="save_fc_{}".format(dk), use_container_width=True):
            db.upsert_food_cost(conn, week_start, dept, cos_val, 0.0,
                                0.0, 0.0, fc_notes, user["username"])
            # Also update COS in weekly_financials
            fin_data = _build_fin_update(fin, {"cos_dollars": cos_val})
            db.upsert_weekly_financials(conn, week_start, dept, fin_data, user["username"])
            st.success("Food cost saved.")
            st.rerun()
        # end premium button

    # Show COS detail breakdown from CTUIT if available
    cos_details = db.fetch_ctuit_details(conn, week_start, dept, section="cos")
    non_zero_cos = [d for d in cos_details if d["amount"] != 0]
    if non_zero_cos:
        mini_divider()
        _detail_display = {}
        for _lbl, (sec, key, disp) in CTUIT_DETAIL_MAP.items():
            if sec == "cos":
                _detail_display[key] = disp
        with st.expander("COS Breakdown (from CTUIT)", expanded=False):
            cos_df = pd.DataFrame([
                {"Item": _detail_display.get(d["line_item"], d["line_item"]),
                 "Amount": fmt_dollar(d["amount"])}
                for d in non_zero_cos
            ])
            st.dataframe(cos_df, use_container_width=True, hide_index=True)



# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Operation Costs
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Invoice Tracker (live from Excel)
# ═══════════════════════════════════════════════════════════════


def _parse_invoice_sheet_date(sheet_name):
    """Extract week-start (Sunday) date from sheet name like 'WE 08.10.25-08.16.25'."""
    cleaned = re.sub(r'^WE\s*', '', str(sheet_name).strip(), flags=re.IGNORECASE).strip()
    parts = re.split(r'\s*-\s*', cleaned)
    if not parts:
        return None
    first_part = parts[0].strip()
    for fmt in ("%m.%d.%y", "%m.%d.%Y", "%m/%d/%y", "%m/%d/%Y",
                "%m-%d-%y", "%m-%d-%Y"):
        try:
            from datetime import datetime as _dt
            d = _dt.strptime(first_part, fmt).date()
            return db.get_week_start(d)
        except ValueError:
            continue
    return None


def _safe_invoice_float(val):
    """Convert a cell value to float, handling NaN/None/strings."""
    if val is None:
        return 0.0
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return 0.0
        return float(val)
    except (ValueError, TypeError):
        return 0.0


@st.cache_data(ttl=300)
def _load_invoice_workbook(file_path):
    """Load all sheets from the invoice tracker Excel file (cached 5 min).
    Returns {week_start_iso: {sheet_name: DataFrame}} or None on error.
    """
    if not os.path.exists(file_path):
        return None
    try:
        all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)
    except Exception:
        return None

    result = {}
    for name, df in all_sheets.items():
        if "BLANK" in name.upper() or "MASTER" in name.upper():
            continue
        if df.empty:
            continue
        parsed = _parse_invoice_sheet_date(name)
        if parsed:
            result[parsed.isoformat()] = (name, df)
    return result


def _extract_section_data(df, dept):
    """Extract vendor rows for a given department from one sheet DataFrame.
    Returns list of dicts with section, vendor, day values, total.
    """
    section_keywords = set(k.upper().strip() for k in INVOICE_EXCEL_SECTION_MAP.keys())
    # Build reverse map: find which sections map to this department
    dept_sections = set()
    for k, v in INVOICE_EXCEL_SECTION_MAP.items():
        if v == dept:
            dept_sections.add(k.upper().strip())

    rows = []
    current_section_label = ""
    is_our_dept = False

    for row_idx in range(len(df)):
        row = df.iloc[row_idx]
        first_cell = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        first_upper = first_cell.upper().strip()

        # Check if this is a section header
        if first_upper in section_keywords:
            current_section_label = first_cell.strip().title()
            is_our_dept = first_upper in dept_sections
            continue

        if not is_our_dept or not first_cell:
            continue

        # Skip header/total/label rows
        skip_words = ["INVOICE TRACKING", "INVOICE(S)", "TOTAL", "GRAND TOTAL",
                      "SUN", "MON", "TUE", "WED", "THUR", "FRI", "SAT"]
        if any(sw in first_upper for sw in skip_words):
            if first_upper.startswith("TOTAL") or first_upper.startswith("GRAND"):
                continue
            if first_upper in ("SUN", "MON", "TUE", "WED", "THUR", "FRI", "SAT"):
                continue
            if "INVOICE" in first_upper:
                continue

        vendor = first_cell.strip()
        if not vendor:
            continue

        day_vals = {}
        row_total = 0.0
        for i, dl in enumerate(INVOICE_DAY_LABELS):
            col_idx = i + 1
            val = 0.0
            if col_idx < len(row):
                val = _safe_invoice_float(row.iloc[col_idx])
            day_vals[dl] = val
            row_total += val

        # Only include rows with at least some data
        if row_total > 0 or any(v != 0 for v in day_vals.values()):
            rows.append({
                "Section": current_section_label,
                "Vendor": vendor,
                **day_vals,
                "Total": round(row_total, 2),
            })

    return rows


def _render_invoice_tracker(conn, user, week_start, dept, editable, fin, dk=""):
    """Render the Invoice Tracker — reads live from the ALMA Excel workbook."""
    section_title("", "Invoice Tracker")

    # Check if file exists
    file_path = INVOICE_TRACKER_FILE
    if not os.path.exists(file_path):
        st.warning(
            "\u26a0\ufe0f Invoice Tracker file not found.\n\n"
            "Expected path: `{}`\n\n"
            "Update `INVOICE_TRACKER_FILE` in `config.py` if the file moved.".format(file_path)
        )
        return

    # Show file info + Open in Excel button
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    info_col, btn_col = st.columns([3, 1])
    with info_col:
        st.caption(
            "\U0001f4c2 Linked to: **{}** ({:.1f} MB)".format(
                os.path.basename(file_path), file_size_mb
            )
        )
    with btn_col:
        if st.button(
            "\U0001f4c4 Open in Excel",
            key="open_excel_{}".format(dk),
            use_container_width=True,
            type="primary",
        ):
            try:
                subprocess.Popen(["open", file_path])
                st.toast("Opening Invoice Tracker in Excel...")
            except Exception as e:
                st.error("Could not open file: {}".format(str(e)))

    # Load workbook (cached)
    wb_data = _load_invoice_workbook(file_path)
    if wb_data is None:
        st.error("Could not read the Invoice Tracker workbook.")
        return

    # Find the sheet matching this week
    week_key = str(week_start)
    if week_key not in wb_data:
        st.info(
            "No invoice data found for the week of **{}** in the workbook.\n\n"
            "Available weeks: **{}**".format(
                week_start,
                len(wb_data),
            )
        )
        # Show available weeks in an expander
        if wb_data:
            with st.expander("View available weeks"):
                avail = sorted(wb_data.keys())
                for wk in avail:
                    sheet_name = wb_data[wk][0]
                    st.text("{} — {}".format(wk, sheet_name))
        return

    sheet_name, sheet_df = wb_data[week_key]
    st.caption("\U0001f4c4 Sheet: **{}**".format(sheet_name))

    # Extract data for this department
    rows = _extract_section_data(sheet_df, dept)

    if not rows:
        st.info("No invoice data for **{}** this week.".format(dept))
        return

    display_df = pd.DataFrame(rows)

    # Show the data table
    col_config = {
        "Section": st.column_config.TextColumn("Section", width="small"),
        "Vendor": st.column_config.TextColumn("Vendor", width="medium"),
        "Total": st.column_config.NumberColumn("Total", format="$%.2f"),
    }
    for dl in INVOICE_DAY_LABELS:
        col_config[dl] = st.column_config.NumberColumn(dl, format="$%.2f")

    st.dataframe(
        display_df,
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
    )

    # ─── Summary Metrics ───
    mini_divider()
    dept_total = sum(r["Total"] for r in rows)
    section_totals = {}
    for r in rows:
        sec = r["Section"]
        section_totals[sec] = section_totals.get(sec, 0.0) + r["Total"]

    cols = st.columns(max(len(section_totals) + 1, 2))
    with cols[0]:
        st.metric("Department Total", fmt_dollar(dept_total))
    for i, (sec, total) in enumerate(sorted(section_totals.items())):
        if sec and i + 1 < len(cols):
            with cols[i + 1]:
                st.metric(sec, fmt_dollar(total))

    # Refresh button
    mini_divider()
    if st.button(
        "\U0001f504 Refresh from Excel",
        key="refresh_inv_{}".format(dk),
        help="Reload latest data from the Excel file",
    ):
        _load_invoice_workbook.clear()
        st.rerun()


# ═══════════════════════════════════════════════════════════════
#  Labor
# ═══════════════════════════════════════════════════════════════


def _render_labor(conn, user, week_start, dept, editable, fin, rollup, dk=""):
    section_title("", "Labor")
    total_revenue = _get_total_revenue(fin)

    if editable:
        lc1, lc2 = st.columns(2)
        with lc1:
            labor_dollars = st.number_input("Total Labor ($)",
                                            value=_fval(fin, "total_labor_dollars", rollup),
                                            min_value=0.0, step=50.0, format="%.2f", key="wf_labor_d_{}".format(dk))
        with lc2:
            labor_hours = st.number_input("Total Labor Hours",
                                          value=_fval(fin, "total_labor_hours", rollup),
                                          min_value=0.0, step=1.0, format="%.1f", key="wf_labor_h_{}".format(dk))
    else:
        labor_dollars = _fval(fin, "total_labor_dollars")
        labor_hours = _fval(fin, "total_labor_hours")
        lc1, lc2 = st.columns(2)
        with lc1:
            st.metric("Labor ($)", fmt_dollar(labor_dollars))
        with lc2:
            st.metric("Labor Hours", fmt_number(labor_hours))

    labor_pct = calc_labor_pct(labor_dollars, total_revenue)
    splh = calc_splh(total_revenue, labor_hours)

    # Get resident meals from operational data for MPLH
    ops = db.fetch_weekly_operational(conn, week_start, dept)
    resident_meals = _fval(ops, "students_resident_plan")
    mplh = calc_mplh(resident_meals, labor_hours)

    budget_kpi_row([
        ("Labor %", fmt_pct(labor_pct), "red"),
        ("SPLH", fmt_dollar(splh), "green"),
        ("MPLH (Res)", fmt_number(mplh), "blue"),
    ])

    if editable:
        # premium button styling applied globally via CSS
        if st.button("Save Labor", key="save_labor_{}".format(dk), use_container_width=True):
            fin_data = _build_fin_update(fin, {
                "total_labor_dollars": labor_dollars,
                "total_labor_hours": labor_hours,
            })
            db.upsert_weekly_financials(conn, week_start, dept, fin_data, user["username"])
            st.success("Labor saved.")
            st.rerun()
        # end premium button


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Financials & Costs (merged)
# ═══════════════════════════════════════════════════════════════


def _render_financials_and_costs(conn, user, week_start, dept, editable, fin, rollup, dk=""):
    section_title("", "Financials & Operating Costs")

    # ─── Total Operating Costs KPI ───
    total_cont = _fval(fin, "direct_expenses")
    total_nc = _fval(fin, "non_cont_expenses")
    total_ops = total_cont + total_nc

    budget_kpi_row([
        ("Total Operating Costs", fmt_dollar(total_ops), "red"),
        ("Controllable", fmt_dollar(total_cont), "amber"),
        ("Non-Controllable", fmt_dollar(total_nc), "blue"),
    ])

    mini_divider()

    # ─── Controllable Section ───
    st.markdown("#### Controllable Expenses")
    if editable:
        oc1, oc2 = st.columns(2)
        with oc1:
            overtime = st.number_input("Overtime ($)",
                                       value=_fval(fin, "overtime_dollars", rollup),
                                       min_value=0.0, step=25.0, format="%.2f", key="wf_ot_{}".format(dk))
        with oc2:
            direct_exp = st.number_input("Direct Expenses / Cont. Total ($)",
                                          value=_fval(fin, "direct_expenses", rollup),
                                          min_value=0.0, step=50.0, format="%.2f", key="wf_de_{}".format(dk))
    else:
        oc1, oc2 = st.columns(2)
        with oc1:
            st.metric("Overtime", fmt_dollar(_fval(fin, "overtime_dollars")))
        with oc2:
            st.metric("Direct Expenses (Cont.)", fmt_dollar(_fval(fin, "direct_expenses")))

    # Controllable breakdown from CTUIT
    _detail_display = {}
    for _lbl, (sec, key, disp) in CTUIT_DETAIL_MAP.items():
        _detail_display[key] = disp

    all_details = db.fetch_ctuit_details(conn, week_start, dept)
    cont_items = [d for d in all_details if d["section"] == "controllable" and d["amount"] != 0]
    if cont_items:
        with st.expander("Controllable Breakdown — {}".format(fmt_dollar(total_cont)), expanded=False):
            cont_df = pd.DataFrame([
                {"Item": _detail_display.get(d["line_item"], d["line_item"]),
                 "Amount": fmt_dollar(d["amount"])}
                for d in cont_items
            ])
            st.dataframe(cont_df, use_container_width=True, hide_index=True)

    mini_divider()

    # ─── Non-Controllable Section ───
    st.markdown("#### Non-Controllable Expenses")
    if editable:
        nc1, nc2, nc3 = st.columns(3)
        with nc1:
            non_cont = st.number_input("Non-Cont. Total ($)",
                                        value=_fval(fin, "non_cont_expenses", rollup),
                                        min_value=0.0, step=50.0, format="%.2f", key="wf_nc_{}".format(dk))
        with nc2:
            insurance = st.number_input("Insurance ($)",
                                         value=_fval(fin, "insurance", rollup),
                                         min_value=0.0, step=25.0, format="%.2f", key="wf_ins_{}".format(dk))
        with nc3:
            mgmt_fees = st.number_input("Management Fees ($)",
                                         value=_fval(fin, "management_fees", rollup),
                                         min_value=0.0, step=25.0, format="%.2f", key="wf_mf_{}".format(dk))
        nf1, nf2 = st.columns(2)
        with nf1:
            profit_fee = st.number_input("Profit / Fee ($)",
                                          value=_fval(fin, "profit_fee", rollup),
                                          min_value=0.0, step=25.0, format="%.2f", key="wf_pf_{}".format(dk))
        with nf2:
            royalties = st.number_input("Royalties / Nat'l Adv ($)",
                                         value=_fval(fin, "royalties", rollup),
                                         min_value=0.0, step=25.0, format="%.2f", key="wf_roy_{}".format(dk))
    else:
        nc1, nc2, nc3 = st.columns(3)
        with nc1:
            st.metric("Non-Cont. Expenses", fmt_dollar(_fval(fin, "non_cont_expenses")))
        with nc2:
            st.metric("Insurance", fmt_dollar(_fval(fin, "insurance")))
        with nc3:
            st.metric("Management Fees", fmt_dollar(_fval(fin, "management_fees")))
        nf1, nf2 = st.columns(2)
        with nf1:
            st.metric("Profit / Fee", fmt_dollar(_fval(fin, "profit_fee")))
        with nf2:
            st.metric("Royalties / Nat'l Adv", fmt_dollar(_fval(fin, "royalties")))

    # Non-controllable breakdown from CTUIT
    nc_items = [d for d in all_details if d["section"] == "non_controllable" and d["amount"] != 0]
    if nc_items:
        with st.expander("Non-Controllable Breakdown — {}".format(fmt_dollar(total_nc)), expanded=False):
            nc_df = pd.DataFrame([
                {"Item": _detail_display.get(d["line_item"], d["line_item"]),
                 "Amount": fmt_dollar(d["amount"])}
                for d in nc_items
            ])
            st.dataframe(nc_df, use_container_width=True, hide_index=True)

    # Save button
    if editable:
        mini_divider()
        # premium button styling applied globally via CSS
        if st.button("Save Financials & Costs", key="save_fin_costs_{}".format(dk), use_container_width=True):
            fin_data = _build_fin_update(fin, {
                "overtime_dollars": overtime,
                "direct_expenses": direct_exp,
                "non_cont_expenses": non_cont,
                "insurance": insurance,
                "management_fees": mgmt_fees,
                "profit_fee": profit_fee,
                "royalties": royalties,
            })
            db.upsert_weekly_financials(conn, week_start, dept, fin_data, user["username"])
            st.success("Financials & costs saved.")
            st.rerun()
        # end premium button

    # ─── P&L Summary ───
    mini_divider()
    gp = _fval(fin, "gross_profit")
    tp = _fval(fin, "total_payroll")
    tf = _fval(fin, "tax_fringe")
    apc = _fval(fin, "after_prime_costs")
    pace = _fval(fin, "pace")
    ni = _fval(fin, "net_income")
    if gp != 0 or ni != 0 or apc != 0:
        st.markdown("#### P&L Summary")
        st.caption("From CTUIT Ops Statement import")
        budget_kpi_row([
            ("Gross Profit", fmt_dollar(gp), "green"),
            ("Total Payroll", fmt_dollar(tp), "red"),
            ("Tax & Fringe", fmt_dollar(tf), "amber"),
        ])
        budget_kpi_row([
            ("After Prime Costs", fmt_dollar(apc), "blue"),
            ("PACE", fmt_dollar(pace), "purple"),
            ("Net Income", fmt_dollar(ni), "navy"),
        ])

    # ─── Labor Detail ───
    labor_items = [d for d in all_details if d["section"] == "labor" and d["amount"] != 0]
    if labor_items:
        with st.expander("Labor Detail (from CTUIT)", expanded=False):
            labor_df = pd.DataFrame([
                {"Item": _detail_display.get(d["line_item"], d["line_item"]),
                 "Amount": fmt_dollar(d["amount"])}
                for d in labor_items
            ])
            st.dataframe(labor_df, use_container_width=True, hide_index=True)

    # ─── Manual Operation Cost Entries ───
    with st.expander("Manual Operation Cost Entries", expanded=False):
        op_cost_values = {}
        oc_cols = st.columns(min(len(OPERATION_COST_CATEGORIES), 4))
        for idx, cat in enumerate(OPERATION_COST_CATEGORIES):
            col_idx = idx % len(oc_cols)
            existing_oc = conn.execute(
                "SELECT amount, description FROM operation_cost WHERE week_start=? AND department=? AND category=?",
                (week_start, dept, cat),
            ).fetchone()
            with oc_cols[col_idx]:
                if editable:
                    amt = st.number_input("{} ($)".format(cat),
                                         value=float(existing_oc["amount"]) if existing_oc else 0.0,
                                         min_value=0.0, step=25.0, format="%.2f",
                                         key="oc_{}_{}".format(cat.lower().replace(" ", "_"), dk))
                    op_cost_values[cat] = amt
                else:
                    st.metric(cat, fmt_dollar(float(existing_oc["amount"]) if existing_oc else 0.0))

        if editable:
            if st.button("Save Manual Costs", key="save_opcost_{}".format(dk), use_container_width=True):
                now_str = __import__("datetime").datetime.now().isoformat()
                for cat, amt in op_cost_values.items():
                    existing = conn.execute(
                        "SELECT id FROM operation_cost WHERE week_start=? AND department=? AND category=?",
                        (week_start, dept, cat),
                    ).fetchone()
                    if existing:
                        conn.execute(
                            "UPDATE operation_cost SET amount=?, updated_by=?, updated_at=? WHERE id=?",
                            (amt, user["username"], now_str, existing["id"]),
                        )
                    else:
                        conn.execute(
                            """INSERT INTO operation_cost (week_start, department, category, amount, updated_by, updated_at)
                               VALUES (?,?,?,?,?,?)""",
                            (week_start, dept, cat, amt, user["username"], now_str),
                        )
                conn.commit()
                st.success("Manual costs saved.")
                st.rerun()

    # ─── Operational Metrics (Board & Catering only) ───
    if dept == "Board & Catering":
        mini_divider()
        _render_operational(conn, user, week_start, dept, editable, dk)


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Operational (standalone — kept for compatibility)
# ═══════════════════════════════════════════════════════════════


def _render_operational(conn, user, week_start, dept, editable, dk=""):
    section_title("", "Operational Metrics")
    ops = db.fetch_weekly_operational(conn, week_start, dept)

    if editable:
        st.markdown("#### Student Plans")
        op1, op2, op3, op4 = st.columns(4)
        with op1:
            v_res = st.number_input("Students Resident", value=int(_fval(ops, "students_resident_plan")),
                                    min_value=0, step=1, key="op_res_{}".format(dk))
        with op2:
            v_com = st.number_input("Students Commuter", value=int(_fval(ops, "students_commuter_plan")),
                                    min_value=0, step=1, key="op_com_{}".format(dk))
        with op3:
            v_part = st.number_input("Participation %", value=_fval(ops, "meals_used_participation_pct"),
                                     min_value=0.0, step=0.1, format="%.2f", key="op_part_{}".format(dk))
        with op4:
            v_bill = st.number_input("Billing Days", value=int(_fval(ops, "board_plan_billing_days")),
                                     min_value=0, step=1, key="op_bill_{}".format(dk))

        st.markdown("#### Labor Hours Breakdown")
        lh1, lh2, lh3, lh4, lh5 = st.columns(5)
        with lh1:
            v_bplh = st.number_input("Board Plan Hrs", value=_fval(ops, "board_plan_labor_hours"),
                                     min_value=0.0, step=1.0, format="%.1f", key="op_bplh_{}".format(dk))
        with lh2:
            v_rlh = st.number_input("Retail Hrs", value=_fval(ops, "retail_labor_hours"),
                                    min_value=0.0, step=1.0, format="%.1f", key="op_rlh_{}".format(dk))
        with lh3:
            v_clh = st.number_input("Catering Hrs", value=_fval(ops, "catering_labor_hours"),
                                    min_value=0.0, step=1.0, format="%.1f", key="op_clh_{}".format(dk))
        with lh4:
            v_cnlh = st.number_input("Concession Hrs", value=_fval(ops, "concession_labor_hours"),
                                     min_value=0.0, step=1.0, format="%.1f", key="op_cnlh_{}".format(dk))
        with lh5:
            v_cflh = st.number_input("Conference Hrs", value=_fval(ops, "conference_labor_hours"),
                                     min_value=0.0, step=1.0, format="%.1f", key="op_cflh_{}".format(dk))

        st.markdown("#### OT / Temp / Wages")
        w1, w2, w3, w4 = st.columns(4)
        with w1:
            v_oth = st.number_input("OT Hours", value=_fval(ops, "ot_hours_included_above"),
                                    min_value=0.0, step=1.0, format="%.1f", key="op_oth_{}".format(dk))
        with w2:
            v_otd = st.number_input("OT Dollars", value=_fval(ops, "ot_dollars_paid"),
                                    min_value=0.0, step=25.0, format="%.2f", key="op_otd_{}".format(dk))
        with w3:
            v_tph = st.number_input("Temp Hours", value=_fval(ops, "temp_hours_included_above"),
                                    min_value=0.0, step=1.0, format="%.1f", key="op_tph_{}".format(dk))
        with w4:
            v_tpd = st.number_input("Temp Dollars", value=_fval(ops, "temp_dollars_paid"),
                                    min_value=0.0, step=25.0, format="%.2f", key="op_tpd_{}".format(dk))

        w5, w6, w7, w8, w9 = st.columns(5)
        with w5:
            v_mw = st.number_input("Mgmt Wages", value=_fval(ops, "management_wages"),
                                   min_value=0.0, step=50.0, format="%.2f", key="op_mw_{}".format(dk))
        with w6:
            v_hw = st.number_input("Hourly Wages", value=_fval(ops, "hourly_wages"),
                                   min_value=0.0, step=50.0, format="%.2f", key="op_hw_{}".format(dk))
        with w7:
            v_ahw = st.number_input("Avg Hourly Wage", value=_fval(ops, "average_hourly_wage"),
                                    min_value=0.0, step=0.5, format="%.2f", key="op_ahw_{}".format(dk))
        with w8:
            v_fee = st.number_input("Fee Account", value=_fval(ops, "fee_account_fee"),
                                    min_value=0.0, step=25.0, format="%.2f", key="op_fee_{}".format(dk))
        with w9:
            v_inv = st.number_input("Total Inventory", value=_fval(ops, "total_inventory"),
                                    min_value=0.0, step=100.0, format="%.2f", key="op_inv_{}".format(dk))

        if st.button("Save Operational Metrics", key="save_ops_{}".format(dk), use_container_width=True):
            ops_data = {
                "students_resident_plan": v_res,
                "students_commuter_plan": v_com,
                "meals_used_participation_pct": v_part,
                "board_plan_billing_days": v_bill,
                "board_plan_labor_hours": v_bplh,
                "retail_labor_hours": v_rlh,
                "catering_labor_hours": v_clh,
                "concession_labor_hours": v_cnlh,
                "conference_labor_hours": v_cflh,
                "ot_hours_included_above": v_oth,
                "ot_dollars_paid": v_otd,
                "temp_hours_included_above": v_tph,
                "temp_dollars_paid": v_tpd,
                "management_wages": v_mw,
                "hourly_wages": v_hw,
                "average_hourly_wage": v_ahw,
                "fee_account_fee": v_fee,
                "total_inventory": v_inv,
            }
            db.upsert_weekly_operational(conn, week_start, dept, ops_data, user["username"])
            st.success("Operational metrics saved.")
            st.rerun()
    else:
        st.caption("Operational metrics are read-only in current status.")
        if ops:
            ro1, ro2, ro3, ro4 = st.columns(4)
            with ro1:
                st.metric("Students Resident", int(ops.get("students_resident_plan", 0) or 0))
            with ro2:
                st.metric("Students Commuter", int(ops.get("students_commuter_plan", 0) or 0))
            with ro3:
                st.metric("Participation %", fmt_pct(ops.get("meals_used_participation_pct")))
            with ro4:
                st.metric("Billing Days", int(ops.get("board_plan_billing_days", 0) or 0))

            mini_divider()
            ro5, ro6, ro7, ro8, ro9 = st.columns(5)
            with ro5:
                st.metric("Board Plan Hrs", fmt_number(ops.get("board_plan_labor_hours")))
            with ro6:
                st.metric("Retail Hrs", fmt_number(ops.get("retail_labor_hours")))
            with ro7:
                st.metric("Catering Hrs", fmt_number(ops.get("catering_labor_hours")))
            with ro8:
                st.metric("Concession Hrs", fmt_number(ops.get("concession_labor_hours")))
            with ro9:
                st.metric("Conference Hrs", fmt_number(ops.get("conference_labor_hours")))
        else:
            st.caption("No operational data for this week.")


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Targets
# ═══════════════════════════════════════════════════════════════


def _render_targets(conn, user, week_start, dept, fin, dk=""):
    total_revenue = _get_total_revenue(fin)
    labor_dollars = _fval(fin, "total_labor_dollars")
    labor_hours = _fval(fin, "total_labor_hours")
    labor_pct = calc_labor_pct(labor_dollars, total_revenue)
    splh = calc_splh(total_revenue, labor_hours)

    # ─── Target Comparison ───
    targets = db.fetch_targets(conn, dept)
    if targets and targets.get("target_labor_pct") and targets.get("target_splh"):
        section_title("", "Targets")
        t_lp = targets["target_labor_pct"]
        t_sp = targets["target_splh"]

        # Build KPI items with target info
        target_items = []
        if labor_pct is not None:
            on_t = labor_pct <= t_lp
            accent = "green" if on_t else "red"
            status = "✓ On Target" if on_t else "✗ Over Target"
            target_items.append(("Labor % (Target: {})".format(fmt_pct(t_lp)),
                                 "{} {}".format(fmt_pct(labor_pct), status), accent))
        else:
            target_items.append(("Labor % (Target: {})".format(fmt_pct(t_lp)), "N/A", "blue"))

        if splh is not None:
            on_t = splh >= t_sp
            accent = "green" if on_t else "red"
            status = "✓ On Target" if on_t else "✗ Below Target"
            target_items.append(("SPLH (Target: {})".format(fmt_dollar(t_sp)),
                                 "{} {}".format(fmt_dollar(splh), status), accent))
        else:
            target_items.append(("SPLH (Target: {})".format(fmt_dollar(t_sp)), "N/A", "blue"))

        budget_kpi_row(target_items)
    else:
        section_title("", "Targets")
        st.caption("No targets set for this department.")

    # ─── Performance Variances ───
    mini_divider()
    _render_variance_sections(conn, week_start, dept, total_revenue, labor_dollars,
                              labor_hours, labor_pct, splh)

    # ─── Comments ───
    mini_divider()
    section_title("", "Comments")
    show_all = st.checkbox("Show closed comments", value=False, key="show_closed_{}".format(dk))
    comments = db.fetch_comments(conn, week_start, dept, open_only=not show_all)

    if comments:
        for c in comments:
            label = "Open" if c["is_open"] else "Closed"
            st.markdown("**[{}]** [{}] {} \u2014 {}  \n*by {} at {}*".format(
                label, c["field"], c["reason_code"], c["comment_text"],
                c["created_by"], c["created_at"]))
            if c["is_open"]:
                if st.button("Close", key="close_{}_{}".format(c["id"], dk)):
                    db.close_comment(conn, c["id"])
                    st.rerun()
    else:
        st.caption("No comments.")

    with st.expander("Add Comment"):
        cf_field = st.selectbox("Field", FIELDS, key="cf_field_{}".format(dk))
        cf_reason = st.selectbox("Reason Code", REASON_CODES, key="cf_reason_{}".format(dk))
        cf_text = st.text_input("Comment", key="cf_text_{}".format(dk))
        if st.button("Add Comment", key="add_comment_{}".format(dk)):
            if cf_text.strip():
                db.add_comment(conn, week_start, dept, cf_field, cf_reason,
                               cf_text, user["username"])
                st.success("Comment added.")
                st.rerun()
            else:
                st.warning("Please enter a comment.")


# ═══════════════════════════════════════════════════════════════
#  SUB-SECTION: Reports (File Attachments + Data Import)
# ═══════════════════════════════════════════════════════════════


def _render_reports(conn, user, week_start, dept, editable, fin, dk=""):
    """Render the Reports sub-section with file attachments and budget data import."""
    _render_file_attachments(conn, user, week_start, dept, editable, dk)
    mini_divider()
    _render_budget_import(conn, user, week_start, dept, editable, fin, dk)


# ─── File Attachments ──────────────────────────────────────────


def _render_file_attachments(conn, user, week_start, dept, editable, dk=""):
    """Upload, view, and download file attachments for a budget week."""
    section_title("", "File Attachments")

    # ─── Upload (only when editable) ───
    if editable:
        allowed_str = ", ".join(ALLOWED_ATTACHMENT_EXTENSIONS)
        st.caption("Attach supporting documents ({}). Max {}MB per file.".format(
            allowed_str, MAX_FILE_SIZE_MB))

        uploaded_file = st.file_uploader(
            "Upload File",
            type=[ext.lstrip(".") for ext in ALLOWED_ATTACHMENT_EXTENSIONS],
            key="attach_upload_{}_{}".format(week_start, dk),
        )

        if uploaded_file is not None:
            file_size = uploaded_file.size
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error("File exceeds {}MB limit.".format(MAX_FILE_SIZE_MB))
            else:
                if st.button("Save Attachment", key="save_attach_{}".format(dk)):
                    _save_attachment(conn, uploaded_file, week_start, dept, user)

    # ─── List existing attachments ───
    attachments = db.fetch_attachments(conn, week_start, dept)
    if attachments:
        st.markdown("**Uploaded Files ({}):**".format(len(attachments)))
        for att in attachments:
            ac1, ac2, ac3, ac4 = st.columns([3, 1, 1, 1])
            with ac1:
                st.markdown("{} ({})".format(
                    att["original_filename"],
                    _format_file_size(att["file_size"]),
                ))
            with ac2:
                st.caption("by {} on {}".format(
                    att["uploaded_by"],
                    att["uploaded_at"][:10] if att["uploaded_at"] else "",
                ))
            with ac3:
                file_path = att["stored_path"]
                if os.path.exists(file_path):
                    with open(file_path, "rb") as fp:
                        st.download_button(
                            "Download",
                            data=fp.read(),
                            file_name=att["original_filename"],
                            key="dl_att_{}_{}".format(att["id"], dk),
                        )
                else:
                    st.caption("File missing")
            with ac4:
                if editable:
                    if st.button("Delete", key="del_att_{}_{}".format(att["id"], dk)):
                        _delete_attachment(conn, att)
                        st.rerun()
    else:
        st.caption("No files attached for this week.")


def _save_attachment(conn, uploaded_file, week_start, dept, user):
    """Save an uploaded file to the filesystem and record in the DB."""
    dept_safe = re.sub(r"[^a-zA-Z0-9_]", "_", dept)
    dir_path = os.path.join(UPLOAD_DIR, week_start, dept_safe)
    os.makedirs(dir_path, exist_ok=True)

    original_name = uploaded_file.name
    base, ext = os.path.splitext(original_name)
    stored_name = original_name
    counter = 1
    while os.path.exists(os.path.join(dir_path, stored_name)):
        stored_name = "{}_{}{}".format(base, counter, ext)
        counter += 1

    stored_path = os.path.join(dir_path, stored_name)
    with open(stored_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    db.insert_attachment(
        conn, week_start, dept, original_name, stored_path,
        ext.lstrip(".").lower(), uploaded_file.size, user["username"],
    )
    st.success("File '{}' uploaded successfully.".format(original_name))
    st.rerun()


def _delete_attachment(conn, att):
    """Delete an attachment from the filesystem and database."""
    if os.path.exists(att["stored_path"]):
        os.remove(att["stored_path"])
    db.delete_attachment(conn, att["id"])


def _format_file_size(size_bytes):
    """Format bytes into a human-readable string."""
    if size_bytes is None or size_bytes == 0:
        return "0 B"
    if size_bytes < 1024:
        return "{} B".format(size_bytes)
    elif size_bytes < 1024 * 1024:
        return "{:.1f} KB".format(size_bytes / 1024)
    else:
        return "{:.1f} MB".format(size_bytes / (1024 * 1024))


# ─── Budget Data Import ───────────────────────────────────────


def _render_budget_import(conn, user, week_start, dept, editable, fin, dk=""):
    """Upload CSV/Excel to auto-fill budget numbers with preview."""
    section_title("", "Budget Data Import")

    if not editable:
        st.caption("Budget must be in Draft or Returned status to import data.")
        return

    st.caption("Upload a CSV, Excel, or PDF ops statement with budget data. "
               "Recognized fields: {}".format(
                   ", ".join(BUDGET_IMPORT_COLUMNS.values())))

    uploaded = st.file_uploader(
        "Upload Budget Data",
        type=[ext.lstrip(".") for ext in ALLOWED_IMPORT_EXTENSIONS],
        key="import_upload_{}_{}".format(week_start, dk),
    )

    if uploaded is None:
        with st.expander("Expected Column Names"):
            for db_col, label in BUDGET_IMPORT_COLUMNS.items():
                st.markdown("- **{}** (maps to `{}`)".format(label, db_col))
        return

    # Read the file
    df, error = _read_import_file(uploaded)
    if error:
        st.error(error)
        return

    if df is None or df.empty:
        st.warning("File is empty or could not be parsed.")
        return

    # Match columns
    matched, unmatched = _match_import_columns(df)

    if not matched:
        st.error("No recognized budget columns found. Expected columns like: {}".format(
            ", ".join(list(BUDGET_IMPORT_COLUMNS.keys())[:5])))
        st.dataframe(df.head(5))
        return

    if unmatched:
        st.warning("Ignored unrecognized columns: {}".format(", ".join(unmatched)))

    # Parse values
    parsed_values = _parse_import_values(df, matched)

    # Preview
    st.markdown("#### Import Preview")
    st.caption("Review the values below before saving. These will overwrite current values.")

    preview_data = []
    for db_col, label in BUDGET_IMPORT_COLUMNS.items():
        if db_col in parsed_values:
            current_val = _get_current_value(fin, conn, week_start, dept, db_col)
            new_val = parsed_values[db_col]
            preview_data.append({
                "Field": label,
                "Current Value": fmt_dollar(current_val) if current_val else "$0.00",
                "Import Value": fmt_dollar(new_val),
                "Change": fmt_dollar(new_val - (current_val or 0)),
            })

    if preview_data:
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)

    # Save / Cancel
    ic1, ic2 = st.columns(2)
    with ic1:
        if st.button("Apply Import", type="primary", key="apply_import_{}".format(dk),
                      use_container_width=True):
            _apply_import(conn, user, week_start, dept, fin, parsed_values)
    with ic2:
        if st.button("Cancel", key="cancel_import_{}".format(dk),
                      use_container_width=True):
            st.rerun()


def _read_import_file(uploaded_file):
    """Read CSV, Excel, or PDF file into a DataFrame."""
    name = (uploaded_file.name or "").lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        elif name.endswith(".pdf"):
            df = _read_pdf_tables(uploaded_file)
        else:
            return None, "Unsupported file type. Please upload CSV, Excel, or PDF."
        if df is not None:
            df.columns = [str(c).strip() if c is not None else "Column_{}".format(i)
                          for i, c in enumerate(df.columns)]
        return df, None
    except Exception as e:
        return None, "Error reading file: {}".format(str(e))


def _read_pdf_tables(uploaded_file):
    """Extract tables from a PDF using pdfplumber and return as DataFrame.

    Strategy:
    1. Try to find structured tables across all pages.
    2. If no tables found, try text-based key/value extraction.
    3. Concatenate all found tables.
    """
    import pdfplumber
    import io

    # pdfplumber needs a file-like object
    pdf_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # reset for potential re-read

    all_tables = []
    key_values = {}

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # Try structured table extraction first
            tables = page.extract_tables()
            if tables:
                for tbl in tables:
                    if not tbl or len(tbl) < 2:
                        continue
                    # Use first row as headers
                    headers = [str(c).strip() if c else "Col_{}".format(i)
                               for i, c in enumerate(tbl[0])]
                    for row in tbl[1:]:
                        if row and any(cell for cell in row):
                            all_tables.append(dict(zip(headers, row)))

            # Also try key/value pattern from text (common in ops statements)
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # Look for "Label: $1,234" or "Label  1234.56" patterns
                    parts = _split_kv_line(line)
                    if parts:
                        key_values[parts[0]] = parts[1]

    # If we found structured tables, use those
    if all_tables:
        return pd.DataFrame(all_tables)

    # Fall back to key/value pairs extracted from text
    if key_values:
        return pd.DataFrame([key_values])

    return None


def _split_kv_line(line):
    """Try to split a line into a key/value pair for PDF text extraction.

    Handles patterns like:
      'Board Revenue: $1,234.56'
      'Board Revenue    $1,234.56'
      'Board Revenue    1,234.56'
      'Total Labor ($)  5678'
    Returns (key, value) tuple or None.
    """
    import re
    # Pattern: label followed by colon or multiple spaces, then a dollar amount or number
    m = re.match(
        r'^(.+?)\s*[:]\s*\$?([\d,]+\.?\d*)\s*$',
        line,
    )
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    # Pattern: label then 2+ spaces then dollar/number value
    m = re.match(
        r'^(.+?)\s{2,}\$?([\d,]+\.?\d*)\s*$',
        line,
    )
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    return None


def _match_import_columns(df):
    """Match DataFrame columns to known budget fields.
    Returns (matched_dict {df_col: db_col}, unmatched_list).
    """
    matched = {}
    unmatched = []
    known_keys = set(BUDGET_IMPORT_COLUMNS.keys())
    known_labels = {}
    for k, v in BUDGET_IMPORT_COLUMNS.items():
        known_labels[v.lower()] = k

    for col in df.columns:
        col_lower = col.strip().lower().replace(" ", "_")
        col_label_lower = col.strip().lower()

        if col_lower in known_keys:
            matched[col] = col_lower
        elif col_label_lower in known_labels:
            matched[col] = known_labels[col_label_lower]
        else:
            # Partial match
            found = False
            for db_key in known_keys:
                if db_key.replace("_", " ") in col_label_lower or col_label_lower in db_key.replace("_", " "):
                    matched[col] = db_key
                    found = True
                    break
            if not found:
                unmatched.append(col)

    return matched, unmatched


def _safe_import_float(val, default=0.0):
    """Convert imported value to float, handling dollar signs, commas, etc."""
    if val is None:
        return default
    try:
        s = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
        if s == "" or s.lower() in ("n/a", "nan", "none", "-"):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def _parse_import_values(df, matched):
    """Extract values from the DataFrame. If multiple rows, sum them."""
    values = {}
    for df_col, db_col in matched.items():
        col_values = df[df_col].apply(_safe_import_float)
        if len(df) == 1:
            values[db_col] = col_values.iloc[0]
        else:
            values[db_col] = col_values.sum()
    return values


def _get_current_value(fin, conn, week_start, dept, db_col):
    """Get the current value for a budget field."""
    food_cost_fields = {"invoice_total", "inventory_start", "inventory_end", "adjustments"}
    if db_col in food_cost_fields:
        food = db.fetch_food_cost(conn, week_start, dept)
        return float(food[db_col]) if food and food.get(db_col) else 0.0
    else:
        return _fval(fin, db_col)


def _apply_import(conn, user, week_start, dept, fin, parsed_values):
    """Apply imported values to weekly_financials and food_cost tables."""
    food_cost_fields = {"invoice_total", "inventory_start", "inventory_end", "adjustments"}
    financial_fields = {"board_revenue", "retail_revenue", "flex_revenue",
                        "catering_revenue", "other_revenue", "total_labor_dollars",
                        "total_labor_hours", "overtime_dollars", "direct_expenses"}

    # Apply financial fields
    fin_overrides = {}
    for key, val in parsed_values.items():
        if key in financial_fields:
            fin_overrides[key] = val

    if fin_overrides:
        fin_data = _build_fin_update(fin, fin_overrides)
        db.upsert_weekly_financials(conn, week_start, dept, fin_data, user["username"])

    # Apply food cost fields
    food_overrides = {}
    for k, v in parsed_values.items():
        if k in food_cost_fields:
            food_overrides[k] = v

    if food_overrides:
        food = db.fetch_food_cost(conn, week_start, dept)
        inv_total = food_overrides.get(
            "invoice_total", float(food["invoice_total"]) if food else 0.0)
        inv_start = food_overrides.get(
            "inventory_start", float(food["inventory_start"]) if food else 0.0)
        inv_end = food_overrides.get(
            "inventory_end", float(food["inventory_end"]) if food else 0.0)
        adj = food_overrides.get(
            "adjustments", float(food["adjustments"]) if food else 0.0)
        notes = food["notes"] if food else ""

        db.upsert_food_cost(conn, week_start, dept, inv_total, inv_start,
                            inv_end, adj, notes, user["username"])

        # Also update COS in weekly_financials
        cos_val = calc_food_cost(inv_total, inv_start, inv_end, adj) or 0.0
        updated_fin = db.fetch_weekly_financials(conn, week_start, dept)
        cos_update = _build_fin_update(updated_fin, {"cos_dollars": cos_val})
        db.upsert_weekly_financials(conn, week_start, dept, cos_update, user["username"])

    st.success("Budget data imported successfully. {} fields updated.".format(
        len(parsed_values)))
    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  CTUIT / Compeat Ops Statement Import
# ═══════════════════════════════════════════════════════════════


def _parse_ctuit_pdf(uploaded_file):
    """Parse a CTUIT / Compeat Ops Statement PDF.

    Returns dict with keys:
      - report_group: str (e.g. 'Alma College-Qdoba')
      - date_range: str (e.g. '2/22/2026 to 2/28/2026')
      - department: str or None (matched department name)
      - sales: dict of {label: dollar_value} from SALES section
      - cos: dict (TOTAL COST OF SALES, individual COS items)
      - labor: dict (TOTAL LABOR, Management, Hourly-Regular, etc.)
      - expenses: dict (TOTAL CONT. EXPENSES items)
      - parsed_values: dict of {db_field: float} ready to import
    Or None on failure.
    """
    import pdfplumber
    import io

    pdf_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    all_text = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)

    if not all_text:
        return None

    full_text = "\n".join(all_text)

    # Extract metadata
    report_group = ""
    date_range = ""
    for line in full_text.split("\n"):
        if "Report Group:" in line:
            report_group = line.split("Report Group:")[-1].strip()
        elif "Date Range:" in line:
            date_range = line.split("Date Range:")[-1].strip()

    # Match department from report group
    department = _match_ctuit_department(report_group)

    # Parse the PERIOD column values from all lines
    parsed = _extract_ctuit_period_values(full_text)

    # Map to our DB fields
    mapped_values, detail_items, budget_values = _map_ctuit_to_budget(parsed)

    return {
        "report_group": report_group,
        "date_range": date_range,
        "department": department,
        "raw_parsed": parsed,
        "parsed_values": mapped_values,
        "detail_items": detail_items,
        "budget_values": budget_values,
    }


def _match_ctuit_department(report_group):
    """Match a CTUIT report group string to one of our departments."""
    rg_lower = report_group.lower()
    for keyword, dept in CTUIT_REPORT_GROUP_MAP.items():
        if keyword in rg_lower:
            return dept
    return None


def _extract_ctuit_period_values(full_text):
    """Extract label -> PERIOD dollar values from CTUIT Ops Statement text.

    The PDF text layout has lines like:
      Retail Sales $1,778 19.1% $0 0.0% ... $1,778 19.1% $3,206 ...
    The PERIOD value is typically the 6th dollar amount on each line (after Week1-5).
    We use a pattern: find all dollar amounts on each line and pick the PERIOD column.
    """
    import re

    results = {}
    lines = full_text.split("\n")

    # Track which section we are in
    current_section = None
    section_markers = {
        "SALES": "sales",
        "COST OF SALES": "cos",
        "LABOR": "labor",
        "TAX & FRINGE": "tax_fringe",
        "CONT. EXPENSES": "expenses",
        "NON-CONT EXPENSE": "non_cont",
        "OTHER FEES": "other_fees",
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check section markers
        for marker, sec_name in section_markers.items():
            if stripped == marker or stripped.startswith(marker + "\n"):
                current_section = sec_name
                break

        # Find all dollar amounts (including negatives) on this line
        # Pattern: optional ( for negative, optional $, digits with commas, optional decimal
        dollar_pattern = re.compile(
            r'[\(\-]?\$?[\d,]+\.?\d*\)?'
        )
        amounts = dollar_pattern.findall(stripped)

        if len(amounts) < 6:
            continue

        # The label is everything before the first dollar/number pattern
        first_match = dollar_pattern.search(stripped)
        if not first_match:
            continue

        label = stripped[:first_match.start()].strip()
        if not label:
            continue

        # In the CTUIT PDF with 5 weeks, the layout is:
        # Week1($+%) Week2($+%) Week3($+%) Week4($+%) Week5($+%) PERIOD($+%) BUDGET($+%) ...
        # Each week/period has a $ value followed by a % value
        # So amounts[0]=W1$, [1]=W1%, [2]=W2$, ... [10]=PERIOD$, [11]=PERIOD%
        # But since some weeks are $0 0.0%, the pattern holds.
        # The PERIOD $ is at index 10 (5 weeks * 2 values each = 10)
        period_idx = 10
        if len(amounts) > period_idx:
            period_val = _ctuit_parse_dollar(amounts[period_idx])
            # BUDGET is at index 12 (PERIOD$ + PERIOD% = 10,11 then BUDGET$ = 12)
            budget_idx = 12
            budget_val = 0.0
            if len(amounts) > budget_idx:
                budget_val = _ctuit_parse_dollar(amounts[budget_idx])
            results[label.lower()] = {
                "label": label,
                "value": period_val,
                "budget": budget_val,
            }

    return results


def _ctuit_parse_dollar(s):
    """Parse a CTUIT dollar string like '$1,778', '($883)', '-$10' to float."""
    if not s:
        return 0.0
    s = s.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    elif s.startswith("-"):
        negative = True
        s = s[1:]
    s = s.replace("$", "").replace(",", "").replace("%", "").strip()
    if not s:
        return 0.0
    try:
        val = float(s)
        return -val if negative else val
    except (ValueError, TypeError):
        return 0.0


def _map_ctuit_to_budget(parsed):
    """Map parsed CTUIT line items to weekly budget DB fields.

    Uses CTUIT_SALES_MAP for sales lines (additive per revenue stream),
    CTUIT_SUMMARY_MAP for summary/total lines.
    Returns (values, detail_items, budget_values).
    """
    values = {}
    budget_values = {}

    # Sales items — multiple lines can map to same revenue field (additive)
    for ctuit_label, db_field in CTUIT_SALES_MAP.items():
        if ctuit_label in parsed:
            amt = parsed[ctuit_label]["value"]
            values[db_field] = values.get(db_field, 0.0) + amt
            bud = parsed[ctuit_label].get("budget", 0.0)
            budget_values[db_field] = budget_values.get(db_field, 0.0) + bud

    # Summary lines — direct mapping
    for ctuit_label, db_field in CTUIT_SUMMARY_MAP.items():
        if ctuit_label in parsed:
            values[db_field] = parsed[ctuit_label]["value"]
            budget_values[db_field] = parsed[ctuit_label].get("budget", 0.0)

    # Labor detail for flash report fields
    for ctuit_label, db_field in CTUIT_LABOR_DETAIL.items():
        if ctuit_label in parsed:
            values[db_field] = parsed[ctuit_label]["value"]
            budget_values[db_field] = parsed[ctuit_label].get("budget", 0.0)

    # Non-controllable expense detail
    for ctuit_label, db_field in CTUIT_NON_CONT_DETAIL.items():
        if ctuit_label in parsed:
            values[db_field] = parsed[ctuit_label]["value"]
            budget_values[db_field] = parsed[ctuit_label].get("budget", 0.0)

    # Detail line items (COS breakdown, expense breakdown, etc.)
    detail_items = []
    for ctuit_label, (section, line_item_key, _display) in CTUIT_DETAIL_MAP.items():
        if ctuit_label in parsed:
            detail_items.append((section, line_item_key, parsed[ctuit_label]["value"]))

    return values, detail_items, budget_values


def _render_ctuit_import(conn, user, week_start, dept, editable, fin, dk=""):
    """Render CTUIT Import sub-section for weekly budget."""
    section_title("", "CTUIT Ops Statement Import")

    if not editable:
        st.caption("Budget must be in Draft or Returned status to import CTUIT data.")
        return

    st.caption(
        "Upload a CTUIT / Compeat Ops Statement PDF, Excel, or CSV. "
        "The system will auto-detect the department and extract PERIOD values "
        "for revenue, cost of sales, labor, and direct expenses."
    )

    uploaded = st.file_uploader(
        "Upload CTUIT Ops Statement",
        type=["pdf", "csv", "xlsx", "xls"],
        key="ctuit_upload_{}_{}".format(week_start, dk),
    )

    if uploaded is None:
        st.info(
            "Supported fields: Retail Sales, Flex Sales, Meal Equivalent (Board), "
            "Catering, Cost of Sales, Total Labor, Overtime, Direct Expenses, "
            "plus all COS and expense detail breakdowns."
        )
        # Show existing detail items if any
        existing_details = db.fetch_ctuit_details(conn, week_start, dept)
        if existing_details:
            _detail_display = {}
            for _lbl, (sec, key, disp) in CTUIT_DETAIL_MAP.items():
                _detail_display[key] = disp
            st.markdown("#### Imported Detail Items")
            for sec_key, sec_label in CTUIT_DETAIL_SECTIONS.items():
                sec_items = [d for d in existing_details if d["section"] == sec_key and d["amount"] != 0]
                if sec_items:
                    with st.expander(sec_label, expanded=False):
                        detail_df = pd.DataFrame([
                            {"Line Item": _detail_display.get(d["line_item"], d["line_item"]),
                             "Amount": fmt_dollar(d["amount"])}
                            for d in sec_items
                        ])
                        st.dataframe(detail_df, use_container_width=True, hide_index=True)
        return

    # Parse based on file type
    name_lower = (uploaded.name or "").lower()
    if name_lower.endswith(".pdf"):
        result = _parse_ctuit_pdf(uploaded)
    else:
        # CSV/Excel — fall back to generic budget import parser
        df, error = _read_import_file(uploaded)
        if error:
            st.error(error)
            return
        if df is None or df.empty:
            st.warning("File is empty or could not be parsed.")
            return
        matched, unmatched = _match_import_columns(df)
        if not matched:
            st.error("No recognized columns found.")
            st.dataframe(df.head(5))
            return
        parsed_values = _parse_import_values(df, matched)
        result = {
            "report_group": "CSV/Excel Import",
            "date_range": "",
            "department": dept,
            "raw_parsed": {},
            "parsed_values": parsed_values,
        }

    if result is None:
        st.error("Could not parse the CTUIT file. Please check the format.")
        return

    # Show detected metadata
    st.markdown("---")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown("**Report Group:** {}".format(result["report_group"] or "N/A"))
    with mc2:
        st.markdown("**Date Range:** {}".format(result["date_range"] or "N/A"))
    with mc3:
        detected_dept = result.get("department")
        if detected_dept:
            match_color = "#16A34A" if detected_dept == dept else "#D97706"
            st.markdown(
                "**Detected Dept:** "
                '<span style="color:{};">{}</span>'.format(match_color, detected_dept),
                unsafe_allow_html=True,
            )
        else:
            st.markdown("**Detected Dept:** _Unknown_")

    # Warn if department mismatch
    if result.get("department") and result["department"] != dept:
        st.warning(
            "This report is for '{}' but you are on the '{}' tab. "
            "Values will be imported into '{}' if you proceed.".format(
                result["department"], dept, dept
            )
        )

    parsed_values = result["parsed_values"]
    detail_items = result.get("detail_items", [])
    if not parsed_values and not detail_items:
        st.error("No importable values found in the file.")
        return

    # Build preview table
    st.markdown("#### Import Preview")
    st.caption("Review values before applying. These will overwrite current budget data.")

    preview_data = []
    field_labels = {
        "retail_revenue": "Retail Revenue",
        "board_revenue": "Board Revenue",
        "flex_revenue": "Flex Revenue",
        "catering_revenue": "Catering Revenue",
        "other_revenue": "Other Revenue",
        "cos_dollars": "Cost of Sales",
        "gross_profit": "Gross Profit",
        "total_labor_dollars": "Total Labor ($)",
        "overtime_dollars": "Overtime ($)",
        "management_wages": "Management Wages",
        "hourly_wages": "Hourly Wages",
        "tax_fringe": "Tax & Fringe",
        "total_payroll": "Total Payroll",
        "after_prime_costs": "After Prime Costs",
        "direct_expenses": "Direct Expenses (Cont.)",
        "pace": "PACE",
        "insurance": "Insurance",
        "profit_fee": "Profit (Fee)",
        "royalties": "Royalties / Nat'l Adv",
        "non_cont_expenses": "Non-Controllable Expenses",
        "net_income": "Net Income",
        "management_fees": "Management Fees",
    }

    ops_only = {"management_wages", "hourly_wages"}
    for db_col, label in field_labels.items():
        if db_col in parsed_values:
            current_val = _fval(fin, db_col) if db_col not in ops_only else 0.0
            new_val = parsed_values[db_col]
            preview_data.append({
                "Field": label,
                "Current": fmt_dollar(current_val),
                "Import Value": fmt_dollar(new_val),
                "Change": fmt_dollar(new_val - current_val),
            })

    if preview_data:
        st.dataframe(
            pd.DataFrame(preview_data),
            use_container_width=True,
            hide_index=True,
        )

    # Detail line items preview (expandable by section)
    if detail_items:
        # Build reverse lookup: line_item_key -> display_label
        _detail_display = {}
        for _lbl, (sec, key, disp) in CTUIT_DETAIL_MAP.items():
            _detail_display[key] = disp

        st.markdown("#### Detail Line Items")
        for sec_key, sec_label in CTUIT_DETAIL_SECTIONS.items():
            sec_items = [(li, amt) for (s, li, amt) in detail_items if s == sec_key and amt != 0]
            if sec_items:
                with st.expander(sec_label, expanded=False):
                    detail_df = pd.DataFrame([
                        {"Line Item": _detail_display.get(li, li), "Amount": fmt_dollar(amt)}
                        for li, amt in sec_items
                    ])
                    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # Apply / Cancel buttons
    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button(
            "Apply CTUIT Import", type="primary",
            key="apply_ctuit_{}".format(dk),
            use_container_width=True,
        ):
            _apply_ctuit_import(conn, user, week_start, dept, fin, parsed_values,
                                detail_items, result.get("budget_values"))
    with ac2:
        if st.button(
            "Cancel", key="cancel_ctuit_{}".format(dk),
            use_container_width=True,
        ):
            st.rerun()


def _apply_ctuit_import(conn, user, week_start, dept, fin, parsed_values,
                        detail_items=None, budget_values=None):
    """Apply CTUIT parsed values to weekly_financials, food_cost, operational, and detail items.
    Also saves CTUIT budget values as flash targets and operational targets."""
    financial_fields = {
        "board_revenue", "retail_revenue", "flex_revenue",
        "catering_revenue", "other_revenue", "cos_dollars",
        "total_labor_dollars", "overtime_dollars", "direct_expenses",
        "gross_profit", "total_payroll", "tax_fringe",
        "after_prime_costs", "pace", "non_cont_expenses",
        "insurance", "profit_fee", "royalties", "net_income", "management_fees",
    }

    fin_overrides = {}
    for key, val in parsed_values.items():
        if key in financial_fields:
            fin_overrides[key] = val

    if fin_overrides:
        fin_data = _build_fin_update(fin, fin_overrides)
        db.upsert_weekly_financials(conn, week_start, dept, fin_data, user["username"])

    count = len(fin_overrides)

    # Also populate food_cost table with COS as invoice_total
    if "cos_dollars" in parsed_values:
        cos_val = parsed_values["cos_dollars"]
        food = db.fetch_food_cost(conn, week_start, dept)
        inv_start = float(food["inventory_start"]) if food else 0.0
        inv_end = float(food["inventory_end"]) if food else 0.0
        adj = float(food["adjustments"]) if food else 0.0
        notes = (food["notes"] or "") if food else ""
        db.upsert_food_cost(conn, week_start, dept, cos_val, inv_start, inv_end, adj,
                            notes, user["username"])
        count += 1

    # Populate weekly_operational with labor detail (management_wages, hourly_wages)
    ops_fields = {"management_wages", "hourly_wages"}
    ops_overrides = {}
    for key, val in parsed_values.items():
        if key in ops_fields:
            ops_overrides[key] = val
    if ops_overrides:
        ops = db.fetch_weekly_operational(conn, week_start, dept)
        ops_data = {}
        if ops:
            ops_data = dict(ops)
        ops_data.update(ops_overrides)
        db.upsert_weekly_operational(conn, week_start, dept, ops_data, user["username"])
        count += len(ops_overrides)

    # Save CTUIT budget values as flash targets and operational targets
    if budget_values:
        # Financial budget -> flash targets
        flash_field_map = {
            "board_revenue": "budget_board_revenue",
            "retail_revenue": "budget_retail_revenue",
            "flex_revenue": "budget_flex_revenue",
            "catering_revenue": "budget_catering_revenue",
            "other_revenue": "budget_other_revenue",
            "cos_dollars": "budget_cos_dollars",
            "total_labor_dollars": "budget_labor_dollars",
            "overtime_dollars": "budget_overtime_dollars",
            "direct_expenses": "budget_direct_expenses",
        }
        target_data = {}
        for src, tgt in flash_field_map.items():
            if src in budget_values and budget_values[src]:
                target_data[tgt] = budget_values[src]
        if target_data:
            db.upsert_weekly_flash_targets(conn, week_start, dept, target_data, user["username"])
            count += len(target_data)

        # Operational budget -> operational targets
        ops_budget_map = {
            "management_wages": "budget_management_wages",
            "hourly_wages": "budget_hourly_wages",
        }
        ops_target_data = {}
        for src, tgt in ops_budget_map.items():
            if src in budget_values and budget_values[src]:
                ops_target_data[tgt] = budget_values[src]
        if ops_target_data:
            db.upsert_weekly_operational_targets(
                conn, week_start, dept, ops_target_data, user["username"])
            count += len(ops_target_data)

    # Save CTUIT detail line items (COS breakdown, expense breakdown, etc.)
    if detail_items:
        db.upsert_ctuit_details(conn, week_start, dept, detail_items, user["username"])
        count += len(detail_items)

    st.success("CTUIT data imported successfully. {} fields updated.".format(count))
    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  Workflow Actions (shown on every sub-section)
# ═══════════════════════════════════════════════════════════════


def _render_workflow_actions(conn, user, week_start, dept, status, editable, budget, fin, dk=""):
    """Render Save Draft / Submit / Approve / Return / Unlock actions."""
    mini_divider()

    if editable:
        # Read current totals from DB for the budget record
        total_revenue = _get_total_revenue(fin)
        labor_dollars = _fval(fin, "total_labor_dollars")
        labor_hours = _fval(fin, "total_labor_hours")

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("Save Draft", use_container_width=True, key="we_save_{}".format(dk)):
                db.upsert_budget(conn, week_start, dept, total_revenue, labor_dollars,
                                 labor_hours, "Draft", user["username"], submit=False)
                st.success("Draft saved.")
                st.rerun()
        with bcol2:
            # premium button styling applied globally via CSS
            if st.button("Submit for Approval", type="primary", use_container_width=True, key="we_submit_{}".format(dk)):
                db.upsert_budget(conn, week_start, dept, total_revenue, labor_dollars,
                                 labor_hours, "Submitted", user["username"], submit=True)
                st.success("Submitted for approval.")
                st.rerun()
            # end premium button
    else:
        if status == "Submitted":
            st.info("Budget is submitted and locked for editing.")
        elif status == "Approved":
            st.info("Budget is approved and locked.")

    # ─── Approver / Admin Actions ───
    ca = can_approve_budget(user, status)
    cr = can_return_budget(user, status)
    cu = can_unlock_budget(user, status)

    if ca or cr or cu:
        mini_divider()
        section_title("", "Actions")
        acol1, acol2, acol3 = st.columns(3)
        with acol1:
            if ca and st.button("Approve", type="primary", use_container_width=True,
                                key="approve_{}".format(dk)):
                db.approve_budget(conn, week_start, dept, user["username"])
                st.success("Budget approved.")
                st.rerun()
        with acol2:
            if cr:
                st.markdown("**Return with comment:**")
                ret_reason = st.selectbox("Reason", REASON_CODES, key="ret_reason_{}".format(dk))
                ret_comment = st.text_input("Comment", key="ret_comment_{}".format(dk))
                if st.button("Return Budget", use_container_width=True,
                             key="ret_budget_{}".format(dk)):
                    if not ret_comment.strip():
                        st.error("A comment is required when returning.")
                    else:
                        db.return_budget(conn, week_start, dept, user["username"])
                        db.add_comment(conn, week_start, dept, "general", ret_reason,
                                       ret_comment, user["username"])
                        st.success("Budget returned.")
                        st.rerun()
        with acol3:
            if cu and st.button("Unlock (Admin)", use_container_width=True,
                                key="unlock_{}".format(dk)):
                db.unlock_budget(conn, week_start, dept, user["username"])
                st.success("Budget unlocked.")
                st.rerun()


# ─── Helper: Variance sections ──────────────────────────────────


def _render_variance_sections(conn, week_start, dept, revenue, labor_dollars,
                              labor_hours, labor_pct, splh):
    section_title("", "Performance Variances")

    # vs Last Year
    ly = db.fetch_ly_actuals(conn, week_start, dept)
    if ly:
        st.markdown("#### vs Last Year")
        ly_lp = calc_labor_pct(ly["labor_dollars"], ly["revenue"])
        ly_sp = calc_splh(ly["revenue"], ly["labor_hours"])

        rev_d, rev_p = variance(revenue, ly["revenue"])
        lab_d, lab_p = variance(labor_dollars, ly["labor_dollars"])
        hrs_d, hrs_p = variance(labor_hours, ly["labor_hours"])
        lp_d = (labor_pct - ly_lp) if labor_pct is not None and ly_lp is not None else None
        sp_d = (splh - ly_sp) if splh is not None and ly_sp is not None else None

        vc = st.columns(5)
        with vc[0]:
            d = "{} ({})".format(fmt_dollar(rev_d), fmt_pct(rev_p)) if rev_d is not None else "N/A"
            st.metric("Revenue Var", fmt_dollar(revenue), d)
        with vc[1]:
            d = "{} ({})".format(fmt_dollar(lab_d), fmt_pct(lab_p)) if lab_d is not None else "N/A"
            st.metric("Labor $ Var", fmt_dollar(labor_dollars), d)
        with vc[2]:
            d = "{} ({})".format(fmt_number(hrs_d), fmt_pct(hrs_p)) if hrs_d is not None else "N/A"
            st.metric("Hours Var", fmt_number(labor_hours), d)
        with vc[3]:
            d = "{} pts".format(fmt_pct(lp_d)) if lp_d is not None else "N/A"
            st.metric("Labor % Diff", fmt_pct(labor_pct), d, delta_color="inverse")
        with vc[4]:
            d = fmt_dollar(sp_d) if sp_d is not None else "N/A"
            st.metric("SPLH Diff", fmt_dollar(splh), d)
    else:
        st.caption("No last-year actuals available.")

    # vs Last Week
    lw = db.fetch_lw_budget(conn, week_start, dept)
    if lw:
        st.markdown("#### vs Last Week")
        lw_lp = calc_labor_pct(lw["labor_dollars"], lw["revenue"])
        lw_sp = calc_splh(lw["revenue"], lw["labor_hours"])

        rev_d, rev_p = variance(revenue, lw["revenue"])
        lab_d, lab_p = variance(labor_dollars, lw["labor_dollars"])
        hrs_d, hrs_p = variance(labor_hours, lw["labor_hours"])
        lp_d = (labor_pct - lw_lp) if labor_pct is not None and lw_lp is not None else None
        sp_d = (splh - lw_sp) if splh is not None and lw_sp is not None else None

        vc = st.columns(5)
        with vc[0]:
            d = "{} ({})".format(fmt_dollar(rev_d), fmt_pct(rev_p)) if rev_d is not None else "N/A"
            st.metric("Revenue Var", fmt_dollar(revenue), d)
        with vc[1]:
            d = "{} ({})".format(fmt_dollar(lab_d), fmt_pct(lab_p)) if lab_d is not None else "N/A"
            st.metric("Labor $ Var", fmt_dollar(labor_dollars), d)
        with vc[2]:
            d = "{} ({})".format(fmt_number(hrs_d), fmt_pct(hrs_p)) if hrs_d is not None else "N/A"
            st.metric("Hours Var", fmt_number(labor_hours), d)
        with vc[3]:
            d = "{} pts".format(fmt_pct(lp_d)) if lp_d is not None else "N/A"
            st.metric("Labor % Diff", fmt_pct(labor_pct), d, delta_color="inverse")
        with vc[4]:
            d = fmt_dollar(sp_d) if sp_d is not None else "N/A"
            st.metric("SPLH Diff", fmt_dollar(splh), d)
    else:
        st.caption("No last-week budget data available.")
