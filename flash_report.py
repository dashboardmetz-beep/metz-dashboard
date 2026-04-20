"""
Flash Report data assembly and rendering.
Builds the two-panel Flash Report (Financial + Operational)
matching the Excel spreadsheet layout.
"""

import pandas as pd
import streamlit as st

from config import FLASH_FINANCIAL_LINES, FLASH_OPERATIONAL_LINES
from calculations import (
    safe_div, sum_revenue_streams, calc_cos_pct, calc_labor_pct,
    calc_splh, calc_mplh, calc_cpm, fmt_dollar, fmt_pct, fmt_number,
    fmt_value, variance_row,
)
import db


def _get_val(d, key, default=0):
    if d and key in d:
        return d[key] if d[key] is not None else default
    return default


def _sum_financials(conn, week_start, departments):
    """Sum financial fields across all departments into a combined dict."""
    _SUM_FIELDS = [
        "board_revenue", "retail_revenue", "flex_revenue",
        "catering_revenue", "other_revenue", "cos_dollars",
        "total_labor_dollars", "total_labor_hours",
        "overtime_dollars", "direct_expenses",
        "gross_profit", "total_payroll", "tax_fringe",
        "after_prime_costs", "pace", "non_cont_expenses",
        "insurance", "profit_fee", "royalties", "net_income", "management_fees",
    ]
    combined = {f: 0.0 for f in _SUM_FIELDS}
    for dept in departments:
        fin = db.fetch_weekly_financials(conn, week_start, dept)
        if fin:
            for f in _SUM_FIELDS:
                combined[f] += float(fin.get(f, 0) or 0)
    return combined


