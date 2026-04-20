"""
Page 3: Flash Report View
Professional Flash Report with KPI strip, sectioned HTML tables,
row hierarchy, clean formatting, and export actions.
"""

from datetime import date, timedelta, datetime

import pandas as pd
import streamlit as st

from config import DEPARTMENTS, FLASH_OPERATIONAL_LINES
from calculations import fmt_clean
from auth import get_user_departments
from flash_report import build_financial_panel, build_operational_panel
from styles import page_header, mini_divider, event_reminders, scroll_to_section
import db
import streamlit.components.v1 as components


# ─── Section definitions ───
# Each section: (section_title, [row labels], summary_rows)

_FINANCIAL_SECTIONS = [
    ("Revenue", ["Board", "Retail", "Flex", "Catering", "Other", "Total"],
     {"Total"}),
    ("Cost of Sales", ["COS ($)", "COS (%)", "CPM (Res Only)"],
     {"COS ($)", "COS (%)"}),
    ("Labor", ["Total Labor ($)", "Total Labor (%)", "SPLH", "MPLH (Res Only)"],
     {"Total Labor ($)", "Total Labor (%)", "SPLH"}),
    ("Other Expenses", ["Overtime", "Direct Expenses"],
     {"Overtime"}),
]

_OPERATIONAL_SECTIONS = [
    ("Meal Plans",
     ["Students on Resident Plan", "Students on Commuter Plan",
      "Meals Used Participation %", "Board Plan Billing Days"],
     set()),
    ("Labor Hours",
     ["Board Plan Labor Hours", "Retail Labor Hours",
      "Catering Labor Hours", "Concession Labor Hours",
      "Conference Labor Hours", "OT Hours Included Above"],
     set()),
    ("Labor Costs",
     ["OT Dollars Paid", "Temp Hours Included Above",
      "Temp Dollars Paid", "Management Wages",
      "Hourly Wages", "Average Hourly Wage"],
     set()),
    ("Other",
     ["Fee Account Fee", "Total Inventory"],
     set()),
]


def _var_color(val):
    """Return CSS color string for a variance value."""
    if val is None:
        return "#94A3B8"
    try:
        num = float(val) if not isinstance(val, (int, float)) else val
    except (ValueError, TypeError):
        return "#94A3B8"
    if num > 0:
        return "#16A34A"
    elif num < 0:
        return "#DC2626"
    return "#94A3B8"


# ─── Shared table cell styles ───

_FONT = "font-family:Inter,sans-serif;font-variant-numeric:tabular-nums;"

_HDR_BASE = (
    "padding:8px 14px;font-size:10px;font-weight:600;"
    "text-transform:uppercase;letter-spacing:0.06em;color:#94A3B8;"
    "background:#FAFBFC;border-bottom:1px solid #E5E7EB;"
    "height:34px;{font}"
).format(font=_FONT)

_SECTION_HDR = (
    "padding:8px 14px;font-size:11px;font-weight:600;"
    "color:#475569;background:#F8FAFC;border-top:1px solid #E5E7EB;"
    "border-bottom:1px solid #F1F5F9;height:32px;"
    "letter-spacing:0.03em;text-transform:uppercase;{font}"
).format(font=_FONT)

_CELL_BASE = (
    "padding:7px 14px;font-size:13px;height:34px;"
    "border-bottom:1px solid #F5F5F7;{font}"
).format(font=_FONT)


