"""
Page 5: Data Import
Dedicated import sections for each data source:
  - US Foods (email or file upload)
  - CTUIT (file upload from website export)
  - Odyssey (file upload from app export)
  - General file upload (daily sales, labor, door counts, etc.)
  - ADP Sync
  - Import History
Admin/Approver only.
"""

from datetime import date, datetime, timedelta
import io

import pandas as pd
import streamlit as st

import re
from config import (
    DEPARTMENTS, IMPORT_TYPES, OPERATION_COST_CATEGORIES,
)
from auth import can_access_imports
from styles import page_header, section_title, mini_divider, app_footer, event_reminders, hero_header
import db


def _read_uploaded_file(uploaded_file):
    """Read CSV, Excel, or PDF into a DataFrame. Returns (df, error_string)."""
    name = (uploaded_file.name or "").lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        elif name.endswith(".pdf"):
            df = _read_pdf(uploaded_file)
        else:
            return None, "Unsupported file type. Please upload CSV, Excel, or PDF."
        # Clean None/NaN column names to avoid join errors
        if df is not None:
            df.columns = [str(c) if c is not None else "Column_{}".format(i)
                          for i, c in enumerate(df.columns)]
        return df, None
    except Exception as e:
        return None, "Error reading file: {}".format(str(e))


def _read_pdf(uploaded_file):
    """Extract tables from a PDF file using pdfplumber. Returns a DataFrame."""
    import pdfplumber

    raw = uploaded_file.read()
    uploaded_file.seek(0)  # reset for potential re-reads

    all_rows = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                # First row as header if it looks like a header
                header = table[0]
                for row in table[1:]:
                    if len(row) == len(header):
                        all_rows.append(dict(zip(header, row)))

    if not all_rows:
        # Fallback: try extracting text and building a simple table
        text_rows = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.strip().split("\n"):
                        parts = line.split()
                        if len(parts) >= 2:
                            text_rows.append({"line": line.strip()})
        if text_rows:
            return pd.DataFrame(text_rows)
        return pd.DataFrame()

    return pd.DataFrame(all_rows)


