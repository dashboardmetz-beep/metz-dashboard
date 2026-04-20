"""
Central configuration constants for the Campus Dining Budget App.
All modules import from here — single source of truth.
"""

DB_PATH = "budget.db"

DEPARTMENTS = ["Board & Catering", "Starbucks", "Qdoba", "Retail & Mac's Grill"]

REVENUE_STREAMS = ["board", "retail", "flex", "catering", "other"]

REVENUE_STREAM_LABELS = {
    "board": "Board",
    "retail": "Retail",
    "flex": "Flex",
    "catering": "Catering",
    "other": "Other",
}

WEATHER_CONDITIONS = ["Clear", "Rain", "Snow", "Storm", "Extreme Heat", "Fog", "Other"]

DAILY_NOTE_CATEGORIES = ["Staffing & Scheduling", "Training", "Other"]

FIELDS = ["revenue", "labor_dollars", "labor_hours", "cos", "overtime",
          "direct_expenses", "operational", "general"]

REASON_CODES = ["Event", "Staffing", "Training", "Seasonal", "Other"]

STATUSES = ["Draft", "Submitted", "Returned", "Approved"]

STATUS_COLORS = {
    "Draft": "\U0001f4dd",
    "Submitted": "\U0001f4e4",
    "Returned": "\U0001f504",
    "Approved": "\u2705",
}

# Flash Report financial line items (left panel) — ordered as in Excel
FLASH_FINANCIAL_LINES = [
    ("board_revenue", "Board", "dollar"),
    ("retail_revenue", "Retail", "dollar"),
    ("flex_revenue", "Flex", "dollar"),
    ("catering_revenue", "Catering", "dollar"),
    ("other_revenue", "Other", "dollar"),
    ("total_revenue", "Total", "dollar"),
    ("cos_dollars", "COS ($)", "dollar"),
    ("cos_pct", "COS (%)", "pct"),
    ("cpm", "CPM (Res Only)", "dollar"),
    ("total_labor_dollars", "Total Labor ($)", "dollar"),
    ("total_labor_pct", "Total Labor (%)", "pct"),
    ("splh", "SPLH", "dollar"),
    ("mplh", "MPLH (Res Only)", "number"),
    ("overtime_dollars", "Overtime", "dollar"),
    ("direct_expenses", "Direct Expenses", "dollar"),
]

# Flash Report operational metrics (right panel) — ordered as in Excel
FLASH_OPERATIONAL_LINES = [
    ("students_resident_plan", "Students on Resident Plan", "number"),
    ("students_commuter_plan", "Students on Commuter Plan", "number"),
    ("meals_used_participation_pct", "Meals Used Participation %", "pct"),
    ("board_plan_billing_days", "Board Plan Billing Days", "number"),
    ("board_plan_labor_hours", "Board Plan Labor Hours", "number"),
    ("retail_labor_hours", "Retail Labor Hours", "number"),
    ("catering_labor_hours", "Catering Labor Hours", "number"),
    ("concession_labor_hours", "Concession Labor Hours", "number"),
    ("conference_labor_hours", "Conference Labor Hours", "number"),
    ("ot_hours_included_above", "OT Hours Included Above", "number"),
    ("ot_dollars_paid", "OT Dollars Paid", "dollar"),
    ("temp_hours_included_above", "Temp Hours Included Above", "number"),
    ("temp_dollars_paid", "Temp Dollars Paid", "dollar"),
    ("management_wages", "Management Wages", "dollar"),
    ("hourly_wages", "Hourly Wages", "dollar"),
    ("average_hourly_wage", "Average Hourly Wage", "dollar"),
    ("fee_account_fee", "Fee Account Fee", "dollar"),
    ("total_inventory", "Total Inventory", "dollar"),
]

IMPORT_TYPES = ["usfoods_invoice", "inventory", "ctuit", "odyssey", "labor_hours_adp",
                "invoice_tracker"]