def _build_sectioned_table(rows, columns, label_key, sections,
                           fmt_type_key="fmt_type"):
    """
    Build HTML table with section headers.

    sections: list of (section_title, [row_labels], summary_row_labels_set)
    columns: list of (data_key, header_label)
    """
    num_cols = 1 + len(columns)

    # ─── Build row lookup ───
    row_map = {}
    for r in rows:
        row_map[r[label_key]] = r

    # ─── Header row ───
    thead = "<tr>"
    thead += '<th style="{s}text-align:left;">{l}</th>'.format(
        s=_HDR_BASE, l=label_key.replace("_", " ").title()
    )
    for i, (dk, dl) in enumerate(columns):
        extra = "border-left:1px solid #E5E7EB;" if i == 3 else ""
        thead += '<th style="{s}text-align:right;{e}">{l}</th>'.format(
            s=_HDR_BASE, e=extra, l=dl
        )
    thead += "</tr>"

    # ─── Body with sections ───
    tbody = ""
    row_idx = 0

    for sec_title, sec_labels, summary_set in sections:
        # Section header row (spans all columns)
        tbody += (
            '<tr><td colspan="{cols}" style="{s}">'
            '{title}</td></tr>'
        ).format(cols=num_cols, s=_SECTION_HDR, title=sec_title)

        for label in sec_labels:
            r = row_map.get(label)
            if r is None:
                continue

            ft = r.get(fmt_type_key, "dollar")
            is_summary = label in summary_set
            row_idx += 1

            # Row style — subtle zebra on non-summary rows
            if is_summary:
                bg = "#F8FAFC"
            elif row_idx % 2 == 0:
                bg = "#FAFBFC"
            else:
                bg = "#FFFFFF"
            fw = "600" if is_summary else "400"
            label_color = "#1E293B" if is_summary else "#475569"
            indent = "padding-left:28px;" if not is_summary else "padding-left:14px;"

            tbody += '<tr style="background:{bg};">'.format(bg=bg)

            # Label cell
            tbody += (
                '<td style="{base}font-weight:{fw};color:{c};{indent}">'
                '{label}</td>'
            ).format(
                base=_CELL_BASE, fw=fw, c=label_color,
                indent=indent, label=label,
            )

            # Data cells
            for i, (dk, dl) in enumerate(columns):
                raw_val = r.get(dk)
                is_variance = i >= 3
                formatted = fmt_clean(raw_val, ft)

                text_color = "#334155"
                cell_fw = fw
                extra = ""

                if is_variance:
                    text_color = _var_color(raw_val)
                    if raw_val is not None and raw_val > 0:
                        formatted = "+{}".format(fmt_clean(raw_val, ft))

                if i == 3:
                    extra = "border-left:1px solid #E5E7EB;"

                tbody += (
                    '<td style="{base}font-weight:{fw};color:{c};'
                    'text-align:right;{extra}">{val}</td>'
                ).format(
                    base=_CELL_BASE, fw=cell_fw, c=text_color,
                    extra=extra, val=formatted,
                )

            tbody += "</tr>"

    html = (
        '<table style="width:100%;border-collapse:collapse;border-spacing:0;'
        'border-radius:8px;overflow:hidden;">'
        '<thead>{thead}</thead>'
        '<tbody>{tbody}</tbody>'
        '</table>'
    ).format(thead=thead, tbody=tbody)

    return html


# ─── Page entry point ───