def build_financial_panel(conn, week_start, department):
    """
    Build a list of dicts for the Flash Report financial panel.
    Each dict: {label, budget, projection, actual, var_budget, var_projection, fmt_type}
    When department is 'Consolidated', sums actuals across all departments.
    """
    from config import DEPARTMENTS as _ALL_DEPTS

    # For consolidated view, sum actuals across all departments
    if department == "Consolidated":
        fin = _sum_financials(conn, week_start, _ALL_DEPTS)
    else:
        fin = db.fetch_weekly_financials(conn, week_start, department)

    # Budget/targets: use Consolidated targets if available, otherwise sum per-dept
    tgt = db.fetch_weekly_flash_targets(conn, week_start, "Consolidated")
    if not tgt:
        tgt = db.fetch_weekly_flash_targets(conn, week_start, department)
    explanations = db.fetch_flash_explanations(conn, week_start, department)
    ops = db.fetch_weekly_operational(conn, week_start, department)
    ops_tgt = db.fetch_weekly_operational_targets(conn, week_start, department)
    resident_meals = db.fetch_weekly_meal_plan_total(conn, week_start)

    # Revenue streams
    streams = ["board", "retail", "flex", "catering", "other"]
    rows = []

    # Individual revenue rows
    for s in streams:
        actual = _get_val(fin, "{}_revenue".format(s))
        budget = _get_val(tgt, "budget_{}_revenue".format(s))
        proj = _get_val(tgt, "projection_{}_revenue".format(s))
        vr = variance_row(budget, proj, actual)
        expl_b = explanations.get(("{}_revenue".format(s), "budget"), "")
        expl_p = explanations.get(("{}_revenue".format(s), "projection"), "")
        rows.append({
            "Line Item": s.title(),
            "Budget": budget,
            "Projection": proj,
            "Actual": actual,
            "Var to Budget": vr["var_budget"],
            "Var to Projection": vr["var_projection"],
            "fmt_type": "dollar",
        })

    # Total revenue
    actual_total = sum_revenue_streams(
        _get_val(fin, "board_revenue"), _get_val(fin, "retail_revenue"),
        _get_val(fin, "flex_revenue"), _get_val(fin, "catering_revenue"),
        _get_val(fin, "other_revenue"),
    )
    budget_total = sum_revenue_streams(
        _get_val(tgt, "budget_board_revenue"), _get_val(tgt, "budget_retail_revenue"),
        _get_val(tgt, "budget_flex_revenue"), _get_val(tgt, "budget_catering_revenue"),
        _get_val(tgt, "budget_other_revenue"),
    )
    proj_total = sum_revenue_streams(
        _get_val(tgt, "projection_board_revenue"), _get_val(tgt, "projection_retail_revenue"),
        _get_val(tgt, "projection_flex_revenue"), _get_val(tgt, "projection_catering_revenue"),
        _get_val(tgt, "projection_other_revenue"),
    )
    vr = variance_row(budget_total, proj_total, actual_total)
    rows.append({
        "Line Item": "Total",
        "Budget": budget_total,
        "Projection": proj_total,
        "Actual": actual_total,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    # COS $
    actual_cos = _get_val(fin, "cos_dollars")
    budget_cos = _get_val(tgt, "budget_cos_dollars")
    proj_cos = _get_val(tgt, "projection_cos_dollars")
    vr = variance_row(budget_cos, proj_cos, actual_cos)
    rows.append({
        "Line Item": "COS ($)",
        "Budget": budget_cos,
        "Projection": proj_cos,
        "Actual": actual_cos,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    # COS %
    a_cos_pct = calc_cos_pct(actual_cos, actual_total)
    b_cos_pct = calc_cos_pct(budget_cos, budget_total)
    p_cos_pct = calc_cos_pct(proj_cos, proj_total)
    vr = variance_row(b_cos_pct, p_cos_pct, a_cos_pct)
    rows.append({
        "Line Item": "COS (%)",
        "Budget": b_cos_pct,
        "Projection": p_cos_pct,
        "Actual": a_cos_pct,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "pct",
    })

    # CPM (Res Only)
    # Use weekly meal plan total (resident meals_used) if available,
    # otherwise fall back to students_resident_plan from operational data.
    if resident_meals and resident_meals > 0:
        actual_meals = resident_meals
    else:
        actual_meals = _get_val(ops, "students_resident_plan")
    budget_meals = _get_val(ops_tgt, "budget_students_resident")
    proj_meals = _get_val(ops_tgt, "projection_students_resident")
    a_cpm = calc_cpm(actual_cos, actual_meals)
    b_cpm = calc_cpm(budget_cos, budget_meals)
    p_cpm = calc_cpm(proj_cos, proj_meals)
    vr = variance_row(b_cpm, p_cpm, a_cpm)
    rows.append({
        "Line Item": "CPM (Res Only)",
        "Budget": b_cpm,
        "Projection": p_cpm,
        "Actual": a_cpm,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    # Total Labor $
    actual_lab = _get_val(fin, "total_labor_dollars")
    budget_lab = _get_val(tgt, "budget_labor_dollars")
    proj_lab = _get_val(tgt, "projection_labor_dollars")
    vr = variance_row(budget_lab, proj_lab, actual_lab)
    rows.append({
        "Line Item": "Total Labor ($)",
        "Budget": budget_lab,
        "Projection": proj_lab,
        "Actual": actual_lab,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    # Total Labor %
    a_lab_pct = calc_labor_pct(actual_lab, actual_total)
    b_lab_pct = calc_labor_pct(budget_lab, budget_total)
    p_lab_pct = calc_labor_pct(proj_lab, proj_total)
    vr = variance_row(b_lab_pct, p_lab_pct, a_lab_pct)
    rows.append({
        "Line Item": "Total Labor (%)",
        "Budget": b_lab_pct,
        "Projection": p_lab_pct,
        "Actual": a_lab_pct,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "pct",
    })

    # SPLH & MPLH — use Board & Catering labor hours ONLY
    _BOARD_DEPT = "Board & Catering"
    _HR_FIELDS = ["board_plan_labor_hours", "retail_labor_hours",
                  "catering_labor_hours", "concession_labor_hours",
                  "conference_labor_hours"]
    _HR_BUD = ["budget_board_labor_hours", "budget_retail_labor_hours",
               "budget_catering_labor_hours", "budget_concession_labor_hours",
               "budget_conference_labor_hours"]
    _HR_PRJ = ["projection_board_labor_hours", "projection_retail_labor_hours",
               "projection_catering_labor_hours", "projection_concession_labor_hours",
               "projection_conference_labor_hours"]

    # Get Board & Catering labor hours from financials
    _bc_fin = db.fetch_weekly_financials(conn, week_start, _BOARD_DEPT)
    _bc_tgt = db.fetch_weekly_flash_targets(conn, week_start, _BOARD_DEPT)
    actual_hrs = _get_val(_bc_fin, "total_labor_hours")
    budget_hrs = _get_val(_bc_tgt, "budget_labor_hours")
    proj_hrs = _get_val(_bc_tgt, "projection_labor_hours")

    # Fallback: sum operational hour fields for Board & Catering only
    if not actual_hrs:
        _bc_ops = db.fetch_weekly_operational(conn, week_start, _BOARD_DEPT)
        for _f in _HR_FIELDS:
            actual_hrs += _get_val(_bc_ops, _f)
    if not budget_hrs:
        _bc_tgt2 = db.fetch_weekly_operational_targets(conn, week_start, _BOARD_DEPT)
        for _f in _HR_BUD:
            budget_hrs += _get_val(_bc_tgt2, _f)
    if not proj_hrs:
        _bc_tgt2 = db.fetch_weekly_operational_targets(conn, week_start, _BOARD_DEPT)
        for _f in _HR_PRJ:
            proj_hrs += _get_val(_bc_tgt2, _f)
    a_splh = calc_splh(actual_total, actual_hrs)
    b_splh = calc_splh(budget_total, budget_hrs)
    p_splh = calc_splh(proj_total, proj_hrs)
    vr = variance_row(b_splh, p_splh, a_splh)
    rows.append({
        "Line Item": "SPLH",
        "Budget": b_splh,
        "Projection": p_splh,
        "Actual": a_splh,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    # MPLH (Res Only) — uses ALL locations' labor hours
    from config import DEPARTMENTS as _ALL_DEPTS
    all_actual_hrs = 0
    all_budget_hrs = 0
    all_proj_hrs = 0
    for _d in _ALL_DEPTS:
        _d_fin = db.fetch_weekly_financials(conn, week_start, _d)
        _d_tgt = db.fetch_weekly_flash_targets(conn, week_start, _d)
        all_actual_hrs += _get_val(_d_fin, "total_labor_hours")
        all_budget_hrs += _get_val(_d_tgt, "budget_labor_hours")
        all_proj_hrs += _get_val(_d_tgt, "projection_labor_hours")
    # Fallback: sum operational hour fields across all depts
    if not all_actual_hrs:
        for _d in _ALL_DEPTS:
            _d_ops = db.fetch_weekly_operational(conn, week_start, _d)
            for _f in _HR_FIELDS:
                all_actual_hrs += _get_val(_d_ops, _f)
    if not all_budget_hrs:
        for _d in _ALL_DEPTS:
            _d_tgt2 = db.fetch_weekly_operational_targets(conn, week_start, _d)
            for _f in _HR_BUD:
                all_budget_hrs += _get_val(_d_tgt2, _f)
    if not all_proj_hrs:
        for _d in _ALL_DEPTS:
            _d_tgt2 = db.fetch_weekly_operational_targets(conn, week_start, _d)
            for _f in _HR_PRJ:
                all_proj_hrs += _get_val(_d_tgt2, _f)
    a_mplh = calc_mplh(actual_meals, all_actual_hrs)
    b_mplh = calc_mplh(budget_meals, all_budget_hrs)
    p_mplh = calc_mplh(proj_meals, all_proj_hrs)
    vr = variance_row(b_mplh, p_mplh, a_mplh)
    rows.append({
        "Line Item": "MPLH (Res Only)",
        "Budget": b_mplh,
        "Projection": p_mplh,
        "Actual": a_mplh,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "number",
    })

    # Overtime
    actual_ot = _get_val(fin, "overtime_dollars")
    budget_ot = _get_val(tgt, "budget_overtime_dollars")
    proj_ot = _get_val(tgt, "projection_overtime_dollars")
    vr = variance_row(budget_ot, proj_ot, actual_ot)
    rows.append({
        "Line Item": "Overtime",
        "Budget": budget_ot,
        "Projection": proj_ot,
        "Actual": actual_ot,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    # Direct Expenses
    actual_de = _get_val(fin, "direct_expenses")
    budget_de = _get_val(tgt, "budget_direct_expenses")
    proj_de = _get_val(tgt, "projection_direct_expenses")
    vr = variance_row(budget_de, proj_de, actual_de)
    rows.append({
        "Line Item": "Direct Expenses",
        "Budget": budget_de,
        "Projection": proj_de,
        "Actual": actual_de,
        "Var to Budget": vr["var_budget"],
        "Var to Projection": vr["var_projection"],
        "fmt_type": "dollar",
    })

    return rows


def build_operational_panel(conn, week_start, department):
    """
    Build operational metrics panel rows.
    Most fields are CONSOLIDATED (summed across all departments) so the
    Flash Report always shows the full operational picture.
    Only student/meal-plan metrics stay per-department.
    """
    from config import DEPARTMENTS

    # For per-dept metrics (students/meal plans), use Board & Catering when Consolidated
    per_dept = "Board & Catering" if department == "Consolidated" else department
    ops = db.fetch_weekly_operational(conn, week_start, per_dept)
    ops_tgt = db.fetch_weekly_operational_targets(conn, week_start, per_dept)

    # ── Per-department target mapping (student/meal plan only) ──
    _PER_DEPT_TARGET_MAP = {
        "students_resident_plan": ("budget_students_resident", "projection_students_resident"),
        "students_commuter_plan": ("budget_students_commuter", "projection_students_commuter"),
        "meals_used_participation_pct": ("budget_participation_pct", "projection_participation_pct"),
        "board_plan_billing_days": ("budget_billing_days", "projection_billing_days"),
    }

    # ── Consolidated fields: (actual_key, budget_target_key, proj_target_key) ──
    _CONSOLIDATED_FIELDS = {
        "board_plan_labor_hours":   ("board_plan_labor_hours",   "budget_board_labor_hours",   "projection_board_labor_hours"),
        "retail_labor_hours":       ("retail_labor_hours",       "budget_retail_labor_hours",   "projection_retail_labor_hours"),
        "catering_labor_hours":     ("catering_labor_hours",     "budget_catering_labor_hours", "projection_catering_labor_hours"),
        "concession_labor_hours":   ("concession_labor_hours",   "budget_concession_labor_hours", "projection_concession_labor_hours"),
        "conference_labor_hours":   ("conference_labor_hours",   "budget_conference_labor_hours", "projection_conference_labor_hours"),
        "ot_hours_included_above":  ("ot_hours_included_above",  "budget_ot_hours",            "projection_ot_hours"),
        "ot_dollars_paid":          ("ot_dollars_paid",          "budget_ot_dollars",           "projection_ot_dollars"),
        "temp_hours_included_above":("temp_hours_included_above","budget_temp_hours",           "projection_temp_hours"),
        "temp_dollars_paid":        ("temp_dollars_paid",        "budget_temp_dollars",          "projection_temp_dollars"),
        "management_wages":         ("management_wages",         "budget_management_wages",      "projection_management_wages"),
        "hourly_wages":             ("hourly_wages",             "budget_hourly_wages",          "projection_hourly_wages"),
        "fee_account_fee":          ("fee_account_fee",          "budget_fee_account_fee",       "projection_fee_account_fee"),
        "total_inventory":          ("total_inventory",          "budget_total_inventory",       "projection_total_inventory"),
    }

    # ── Sum consolidated fields across all departments ──
    con_actual = {k: 0 for k in _CONSOLIDATED_FIELDS}
    con_budget = {k: 0 for k in _CONSOLIDATED_FIELDS}
    con_proj = {k: 0 for k in _CONSOLIDATED_FIELDS}

    for dept in DEPARTMENTS:
        d_ops = db.fetch_weekly_operational(conn, week_start, dept)
        d_tgt = db.fetch_weekly_operational_targets(conn, week_start, dept)
        for ckey, (act_col, bud_col, prj_col) in _CONSOLIDATED_FIELDS.items():
            con_actual[ckey] += _get_val(d_ops, act_col)
            con_budget[ckey] += _get_val(d_tgt, bud_col)
            con_proj[ckey] += _get_val(d_tgt, prj_col)

    # ── Pre-compute total labor hours (for Avg Hourly Wage) ──
    _HOUR_KEYS = [
        "board_plan_labor_hours", "retail_labor_hours", "catering_labor_hours",
        "concession_labor_hours", "conference_labor_hours",
    ]
    total_hrs_actual = sum(con_actual[k] for k in _HOUR_KEYS)
    total_hrs_budget = sum(con_budget[k] for k in _HOUR_KEYS)
    total_hrs_proj = sum(con_proj[k] for k in _HOUR_KEYS)

    rows = []

    for key, label, fmt_type in FLASH_OPERATIONAL_LINES:

        # ── Consolidated metrics (summed across all departments) ──
        if key in _CONSOLIDATED_FIELDS:
            actual = con_actual[key]
            budget = con_budget[key]
            projected = con_proj[key]
            vr = variance_row(budget, projected, actual)
            rows.append({
                "Metric": label,
                "Actual": actual,
                "Budget": budget,
                "Projected": projected,
                "Var to Budget": vr["var_budget"],
                "Var to Projection": vr["var_projection"],
                "fmt_type": fmt_type,
            })
            continue

        # ── Average Hourly Wage = consolidated Hourly Wages / Total Hours ──
        if key == "average_hourly_wage":
            actual = safe_div(con_actual["hourly_wages"], total_hrs_actual)
            budget = safe_div(con_budget["hourly_wages"], total_hrs_budget)
            projected = safe_div(con_proj["hourly_wages"], total_hrs_proj)
            vr = variance_row(budget, projected, actual)
            rows.append({
                "Metric": label,
                "Actual": actual,
                "Budget": budget,
                "Projected": projected,
                "Var to Budget": vr["var_budget"],
                "Var to Projection": vr["var_projection"],
                "fmt_type": fmt_type,
            })
            continue

        # ── Per-department metrics ──
        actual = _get_val(ops, key)

        # Default billing days to 7 only when no data exists
        if key == "board_plan_billing_days" and not actual:
            actual = 7

        budget_col, proj_col = _PER_DEPT_TARGET_MAP.get(key, (None, None))
        budget = _get_val(ops_tgt, budget_col) if budget_col else 0
        projected = _get_val(ops_tgt, proj_col) if proj_col else 0

        if key == "board_plan_billing_days":
            if not budget:
                budget = 7
            if not projected:
                projected = 7

        vr = variance_row(budget, projected, actual)
        rows.append({
            "Metric": label,
            "Actual": actual,
            "Budget": budget,
            "Projected": projected,
            "Var to Budget": vr["var_budget"],
            "Var to Projection": vr["var_projection"],
            "fmt_type": fmt_type,
        })

    return rows


def render_flash_table(rows, title, is_financial=True):
    """Render a Flash Report panel as a styled dataframe."""
    st.markdown("#### {}".format(title))

    if not rows:
        st.caption("No data available.")
        return

    if is_financial:
        display_rows = []
        for r in rows:
            ft = r["fmt_type"]
            display_rows.append({
                "Line Item": r["Line Item"],
                "Budget": fmt_value(r["Budget"], ft),
                "Projection": fmt_value(r["Projection"], ft),
                "Actual": fmt_value(r["Actual"], ft),
                "Var to Budget": fmt_value(r["Var to Budget"], ft),
                "Var to Projection": fmt_value(r["Var to Projection"], ft),
            })
    else:
        display_rows = []
        for r in rows:
            ft = r["fmt_type"]
            display_rows.append({
                "Metric": r["Metric"],
                "Budget": fmt_value(r["Budget"], ft),
                "Projected": fmt_value(r["Projected"], ft),
                "Actual": fmt_value(r["Actual"], ft),
                "Var to Budget": fmt_value(r["Var to Budget"], ft),
                "Var to Projection": fmt_value(r["Var to Projection"], ft),
            })

    df = pd.DataFrame(display_rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=600)