def _parse_date(value):
    """Parse a date value into a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    # Try common formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return datetime.strptime(s, "%Y-%m-%d").date()


def _safe_float(val, default=0.0):
    """Convert a value to float safely."""
    if val is None:
        return default
    try:
        s = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
        if s == "" or s.lower() in ("n/a", "nan", "none", "-"):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    """Convert a value to int safely."""
    return int(_safe_float(val, float(default)))


def _parse_dollar_amount(s):
    """Parse a dollar amount string like '$16,364' or '($5,155)' into a float."""
    s = s.strip()
    negative = s.startswith("(")
    s = s.replace("(", "").replace(")", "").replace("$", "").replace(",", "")
    try:
        val = float(s)
        return -val if negative else val
    except (ValueError, TypeError):
        return 0.0


def _parse_ctuit_ops_pdf(uploaded_file, week_number=1):
    """
    Parse a CTUIT / Compeat Ops Statement PDF.
    Extracts Actuals (for the selected week) and Budget values.

    Returns dict with keys like:
      'retail_revenue_actual', 'retail_revenue_budget',
      'total_cos_actual', 'total_labor_actual', etc.
    """
    import pdfplumber
    import re

    raw = uploaded_file.read()
    uploaded_file.seek(0)

    all_text = ""
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for pg in pdf.pages:
            text = pg.extract_text()
            if text:
                all_text += text + "\n"

    # Check if this looks like a CTUIT Ops Statement
    if "Ops Statement" not in all_text and "Compeat" not in all_text:
        return None, "This does not appear to be a CTUIT Ops Statement PDF."

    # Regex to find dollar amounts: $16,364 or ($5,155)
    # Use strict comma-formatting to avoid picking up adjacent percentages
    dollar_re = re.compile(r'\(\$\d{1,3}(?:,\d{3})*\)|\$\d{1,3}(?:,\d{3})*')

    # Line items we care about and their keys
    # Order matters: longer/more specific labels first to avoid partial matches
    line_items = [
        ("TOTAL SALES", "total_sales"),
        ("TOTAL COST OF SALES", "total_cos"),
        ("GROSS PROFIT", "gross_profit"),
        ("TOTAL LABOR", "total_labor"),
        ("TOTAL TAX & FRINGE", "total_tax_fringe"),
        ("TOTAL PAYROLL", "total_payroll"),
        ("AFTER PRIME COSTS", "after_prime_costs"),
        ("TOTAL CONT", "total_cont_expenses"),
        ("TOTAL NON-CONT", "total_noncont_expenses"),
        ("PACE", "pace"),
        ("INCOME BEFORE FEES", "income_before_fees"),
        ("NET INCOME", "net_income"),
        ("RETAIL", "retail_revenue"),
        ("CATERING", "catering_revenue"),
        ("BOARD", "board_revenue"),
        ("FLEX", "flex_revenue"),
        ("SUMMER", "summer_revenue"),
        ("PROGRAM", "program_revenue"),
        ("MANAGEMENT", "labor_management"),
        ("HOURLY DRIVERS", "labor_hourly_drivers"),
        ("HOURLY WAREHOUSE", "labor_hourly_warehouse"),
        ("HOURLY", "labor_hourly"),
        ("OVERTIME", "labor_overtime"),
        ("VAC/SICK/HOL", "labor_vac_sick_hol"),
        ("BONUS", "labor_bonus"),
    ]

    result = {}
    lines = all_text.split("\n")

    # Week N actual = dollar amount at index (week_number - 1)
    # Budget = dollar amount at index 6
    # Prior Year = dollar amount at index 8
    actual_idx = week_number - 1
    budget_idx = 6
    prior_year_idx = 8

    matched_labels = set()

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        for label, key in line_items:
            if key in matched_labels:
                continue
            if line_stripped.upper().startswith(label):
                amounts = dollar_re.findall(line_stripped)
                if len(amounts) > actual_idx:
                    result[key + "_actual"] = _parse_dollar_amount(amounts[actual_idx])
                if len(amounts) > budget_idx:
                    result[key + "_budget"] = _parse_dollar_amount(amounts[budget_idx])
                if len(amounts) > prior_year_idx:
                    result[key + "_prior_year"] = _parse_dollar_amount(amounts[prior_year_idx])
                matched_labels.add(key)
                break

    if not result:
        return None, "Could not parse any financial data from this PDF."

    return result, None


# ═══════════════════════════════════════════════════════
# LABOR HOURS IMPORT (ADP "Hours by Labor Account" PDF)
# ═══════════════════════════════════════════════════════


# Default mapping from ADP account suffix to (department, operational field)
# ── Odyssey Plan Membership: Resident vs Commuter ──
# Plan IDs that count as "Resident" (mandatory board plan students)
_RESIDENT_PLAN_IDS = {1, 17, 18, 32}   # 19 Meal, 160 Block, 210 Block, 120 Block Career
# Plan IDs that count as "Commuter" (voluntary block plans)
_COMMUTER_PLAN_IDS = {5, 10, 13, 14, 16, 19}  # Voluntary 25/50/100 blocks


# The account code format is MX8/0{home}/{work}/...
# We group by the WORK department code (second segment).
_LABOR_ACCOUNT_MAP = {
    "4068A": ("Board & Catering", "board_plan_labor_hours"),
    "4068B": ("Retail & Mac's Grill", "retail_labor_hours"),
    "4068C": ("Starbucks", "retail_labor_hours"),
    "4068D": ("Qdoba", "retail_labor_hours"),
}


def _parse_labor_hours_pdf(uploaded_file):
    """
    Parse an ADP 'Hours by Labor Account' PDF.

    Returns (result_dict, error_string).
    result_dict has:
      - 'time_period': str (e.g. '2/22/2026 - 2/28/2026')
      - 'departments': dict mapping work-dept code to {
            'total_hours', 'regular_hours', 'overtime_hours',
            'overtime_wages', 'total_wages'
        }
      - 'pay_code_summary': dict mapping pay code to {'hours', 'wages'}
      - 'grand_total_hours': float
      - 'grand_total_wages': float
    """
    import pdfplumber
    import re

    raw = uploaded_file.read()
    uploaded_file.seek(0)

    all_text = ""
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for pg in pdf.pages:
            text = pg.extract_text()
            if text:
                all_text += text + "\n"

    # Validate it looks like an Hours by Labor Account report
    if "Hours by Labor Account" not in all_text and "Labor Account" not in all_text:
        return None, "This does not appear to be an ADP 'Hours by Labor Account' PDF."

    lines = all_text.split("\n")

    # Extract time period
    time_period = ""
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("Time Period:"):
            time_period = line_s.replace("Time Period:", "").strip()
            break
        # Sometimes the time period is on the same line as other metadata
        tp_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})', line_s)
        if tp_match and not time_period:
            time_period = tp_match.group(0)

    # Parse account sections
    # Account code pattern: MX8/0XXXX/XXXX/...
    account_re = re.compile(r'MX8/0?(\w+)/(\w+)/')
    # Number pattern for hours/wages columns: supports 1,170.42 or 0.00
    number_re = re.compile(r'\$[\d,]+\.\d{2}|[\d,]+\.\d{2}')

    departments = {}  # work_dept_code -> {total_hours, regular_hours, overtime_hours, ...}
    current_work_dept = None
    in_pay_summary = False
    pay_code_summary = {}
    grand_total_hours = 0.0
    grand_total_wages = 0.0

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        # Check for Pay Code Summary section
        if "Pay Code Summary" in line_s:
            in_pay_summary = True
            continue

        # Parse Pay Code Summary rows
        if in_pay_summary:
            if "Grand Totals:" in line_s:
                nums = number_re.findall(line_s)
                if len(nums) >= 4:
                    grand_total_hours = _safe_float(nums[1])
                    grand_total_wages = _safe_float(nums[3])
                in_pay_summary = False
                continue

            # Pay code lines: Overtime $0.00 23.08 0.00 $711.20
            pay_codes = ["Overtime", "Regular2", "Regular", "SICK", "Vacation",
                         "BEREAVEMENT", "HOLIDAY", "Bonus", "Personal",
                         "Jury Duty", "OTHER", "PAYADJ", "Referral",
                         "Prenatal Leave"]
            for pc in pay_codes:
                if line_s.startswith(pc):
                    nums = number_re.findall(line_s)
                    if len(nums) >= 4:
                        pay_code_summary[pc] = {
                            "hours": _safe_float(nums[1]),
                            "wages": _safe_float(nums[3]),
                        }
                    break
            continue

        # Check for account code header
        acct_match = account_re.search(line_s)
        if acct_match:
            current_work_dept = acct_match.group(2)  # work department
            if current_work_dept not in departments:
                departments[current_work_dept] = {
                    "total_hours": 0.0,
                    "regular_hours": 0.0,
                    "regular2_hours": 0.0,
                    "regular2_wages": 0.0,
                    "overtime_hours": 0.0,
                    "overtime_wages": 0.0,
                    "total_wages": 0.0,
                }
            continue

        if current_work_dept is None:
            continue

        # Check for "Totals for MX8:" which ends all account sections
        if line_s.startswith("Totals for"):
            current_work_dept = None
            continue

        # Check for "Grand Totals:" (before Pay Code Summary)
        if line_s.startswith("Grand Totals:") and not in_pay_summary:
            current_work_dept = None
            continue

        # Parse section Totals line
        if line_s.startswith("Totals:"):
            nums = number_re.findall(line_s)
            if len(nums) >= 4:
                section_hours = _safe_float(nums[1])
                section_wages = _safe_float(nums[3])
                departments[current_work_dept]["total_hours"] += section_hours
                departments[current_work_dept]["total_wages"] += section_wages
            continue

        # Parse individual pay code lines within an account section
        # Regular2 = Catering hours (tracked separately)
        if line_s.startswith("Regular2"):
            nums = number_re.findall(line_s)
            if len(nums) >= 4:
                departments[current_work_dept]["regular2_hours"] += _safe_float(nums[1])
                departments[current_work_dept]["regular2_wages"] += _safe_float(nums[3])
        elif line_s.startswith("Overtime"):
            nums = number_re.findall(line_s)
            if len(nums) >= 4:
                departments[current_work_dept]["overtime_hours"] += _safe_float(nums[1])
                departments[current_work_dept]["overtime_wages"] += _safe_float(nums[3])
        elif line_s.startswith("Regular"):
            nums = number_re.findall(line_s)
            if len(nums) >= 4:
                departments[current_work_dept]["regular_hours"] += _safe_float(nums[1])

    if not departments and not pay_code_summary:
        return None, "Could not parse any labor hours data from this PDF."

    result = {
        "time_period": time_period,
        "departments": departments,
        "pay_code_summary": pay_code_summary,
        "grand_total_hours": grand_total_hours,
        "grand_total_wages": grand_total_wages,
    }
    return result, None


def _render_labor_hours_import(conn, user):
    """Render the ADP Labor Hours import section."""
    section_title("", "ADP Labor Hours Import")
    st.info(
        "Import labor hours from an **ADP Hours by Labor Account** PDF.\n\n"
        "**Pay Code Mapping:**\n"
        "- **Regular** = Department labor hours\n"
        "- **Regular2** = Catering labor hours\n"
        "- **Overtime** = OT hours\n\n"
        "**How to get your report:**\n"
        "1. Log into ADP\n"
        "2. Go to **Reports** \u2192 **Hours by Labor Account**\n"
        "3. Set the time period for the week you want to import\n"
        "4. Make sure **All Depts** is selected\n"
        "5. Export or print as **PDF**\n"
        "6. Upload the PDF below"
    )

    # Default to previous completed week
    week_end_date2 = (db.get_week_start(date.today()) - timedelta(weeks=1)) + timedelta(days=6)
    week_end_input = st.date_input(
        "Week Ending (Saturday)",
        value=week_end_date2,
        key="labor_hrs_week",
    )
    week_sunday = db.get_week_start(week_end_input)

    uploaded = st.file_uploader(
        "Upload ADP Hours by Labor Account PDF",
        type=["pdf"],
        key="labor_hrs_upload",
    )

    if uploaded is not None:
        parsed, err = _parse_labor_hours_pdf(uploaded)

        if err:
            st.error(err)
        elif parsed:
            week_end_display = (week_sunday + timedelta(days=6)).strftime("%B %d, %Y")
            st.success("Parsed labor hours report for **Week Ending {}**".format(
                week_end_display
            ))

            if parsed["time_period"]:
                st.caption("Report Time Period: {}".format(parsed["time_period"]))

            # ─── Preview: Hours by Department ───
            mini_divider()
            st.markdown("#### Hours by Department")

            dept_rows = []
            depts_data = parsed["departments"]
            total_regular = 0.0
            total_catering = 0.0
            total_ot = 0.0
            for code in sorted(depts_data.keys()):
                info = depts_data[code]
                mapped = _LABOR_ACCOUNT_MAP.get(code, ("Unknown", ""))
                reg_hrs = info["regular_hours"]
                cat_hrs = info.get("regular2_hours", 0.0)
                ot_hrs = info["overtime_hours"]
                total_regular += reg_hrs
                total_catering += cat_hrs
                total_ot += ot_hrs
                dept_rows.append({
                    "Account Code": code,
                    "Department": mapped[0],
                    "Regular Hrs": "{:,.2f}".format(reg_hrs),
                    "Catering (Regular2)": "{:,.2f}".format(cat_hrs),
                    "OT Hrs": "{:,.2f}".format(ot_hrs),
                })

            # Grand total row
            dept_rows.append({
                "Account Code": "",
                "Department": "**GRAND TOTAL**",
                "Regular Hrs": "{:,.2f}".format(total_regular),
                "Catering (Regular2)": "{:,.2f}".format(total_catering),
                "OT Hrs": "{:,.2f}".format(total_ot),
            })

            st.dataframe(pd.DataFrame(dept_rows), use_container_width=True, hide_index=True)

            # ─── Preview: Pay Code Summary ───
            if parsed["pay_code_summary"]:
                st.markdown("#### Pay Code Summary")
                pc_rows = []
                for pc, vals in parsed["pay_code_summary"].items():
                    pc_rows.append({
                        "Pay Code": pc,
                        "Hours": "{:,.2f}".format(vals["hours"]),
                        "Wages": "${:,.2f}".format(vals["wages"]),
                    })
                st.dataframe(pd.DataFrame(pc_rows), use_container_width=True, hide_index=True)

            # ─── Check for unmapped codes ───
            unmapped = [c for c in depts_data.keys() if c not in _LABOR_ACCOUNT_MAP]
            if unmapped:
                st.warning(
                    "Unknown account codes: **{}**. "
                    "These hours will not be imported. "
                    "Contact support to add them to the mapping.".format(
                        ", ".join(unmapped)
                    )
                )

            # ─── Import Button ───
            mini_divider()
            st.info(
                "This is a **consolidated** report. Hours will be written to "
                "**each department** automatically based on the account codes."
            )
            st.warning(
                "This will update **labor hours** in the Flash Report for "
                "**all departments** \u2192 **Week Ending {}**.".format(week_end_display)
            )

            if st.button("Import Labor Hours", type="primary", key="labor_hrs_import_btn"):
                total_ot_hours = 0.0
                depts_written = []

                for code, info in depts_data.items():
                    mapping = _LABOR_ACCOUNT_MAP.get(code)
                    if not mapping:
                        continue

                    dept_name, field_name = mapping
                    reg_hrs = info["regular_hours"]
                    cat_hrs = info.get("regular2_hours", 0.0)
                    ot_hrs = info["overtime_hours"]
                    total_ot_hours += ot_hrs

                    # Start with ALL labor fields zeroed out so stale data
                    # from previous imports is cleared
                    dept_ops = {
                        "board_plan_labor_hours": 0.0,
                        "retail_labor_hours": 0.0,
                        "catering_labor_hours": 0.0,
                        "concession_labor_hours": 0.0,
                        "conference_labor_hours": 0.0,
                        "ot_hours_included_above": 0.0,
                    }
                    # Write Regular hours to this department's field only
                    dept_ops[field_name] = reg_hrs
                    # Regular2 = catering hours (separate field)
                    dept_ops["catering_labor_hours"] = cat_hrs
                    dept_ops["ot_hours_included_above"] = ot_hrs

                    db.upsert_weekly_operational(
                        conn, week_sunday.isoformat(), dept_name,
                        dept_ops, user["username"]
                    )

                    # Write total_labor_hours to this department's financials
                    # Use parsed total (includes SICK, Vacation, etc.)
                    db.upsert_weekly_financials(
                        conn, week_sunday.isoformat(), dept_name,
                        {"total_labor_hours": info["total_hours"]},
                        user["username"]
                    )

                    depts_written.append(
                        "- **{}**: {:,.2f} regular, {:,.2f} catering, {:,.2f} OT".format(
                            dept_name, reg_hrs, cat_hrs, ot_hrs
                        )
                    )

                # Log the import
                db.add_email_import_log(
                    conn,
                    uploaded.name, "file_upload",
                    datetime.now().isoformat(),
                    "labor_hours_adp", "success",
                    len(depts_written),
                    "Imported ADP Labor Hours for all depts (Week Ending {})".format(
                        week_end_display
                    ),
                    user["username"],
                )

                st.success(
                    "**Imported successfully!**\n\n"
                    "**Hours by department:**\n"
                    "{}\n\n"
                    "**Grand Total:** {:,.2f} hrs ({:,.2f} OT)\n\n"
                    "Go to **Flash Report** to see the data.".format(
                        "\n".join(depts_written),
                        parsed["grand_total_hours"],
                        total_ot_hours,
                    )
                )
                st.balloons()
        else:
            st.warning("Could not parse any data from this PDF.")


# ═══════════════════════════════════════════════════════
# TOTAL INVENTORY
# ═══════════════════════════════════════════════════════


def _parse_inventory_pdf(uploaded_file):
    """
    Parse a Metz Culinary Management Inventory PDF (consolidated report).
    Extracts category totals and grand total from lines like:
      '40010-0000 - Dry Grocery $17,902.20'
    Returns (categories_list, grand_total, inventory_date, error).
    """
    import pdfplumber
    import re

    raw = uploaded_file.read()
    uploaded_file.seek(0)

    all_text = ""
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for pg in pdf.pages:
            text = pg.extract_text()
            if text:
                all_text += text + "\n"

    if not all_text.strip():
        return None, 0, None, "Could not extract text from PDF."

    # Extract inventory date
    inv_date = None
    date_match = re.search(r'Inventory Date:\s*(\d{1,2}/\d{1,2}/\d{4})', all_text)
    if date_match:
        inv_date = date_match.group(1)

    # Extract category totals: lines like "40010-0000 - Dry Grocery $17,902.20"
    # Pattern: account code - category name $amount
    category_re = re.compile(
        r'(\d{5}-\d{4})\s*-\s*(.+?)\s+\$([0-9,]+(?:\.\d{2})?)'
    )

    categories = []
    grand_total = 0.0

    for match in category_re.finditer(all_text):
        code = match.group(1)
        name = match.group(2).strip()
        amount = _safe_float(match.group(3), 0.0)
        categories.append({
            "code": code,
            "name": name,
            "amount": amount,
        })
        grand_total += amount

    # Also check for a "Grand Total" or "Total Inventory" line
    total_re = re.search(
        r'(?:Grand Total|Total Inventory|TOTAL)[:\s]*\$([0-9,]+(?:\.\d{2})?)',
        all_text, re.IGNORECASE
    )
    if total_re:
        parsed_total = _safe_float(total_re.group(1), 0.0)
        if parsed_total > 0:
            grand_total = parsed_total

    if not categories:
        return None, 0, inv_date, "Could not find inventory category totals in this PDF."

    return categories, grand_total, inv_date, None


def _save_consolidated_inventory(conn, week_start_str, total_amount, username):
    """
    Save consolidated inventory: store the full amount on the first department
    and zero on all others. The Flash Report sums across all departments.
    """
    from config import DEPARTMENTS
    for i, dept in enumerate(DEPARTMENTS):
        val = total_amount if i == 0 else 0.0
        db.upsert_weekly_operational(
            conn, week_start_str, dept,
            {"total_inventory": val},
            username,
        )


def _render_total_inventory(conn, user):
    """Render the Total Inventory entry/import section (consolidated)."""
    from config import DEPARTMENTS

    section_title("", "Total Inventory (Consolidated)")
    st.info(
        "Upload the **Metz Inventory Report PDF** or enter the consolidated total manually.\n\n"
        "This is a **single consolidated value** across all departments that appears "
        "on the Flash Report."
    )

    # Default to previous completed week
    week_end_date = (db.get_week_start(date.today()) - timedelta(weeks=1)) + timedelta(days=6)
    week_end_input = st.date_input(
        "Week Ending (Saturday)",
        value=week_end_date,
        key="inv_week",
    )
    week_sunday = db.get_week_start(week_end_input)
    week_start_str = week_sunday.isoformat()
    week_end_display = (week_sunday + timedelta(days=6)).strftime("%B %d, %Y")

    # Show current consolidated total
    current_total = 0.0
    for dept in DEPARTMENTS:
        ops = db.fetch_weekly_operational(conn, week_start_str, dept)
        if ops and ops.get("total_inventory") is not None:
            try:
                current_total += float(ops["total_inventory"])
            except (ValueError, TypeError):
                pass

    st.markdown(
        '<div style="background:#F8FAFC;border:1px solid #E5E7EB;border-radius:8px;'
        'padding:12px 16px;margin:12px 0;font-family:Inter,sans-serif;">'
        '<span style="font-size:12px;color:#64748B;">Current Total Inventory:</span> '
        '<strong style="font-size:16px;color:#1E293B;">${:,.2f}</strong>'
        '&nbsp;&nbsp;'
        '<span style="font-size:12px;color:#94A3B8;">Week Ending {}</span>'
        '</div>'.format(current_total, week_end_display),
        unsafe_allow_html=True,
    )

    mini_divider()

    # ── Option A: Upload Inventory PDF ──
    st.markdown("#### Upload Metz Inventory Report")
    st.caption(
        "Upload the **Metz Culinary Management Inventory** PDF. "
        "The system will extract category totals and calculate the grand total."
    )

    uploaded = st.file_uploader(
        "Upload Inventory Report PDF",
        type=["pdf"],
        key="inv_pdf_upload",
    )

    if uploaded is not None:
        categories, grand_total, inv_date, err = _parse_inventory_pdf(uploaded)

        if err:
            st.error(err)
        elif categories:
            if inv_date:
                st.success("Parsed inventory report — **Inventory Date: {}**".format(inv_date))
            else:
                st.success("Parsed inventory report successfully.")

            # Show category breakdown
            cat_rows = []
            for cat in categories:
                cat_rows.append({
                    "Account": cat["code"],
                    "Category": cat["name"],
                    "Amount": "${:,.2f}".format(cat["amount"]),
                })
            cat_rows.append({
                "Account": "",
                "Category": "**GRAND TOTAL**",
                "Amount": "${:,.2f}".format(grand_total),
            })
            st.dataframe(
                pd.DataFrame(cat_rows),
                use_container_width=True,
                hide_index=True,
            )

            st.warning(
                "This will set the **consolidated Total Inventory** to "
                "**${:,.2f}** for **Week Ending {}**.".format(grand_total, week_end_display)
            )

            if st.button(
                "Import Inventory (${:,.2f})".format(grand_total),
                type="primary",
                key="inv_pdf_import_btn",
            ):
                _save_consolidated_inventory(
                    conn, week_start_str, grand_total, user["username"]
                )

                db.add_email_import_log(
                    conn,
                    uploaded.name, "file_upload",
                    datetime.now().isoformat(),
                    "total_inventory", "success",
                    len(categories),
                    "Inventory PDF import: ${:,.2f} ({} categories, Week Ending {})".format(
                        grand_total, len(categories), week_end_display
                    ),
                    user["username"],
                )
                st.success(
                    "**Inventory imported!**\n\n"
                    "**Grand Total:** ${:,.2f}\n\n"
                    "**Categories:** {}\n\n"
                    "Week Ending: **{}**\n\n"
                    "This value now appears on the **Flash Report** under Total Inventory.".format(
                        grand_total, len(categories), week_end_display
                    )
                )
                st.balloons()

    # ── Option B: Manual Entry ──
    mini_divider()
    st.markdown("#### Manual Entry")
    st.caption("Enter the consolidated total inventory amount directly.")

    manual_val = st.number_input(
        "Total Inventory ($)",
        value=current_total,
        min_value=0.0,
        step=500.0,
        format="%.2f",
        key="inv_manual_total",
    )

    if st.button("Save Inventory", type="primary", key="inv_manual_save_btn", use_container_width=True):
        _save_consolidated_inventory(
            conn, week_start_str, manual_val, user["username"]
        )

        db.add_email_import_log(
            conn,
            "manual_entry", "manual",
            datetime.now().isoformat(),
            "total_inventory", "success",
            1,
            "Manual inventory entry: ${:,.2f} (Week Ending {})".format(
                manual_val, week_end_display
            ),
            user["username"],
        )
        st.success(
            "**Inventory saved!**\n\n"
            "**Total Inventory:** ${:,.2f}\n\n"
            "Week Ending: **{}**".format(manual_val, week_end_display)
        )
        st.rerun()


# ═══════════════════════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════════════════════


def _render_gmail_connection_panel():
    """Premium Gmail connection card with live status + Reconnect button."""
    from gmail_import import get_token_status, force_reauth

    status = get_token_status()
    state = status.get("state")

    if state == "linked":
        badge_cls = "gc-badge ok"
        badge_text = "✓ Connected"
        msg = "Auto-import is live. Token will auto-refresh."
    elif state == "expired":
        badge_cls = "gc-badge warn"
        badge_text = "⚠ Token expired"
        err = status.get("error") or ""
        msg = "Click Reconnect to re-authorize. " + err
    elif state == "no_creds":
        badge_cls = "gc-badge err"
        badge_text = "✗ Missing credentials.json"
        msg = status.get("error") or "Place credentials.json in the project root."
    else:
        badge_cls = "gc-badge warn"
        badge_text = "⚠ Not connected"
        msg = "Click Reconnect to sign in with your Google account."

    expiry = status.get("expiry") or "—"

    c1, c2 = st.columns([5, 2])
    with c1:
        st.markdown(
            '<div class="gc-card">'
            '<div class="gc-row">'
            '<div class="gc-icon">'
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
            'stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round">'
            '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>'
            '<polyline points="22,6 12,13 2,6"/></svg>'
            '</div>'
            '<div class="gc-body">'
            '<div class="gc-title">Gmail Connection '
            '<span class="{bc}">{bt}</span></div>'
            '<div class="gc-msg">{m}</div>'
            '<div class="gc-meta">Token expiry: <code>{e}</code></div>'
            '</div>'
            '</div>'
            '</div>'.format(bc=badge_cls, bt=badge_text, m=msg, e=expiry),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)
        if st.button("🔗  Reconnect Gmail", key="gmail_reconnect",
                     use_container_width=True, type="primary"):
            with st.spinner("Opening browser for Google sign-in…"):
                result = force_reauth()
            if result.get("ok"):
                acct = result.get("account") or "your account"
                st.toast("Gmail reconnected as {}".format(acct), icon="✅")
                st.rerun()
            else:
                st.error("Reconnect failed: {}".format(
                    result.get("error", "unknown error")))


def page_data_import(conn, user):
    hero_header("Data Import Center", "Import data from US Foods, CTUIT, Odyssey, and more")
    event_reminders(conn)

    if not can_access_imports(user):
        st.error("You do not have permission to access this page.")
        return

    _render_gmail_connection_panel()

    active_sub = st.session_state.get("current_subsection", "CTUIT — Weekly Budget")

    if active_sub == "CTUIT — Weekly Budget":
        _render_ctuit_weekly_import(conn, user)
    elif active_sub == "CTUIT — Consolidated":
        _render_ctuit_consolidated_import(conn, user)
    elif active_sub == "Odyssey Reports":
        _render_odyssey_import(conn, user)
    elif active_sub == "Labor Hours":
        _render_labor_hours_import(conn, user)
    elif active_sub == "Total Inventory":
        _render_total_inventory(conn, user)
    elif active_sub == "Projections":
        _render_projections(conn, user)
    elif active_sub == "ADP Sync":
        _render_adp_sync(conn, user)
    elif active_sub == "Import History":
        _render_import_history(conn)



# ═══════════════════════════════════════════════════════
# US FOODS IMPORT
# ═══════════════════════════════════════════════════════


def _render_usfoods_import(conn, user):
    section_title("", "US Foods Invoice Import")
    st.info(
        "Import US Foods invoices to track **food cost** data.\n\n"
        "**Option A:** Upload a file exported from US Foods (CSV, Excel, or PDF)\n\n"
        "**Option B:** Auto-import from Outlook email (requires Microsoft 365 setup)"
    )

    # ── Option A: File Upload ──
    st.markdown("#### Option A: Upload US Foods File")
    st.caption(
        "Download your invoice from US Foods and upload it here. "
        "The app will try to find columns for: **date, department, invoice_total, description**"
    )

    dept = st.selectbox("Department", DEPARTMENTS, key="usf_dept")
    # Default to previous completed week (the one being closed)
    week_end_date = (db.get_week_start(date.today()) - timedelta(weeks=1)) + timedelta(days=6)
    week_start = st.date_input(
        "Week Ending (Saturday)",
        value=week_end_date,
        key="usf_week",
    )
    # Snap to the Sunday that starts this week
    week_sunday = db.get_week_start(week_start)

    uploaded = st.file_uploader(
        "Upload US Foods invoice file",
        type=["csv", "xlsx", "xls", "pdf"],
        key="usf_upload",
    )

    if uploaded is not None:
        df, err = _read_uploaded_file(uploaded)
        if err:
            st.error(err)
        elif df is not None and not df.empty:
            st.markdown("**Preview** ({} rows, {} columns):".format(len(df), len(df.columns)))
            st.dataframe(df.head(20), use_container_width=True, hide_index=True)

            # Try to auto-detect the invoice total column
            total_col = _find_column(df, ["invoice_total", "total", "amount", "inv_total",
                                          "net_amount", "net_total", "extended_price",
                                          "ext_price", "order_total"])
            if total_col:
                st.success("Auto-detected invoice total column: **{}**".format(total_col))
            else:
                total_col = st.selectbox(
                    "Which column has the invoice total?",
                    df.columns.tolist(),
                    key="usf_total_col",
                )

            desc_col = _find_column(df, ["description", "desc", "item", "product",
                                         "item_description", "product_name"])

            if st.button("Import US Foods Data", type="primary", key="usf_import_btn"):
                invoice_sum = _safe_float(df[total_col].apply(_safe_float).sum())
                desc_text = "US Foods import from {}".format(uploaded.name)
                if desc_col and desc_col in df.columns:
                    items = df[desc_col].dropna().unique()
                    if len(items) <= 5:
                        desc_text = "; ".join(str(x) for x in items)

                db.upsert_food_cost(
                    conn,
                    week_sunday.isoformat(),
                    dept,
                    invoice_sum,
                    0, 0, 0,  # inv_start, inv_end, adjustments — keep existing
                    desc_text,
                    user["username"],
                )
                db.add_email_import_log(
                    conn,
                    uploaded.name, "file_upload",
                    datetime.now().isoformat(),
                    "usfoods_invoice", "success",
                    1,
                    "Invoice total: ${:,.2f} for {}".format(invoice_sum, dept),
                    user["username"],
                )
                st.success("Imported! Invoice total **${:,.2f}** saved to food cost for {} (week of {}).".format(
                    invoice_sum, dept, week_sunday.isoformat()
                ))
                st.rerun()
        else:
            st.warning("Could not read any data from the file.")

    # ── Option B: Email Import ──
    mini_divider()
    st.markdown("#### Option B: Auto-Import from Outlook Email")

    import os
    has_config = all([
        os.environ.get("MS_GRAPH_TENANT_ID"),
        os.environ.get("MS_GRAPH_CLIENT_ID"),
        os.environ.get("MS_GRAPH_CLIENT_SECRET"),
        os.environ.get("MS_GRAPH_MAILBOX"),
    ])

    if not has_config:
        st.warning(
            "Microsoft 365 email is not connected yet. To set up:\n"
            "1. Edit `setup_env.sh` with your Azure AD credentials\n"
            "2. Run `source setup_env.sh` before starting the app\n"
            "3. Then click 'Check for US Foods Emails' below"
        )
    else:
        st.caption("Mailbox: {}".format(os.environ.get("MS_GRAPH_MAILBOX", "")))

    if st.button("Check for US Foods Emails", disabled=not has_config, key="usf_email_btn"):
        _check_emails_by_type(conn, user, "usfoods_invoice")


# ═══════════════════════════════════════════════════════
# CTUIT IMPORT
# ═══════════════════════════════════════════════════════


def _ctuit_preview_and_import(conn, user, parsed, dept, week_sunday, week_choice, btn_key, target_label):
    """Shared preview + import logic for CTUIT Ops Statement."""
    week_num = int(week_choice.split(" ")[1])

    st.success("Parsed {} for **{}** (Week Ending {})".format(
        week_choice, dept, (week_sunday + timedelta(days=6)).strftime("%B %d, %Y")
    ))

    # ─── Preview: Sales ───
    mini_divider()
    st.markdown("#### Sales (Revenue)")
    sales_items = [
        ("Board", "board_revenue"),
        ("Retail", "retail_revenue"),
        ("Flex", "flex_revenue"),
        ("Catering", "catering_revenue"),
        ("Program/Other", "program_revenue"),
        ("**Total Sales**", "total_sales"),
    ]
    sales_rows = []
    for label, key in sales_items:
        sales_rows.append({
            "Line Item": label,
            "Actual": "${:,.0f}".format(parsed.get(key + "_actual", 0)),
            "Budget": "${:,.0f}".format(parsed.get(key + "_budget", 0)),
        })
    st.dataframe(pd.DataFrame(sales_rows), use_container_width=True, hide_index=True)

    # ─── Preview: Cost of Sales ───
    st.markdown("#### Cost of Sales")
    cos_rows = [{
        "Line Item": "**Total Cost of Sales**",
        "Actual": "${:,.0f}".format(parsed.get("total_cos_actual", 0)),
        "Budget": "${:,.0f}".format(parsed.get("total_cos_budget", 0)),
    }]
    st.dataframe(pd.DataFrame(cos_rows), use_container_width=True, hide_index=True)

    # ─── Preview: Labor ───
    st.markdown("#### Labor & Payroll")
    labor_items = [
        ("Management", "labor_management"),
        ("Hourly", "labor_hourly"),
        ("Overtime", "labor_overtime"),
        ("Vac/Sick/Hol", "labor_vac_sick_hol"),
        ("Bonus", "labor_bonus"),
        ("**Total Labor**", "total_labor"),
        ("Tax & Fringe", "total_tax_fringe"),
        ("**Total Payroll**", "total_payroll"),
    ]
    labor_rows = []
    for label, key in labor_items:
        labor_rows.append({
            "Line Item": label,
            "Actual": "${:,.0f}".format(parsed.get(key + "_actual", 0)),
            "Budget": "${:,.0f}".format(parsed.get(key + "_budget", 0)),
        })
    st.dataframe(pd.DataFrame(labor_rows), use_container_width=True, hide_index=True)

    # ─── Preview: Expenses ───
    st.markdown("#### Expenses & Bottom Line")
    exp_items = [
        ("Controllable Expenses", "total_cont_expenses"),
        ("Non-Controllable Expenses", "total_noncont_expenses"),
        ("**PACE**", "pace"),
        ("**Net Income**", "net_income"),
    ]
    exp_rows = []
    for label, key in exp_items:
        exp_rows.append({
            "Line Item": label,
            "Actual": "${:,.0f}".format(parsed.get(key + "_actual", 0)),
            "Budget": "${:,.0f}".format(parsed.get(key + "_budget", 0)),
        })
    st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)

    # ─── Import Button ───
    mini_divider()
    st.warning(
        "This will import **Actuals + Budget** into **{}** for "
        "**{}** → **Week Ending {}**.".format(
            target_label, dept, (week_sunday + timedelta(days=6)).strftime("%B %d, %Y")
        )
    )

    if st.button("Import into {}".format(target_label), type="primary", key=btn_key):
        other_rev = parsed.get("program_revenue_actual", 0) + parsed.get("summer_revenue_actual", 0)
        fin_data = {
            "board_revenue": parsed.get("board_revenue_actual", 0),
            "retail_revenue": parsed.get("retail_revenue_actual", 0),
            "flex_revenue": parsed.get("flex_revenue_actual", 0),
            "catering_revenue": parsed.get("catering_revenue_actual", 0),
            "other_revenue": other_rev,
            "cos_dollars": parsed.get("total_cos_actual", 0),
            "total_labor_dollars": parsed.get("total_labor_actual", 0),
            "overtime_dollars": parsed.get("labor_overtime_actual", 0),
            "direct_expenses": (parsed.get("total_cont_expenses_actual", 0)
                                + parsed.get("total_noncont_expenses_actual", 0)),
        }
        db.upsert_weekly_financials(
            conn, week_sunday.isoformat(), dept, fin_data, user["username"]
        )

        other_rev_budget = parsed.get("program_revenue_budget", 0) + parsed.get("summer_revenue_budget", 0)
        targets_data = {
            "budget_board_revenue": parsed.get("board_revenue_budget", 0),
            "budget_retail_revenue": parsed.get("retail_revenue_budget", 0),
            "budget_flex_revenue": parsed.get("flex_revenue_budget", 0),
            "budget_catering_revenue": parsed.get("catering_revenue_budget", 0),
            "budget_other_revenue": other_rev_budget,
            "budget_cos_dollars": parsed.get("total_cos_budget", 0),
            "budget_labor_dollars": parsed.get("total_labor_budget", 0),
            "budget_overtime_dollars": parsed.get("labor_overtime_budget", 0),
            "budget_direct_expenses": (parsed.get("total_cont_expenses_budget", 0)
                                       + parsed.get("total_noncont_expenses_budget", 0)),
        }
        db.upsert_weekly_flash_targets(
            conn, week_sunday.isoformat(), dept, targets_data, user["username"]
        )

        ops_data = {
            "management_wages": parsed.get("labor_management_actual", 0),
            "hourly_wages": parsed.get("labor_hourly_actual", 0),
            "ot_dollars_paid": parsed.get("labor_overtime_actual", 0),
        }
        db.upsert_weekly_operational(
            conn, week_sunday.isoformat(), dept, ops_data, user["username"]
        )

        ops_targets_data = {
            "budget_management_wages": parsed.get("labor_management_budget", 0),
            "budget_hourly_wages": parsed.get("labor_hourly_budget", 0),
            "budget_ot_dollars": parsed.get("labor_overtime_budget", 0),
        }
        db.upsert_weekly_operational_targets(
            conn, week_sunday.isoformat(), dept, ops_targets_data, user["username"]
        )

        db.add_email_import_log(
            conn,
            "ctuit_import", "file_upload",
            datetime.now().isoformat(),
            "ctuit_ops_statement", "success",
            len(fin_data) + len(targets_data),
            "Imported Ops Statement {} for {} (Week Ending {})".format(
                week_choice, dept,
                (week_sunday + timedelta(days=6)).strftime("%Y-%m-%d")
            ),
            user["username"],
        )

        st.success(
            "**Imported successfully!**\n\n"
            "**Financial:** Actuals + Budget (revenue, COS, labor, expenses)\n\n"
            "**Operational:** Management Wages, Hourly Wages, OT Dollars (actuals + budget)\n\n"
            "Go to **{}** to see the data.".format(target_label)
        )


# ─── CTUIT Weekly Budget (per department) ───

def _render_ctuit_weekly_import(conn, user):
    section_title("", "CTUIT — Weekly Budget Import (Per Department)")
    st.info(
        "Upload **one PDF per department** from CTUIT / Compeat Ops Statement.\n\n"
        "Each report is imported into the **Weekly Budget** for that department.\n\n"
        "**Departments:** Board & Catering, Starbucks, Qdoba, Retail & Mac's Grill"
    )

    week_choice = st.selectbox(
        "Which week to import?",
        ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
        key="ctuit_wk_week_num",
    )
    week_num = int(week_choice.split(" ")[1])

    week_end_date2 = (db.get_week_start(date.today()) - timedelta(weeks=1)) + timedelta(days=6)
    week_end_input = st.date_input(
        "Week Ending (Saturday)",
        value=week_end_date2,
        key="ctuit_wk_week",
    )
    week_sunday = db.get_week_start(week_end_input)

    st.markdown("---")

    for dept in DEPARTMENTS:
        st.markdown("### {}".format(dept))
        uploaded = st.file_uploader(
            "Upload {} Ops Statement PDF".format(dept),
            type=["pdf"],
            key="ctuit_wk_upload_{}".format(dept.replace(" ", "_").replace("&", "").replace("'", "")),
        )

        if uploaded is not None:
            parsed, err = _parse_ctuit_ops_pdf(uploaded, week_number=week_num)
            if err:
                st.error(err)
            elif parsed:
                _ctuit_preview_and_import(
                    conn, user, parsed, dept, week_sunday, week_choice,
                    btn_key="ctuit_wk_btn_{}".format(dept.replace(" ", "_")),
                    target_label="Weekly Budget",
                )
        else:
            st.caption("No file uploaded for {}.".format(dept))

        mini_divider()


# ─── CTUIT Consolidated (for Flash Report) ───

def _render_ctuit_consolidated_import(conn, user):
    section_title("", "CTUIT — Consolidated Import (Flash Report)")
    st.info(
        "Upload the **Consolidated** CTUIT / Compeat Ops Statement PDF.\n\n"
        "This imports the combined data across all departments into the **Flash Report**."
    )

    week_choice = st.selectbox(
        "Which week to import?",
        ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
        key="ctuit_cons_week_num",
    )
    week_num = int(week_choice.split(" ")[1])

    week_end_date2 = (db.get_week_start(date.today()) - timedelta(weeks=1)) + timedelta(days=6)
    week_end_input = st.date_input(
        "Week Ending (Saturday)",
        value=week_end_date2,
        key="ctuit_cons_week",
    )
    week_sunday = db.get_week_start(week_end_input)

    uploaded = st.file_uploader(
        "Upload Consolidated Ops Statement PDF",
        type=["pdf"],
        key="ctuit_cons_upload",
    )

    if uploaded is not None:
        parsed, err = _parse_ctuit_ops_pdf(uploaded, week_number=week_num)
        if err:
            st.error(err)
        elif parsed:
            _ctuit_preview_and_import(
                conn, user, parsed, "Consolidated", week_sunday, week_choice,
                btn_key="ctuit_cons_btn",
                target_label="Flash Report",
            )


# ═══════════════════════════════════════════════════════
# ODYSSEY IMPORT  (Plan Membership + Transaction Counts)
# ═══════════════════════════════════════════════════════


def _parse_plan_membership_pdf(uploaded_file):
    """
    Parse an Odyssey 'Plan Membership Summary' PDF.
    Returns (result_dict, error_string).
    result_dict has:
      - 'as_of': str (date stamp)
      - 'plans': list of {plan_id, plan_name, count}
      - 'resident_count': int
      - 'commuter_count': int
      - 'resident_plans': list of (name, count)
      - 'commuter_plans': list of (name, count)
      - 'total_members': int
    """
    import pdfplumber
    import re

    raw = uploaded_file.read()
    uploaded_file.seek(0)

    all_text = ""
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for pg in pdf.pages:
            text = pg.extract_text()
            if text:
                all_text += text + "\n"

    if "Plan Membership Summary" not in all_text:
        return None, "This does not appear to be a Plan Membership Summary PDF."

    lines = all_text.split("\n")

    # Extract as-of date
    as_of = ""
    for line in lines:
        if "As of" in line:
            m = re.search(r'As of\s+(\d{2}/\d{2}/\d{4})', line)
            if m:
                as_of = m.group(1)
            break

    # Parse plan rows: Plan ID, Plan Name, Membership Count, Percentage
    # The PDF text has plan ID and name on the left, count and pct on the right
    plans = []
    number_re = re.compile(r'[\d,]+')

    for line in lines:
        line_s = line.strip()
        if not line_s or "Plan ID" in line_s or "Count Totals" in line_s:
            continue
        if "Plan Membership" in line_s or "CBORD" in line_s or "Metz Campus" in line_s:
            continue

        # Try to match: starts with a number (plan ID), has a name, then count and pct
        m = re.match(r'^\s*(\d+)\s+(.+?)\s+([\d,]+)\s+([\d.]+)\s*$', line_s)
        if m:
            plan_id = int(m.group(1))
            plan_name = m.group(2).strip()
            count = int(m.group(3).replace(",", ""))
            plans.append({
                "plan_id": plan_id,
                "plan_name": plan_name,
                "count": count,
            })

    if not plans:
        return None, "Could not parse any plan data from this PDF."

    # Categorize
    resident_count = 0
    commuter_count = 0
    resident_plans = []
    commuter_plans = []

    for p in plans:
        pid = p["plan_id"]
        if pid in _RESIDENT_PLAN_IDS:
            resident_count += p["count"]
            resident_plans.append((p["plan_name"], p["count"]))
        elif pid in _COMMUTER_PLAN_IDS:
            commuter_count += p["count"]
            commuter_plans.append((p["plan_name"], p["count"]))

    total_members = sum(p["count"] for p in plans)

    return {
        "as_of": as_of,
        "plans": plans,
        "resident_count": resident_count,
        "commuter_count": commuter_count,
        "resident_plans": resident_plans,
        "commuter_plans": commuter_plans,
        "total_members": total_members,
    }, None


def _parse_transaction_counts_pdf(uploaded_file):
    """
    Parse an Odyssey 'Weekly Transaction Counts Board' PDF.
    Returns (result_dict, error_string).
    result_dict has:
      - 'time_period': str
      - 'units': dict mapping unit_name to {bfast, cbfast, brunch, lunch, dinner, late, total}
      - 'grand_total': int
    """
    import pdfplumber
    import re

    raw = uploaded_file.read()
    uploaded_file.seek(0)

    all_text = ""
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for pg in pdf.pages:
            text = pg.extract_text()
            if text:
                all_text += text + "\n"

    if "Transaction Counts" not in all_text:
        return None, "This does not appear to be a Transaction Counts PDF."

    lines = all_text.split("\n")

    # Extract time period
    time_period = ""
    for line in lines:
        m = re.search(
            r'(\d{2}/\d{2}/\d{4})\s+at\s+[\d:]+\s*[AP]M\s+through\s+'
            r'(\d{2}/\d{2}/\d{4})\s+at\s+[\d:]+\s*[AP]M',
            line
        )
        if m:
            time_period = "{} - {}".format(m.group(1), m.group(2))
            break

    # Parse unit sections and their Period Totals
    # The PDF has two lines per data row:
    #   Line A: whole numbers (actual counts)
    #   Line B: decimal equivalents (with .00)
    # Period Totals has the same pattern:
    #   Line A: "1,282 0 312 2,132 2,442 0 6,168" (whole nums, previous line)
    #   Line B: "Period Totals: 1,283.00 0.00 314.00 ..." (decimals)
    # We use the line BEFORE "Period Totals:" for the whole number counts.
    units = {}
    current_unit = None
    prev_line = ""
    number_re = re.compile(r'[\d,]+')

    for line in lines:
        line_s = line.strip()

        # Detect unit header: "Unit ID: 1, HAMILTON COMMONS UNIT"
        unit_match = re.match(r'Unit ID:\s*\d+,\s*(.+)', line_s)
        if unit_match:
            current_unit = unit_match.group(1).strip()
            units[current_unit] = {
                "bfast": 0, "cbfast": 0, "brunch": 0,
                "lunch": 0, "dinner": 0, "late": 0, "total": 0,
            }
            prev_line = ""
            continue

        # Detect Period Totals — use the PREVIOUS line for whole numbers
        if current_unit and "Period Totals:" in line_s:
            # prev_line has the whole number counts: "1,282 0 312 2,132 2,442 0 6,168"
            nums = number_re.findall(prev_line)
            if len(nums) >= 7:
                units[current_unit]["bfast"] = int(nums[0].replace(",", ""))
                units[current_unit]["cbfast"] = int(nums[1].replace(",", ""))
                units[current_unit]["brunch"] = int(nums[2].replace(",", ""))
                units[current_unit]["lunch"] = int(nums[3].replace(",", ""))
                units[current_unit]["dinner"] = int(nums[4].replace(",", ""))
                units[current_unit]["late"] = int(nums[5].replace(",", ""))
                units[current_unit]["total"] = int(nums[6].replace(",", ""))
            current_unit = None
            continue

        prev_line = line_s

    if not units:
        return None, "Could not parse any transaction data from this PDF."

    grand_total = sum(u["total"] for u in units.values())

    return {
        "time_period": time_period,
        "units": units,
        "grand_total": grand_total,
    }, None


def _render_odyssey_import(conn, user):
    section_title("", "Odyssey Reports Import")
    st.info(
        "Import data from **CBORD Odyssey PCS** PDF reports.\n\n"
        "**Supported reports:**\n"
        "- **Plan Membership Summary** \u2192 Students on Resident/Commuter Plans\n"
        "- **Weekly Transaction Counts Board** \u2192 Meals Used (for Participation %)\n\n"
        "Upload one or both reports below \u2014 the app will auto-detect each report type."
    )

    # Default to previous completed week
    week_end_date3 = (db.get_week_start(date.today()) - timedelta(weeks=1)) + timedelta(days=6)
    week_end_ody = st.date_input(
        "Week Ending (Saturday)",
        value=week_end_date3,
        key="ody_week",
    )
    week_sunday_ody = db.get_week_start(week_end_ody)

    uploaded_files = st.file_uploader(
        "Upload Odyssey PDF Reports",
        type=["pdf"],
        key="odyssey_upload",
        accept_multiple_files=True,
    )

    if uploaded_files:
        import pdfplumber

        # Sort so Plan Membership is processed first (needed for participation %)
        membership_files = []
        transaction_files = []
        unknown_files = []

        for uf in uploaded_files:
            raw_bytes = uf.read()
            uf.seek(0)
            raw_text = ""
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                for pg in pdf.pages:
                    t = pg.extract_text()
                    if t:
                        raw_text += t + "\n"

            if "Plan Membership Summary" in raw_text:
                membership_files.append(uf)
            elif "Transaction Counts" in raw_text:
                transaction_files.append(uf)
            else:
                unknown_files.append(uf)

        # Process membership first, then transactions
        for uf in membership_files:
            st.markdown("---")
            st.markdown("##### {}".format(uf.name))
            _handle_plan_membership(conn, user, uf, week_sunday_ody, week_end_ody)

        for uf in transaction_files:
            st.markdown("---")
            st.markdown("##### {}".format(uf.name))
            _handle_transaction_counts(conn, user, uf, week_sunday_ody, week_end_ody)

        for uf in unknown_files:
            st.markdown("---")
            st.error(
                "Could not recognize **{}**. "
                "Please upload a **Plan Membership Summary** or "
                "**Weekly Transaction Counts Board** report.".format(uf.name)
            )


def _handle_plan_membership(conn, user, uploaded, week_sunday, week_end):
    """Handle Plan Membership Summary PDF."""
    parsed, err = _parse_plan_membership_pdf(uploaded)
    if err:
        st.error(err)
        return

    week_end_display = (week_sunday + timedelta(days=6)).strftime("%B %d, %Y")
    st.success("Detected: **Plan Membership Summary**")
    if parsed["as_of"]:
        st.caption("Report as of: {}".format(parsed["as_of"]))

    # ─── Resident Plans ───
    mini_divider()
    st.markdown("#### Resident Plan Students: **{:,}**".format(parsed["resident_count"]))
    if parsed["resident_plans"]:
        res_rows = []
        for name, cnt in parsed["resident_plans"]:
            res_rows.append({"Plan": name, "Students": "{:,}".format(cnt)})
        st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)

    # ─── Commuter Plans ───
    st.markdown("#### Commuter Plan Students: **{:,}**".format(parsed["commuter_count"]))
    if parsed["commuter_plans"]:
        com_rows = []
        for name, cnt in parsed["commuter_plans"]:
            com_rows.append({"Plan": name, "Students": "{:,}".format(cnt)})
        st.dataframe(pd.DataFrame(com_rows), use_container_width=True, hide_index=True)

    st.caption("Total across all plans: {:,}".format(parsed["total_members"]))

    # ─── Import ───
    mini_divider()
    st.warning(
        "This will update **Students on Resident Plan** and "
        "**Students on Commuter Plan** for **Board & Catering** "
        "\u2192 **Week Ending {}**.".format(week_end_display)
    )

    if st.button("Import Plan Membership", type="primary", key="ody_member_btn"):
        ops_data = {
            "students_resident_plan": parsed["resident_count"],
            "students_commuter_plan": parsed["commuter_count"],
            "board_plan_billing_days": parsed.get("billing_days", 7),
        }
        db.upsert_weekly_operational(
            conn, week_sunday.isoformat(), "Board & Catering",
            ops_data, user["username"]
        )

        db.add_email_import_log(
            conn,
            uploaded.name, "file_upload",
            datetime.now().isoformat(),
            "odyssey", "success",
            2,
            "Plan Membership: {} resident, {} commuter (Week Ending {})".format(
                parsed["resident_count"], parsed["commuter_count"],
                week_end_display
            ),
            user["username"],
        )

        st.success(
            "**Imported!**\n\n"
            "- Students on Resident Plan: **{:,}**\n"
            "- Students on Commuter Plan: **{:,}**".format(
                parsed["resident_count"], parsed["commuter_count"]
            )
        )
        st.balloons()


def _handle_transaction_counts(conn, user, uploaded, week_sunday, week_end):
    """Handle Weekly Transaction Counts Board PDF."""
    parsed, err = _parse_transaction_counts_pdf(uploaded)
    if err:
        st.error(err)
        return

    week_end_display = (week_sunday + timedelta(days=6)).strftime("%B %d, %Y")
    st.success("Detected: **Weekly Transaction Counts Board**")
    if parsed["time_period"]:
        st.caption("Report Period: {}".format(parsed["time_period"]))

    # ─── Preview by unit ───
    mini_divider()
    for unit_name, data in parsed["units"].items():
        st.markdown("#### {}".format(unit_name))
        row = {
            "Breakfast": "{:,}".format(data["bfast"]),
            "Brunch": "{:,}".format(data["brunch"]),
            "Lunch": "{:,}".format(data["lunch"]),
            "Dinner": "{:,}".format(data["dinner"]),
            "Total": "{:,}".format(data["total"]),
        }
        st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)

    st.markdown("**Grand Total Transactions: {:,}**".format(parsed["grand_total"]))

    # ─── Import ───
    mini_divider()
    st.warning(
        "This will update **Meals Used** for **Board & Catering** "
        "\u2192 **Week Ending {}**.".format(week_end_display)
    )

    if st.button("Import Transaction Counts", type="primary", key="ody_txn_btn"):
        # Get current resident count to calculate participation %
        existing_ops = db.fetch_weekly_operational(
            conn, week_sunday.isoformat(), "Board & Catering"
        )
        resident_count = 0
        if existing_ops:
            resident_count = existing_ops.get("students_resident_plan", 0) or 0

        # meals_used_participation_pct = total meals / (residents * 7 days * 3 meals) * 100
        # If no resident count yet, store the raw total for now
        participation_pct = 0.0
        possible_meals = resident_count * 7 * 3
        if possible_meals > 0:
            participation_pct = round(
                (parsed["grand_total"] / possible_meals) * 100, 1
            )

        ops_data = {
            "meals_used_participation_pct": participation_pct,
        }
        db.upsert_weekly_operational(
            conn, week_sunday.isoformat(), "Board & Catering",
            ops_data, user["username"]
        )

        db.add_email_import_log(
            conn,
            uploaded.name, "file_upload",
            datetime.now().isoformat(),
            "odyssey", "success",
            1,
            "Transaction Counts: {:,} total meals, {:.1f}% participation (Week Ending {})".format(
                parsed["grand_total"], participation_pct, week_end_display
            ),
            user["username"],
        )

        participation_note = ""
        if resident_count > 0:
            participation_note = (
                "- Participation: **{:.1f}%** "
                "({:,} meals / {:,} possible)".format(
                    participation_pct, parsed["grand_total"], possible_meals
                )
            )
        else:
            participation_note = (
                "- Participation: **N/A** "
                "(import Plan Membership first to calculate %)"
            )

        st.success(
            "**Imported!**\n\n"
            "- Total Meals Used: **{:,}**\n"
            "{}".format(parsed["grand_total"], participation_note)
        )
        st.balloons()


# ═══════════════════════════════════════════════════════
# GENERAL FILE UPLOAD
# ═══════════════════════════════════════════════════════


def _render_file_upload(conn, user):
    section_title("", "General File Upload")
    st.caption("Upload CSV or Excel files for other data types.")

    import_type = st.selectbox("Import Type", [
        "Daily Sales",
        "Daily Labor",
        "Food Cost",
        "Labor Schedule",
        "Door Counts",
        "Meal Exchange",
        "Operation Costs",
    ], key="upload_type")

    if import_type == "Door Counts":
        department = "Board & Catering"
        st.info("Door counts apply to Board & Catering only.")
    elif import_type == "Meal Exchange":
        department = st.selectbox("Department", ["Qdoba", "Retail & Mac's Grill"], key="upload_dept_mx")
        st.info("Meal exchange applies to Qdoba and Retail & Mac's Grill only.")
    else:
        department = st.selectbox("Department", DEPARTMENTS, key="upload_dept")

    uploaded_file = st.file_uploader(
        "Choose a CSV, Excel, or PDF file",
        type=["csv", "xlsx", "xls", "pdf"],
        key="file_uploader",
    )

    if uploaded_file is not None:
        df, err = _read_uploaded_file(uploaded_file)
        if err:
            st.error(err)
        elif df is not None and not df.empty:
            st.markdown("**Preview** ({} rows):".format(len(df)))
            st.dataframe(df.head(20), use_container_width=True, hide_index=True)
            st.markdown("**Columns found:** {}".format(", ".join(df.columns.tolist())))

            if st.button("Confirm Import", type="primary", key="confirm_upload"):
                count = _process_file_upload(conn, df, import_type, department, user)
                if count >= 0:
                    db.add_email_import_log(
                        conn,
                        uploaded_file.name,
                        "file_upload",
                        datetime.now().isoformat(),
                        import_type.lower().replace(" ", "_"),
                        "success",
                        count,
                        None,
                        user["username"],
                    )
                    st.success("Imported {} records.".format(count))
                    st.rerun()
        else:
            st.warning("Could not read any data from the file.")


def _process_file_upload(conn, df, import_type, department, user):
    """Process uploaded file based on import type. Returns record count or -1 on error."""
    count = 0
    try:
        if import_type == "Daily Sales":
            required = ["entry_date", "board_revenue", "retail_revenue",
                        "flex_revenue", "catering_revenue", "other_revenue"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            for _, row in df.iterrows():
                db.upsert_daily_sales(
                    conn, str(row["entry_date"]), department,
                    _safe_float(row.get("board_revenue")),
                    _safe_float(row.get("retail_revenue")),
                    _safe_float(row.get("flex_revenue")),
                    _safe_float(row.get("catering_revenue")),
                    _safe_float(row.get("other_revenue")),
                    user["username"],
                )
                count += 1

        elif import_type == "Daily Labor":
            required = ["entry_date", "labor_hours"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            for _, row in df.iterrows():
                db.upsert_daily_labor(
                    conn, str(row["entry_date"]), department,
                    _safe_float(row.get("labor_hours")),
                    user["username"],
                )
                count += 1

        elif import_type == "Food Cost":
            required = ["week_start", "invoice_total"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            for _, row in df.iterrows():
                db.upsert_food_cost(
                    conn, str(row["week_start"]), department,
                    _safe_float(row.get("invoice_total")),
                    _safe_float(row.get("inventory_start")),
                    _safe_float(row.get("inventory_end")),
                    _safe_float(row.get("adjustments")),
                    str(row.get("notes", "") or ""),
                    user["username"],
                )
                count += 1

        elif import_type == "Labor Schedule":
            required = ["entry_date", "scheduled_hours"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            for _, row in df.iterrows():
                db.upsert_labor_schedule(
                    conn, str(row["entry_date"]), department,
                    _safe_float(row.get("scheduled_hours")),
                    _safe_float(row.get("actual_hours")),
                    "file_upload",
                )
                count += 1

        elif import_type == "Door Counts":
            required = ["entry_date", "meal_period", "count"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            for _, row in df.iterrows():
                mp = str(row["meal_period"]).strip().lower()
                if mp not in ("breakfast", "lunch", "dinner"):
                    continue
                db.upsert_door_count(
                    conn, str(row["entry_date"]), department,
                    mp, _safe_int(row.get("count")), "file_upload",
                )
                count += 1

        elif import_type == "Meal Exchange":
            required = ["entry_date", "exchange_count", "dollar_amount"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            for _, row in df.iterrows():
                db.upsert_meal_exchange(
                    conn, str(row["entry_date"]), department,
                    _safe_int(row["exchange_count"]),
                    _safe_float(row.get("dollar_amount")),
                    user["username"],
                )
                count += 1

        elif import_type == "Operation Costs":
            required = ["category", "amount"]
            if not all(c in df.columns for c in required):
                st.error("Missing columns. Required: {}".format(", ".join(required)))
                return -1
            week_col = _find_column(df, ["week_start", "week", "date"])
            for _, row in df.iterrows():
                ws = str(row[week_col]) if week_col else (db.get_week_start(date.today()) - timedelta(weeks=1)).isoformat()
                cat = str(row["category"])
                amt = _safe_float(row["amount"])
                desc = str(row.get("description", "") or "")
                conn.execute(
                    "INSERT INTO operation_cost (week_start, department, category, amount, description) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (ws, department, cat, amt, desc),
                )
                count += 1
            conn.commit()

        return count

    except Exception as e:
        st.error("Error during import: {}".format(str(e)))
        return -1


# ═══════════════════════════════════════════════════════
# EMAIL CHECK (shared helper)
# ═══════════════════════════════════════════════════════


def _check_emails_by_type(conn, user, target_type):
    """Check Outlook for emails of a specific type and offer import."""
    try:
        from integrations.ms_graph import fetch_unread_emails, detect_email_type, mark_email_read
        from integrations.email_parsers import parse_email

        with st.spinner("Checking mailbox..."):
            emails = fetch_unread_emails()

        # Filter to target type
        matched = []
        for email in emails:
            detected = detect_email_type(email)
            if detected == target_type:
                matched.append(email)

        if not matched:
            st.info("No new {} emails found.".format(target_type.replace("_", " ").title()))
        else:
            st.success("Found {} {} email(s).".format(len(matched), target_type.replace("_", " ").title()))
            for i, email in enumerate(matched):
                with st.expander("{} \u2014 {}".format(
                    email.get("subject", "No subject"),
                    email.get("date", "")[:10],
                )):
                    st.markdown("**From:** {}".format(email.get("from", "Unknown")))
                    st.markdown("**Date:** {}".format(email.get("date", "Unknown")))
                    att_count = len(email.get("attachments", []))
                    st.markdown("**Attachments:** {}".format(att_count))

                    if st.button("Import This Email", key="import_{}_{}".format(target_type, i)):
                        result = parse_email(email, target_type)
                        if result.get("success"):
                            data = result.get("data", [])
                            written = 0
                            try:
                                if target_type == "usfoods_invoice":
                                    written = _write_usfoods_from_email(conn, data, user)
                                elif target_type == "inventory":
                                    written = _write_inventory_from_email(conn, data, user)
                                elif target_type == "ctuit":
                                    written = _write_ctuit_from_email(conn, data, user)
                                elif target_type == "odyssey":
                                    written = _write_odyssey_from_email(conn, data, user)
                            except Exception as write_err:
                                st.error("Parse OK but DB write failed: {}".format(str(write_err)))
                                return

                            # Mark email as read
                            try:
                                mark_email_read(email["id"])
                            except Exception:
                                pass  # Non-critical

                            db.add_email_import_log(
                                conn,
                                email.get("subject", ""),
                                email.get("from", ""),
                                email.get("date", ""),
                                target_type, "success", written, None,
                                user["username"],
                            )
                            st.success("Imported {} records!".format(written))
                        else:
                            error = result.get("error", "Unknown error")
                            db.add_email_import_log(
                                conn,
                                email.get("subject", ""),
                                email.get("from", ""),
                                email.get("date", ""),
                                target_type, "error", 0, error,
                                user["username"],
                            )
                            st.error("Import failed: {}".format(error))

    except ImportError:
        st.error("Microsoft Graph module not available. Install `msal` and `requests`.")
    except Exception as e:
        st.error("Error: {}".format(str(e)))


# ── Email data writers ──

def _write_usfoods_from_email(conn, data, user):
    written = 0
    for record in data:
        record_date = _parse_date(record["date"])
        week_start = db.get_week_start(record_date)
        dept = str(record.get("department", "Board & Catering"))
        invoice_total = _safe_float(record.get("invoice_total"))
        desc = str(record.get("description", "") or "")
        db.upsert_food_cost(
            conn, week_start.isoformat(), dept,
            invoice_total, 0, 0, 0, desc, user["username"],
        )
        written += 1
    return written


def _write_inventory_from_email(conn, data, user):
    written = 0
    for record in data:
        week_start = str(record["week_start"])
        dept = str(record["department"])
        inv_start = _safe_float(record.get("inventory_start"))
        inv_end = _safe_float(record.get("inventory_end"))
        existing = db.fetch_food_cost(conn, week_start, dept)
        existing_invoice = _safe_float((existing or {}).get("invoice_total"))
        existing_adj = _safe_float((existing or {}).get("adjustments"))
        existing_notes = str((existing or {}).get("notes", "") or "")
        db.upsert_food_cost(
            conn, week_start, dept,
            existing_invoice, inv_start, inv_end,
            existing_adj, existing_notes, user["username"],
        )
        written += 1
    return written


def _write_ctuit_from_email(conn, data, user):
    written = 0
    for record in data:
        week_start = str(record.get("week_start", ""))
        dept = str(record.get("department", ""))
        db.upsert_weekly_operational(
            conn, week_start, dept, record, user["username"],
        )
        written += 1
    return written


def _write_odyssey_from_email(conn, data, user):
    written = 0
    for record in data:
        entry_date = str(record["entry_date"])
        plan_type = str(record["plan_type"])
        enrolled = _safe_int(record.get("enrolled_count"))
        meals = _safe_int(record.get("meals_used"))
        db.upsert_meal_plan(
            conn, entry_date, plan_type, enrolled, meals, 0, user["username"],
        )
        written += 1
    return written


# ═══════════════════════════════════════════════════════
# ADP SYNC
# ═══════════════════════════════════════════════════════
# PROJECTIONS ENTRY
# ═══════════════════════════════════════════════════════


def _render_projections(conn, user):
    """Manual entry or file upload for weekly projection values."""
    section_title("", "Weekly Projections")

    # ── Week selector ──
    col_wk, col_dept = st.columns(2)
    with col_wk:
        today = date.today()
        days_since_mon = today.weekday()
        this_monday = today - timedelta(days=days_since_mon)
        week_options = [this_monday - timedelta(weeks=i) for i in range(12)]
        week_start = st.selectbox(
            "Week Starting",
            week_options,
            format_func=lambda d: d.strftime("%b %d, %Y"),
            key="proj_week",
        )
    with col_dept:
        dept = st.selectbox("Department", DEPARTMENTS, key="proj_dept")

    week_str = str(week_start)

    # ── Load existing values ──
    existing_fin = db.fetch_weekly_flash_targets(conn, week_str, dept)
    existing_ops = db.fetch_weekly_operational_targets(conn, week_str, dept)

    def _cur(source, key, default=0.0):
        if source and key in source and source[key] is not None:
            return float(source[key])
        return default

    # ── Entry mode tabs ──
    tab_manual, tab_upload = st.tabs(["Manual Entry", "File Upload"])

    # ──────────────── MANUAL ENTRY TAB ────────────────
    with tab_manual:
        st.markdown("##### Financial Projections")

        fin_col1, fin_col2 = st.columns(2)
        with fin_col1:
            proj_board_rev = st.number_input(
                "Board Revenue", value=_cur(existing_fin, "projection_board_revenue"),
                step=100.0, format="%.2f", key="proj_board_rev")
            proj_retail_rev = st.number_input(
                "Retail Revenue", value=_cur(existing_fin, "projection_retail_revenue"),
                step=100.0, format="%.2f", key="proj_retail_rev")
            proj_flex_rev = st.number_input(
                "Flex Revenue", value=_cur(existing_fin, "projection_flex_revenue"),
                step=100.0, format="%.2f", key="proj_flex_rev")
            proj_catering_rev = st.number_input(
                "Catering Revenue", value=_cur(existing_fin, "projection_catering_revenue"),
                step=100.0, format="%.2f", key="proj_catering_rev")
            proj_other_rev = st.number_input(
                "Other Revenue", value=_cur(existing_fin, "projection_other_revenue"),
                step=100.0, format="%.2f", key="proj_other_rev")
        with fin_col2:
            proj_cos = st.number_input(
                "COS ($)", value=_cur(existing_fin, "projection_cos_dollars"),
                step=100.0, format="%.2f", key="proj_cos")
            proj_labor = st.number_input(
                "Total Labor ($)", value=_cur(existing_fin, "projection_labor_dollars"),
                step=100.0, format="%.2f", key="proj_labor_dollars")
            proj_labor_hrs = st.number_input(
                "Total Labor Hours", value=_cur(existing_fin, "projection_labor_hours"),
                step=1.0, format="%.2f", key="proj_labor_hrs")
            proj_ot = st.number_input(
                "Overtime ($)", value=_cur(existing_fin, "projection_overtime_dollars"),
                step=100.0, format="%.2f", key="proj_ot")
            proj_de = st.number_input(
                "Direct Expenses", value=_cur(existing_fin, "projection_direct_expenses"),
                step=100.0, format="%.2f", key="proj_de")

        mini_divider()
        st.markdown("##### Operational Projections")

        ops_col1, ops_col2 = st.columns(2)
        with ops_col1:
            proj_students_res = st.number_input(
                "Students Resident Plan", value=int(_cur(existing_ops, "projection_students_resident", 0)),
                step=1, key="proj_students_res")
            proj_students_com = st.number_input(
                "Students Commuter Plan", value=int(_cur(existing_ops, "projection_students_commuter", 0)),
                step=1, key="proj_students_com")
            proj_participation = st.number_input(
                "Participation %", value=_cur(existing_ops, "projection_participation_pct"),
                step=0.1, format="%.1f", key="proj_participation")
            proj_billing_days = st.number_input(
                "Billing Days", value=int(_cur(existing_ops, "projection_billing_days", 7)),
                step=1, key="proj_billing_days")
            proj_board_hrs = st.number_input(
                "Board Plan Labor Hours", value=_cur(existing_ops, "projection_board_labor_hours"),
                step=1.0, format="%.2f", key="proj_board_hrs")
            proj_retail_hrs = st.number_input(
                "Retail Labor Hours", value=_cur(existing_ops, "projection_retail_labor_hours"),
                step=1.0, format="%.2f", key="proj_retail_hrs")
            proj_catering_hrs = st.number_input(
                "Catering Labor Hours", value=_cur(existing_ops, "projection_catering_labor_hours"),
                step=1.0, format="%.2f", key="proj_catering_hrs")
            proj_concession_hrs = st.number_input(
                "Concession Labor Hours", value=_cur(existing_ops, "projection_concession_labor_hours"),
                step=1.0, format="%.2f", key="proj_concession_hrs")
            proj_conference_hrs = st.number_input(
                "Conference Labor Hours", value=_cur(existing_ops, "projection_conference_labor_hours"),
                step=1.0, format="%.2f", key="proj_conference_hrs")
        with ops_col2:
            proj_ot_hrs = st.number_input(
                "OT Hours", value=_cur(existing_ops, "projection_ot_hours"),
                step=1.0, format="%.2f", key="proj_ot_hrs")
            proj_ot_dollars = st.number_input(
                "OT Dollars", value=_cur(existing_ops, "projection_ot_dollars"),
                step=100.0, format="%.2f", key="proj_ot_dollars")
            proj_temp_hrs = st.number_input(
                "Temp Hours", value=_cur(existing_ops, "projection_temp_hours"),
                step=1.0, format="%.2f", key="proj_temp_hrs")
            proj_temp_dollars = st.number_input(
                "Temp Dollars", value=_cur(existing_ops, "projection_temp_dollars"),
                step=100.0, format="%.2f", key="proj_temp_dollars")
            proj_mgmt_wages = st.number_input(
                "Management Wages", value=_cur(existing_ops, "projection_management_wages"),
                step=100.0, format="%.2f", key="proj_mgmt_wages")
            proj_hourly_wages = st.number_input(
                "Hourly Wages", value=_cur(existing_ops, "projection_hourly_wages"),
                step=100.0, format="%.2f", key="proj_hourly_wages")
            proj_fee = st.number_input(
                "Fee Account Fee", value=_cur(existing_ops, "projection_fee_account_fee"),
                step=100.0, format="%.2f", key="proj_fee")
            proj_inventory = st.number_input(
                "Total Inventory", value=_cur(existing_ops, "projection_total_inventory"),
                step=100.0, format="%.2f", key="proj_inventory")

        if st.button("Save Projections", type="primary", key="proj_save_manual"):
            # Financial projections
            fin_data = {
                "projection_board_revenue": proj_board_rev,
                "projection_retail_revenue": proj_retail_rev,
                "projection_flex_revenue": proj_flex_rev,
                "projection_catering_revenue": proj_catering_rev,
                "projection_other_revenue": proj_other_rev,
                "projection_cos_dollars": proj_cos,
                "projection_labor_dollars": proj_labor,
                "projection_labor_hours": proj_labor_hrs,
                "projection_overtime_dollars": proj_ot,
                "projection_direct_expenses": proj_de,
            }
            db.upsert_weekly_flash_targets(conn, week_str, dept, fin_data, user["username"])

            # Operational projections
            ops_data = {
                "projection_students_resident": proj_students_res,
                "projection_students_commuter": proj_students_com,
                "projection_participation_pct": proj_participation,
                "projection_billing_days": proj_billing_days,
                "projection_board_labor_hours": proj_board_hrs,
                "projection_retail_labor_hours": proj_retail_hrs,
                "projection_catering_labor_hours": proj_catering_hrs,
                "projection_concession_labor_hours": proj_concession_hrs,
                "projection_conference_labor_hours": proj_conference_hrs,
                "projection_ot_hours": proj_ot_hrs,
                "projection_ot_dollars": proj_ot_dollars,
                "projection_temp_hours": proj_temp_hrs,
                "projection_temp_dollars": proj_temp_dollars,
                "projection_management_wages": proj_mgmt_wages,
                "projection_hourly_wages": proj_hourly_wages,
                "projection_fee_account_fee": proj_fee,
                "projection_total_inventory": proj_inventory,
            }
            db.upsert_weekly_operational_targets(conn, week_str, dept, ops_data, user["username"])

            st.success("Projections saved for {} — {}".format(dept, week_start.strftime("%b %d, %Y")))

    # ──────────────── FILE UPLOAD TAB ────────────────
    with tab_upload:
        st.markdown(
            "Upload a CSV or Excel file with projection values. "
            "The file should have a **Metric** column and a **Value** column."
        )
        st.markdown(
            '<span style="color:#64748B;font-size:13px;">'
            "Accepted metric names (case-insensitive): Board Revenue, Retail Revenue, "
            "Flex Revenue, Catering Revenue, Other Revenue, COS, Total Labor $, "
            "Labor Hours, Overtime, Direct Expenses, Students Resident, "
            "Students Commuter, Participation %, Billing Days, "
            "Board Labor Hours, Retail Labor Hours, Catering Labor Hours, "
            "Concession Labor Hours, Conference Labor Hours, OT Hours, OT Dollars, "
            "Temp Hours, Temp Dollars, Management Wages, Hourly Wages, "
            "Fee Account Fee, Total Inventory"
            "</span>",
            unsafe_allow_html=True,
        )

        uploaded = st.file_uploader(
            "Upload Projections File",
            type=["csv", "xlsx", "xls"],
            key="proj_file_upload",
        )

        if uploaded:
            df_upload, err = _read_uploaded_file(uploaded)
            if err:
                st.error(err)
            elif df_upload is not None and len(df_upload) > 0:
                # Normalize column names
                df_upload.columns = [str(c).strip().lower() for c in df_upload.columns]

                metric_col = None
                value_col = None
                for c in df_upload.columns:
                    if c in ("metric", "name", "line item", "label", "field"):
                        metric_col = c
                    if c in ("value", "projection", "projected", "amount"):
                        value_col = c

                if not metric_col or not value_col:
                    st.error("Could not find Metric and Value columns. "
                             "Please ensure your file has columns named 'Metric' and 'Value'.")
                else:
                    st.dataframe(df_upload, use_container_width=True, hide_index=True)

                    # Map friendly names to DB columns
                    _FIN_MAP = {
                        "board revenue": "projection_board_revenue",
                        "retail revenue": "projection_retail_revenue",
                        "flex revenue": "projection_flex_revenue",
                        "catering revenue": "projection_catering_revenue",
                        "other revenue": "projection_other_revenue",
                        "cos": "projection_cos_dollars",
                        "cos ($)": "projection_cos_dollars",
                        "total labor $": "projection_labor_dollars",
                        "total labor ($)": "projection_labor_dollars",
                        "labor dollars": "projection_labor_dollars",
                        "labor hours": "projection_labor_hours",
                        "total labor hours": "projection_labor_hours",
                        "overtime": "projection_overtime_dollars",
                        "overtime ($)": "projection_overtime_dollars",
                        "direct expenses": "projection_direct_expenses",
                    }
                    _OPS_MAP = {
                        "students resident": "projection_students_resident",
                        "students resident plan": "projection_students_resident",
                        "students commuter": "projection_students_commuter",
                        "students commuter plan": "projection_students_commuter",
                        "participation %": "projection_participation_pct",
                        "participation pct": "projection_participation_pct",
                        "billing days": "projection_billing_days",
                        "board labor hours": "projection_board_labor_hours",
                        "board plan labor hours": "projection_board_labor_hours",
                        "retail labor hours": "projection_retail_labor_hours",
                        "catering labor hours": "projection_catering_labor_hours",
                        "concession labor hours": "projection_concession_labor_hours",
                        "conference labor hours": "projection_conference_labor_hours",
                        "ot hours": "projection_ot_hours",
                        "ot dollars": "projection_ot_dollars",
                        "temp hours": "projection_temp_hours",
                        "temp dollars": "projection_temp_dollars",
                        "management wages": "projection_management_wages",
                        "hourly wages": "projection_hourly_wages",
                        "fee account fee": "projection_fee_account_fee",
                        "total inventory": "projection_total_inventory",
                    }

                    if st.button("Import Projections from File", type="primary", key="proj_import_file"):
                        fin_data = {}
                        ops_data = {}
                        matched = 0

                        for _, row in df_upload.iterrows():
                            metric_name = str(row[metric_col]).strip().lower()
                            try:
                                val = float(row[value_col])
                            except (ValueError, TypeError):
                                continue

                            if metric_name in _FIN_MAP:
                                fin_data[_FIN_MAP[metric_name]] = val
                                matched += 1
                            elif metric_name in _OPS_MAP:
                                ops_data[_OPS_MAP[metric_name]] = val
                                matched += 1

                        if fin_data:
                            db.upsert_weekly_flash_targets(
                                conn, week_str, dept, fin_data, user["username"])
                        if ops_data:
                            db.upsert_weekly_operational_targets(
                                conn, week_str, dept, ops_data, user["username"])

                        if matched > 0:
                            st.success("Imported {} projection values for {} — {}".format(
                                matched, dept, week_start.strftime("%b %d, %Y")))
                        else:
                            st.warning("No matching metric names found in the file.")


# ═══════════════════════════════════════════════════════
# ADP SYNC
# ═══════════════════════════════════════════════════════


def _render_adp_sync(conn, user):
    section_title("", "ADP Schedule Sync")
    st.info(
        "Sync scheduled and actual labor hours from ADP.\n"
        "This updates the labor_schedule table for scheduled vs actual comparison."
    )

    import os
    has_adp_config = all([
        os.environ.get("ADP_API_BASE_URL"),
        os.environ.get("ADP_CLIENT_ID"),
        os.environ.get("ADP_CLIENT_SECRET"),
    ])

    if not has_adp_config:
        st.warning(
            "ADP API is not configured. Set the following environment variables:\n"
            "- `ADP_API_BASE_URL`\n"
            "- `ADP_CLIENT_ID`\n"
            "- `ADP_CLIENT_SECRET`\n"
            "- `ADP_CERT_PATH` (optional, for mutual TLS)"
        )

    col1, col2 = st.columns(2)
    with col1:
        sync_start = st.date_input("Start Date", key="adp_start")
    with col2:
        sync_end = st.date_input("End Date", key="adp_end")

    if st.button("Sync ADP Data", disabled=not has_adp_config, key="adp_sync"):
        try:
            from integrations.adp_client import sync_schedules
            with st.spinner("Syncing with ADP..."):
                result = sync_schedules(conn, sync_start.isoformat(), sync_end.isoformat())
                if result.get("success"):
                    records = result.get("records", 0)
                    db.add_adp_sync_log(
                        conn, "schedule_sync", "success", records, None, user["username"]
                    )
                    st.success("Synced {} records from ADP.".format(records))
                else:
                    error = result.get("error", "Unknown error")
                    db.add_adp_sync_log(
                        conn, "schedule_sync", "error", 0, error, user["username"]
                    )
                    st.error("ADP sync failed: {}".format(error))
        except ImportError:
            st.error("ADP client module not available.")
        except Exception as e:
            st.error("ADP sync error: {}".format(str(e)))

    # Manual CSV fallback
    mini_divider()
    st.markdown("#### Manual Schedule Upload (Fallback)")
    st.caption("Upload a schedule CSV with columns: "
               "entry_date, department, scheduled_hours, actual_hours")
    adp_file = st.file_uploader("Upload ADP CSV", type=["csv"], key="adp_csv")
    if adp_file:
        try:
            adp_df = pd.read_csv(adp_file)
            st.dataframe(adp_df.head(10), use_container_width=True, hide_index=True)
            if st.button("Import Schedule", key="import_adp_csv"):
                count = 0
                for _, row in adp_df.iterrows():
                    dept = str(row.get("department", ""))
                    if dept in DEPARTMENTS:
                        db.upsert_labor_schedule(
                            conn, str(row["entry_date"]), dept,
                            _safe_float(row.get("scheduled_hours")),
                            _safe_float(row.get("actual_hours")),
                            "csv_upload",
                        )
                        count += 1
                db.add_adp_sync_log(
                    conn, "csv_upload", "success", count, None, user["username"]
                )
                st.success("Imported {} schedule records.".format(count))
                st.rerun()
        except Exception as e:
            st.error("Error reading ADP CSV: {}".format(str(e)))


# ═══════════════════════════════════════════════════════
# IMPORT HISTORY
# ═══════════════════════════════════════════════════════


def _render_import_history(conn):
    section_title("", "Import History")

    # Email / file imports
    st.markdown("#### Email / File Imports")
    email_logs = db.fetch_import_logs(conn, limit=50)
    if email_logs:
        log_df = pd.DataFrame(email_logs)
        display_cols = ["import_timestamp", "email_subject", "email_sender",
                        "import_type", "status", "records_imported", "error_message"]
        available_cols = [c for c in display_cols if c in log_df.columns]
        st.dataframe(log_df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.caption("No import history yet.")

    # ADP sync logs
    st.markdown("#### ADP Sync Logs")
    adp_logs = conn.execute(
        "SELECT * FROM adp_sync_log ORDER BY sync_timestamp DESC LIMIT 50"
    ).fetchall()
    if adp_logs:
        adp_df = pd.DataFrame([dict(r) for r in adp_logs])
        st.dataframe(adp_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No ADP sync history yet.")


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════


def _find_column(df, candidates):
    """Find a column in the DataFrame that matches one of the candidate names (case-insensitive)."""
    df_cols_lower = {c.lower().replace(" ", "_"): c for c in df.columns}
    for candidate in candidates:
        c_lower = candidate.lower().replace(" ", "_")
        if c_lower in df_cols_lower:
            return df_cols_lower[c_lower]
    # Partial match
    for candidate in candidates:
        c_lower = candidate.lower()
        for col_lower, col_orig in df_cols_lower.items():
            if c_lower in col_lower or col_lower in c_lower:
                return col_orig
    return None


def _auto_idx(col_options, df, candidates):
    """Return the index in col_options for the best auto-detected column, or 0 for (skip)."""
    found = _find_column(df, candidates)
    if found and found in col_options:
        return col_options.index(found)
    return 0


# ═══════════════════════════════════════════════════════
# INVOICE TRACKER IMPORT
# ═══════════════════════════════════════════════════════