def page_flash_report(conn, user):
    today = date.today()

    # ─── Week State ───
    if "flash_week" not in st.session_state:
        st.session_state.flash_week = db.get_week_start(today) - timedelta(weeks=1)
    target_fr = st.session_state.flash_week + timedelta(days=6)
    if st.session_state.get("fr_date") != target_fr:
        st.session_state.fr_date = target_fr

    # ─── Week Navigation (compact) ───
    col_prev, col_date, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("Prev Week", key="fr_prev"):
            st.session_state.flash_week -= timedelta(weeks=1)
            st.rerun()
    with col_next:
        if st.button("Next Week", key="fr_next"):
            st.session_state.flash_week += timedelta(weeks=1)
            st.rerun()
    with col_date:
        picked = st.date_input("Week Ending", key="fr_date")
        new_week = db.get_week_start(picked)
        if new_week != st.session_state.flash_week:
            st.session_state.flash_week = new_week
            st.rerun()

    week_start = st.session_state.flash_week.isoformat()
    week_end_date = st.session_state.flash_week + timedelta(days=6)

    # ─── Last import info ───
    last_import_ts = db.fetch_last_import_timestamp(conn)
    if last_import_ts:
        try:
            dt = datetime.fromisoformat(last_import_ts)
            import_display = dt.strftime("%m/%d/%Y %I:%M %p")
            import_status = "Imported"
        except Exception:
            import_display = last_import_ts
            import_status = "Imported"
    else:
        import_display = "No imports yet"
        import_status = "Pending"

    # ─── Page Header with metadata ───
    status_color = "#16A34A" if import_status == "Imported" else "#D97706"
    meta_html = (
        '<span style="font-size:12px;color:#64748B;">Week Ending</span><br>'
        '<span style="font-size:14px;font-weight:600;color:#1E293B;">{we}</span>'
        '&nbsp;&nbsp;&nbsp;'
        '<span style="display:inline-block;padding:3px 10px;border-radius:12px;'
        'font-size:11px;font-weight:600;background:{sc}15;color:{sc};">'
        '{status}</span>'
    ).format(
        we=week_end_date.strftime("%B %d, %Y"),
        sc=status_color,
        status=import_status,
    )
    page_header(
        "Flash Report",
        "Weekly financial and operational performance summary",
        metadata_right=meta_html,
    )
    event_reminders(conn)

    # Flash Report is always Consolidated
    dept = "Consolidated"

    # ─── Build data ───
    fin_rows = build_financial_panel(conn, week_start, dept)
    ops_rows = build_operational_panel(conn, week_start, dept)

    # ─── Import status bar ───
    st.markdown(
        '<div style="background:#F8FAFC;border:1px solid #E5E7EB;border-radius:8px;'
        'padding:8px 16px;margin-bottom:20px;display:flex;justify-content:space-between;'
        'align-items:center;font-family:Inter,sans-serif;">'
        '<span style="font-size:12px;color:#64748B;">'
        'Last Updated: <strong style="color:#1E293B;">{ts}</strong>'
        '</span>'
        '<span style="font-size:12px;color:#64748B;">'
        'Department: <strong style="color:#1E293B;">{dept}</strong>'
        '</span>'
        '</div>'.format(ts=import_display, dept=dept),
        unsafe_allow_html=True,
    )

    # ─── Sub-section dispatch ───
    active_sub = st.session_state.get("current_subsection", "Financial Summary")

    if active_sub == "Financial Summary":
        _render_financial_table(fin_rows)

        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

        # ─── Variance Explanations ───
        explanations = db.fetch_flash_explanations(conn, week_start, dept)
        if explanations:
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                'border-radius:14px;padding:20px;margin-top:20px;">'
                '<div style="font-size:16px;font-weight:600;color:#1E293B;'
                'margin-bottom:12px;font-family:Inter,sans-serif;">'
                'Variance Explanations</div>',
                unsafe_allow_html=True,
            )
            for (line_item, var_type), explanation in explanations.items():
                st.markdown("**{} ({}):** {}".format(line_item, var_type, explanation))
            st.markdown('</div>', unsafe_allow_html=True)

    elif active_sub == "Operational Metrics":
        _render_operational_table(ops_rows)

    elif active_sub == "Budget & Projections":
        _render_budget_projections(conn, user, week_start, dept)

    # ─── Footer Action Bar ───
    _render_footer_actions(conn, fin_rows, ops_rows, dept, week_start)


# ─── Table Renderers ───