# ─── Invoice Tracker ─────────────────────────────────────
INVOICE_EXCEL_SECTION_MAP = {
    "HAMILTON": "Board & Catering",
    "HAMILTON ": "Board & Catering",
    "CATERING": "Board & Catering",
    "CATERING ": "Board & Catering",
    "STARBUCKS": "Starbucks",
    "STARBUCKS ": "Starbucks",
    "MACS/RETAIL": "Retail & Mac's Grill",
    "MACS/RETAIL ": "Retail & Mac's Grill",
    "QDOBA": "Qdoba",
}

INVOICE_DAY_COLUMNS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
INVOICE_DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# Path to the ALMA Invoice Tracker Excel workbook (linked, read directly)
# Uses environment variable if set, otherwise falls back to default path
import os as _os
INVOICE_TRACKER_FILE = _os.environ.get(
    "INVOICE_TRACKER_PATH",
    _os.path.join(_os.path.expanduser("~"), "Downloads", "ALMA INVOICE TRACKER 2025-26.xlsx"),
)

OPERATION_COST_CATEGORIES = [
    "Supplies", "Maintenance", "Utilities", "Equipment",
    "Marketing", "Cleaning", "Miscellaneous",
]

# ─── File Upload Config ───────────────────────────────────────
UPLOAD_DIR = "uploads"