def _render_financial_table(fin_rows):
    """Render Financial Summary with section grouping."""
    if not fin_rows:
        st.caption("No financial data available for this week.")
        return

    columns = [
        ("Budget", "Budget"),
        ("Projection", "Projection"),
        ("Actual", "Actual"),
        ("Var to Budget", "Var Budget"),
        ("Var to Projection", "Var Proj"),
    ]

    table_html = _build_sectioned_table(
        fin_rows, columns, "Line Item",
        _FINANCIAL_SECTIONS, "fmt_type",
    )

    full_html = (
        '<html><body style="margin:0;padding:0;font-family:Inter,-apple-system,'
        'BlinkMacSystemFont,sans-serif;">'
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:12px;padding:24px 24px 16px 24px;'
        'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        '<div style="font-size:15px;font-weight:600;color:#1E293B;'
        'margin-bottom:14px;letter-spacing:-0.01em;">Financial Summary</div>'
        '{table}'
        '</div></body></html>'
    ).format(table=table_html)

    # Count rows to estimate height
    row_count = sum(
        1 + len(labels) for _, labels, _ in _FINANCIAL_SECTIONS
    )
    height = 60 + row_count * 36 + 40
    components.html(full_html, height=height, scrolling=False)


def _render_operational_table(ops_rows):
    """Render Operational Metrics with section grouping."""
    if not ops_rows:
        st.caption("No operational data available for this week.")
        return

    columns = [
        ("Budget", "Budget"),
        ("Projected", "Projected"),
        ("Actual", "Actual"),
        ("Var to Budget", "Var Budget"),
        ("Var to Projection", "Var Proj"),
    ]

    table_html = _build_sectioned_table(
        ops_rows, columns, "Metric",
        _OPERATIONAL_SECTIONS, "fmt_type",
    )

    full_html = (
        '<html><body style="margin:0;padding:0;font-family:Inter,-apple-system,'
        'BlinkMacSystemFont,sans-serif;">'
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:12px;padding:24px 24px 16px 24px;'
        'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        '<div style="font-size:15px;font-weight:600;color:#1E293B;'
        'margin-bottom:14px;letter-spacing:-0.01em;">Operational Metrics</div>'
        '{table}'
        '</div></body></html>'
    ).format(table=table_html)

    row_count = sum(
        1 + len(labels) for _, labels, _ in _OPERATIONAL_SECTIONS
    )
    height = 60 + row_count * 36 + 40
    components.html(full_html, height=height, scrolling=False)


# ─── Footer Actions ───


def _render_footer_actions(conn, fin_rows, ops_rows, dept, week_start):
    """Render the bottom action bar with export buttons."""
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:14px;padding:16px 20px;margin-top:24px;'
        'box-shadow:0 2px 8px rgba(0,0,0,0.03);">'
        '<div style="font-size:14px;font-weight:600;color:#1E293B;'
        'margin-bottom:12px;font-family:Inter,sans-serif;">'
        'Actions</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if fin_rows:
            export_rows = []
            for r in fin_rows:
                export_rows.append({
                    "Line Item": r["Line Item"],
                    "Budget": r["Budget"],
                    "Projection": r["Projection"],
                    "Actual": r["Actual"],
                    "Var to Budget": r["Var to Budget"],
                    "Var to Projection": r["Var to Projection"],
                })
            csv_df = pd.DataFrame(export_rows)
            csv_data = csv_df.to_csv(index=False)
            st.download_button(
                "Export Financial CSV", csv_data,
                "flash_financial_{}_{}.csv".format(
                    dept.replace(" ", "_"), week_start),
                "text/csv", key="dl_fin",
            )
        else:
            st.button("Export Financial CSV", disabled=True, key="dl_fin_dis")

    with c2:
        if ops_rows:
            export_rows = []
            for r in ops_rows:
                export_rows.append({
                    "Metric": r["Metric"],
                    "Budget": r["Budget"],
                    "Projected": r["Projected"],
                    "Actual": r["Actual"],
                    "Var to Budget": r.get("Var to Budget"),
                    "Var to Projection": r.get("Var to Projection"),
                })
            csv_df = pd.DataFrame(export_rows)
            csv_data = csv_df.to_csv(index=False)
            st.download_button(
                "Export Operational CSV", csv_data,
                "flash_operational_{}_{}.csv".format(
                    dept.replace(" ", "_"), week_start),
                "text/csv", key="dl_ops",
            )
        else:
            st.button("Export Operational CSV", disabled=True, key="dl_ops_dis")

    with c3:
        if st.button("Notes / Comments", key="fr_notes_btn"):
            st.session_state["fr_show_notes"] = not st.session_state.get("fr_show_notes", False)

    with c4:
        if st.button("Refresh Data", key="fr_refresh"):
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Notes / Comments Panel ──
    if st.session_state.get("fr_show_notes", False):
        st.markdown("---")
        st.subheader("Flash Report Notes / Comments")
        comments = db.fetch_comments(conn, week_start, dept, open_only=False)
        if comments:
            for c in comments:
                status_icon = "🟢" if c.get("is_open") else "⚪"
                st.markdown("{} **{}** — _{}_  \n{}".format(
                    status_icon,
                    c.get("field", "General"),
                    c.get("created_by", "—"),
                    c.get("comment_text", ""),
                ))
        else:
            st.caption("No comments for this week.")

        # Add new comment
        with st.expander("Add a Note", expanded=False):
            note_text = st.text_area("Comment", key="fr_note_text", height=80)
            if st.button("Save Note", key="fr_save_note"):
                if note_text.strip():
                    db.add_comment(conn, week_start, dept, "Flash Report", "note", note_text.strip(), user["username"])
                    st.success("Note saved.")
                    st.rerun()


# ─── Budget & Projections Manual Input ────────────────────


def _render_budget_projections(conn, user, week_start, dept):
    """Manual input form for Budget and Projection numbers."""
    from calculations import fmt_dollar
    from styles import section_title, budget_summary_metric

    section_title("", "Budget & Projections")
    st.caption(
        "Enter budget and projection values for the flash report. "
        "These numbers appear in the Budget and Projected columns."
    )

    # Load existing targets
    targets = db.fetch_weekly_flash_targets(conn, week_start, dept) or {}

    def _tv(key):
        val = targets.get(key, 0.0)
        return float(val) if val else 0.0

    # ── Field definitions: (label, budget_col, projection_col) ──
    _FIELDS = [
        ("Revenue", [
            ("Board Revenue", "budget_board_revenue", "projection_board_revenue"),
            ("Retail Revenue", "budget_retail_revenue", "projection_retail_revenue"),
            ("Flex Revenue", "budget_flex_revenue", "projection_flex_revenue"),
            ("Catering Revenue", "budget_catering_revenue", "projection_catering_revenue"),
            ("Other Revenue", "budget_other_revenue", "projection_other_revenue"),
        ]),
        ("Cost of Sales", [
            ("COS ($)", "budget_cos_dollars", "projection_cos_dollars"),
        ]),
        ("Labor", [
            ("Labor ($)", "budget_labor_dollars", "projection_labor_dollars"),
            ("Labor Hours", "budget_labor_hours", "projection_labor_hours"),
            ("Overtime ($)", "budget_overtime_dollars", "projection_overtime_dollars"),
        ]),
        ("Other Expenses", [
            ("Direct Expenses", "budget_direct_expenses", "projection_direct_expenses"),
        ]),
    ]

    all_values = {}

    for section_name, fields in _FIELDS:
        st.markdown("#### {}".format(section_name))
        for label, b_col, p_col in fields:
            c1, c2 = st.columns(2)
            with c1:
                all_values[b_col] = st.number_input(
                    "{} — Budget".format(label),
                    value=_tv(b_col),
                    min_value=0.0, step=100.0, format="%.2f",
                    key="bp_{}_{}".format(b_col, week_start),
                )
            with c2:
                all_values[p_col] = st.number_input(
                    "{} — Projected".format(label),
                    value=_tv(p_col),
                    min_value=0.0, step=100.0, format="%.2f",
                    key="bp_{}_{}".format(p_col, week_start),
                )
        st.markdown("---")

    # Save button
    if st.button("Save Budget & Projections", type="primary",
                  key="save_bp_{}".format(week_start), use_container_width=True):
        db.upsert_weekly_flash_targets(conn, week_start, dept, all_values, user["username"])
        st.success("Budget & Projection values saved.")
        st.rerun()