ALLOWED_ATTACHMENT_EXTENSIONS = [".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".gif"]

ALLOWED_IMPORT_EXTENSIONS = [".csv", ".xlsx", ".xls", ".pdf"]

MAX_FILE_SIZE_MB = 10

BUDGET_IMPORT_COLUMNS = {
    "board_revenue": "Board Revenue",
    "retail_revenue": "Retail Revenue",
    "flex_revenue": "Flex Revenue",
    "catering_revenue": "Catering Revenue",
    "other_revenue": "Other Revenue",
    "total_labor_dollars": "Total Labor ($)",
    "total_labor_hours": "Total Labor Hours",
    "invoice_total": "Invoice Total (Food Cost)",
    "inventory_start": "Inventory Start",
    "inventory_end": "Inventory End",
    "adjustments": "Adjustments",
    "overtime_dollars": "Overtime ($)",
    "direct_expenses": "Direct Expenses",
}

# ─── CTUIT / Compeat Ops Statement Mapping ─────────────────────
# Maps Report Group keywords to our department names.

CTUIT_REPORT_GROUP_MAP = {
    "qdoba": "Qdoba",
    "starbucks": "Starbucks",
    "retail": "Retail & Mac's Grill",
    "mac grill": "Retail & Mac's Grill",
    "mac's grill": "Retail & Mac's Grill",
    "board": "Board & Catering",
    "catering": "Board & Catering",
    "consolidated": "Consolidated",
}

# Sales line items -> which DB revenue field they map to (additive)
CTUIT_SALES_MAP = {
    "retail sales": "retail_revenue",
    "retail comps": "retail_revenue",
    "meal equivalent": "board_revenue",
    "board sales": "board_revenue",
    "flex sales": "flex_revenue",
    "flex non meal": "flex_revenue",
    "catering-inside": "catering_revenue",
    "catering-outsid": "catering_revenue",
    "in-house": "other_revenue",
    "program": "other_revenue",
    "vending income": "other_revenue",
    "summer conferen": "other_revenue",
    "non-academic da": "other_revenue",
    "sales commissio": "other_revenue",
    # Consolidated report (uppercase labels)
    "retail": "retail_revenue",
    "board": "board_revenue",
    "flex": "flex_revenue",
    "catering": "catering_revenue",
    "summer": "other_revenue",
    "other": "other_revenue",
}

# Summary / total line items -> direct DB field mapping
CTUIT_SUMMARY_MAP = {
    "total cost of sales": "cos_dollars",
    "total labor": "total_labor_dollars",
    "hourly-overtime": "overtime_dollars",
    "total cont. expenses": "direct_expenses",
    "total cont.\nexpenses": "direct_expenses",
    "total cont.": "direct_expenses",
    "gross profit": "gross_profit",
    "total payroll": "total_payroll",
    "total tax & fringe": "tax_fringe",
    "after prime costs": "after_prime_costs",
    "pace": "pace",
    "total non-cont\nexpense": "non_cont_expenses",
    "total non-cont expense": "non_cont_expenses",
    "total non-cont": "non_cont_expenses",
    "net income": "net_income",
    "income before fees": "net_income",
    "total other fees": "management_fees",
    # Consolidated report labels
    "management": "management_wages",
    "hourly": "hourly_wages",
    "overtime": "overtime_dollars",
    "vac/sick/hol": "vac_sick_hol",
    "bonus": "bonus",
}

# Labor detail lines for flash report extra fields
CTUIT_LABOR_DETAIL = {
    "management": "management_wages",
    "hourly-regular": "hourly_wages",
    "hourly-overtime": "overtime_dollars",
    "tax & fringe": "tax_fringe",
}

# Non-controllable expense detail lines
CTUIT_NON_CONT_DETAIL = {
    "general insurance": "insurance",
    "profit": "profit_fee",
    "royalties/nat'l adv": "royalties",
    "comm / profit": "profit_fee",
}

# ─── CTUIT Detail Line Items ─────────────────────────────────
# Maps CTUIT PDF label (lowercase) -> (section, db_key, display_label)
# These are the individual breakdowns within each section.

CTUIT_DETAIL_MAP = {
    # COS Detail
    "dry grocery":          ("cos", "dry_grocery", "Dry Grocery"),
    "dairy":                ("cos", "dairy", "Dairy"),
    "beverages":            ("cos", "beverages", "Beverages"),
    "grocery":              ("cos", "grocery", "Grocery"),
    "bakery":               ("cos", "bakery", "Bakery"),
    "meat-pork/beef":       ("cos", "meat_pork_beef", "Meat-Pork/Beef"),
    "poultry":              ("cos", "poultry", "Poultry"),
    "produce":              ("cos", "produce", "Produce"),
    "seafood":              ("cos", "seafood", "Seafood"),
    "c-store merchandise":  ("cos", "c_store_merchandise", "C-Store Merchandise"),
    "misc. cost":           ("cos", "misc_cost", "Misc. Cost"),
    "disposables":          ("cos", "disposables", "Disposables"),
    # Controllable Expenses Detail
    "credit card/bank fees": ("controllable", "credit_card_bank_fees", "Credit Card/Bank Fees"),
    "equipment/supplies":    ("controllable", "equipment_supplies", "Equipment/Supplies"),
    "janitorial/hazardous":  ("controllable", "janitorial_hazardous", "Janitorial/Hazardous"),
    "misc expense":          ("controllable", "misc_expense", "Misc Expense"),
    "marketing/ad/decor":    ("controllable", "marketing_ad_decor", "Marketing/Ad/Decor"),
    "laundry":               ("controllable", "laundry", "Laundry"),
    "uniforms":              ("controllable", "uniforms", "Uniforms"),
    "menus":                 ("controllable", "menus", "Menus"),
    "over/short":            ("controllable", "over_short", "Over/Short"),
    "employee recruit":      ("controllable", "employee_recruit", "Employee Recruit"),
    # Non-Controllable Expenses Detail
    "license/permits/taxes": ("non_controllable", "license_permits_taxes", "License/Permits/Taxes"),
    "depreciation":          ("non_controllable", "depreciation", "Depreciation"),
    "rent":                  ("non_controllable", "rent", "Rent"),
    "telephone/utilities":   ("non_controllable", "telephone_utilities", "Telephone/Utilities"),
    "repairs":               ("non_controllable", "repairs", "Repairs"),
    "service contracts":     ("non_controllable", "service_contracts", "Service Contracts"),
    "refuse/pest control":   ("non_controllable", "refuse_pest_control", "Refuse/Pest Control"),
    "auto expense":          ("non_controllable", "auto_expense", "Auto Expense"),
    "computer eexpense":     ("non_controllable", "computer_expense", "Computer Expense"),
    "postage":               ("non_controllable", "postage", "Postage"),
    "travel & lodging":      ("non_controllable", "travel_lodging", "Travel & Lodging"),
    "dues & subscriptions":  ("non_controllable", "dues_subscriptions", "Dues & Subscriptions"),
    "opening exp":           ("non_controllable", "opening_exp", "Opening Exp"),
    "interest exp":          ("non_controllable", "interest_exp", "Interest Exp"),
    "contributions":         ("non_controllable", "contributions", "Contributions"),
    "deferred contract":     ("non_controllable", "deferred_contract", "Deferred Contract"),
    "leases":                ("non_controllable", "leases", "Leases"),
    "admin fees":            ("non_controllable", "admin_fees", "Admin Fees"),
    "vending supplies":      ("non_controllable", "vending_supplies", "Vending Supplies"),
    # Consolidated report labels (uppercase -> same keys)
    "protein":               ("cos", "meat_pork_beef", "Protein"),
    "c-store merchandise":   ("cos", "c_store_merchandise", "C-Store Merchandise"),
    "telephone/utilities":   ("non_controllable", "telephone_utilities", "Telephone/Utilities"),
    "menus & printing":      ("controllable", "menus", "Menus & Printing"),
    "equipment rental":      ("controllable", "equipment_rental", "Equipment Rental"),
    "travel and lodging":    ("non_controllable", "travel_lodging", "Travel & Lodging"),
    "dues & subs":           ("non_controllable", "dues_subscriptions", "Dues & Subs"),
    "credit card":           ("controllable", "credit_card_bank_fees", "Credit Card"),
    "over / short":          ("controllable", "over_short", "Over/Short"),
    "refuse/pest":           ("non_controllable", "refuse_pest_control", "Refuse/Pest"),
    "marketing/adv/deco":    ("controllable", "marketing_ad_decor", "Marketing/Adv/Deco"),
    "license/permits/tax":   ("non_controllable", "license_permits_taxes", "License/Permits/Tax"),
    "general insurance":     ("non_controllable", "general_insurance", "General Insurance"),
    "comm / profit":         ("non_controllable", "comm_profit", "Comm / Profit"),
    "royalties/nat'l adv":   ("non_controllable", "royalties_natl_adv", "Royalties/Nat'l Adv"),
    "mgmnt/admin fees":      ("non_controllable", "admin_fees", "Mgmnt/Admin Fees"),
    "technology":            ("non_controllable", "technology", "Technology"),
    "cam":                   ("non_controllable", "cam", "CAM"),
    "office supplies":       ("controllable", "office_supplies", "Office Supplies"),
    "equipment/supplies":    ("controllable", "equipment_supplies", "Equipment/Supplies"),
    "janitorial/hazardou":   ("controllable", "janitorial_hazardous", "Janitorial/Hazardous"),
    "employee recruit":      ("controllable", "employee_recruit", "Employee Recruit"),
    "misc expense":          ("controllable", "misc_expense", "Misc Expense"),
    # Labor Detail
    "hourly-vac/sick/hol":   ("labor", "hourly_vac_sick_hol", "Hourly-Vac/Sick/Hol"),
    "contract labor":        ("labor", "contract_labor", "Contract Labor"),
    "bonus":                 ("labor", "bonus", "Bonus"),
}

CTUIT_DETAIL_SECTIONS = {
    "cos": "Cost of Sales Detail",
    "controllable": "Controllable Expenses Detail",
    "non_controllable": "Non-Controllable Expenses Detail",
    "labor": "Labor Detail",
}

# ─── AI Copilot ──────────────────────────────────────────────────
COPILOT_MODEL = "claude-sonnet-4-20250514"
COPILOT_MAX_TOKENS = 2048
COPILOT_MAX_QUERY_ROWS = 100