def _save_budget_as_flash_targets(conn, user, week_start, dept, budget_values):
    """Map CTUIT budget values to weekly_flash_targets columns and save."""
    budget_field_map = {
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
    for src_field, tgt_field in budget_field_map.items():
        if src_field in budget_values and budget_values[src_field]:
            target_data[tgt_field] = budget_values[src_field]
    if target_data:
        db.upsert_weekly_flash_targets(conn, week_start, dept, target_data, user["username"])


# ─── CTUIT Upload (Flash → Weekly Budget) ────────────────────


def _render_ctuit_flash_upload(conn, user, week_start, dept):
    """Upload CTUIT Consolidated Ops Statement from Flash Report."""
    from views.weekly_entry import (
        _parse_ctuit_pdf, _fval, _apply_ctuit_import,
    )
    from calculations import fmt_dollar
    from styles import section_title

    section_title("", "CTUIT Consolidated Upload")

    st.caption(
        "Upload the CTUIT Consolidated Ops Statement PDF. "
        "Parsed values will be saved into the Weekly Budget as consolidated totals."
    )

    uploaded = st.file_uploader(
        "Upload Consolidated Ops Statement",
        type=["pdf"],
        key="ctuit_flash_consolidated",
    )

    if uploaded is None:
        st.info(
            "Upload the Consolidated Ops Statement PDF to auto-fill the flash report "
            "with revenue, cost of sales, labor, and expense data."
        )
        return

    result = _parse_ctuit_pdf(uploaded)

    if result is None:
        st.error("Could not parse the CTUIT file. Please check the format.")
        return

    # Show metadata
    st.markdown("---")
    mc1, mc2 = st.columns(2)
    with mc1:
        st.markdown("**Report Group:** {}".format(result.get("report_group", "N/A")))
    with mc2:
        st.markdown("**Date Range:** {}".format(result.get("date_range", "N/A")))

    detected_dept = result.get("department")
    if detected_dept and detected_dept != "Consolidated":
        st.warning(
            "This report is for '{}', not a Consolidated report. "
            "Data will still be imported as Consolidated.".format(detected_dept)
        )

    parsed_values = result.get("parsed_values", {})
    detail_items = result.get("detail_items", [])
    if not parsed_values and not detail_items:
        st.error("No importable values found in the file.")
        return

    # Preview
    target_dept = "Consolidated"
    fin = db.fetch_weekly_financials(conn, week_start, target_dept)
    st.markdown("#### Import Preview")
    st.caption("These values will be saved as **Consolidated** totals.")

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

    preview_rows = []
    for db_col, label in field_labels.items():
        if db_col in parsed_values:
            current = _fval(fin, db_col)
            new_val = parsed_values[db_col]
            preview_rows.append({
                "Field": label,
                "Current": fmt_dollar(current),
                "Import Value": fmt_dollar(new_val),
                "Change": fmt_dollar(new_val - current),
            })

    if preview_rows:
        st.dataframe(
            pd.DataFrame(preview_rows),
            use_container_width=True, hide_index=True,
        )

    # Show detail items count
    if detail_items:
        non_zero = [d for d in detail_items if d[2] != 0]
        st.caption("{} detail line items will also be saved (COS breakdown, expenses, etc.)".format(len(non_zero)))

    # Apply / Cancel
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button(
            "Apply Consolidated Data", type="primary",
            key="apply_ctuit_flash_consolidated",
            use_container_width=True,
        ):
            budget_values = result.get("budget_values", {})
            _apply_ctuit_import(conn, user, week_start, target_dept, fin, parsed_values,
                                detail_items, budget_values)

    with bc2:
        if st.button(
            "Cancel",
            key="cancel_ctuit_flash_consolidated",
            use_container_width=True,
        ):
            st.rerun()
