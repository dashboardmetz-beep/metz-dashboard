"""
Database initialization script for Campus Dining Budget App.
Creates all tables and seeds sample data.
Run once, or re-run safely (uses IF NOT EXISTS / INSERT OR IGNORE).
"""
import sqlite3
from datetime import date, timedelta

DB_PATH = "budget.db"


def get_week_start(d):
    """Return Sunday of the week containing d (Sun-Sat week)."""
    days_since_sunday = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sunday)


def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Enable WAL mode for concurrent reads
    c.execute("PRAGMA journal_mode=WAL")

    # ═══════════════════════════════════════════════════════
    # EXISTING TABLES (preserved from v1)
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            revenue REAL DEFAULT 0,
            labor_dollars REAL DEFAULT 0,
            labor_hours REAL DEFAULT 0,
            status TEXT DEFAULT 'Draft',
            version INTEGER DEFAULT 1,
            updated_by TEXT,
            updated_at DATETIME,
            submitted_by TEXT,
            submitted_at DATETIME,
            approved_by TEXT,
            approved_at DATETIME,
            UNIQUE(week_start, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            field TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            is_open INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS last_year_actuals (
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            revenue REAL DEFAULT 0,
            labor_dollars REAL DEFAULT 0,
            labor_hours REAL DEFAULT 0,
            PRIMARY KEY(week_start, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            department TEXT PRIMARY KEY,
            target_labor_pct REAL,
            target_splh REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            password_hash TEXT
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: DAILY TABLES
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            board_revenue REAL DEFAULT 0,
            retail_revenue REAL DEFAULT 0,
            flex_revenue REAL DEFAULT 0,
            catering_revenue REAL DEFAULT 0,
            other_revenue REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_labor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            labor_hours REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            condition TEXT NOT NULL,
            weather_affected_staffing INTEGER DEFAULT 0,
            notes TEXT,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            notes TEXT,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date, department, category)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: WEEKLY FINANCIAL TABLES (Flash Report Left Panel)
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            board_revenue REAL DEFAULT 0,
            retail_revenue REAL DEFAULT 0,
            flex_revenue REAL DEFAULT 0,
            catering_revenue REAL DEFAULT 0,
            other_revenue REAL DEFAULT 0,
            cos_dollars REAL DEFAULT 0,
            total_labor_dollars REAL DEFAULT 0,
            total_labor_hours REAL DEFAULT 0,
            overtime_dollars REAL DEFAULT 0,
            direct_expenses REAL DEFAULT 0,
            gross_profit REAL DEFAULT 0,
            total_payroll REAL DEFAULT 0,
            tax_fringe REAL DEFAULT 0,
            after_prime_costs REAL DEFAULT 0,
            pace REAL DEFAULT 0,
            non_cont_expenses REAL DEFAULT 0,
            insurance REAL DEFAULT 0,
            profit_fee REAL DEFAULT 0,
            royalties REAL DEFAULT 0,
            net_income REAL DEFAULT 0,
            management_fees REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_flash_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            budget_board_revenue REAL DEFAULT 0,
            budget_retail_revenue REAL DEFAULT 0,
            budget_flex_revenue REAL DEFAULT 0,
            budget_catering_revenue REAL DEFAULT 0,
            budget_other_revenue REAL DEFAULT 0,
            projection_board_revenue REAL DEFAULT 0,
            projection_retail_revenue REAL DEFAULT 0,
            projection_flex_revenue REAL DEFAULT 0,
            projection_catering_revenue REAL DEFAULT 0,
            projection_other_revenue REAL DEFAULT 0,
            budget_cos_dollars REAL DEFAULT 0,
            projection_cos_dollars REAL DEFAULT 0,
            budget_labor_dollars REAL DEFAULT 0,
            budget_labor_hours REAL DEFAULT 0,
            projection_labor_dollars REAL DEFAULT 0,
            projection_labor_hours REAL DEFAULT 0,
            budget_overtime_dollars REAL DEFAULT 0,
            projection_overtime_dollars REAL DEFAULT 0,
            budget_direct_expenses REAL DEFAULT 0,
            projection_direct_expenses REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS flash_explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            line_item TEXT NOT NULL,
            variance_type TEXT NOT NULL,
            explanation TEXT NOT NULL,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department, line_item, variance_type)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: WEEKLY OPERATIONAL TABLES (Flash Report Right Panel)
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_operational (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            students_resident_plan INTEGER DEFAULT 0,
            students_commuter_plan INTEGER DEFAULT 0,
            meals_used_participation_pct REAL DEFAULT 0,
            board_plan_billing_days INTEGER DEFAULT 0,
            board_plan_labor_hours REAL DEFAULT 0,
            retail_labor_hours REAL DEFAULT 0,
            catering_labor_hours REAL DEFAULT 0,
            concession_labor_hours REAL DEFAULT 0,
            conference_labor_hours REAL DEFAULT 0,
            ot_hours_included_above REAL DEFAULT 0,
            ot_dollars_paid REAL DEFAULT 0,
            temp_hours_included_above REAL DEFAULT 0,
            temp_dollars_paid REAL DEFAULT 0,
            management_wages REAL DEFAULT 0,
            hourly_wages REAL DEFAULT 0,
            average_hourly_wage REAL DEFAULT 0,
            fee_account_fee REAL DEFAULT 0,
            total_inventory REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_operational_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            budget_students_resident INTEGER DEFAULT 0,
            budget_students_commuter INTEGER DEFAULT 0,
            budget_participation_pct REAL DEFAULT 0,
            budget_billing_days INTEGER DEFAULT 0,
            budget_board_labor_hours REAL DEFAULT 0,
            budget_retail_labor_hours REAL DEFAULT 0,
            budget_catering_labor_hours REAL DEFAULT 0,
            budget_concession_labor_hours REAL DEFAULT 0,
            budget_conference_labor_hours REAL DEFAULT 0,
            budget_ot_hours REAL DEFAULT 0,
            budget_ot_dollars REAL DEFAULT 0,
            budget_temp_hours REAL DEFAULT 0,
            budget_temp_dollars REAL DEFAULT 0,
            budget_management_wages REAL DEFAULT 0,
            budget_hourly_wages REAL DEFAULT 0,
            budget_avg_hourly_wage REAL DEFAULT 0,
            budget_fee_account_fee REAL DEFAULT 0,
            budget_total_inventory REAL DEFAULT 0,
            projection_students_resident INTEGER DEFAULT 0,
            projection_students_commuter INTEGER DEFAULT 0,
            projection_participation_pct REAL DEFAULT 0,
            projection_billing_days INTEGER DEFAULT 0,
            projection_board_labor_hours REAL DEFAULT 0,
            projection_retail_labor_hours REAL DEFAULT 0,
            projection_catering_labor_hours REAL DEFAULT 0,
            projection_concession_labor_hours REAL DEFAULT 0,
            projection_conference_labor_hours REAL DEFAULT 0,
            projection_ot_hours REAL DEFAULT 0,
            projection_ot_dollars REAL DEFAULT 0,
            projection_temp_hours REAL DEFAULT 0,
            projection_temp_dollars REAL DEFAULT 0,
            projection_management_wages REAL DEFAULT 0,
            projection_hourly_wages REAL DEFAULT 0,
            projection_avg_hourly_wage REAL DEFAULT 0,
            projection_fee_account_fee REAL DEFAULT 0,
            projection_total_inventory REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: FOOD COST & OPERATIONS
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS food_cost (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            invoice_total REAL DEFAULT 0,
            inventory_start REAL DEFAULT 0,
            inventory_end REAL DEFAULT 0,
            adjustments REAL DEFAULT 0,
            notes TEXT,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS operation_cost (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL DEFAULT 0,
            description TEXT,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department, category)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: INVOICE TRACKER
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS invoice_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            vendor TEXT NOT NULL,
            sun REAL DEFAULT 0,
            mon REAL DEFAULT 0,
            tue REAL DEFAULT 0,
            wed REAL DEFAULT 0,
            thu REAL DEFAULT 0,
            fri REAL DEFAULT 0,
            sat REAL DEFAULT 0,
            weekly_total REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department, section, vendor)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: BUDGET ATTACHMENTS
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS budget_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            uploaded_by TEXT NOT NULL,
            uploaded_at DATETIME NOT NULL,
            updated_by TEXT,
            updated_at DATETIME
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: CTUIT DETAIL LINE ITEMS
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS ctuit_detail_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL,
            line_item TEXT NOT NULL,
            amount REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(week_start, department, section, line_item)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: LABOR / ADP SCHEDULE
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS labor_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            scheduled_hours REAL DEFAULT 0,
            actual_hours REAL DEFAULT 0,
            variance_hours REAL DEFAULT 0,
            source TEXT DEFAULT 'manual',
            updated_at DATETIME,
            UNIQUE(entry_date, department)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: POS DATA
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS meal_plan_participation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            plan_type TEXT NOT NULL,
            enrolled_count INTEGER DEFAULT 0,
            meals_used INTEGER DEFAULT 0,
            billing_days INTEGER DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date, plan_type)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS meal_exchange (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            exchange_count INTEGER DEFAULT 0,
            dollar_amount REAL DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date, department)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS split_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date DATE NOT NULL,
            department TEXT NOT NULL,
            transaction_id TEXT,
            tender_type_1 TEXT,
            amount_1 REAL DEFAULT 0,
            tender_type_2 TEXT,
            amount_2 REAL DEFAULT 0,
            tender_type_3 TEXT,
            amount_3 REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            updated_at DATETIME
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS door_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            meal_period TEXT NOT NULL DEFAULT 'lunch',
            count INTEGER DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(entry_date, department, meal_period)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: IMPORT LOGS
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS email_import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_timestamp DATETIME NOT NULL,
            email_subject TEXT,
            email_sender TEXT,
            email_date DATETIME,
            import_type TEXT NOT NULL,
            status TEXT NOT NULL,
            records_imported INTEGER DEFAULT 0,
            error_message TEXT,
            triggered_by TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS adp_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_timestamp DATETIME NOT NULL,
            sync_type TEXT NOT NULL,
            status TEXT NOT NULL,
            records_synced INTEGER DEFAULT 0,
            error_message TEXT,
            triggered_by TEXT
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: CALENDAR EVENTS
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date DATE NOT NULL,
            end_date DATE,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL DEFAULT 'other',
            affects_dining INTEGER DEFAULT 0,
            dining_impact TEXT,
            created_by TEXT DEFAULT 'system',
            created_at DATETIME,
            UNIQUE(event_date, title)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: CATERING EVENTS (BEO System)
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS catering_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date DATE NOT NULL,
            event_name TEXT NOT NULL,
            client_name TEXT,
            department TEXT DEFAULT 'Board & Catering',
            event_type TEXT DEFAULT 'catering',
            location TEXT,
            start_time TEXT,
            end_time TEXT,
            guest_count INTEGER DEFAULT 0,
            setup_style TEXT,
            menu_notes TEXT,
            special_requests TEXT,
            dietary_notes TEXT,
            equipment_needed TEXT,
            staffing_notes TEXT,
            status TEXT DEFAULT 'Pending',
            total_cost REAL DEFAULT 0,
            billed_amount REAL DEFAULT 0,
            created_by TEXT,
            created_at DATETIME,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(event_date, event_name)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS catering_event_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_cost REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            category TEXT DEFAULT 'food',
            notes TEXT,
            FOREIGN KEY (event_id) REFERENCES catering_events(id)
        )
    """)

    # ═══════════════════════════════════════════════════════
    # NEW: SAFETY & COMPLIANCE
    # ═══════════════════════════════════════════════════════

    c.execute("""
        CREATE TABLE IF NOT EXISTS safety_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_date DATE NOT NULL,
            department TEXT NOT NULL,
            checklist_type TEXT NOT NULL,
            completed_by TEXT,
            completed_at DATETIME,
            status TEXT DEFAULT 'Incomplete',
            notes TEXT,
            UNIQUE(checklist_date, department, checklist_type)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS safety_checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            is_checked INTEGER DEFAULT 0,
            value TEXT,
            notes TEXT,
            checked_by TEXT,
            checked_at DATETIME,
            FOREIGN KEY (checklist_id) REFERENCES safety_checklists(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS temp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date DATE NOT NULL,
            department TEXT NOT NULL,
            equipment_name TEXT NOT NULL,
            temp_reading REAL,
            temp_unit TEXT DEFAULT 'F',
            in_range INTEGER DEFAULT 1,
            corrective_action TEXT,
            logged_by TEXT,
            logged_at DATETIME,
            UNIQUE(log_date, department, equipment_name, logged_at)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS waste_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date DATE NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            item_description TEXT,
            weight_lbs REAL DEFAULT 0,
            estimated_cost REAL DEFAULT 0,
            reason TEXT,
            meal_period TEXT,
            corrective_action TEXT,
            logged_by TEXT,
            logged_at DATETIME
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS preservice_meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_date DATE NOT NULL,
            department TEXT NOT NULL,
            meal_period TEXT NOT NULL DEFAULT 'lunch',
            led_by TEXT,
            attendee_count INTEGER DEFAULT 0,
            menu_highlights TEXT,
            items_86d TEXT,
            vip_info TEXT,
            event_notes TEXT,
            safety_reminders TEXT,
            general_notes TEXT,
            action_items TEXT,
            created_by TEXT,
            created_at DATETIME,
            UNIQUE(meeting_date, department, meal_period)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            department TEXT,
            phone TEXT,
            email TEXT,
            is_emergency INTEGER DEFAULT 0,
            category TEXT DEFAULT 'staff',
            notes TEXT,
            created_by TEXT,
            updated_at DATETIME
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS area_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_name TEXT NOT NULL,
            department TEXT NOT NULL,
            assigned_to TEXT,
            shift TEXT DEFAULT 'All Day',
            responsibilities TEXT,
            notes TEXT,
            effective_date DATE,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(area_name, department, shift)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS key_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            department TEXT,
            priority INTEGER DEFAULT 0,
            updated_by TEXT,
            updated_at DATETIME,
            UNIQUE(category, title, department)
        )
    """)


    c.execute("""
        CREATE TABLE IF NOT EXISTS shift_communications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comm_date DATE NOT NULL,
            department TEXT NOT NULL,
            shift_type TEXT NOT NULL DEFAULT 'AM',
            author TEXT,
            tasks_completed TEXT,
            tasks_pending TEXT,
            equipment_issues TEXT,
            inventory_notes TEXT,
            staff_notes TEXT,
            safety_concerns TEXT,
            general_notes TEXT,
            urgent_flag INTEGER DEFAULT 0,
            read_by TEXT,
            created_by TEXT,
            created_at DATETIME,
            UNIQUE(comm_date, department, shift_type)
        )
    """)


    conn.commit()

    # ═══════════════════════════════════════════════════════
    # SEED DATA
    # ═══════════════════════════════════════════════════════

    import hashlib

    def _pw(p):
        return hashlib.sha256(p.encode()).hexdigest()

    users = [
        ("bc_editor", "Board & Catering", "editor", "Board & Catering", _pw("board123")),
        ("sb_editor", "Starbucks", "editor", "Starbucks", _pw("starbucks123")),
        ("qd_editor", "Qdoba", "editor", "Qdoba", _pw("qdoba123")),
        ("ll_editor", "Retail & Mac's Grill", "editor", "Retail & Mac's Grill", _pw("lochlomond123")),
        ("director", "Director", "approver", None, _pw("director123")),
        ("admin", "Admin", "admin", None, _pw("admin123")),
    ]
    for u in users:
        c.execute(
            "INSERT OR IGNORE INTO users (username, display_name, role, department, password_hash) "
            "VALUES (?,?,?,?,?)",
            u,
        )

    targets = [
        ("Board & Catering", 30.0, 45.0),
        ("Starbucks", 28.0, 50.0),
        ("Qdoba", 32.0, 40.0),
        ("Retail & Mac's Grill", 25.0, 55.0),
    ]
    for t in targets:
        c.execute(
            "INSERT OR IGNORE INTO targets (department, target_labor_pct, target_splh) VALUES (?,?,?)",
            t,
        )

    # Seed last-year actuals
    departments = ["Board & Catering", "Starbucks", "Qdoba", "Retail & Mac's Grill"]
    today = date.today()
    this_week = get_week_start(today)

    sample_data = {
        "Board & Catering": (12000, 3500, 80),
        "Starbucks": (8500, 2300, 55),
        "Qdoba": (9000, 2800, 70),
        "Retail & Mac's Grill": (15000, 3700, 65),
    }

    for i in range(-4, 5):
        week = this_week + timedelta(weeks=i)
        ly_week = week - timedelta(weeks=52)
        for dept in departments:
            base_rev, base_lab, base_hrs = sample_data[dept]
            factor = 1.0 + (i * 0.02)
            c.execute(
                "INSERT OR IGNORE INTO last_year_actuals (week_start, department, revenue, labor_dollars, labor_hours) VALUES (?,?,?,?,?)",
                (
                    ly_week.isoformat(),
                    dept,
                    round(base_rev * factor, 2),
                    round(base_lab * factor, 2),
                    round(base_hrs * factor, 1),
                ),
            )

    # ═══════════════════════════════════════════════════════
    # MIGRATIONS (safe re-run on existing databases)
    # ═══════════════════════════════════════════════════════

    # meal_exchange table already created above — no duplicate needed

    # ─── Seed Calendar Events ───
    calendar_events = [
        # ═══ ACADEMIC CALENDAR 2026-2027 ═══
        # Fall 2026
        ("2026-08-31", None, "Fall Term Classes Begin", "14-week and 1st 7-Week Classes", "academic", 1, "Full dining service resumes"),
        ("2026-09-07", None, "Labor Day", "No Classes - Offices Closed", "holiday", 1, "Holiday schedule - limited service"),
        ("2026-10-12", "2026-10-13", "Fall Term Recess", "No Classes - Offices Open", "academic", 1, "Reduced meal plan traffic expected"),
        ("2026-11-25", None, "Thanksgiving Recess Begins", "No classes - Offices Open", "holiday", 1, "Hamilton reduced hours"),
        ("2026-11-26", "2026-11-27", "Thanksgiving", "No Classes - Offices Closed", "holiday", 1, "Hamilton closed"),
        ("2026-12-07", "2026-12-11", "Final Exam Week", "See Registrar for schedule", "academic", 1, "Extended hours possible"),
        ("2026-12-12", "2027-01-10", "Winter Recess", "Offices Closed Dec 23 - Jan 3", "academic", 1, "Hamilton closed / limited athlete meals"),
        # Winter 2027
        ("2027-01-04", None, "Offices Open", "Staff return", "academic", 0, None),
        ("2027-01-11", None, "Winter Term Classes Begin", "14-week and 1st 7-Week Classes", "academic", 1, "Full dining service resumes"),
        ("2027-01-18", None, "Martin Luther King Jr. Day", "No Classes - Offices Open", "holiday", 1, "Brunch and dinner only"),
        ("2027-03-01", "2027-03-05", "Winter Break", "No Classes - Offices Open", "academic", 1, "Hamilton closed / athlete meals off-plan"),
        ("2027-03-26", None, "Good Friday", "No Classes - Offices Close at Noon", "holiday", 1, "No breakfast, brunch & dinner only. Retail closed"),
        ("2027-04-08", None, "Honors Day", "No Classes - Offices Open", "academic", 1, "Hamilton brunch and dinner only"),
        ("2027-04-19", "2027-04-23", "Final Exam Week", "See Registrar for schedule", "academic", 1, "Extended hours possible"),
        ("2027-04-24", None, "Commencement", "Ceremonies at 2 PM", "academic", 1, "Heavy catering - Senior celebration"),
        # Spring 2027
        ("2027-05-02", None, "Spring Term Classes Begin", None, "academic", 1, "Limited staff - reduced hours"),
        ("2027-05-27", None, "Spring Term Ends", None, "academic", 1, "Last meal dinner - Hamilton closes at 6pm"),
        # Summer 2027
        ("2027-06-01", None, "Summer Session I Begins", "19 days", "academic", 1, "Summer dining TBD"),
        ("2027-06-28", None, "Summer Session II Begins", "19 days", "academic", 0, None),
        ("2027-07-26", None, "Summer Session III Begins", "19 days", "academic", 0, None),

        # ═══ KEY DINING SERVICE DATES 2026 ═══
        ("2026-01-02", None, "Welcome Back Meeting", "Staff meeting", "dining", 0, None),
        ("2026-01-04", None, "Hamilton Opens PM Service", "5pm-7:30pm", "dining", 1, "Check staffing schedules"),
        ("2026-01-05", None, "Hamilton & Retail Normal Service", "Full service resumes", "dining", 1, "Normal hours resume"),
        ("2026-01-10", None, "Esports Event + Admissions Visit", "Lunch 12:45-1:30pm", "admissions", 1, "Esports catering lunch"),
        ("2026-01-19", None, "MLK Day", "Hamilton closed breakfast, brunch & dinner", "holiday", 1, "No breakfast - brunch and dinner only"),
        ("2026-01-31", None, "Distinguished Scholars", "Catering event only", "admissions", 1, "Catering needed"),
        ("2026-02-05", "2026-02-06", "Board of Trustees Meetings", "Catering needed", "catering", 1, "Heavy catering"),
        ("2026-02-07", None, "Academic Discovery Day", "Lunch 12:20-1:15pm", "admissions", 1, "Extra lunch capacity needed"),
        ("2026-02-18", None, "Ash Wednesday / Ramadan Begins", "Start of Lent & Ramadan", "dining", 1, "Ramadan containers + retail options"),
        ("2026-02-27", None, "Hamilton Closed After PM Service", "Closes at 7pm for break prep", "dining", 1, "Early close"),
        ("2026-02-28", None, "Hamilton Closed - Winter Break", "Athlete meals off-plan through break", "dining", 1, "Closed - athlete boxed meals"),
        ("2026-03-07", None, "Hamilton Reopens PM Service", "5pm dinner service", "dining", 1, "PM service only"),
        ("2026-03-09", None, "Hamilton Normal Hours Resume", "Full service", "dining", 1, "Normal hours"),
        ("2026-03-17", None, "St. Patrick's Day", "Hamilton special event", "dining", 1, "Special menu"),
        ("2026-03-20", None, "Eid Al-Fitr", "Halal dinner", "dining", 1, "Special halal dinner menu"),
        ("2026-03-21", None, "Admitted Student Day", "Admissions event", "admissions", 1, "Extra lunch capacity"),
        ("2026-04-02", None, "Honors Day", "No classes - brunch & dinner only", "academic", 1, "No breakfast"),
        ("2026-04-03", None, "Good Friday", "Offices close at noon", "holiday", 1, "No breakfast, brunch & dinner. Retail closed"),
        ("2026-04-05", None, "Easter Sunday", "Hamilton normal hours, retail closed", "holiday", 1, "Retail closed"),
        ("2026-04-17", None, "Winter Term Last Day", "Hamilton PM close at 6pm", "academic", 1, "Retail closes for year"),
        ("2026-04-18", None, "Commencement", "Senior celebration TBD", "academic", 1, "Heavy catering"),
        ("2026-04-19", "2026-04-25", "Transition Week", "Athletes meals off-plan", "dining", 1, "Limited service"),
        ("2026-04-26", None, "Spring Term Starts - Dinner Only", "Hamilton dinner 5pm-7pm", "dining", 1, "Dinner service only"),
        ("2026-05-04", "2026-05-05", "Board of Trustees", "Heavy catering", "catering", 1, "Heavy catering needed"),
        ("2026-05-10", None, "Mother's Day", "Special menu consideration", "dining", 1, "Special menu"),
        ("2026-05-21", None, "Spring Term Last Day", "Hamilton last meal dinner, close 6pm", "dining", 1, "Last day of service"),
        ("2026-05-22", None, "Hamilton Cleaning Days", "Limited staffing", "dining", 1, "No meal service"),
        ("2026-05-23", None, "Summer Layoff", "Staff layoff begins", "dining", 0, None),
        ("2026-06-12", None, "Camps & Conference Season Begins", "TBD", "dining", 1, "Camp meal service begins"),
        ("2026-07-01", None, "New Fiscal Year Begins", "FY2027", "fiscal", 0, None),

        # ═══ FISCAL CALENDAR (Metz 4-4-5 Pattern) ═══
        # Fiscal periods for 2026 (based on Sun-Sat weeks, Metz BICU pattern)
        ("2026-01-04", "2026-01-31", "Fiscal Period 1 (January)", "4 weeks", "fiscal", 0, None),
        ("2026-02-01", "2026-02-28", "Fiscal Period 2 (February)", "4 weeks", "fiscal", 0, None),
        ("2026-03-01", "2026-04-04", "Fiscal Period 3 (March)", "5 weeks", "fiscal", 0, None),
        ("2026-04-05", "2026-05-02", "Fiscal Period 4 (April)", "4 weeks", "fiscal", 0, None),
        ("2026-05-03", "2026-05-30", "Fiscal Period 5 (May)", "4 weeks", "fiscal", 0, None),
        ("2026-05-31", "2026-07-04", "Fiscal Period 6 (June)", "5 weeks", "fiscal", 0, None),
        ("2026-07-05", "2026-08-01", "Fiscal Period 7 (July)", "4 weeks", "fiscal", 0, None),
        ("2026-08-02", "2026-08-29", "Fiscal Period 8 (August)", "4 weeks", "fiscal", 0, None),
        ("2026-08-30", "2026-10-03", "Fiscal Period 9 (September)", "5 weeks", "fiscal", 0, None),
        ("2026-10-04", "2026-10-31", "Fiscal Period 10 (October)", "4 weeks", "fiscal", 0, None),
        ("2026-11-01", "2026-11-28", "Fiscal Period 11 (November)", "4 weeks", "fiscal", 0, None),
        ("2026-11-29", "2027-01-02", "Fiscal Period 12 (December)", "5 weeks", "fiscal", 0, None),
    ]

    for ev in calendar_events:
        c.execute(
            "INSERT OR IGNORE INTO calendar_events "
            "(event_date, end_date, title, description, category, affects_dining, dining_impact, created_by, created_at) "
            "VALUES (?,?,?,?,?,?,?,'system', datetime('now'))",
            ev,
        )


    # Seed key info entries
    key_info_seeds = [
        ("hours", "Board & Catering Hours", "Breakfast: 7:00 AM - 9:30 AM\nLunch: 11:00 AM - 1:30 PM\nDinner: 5:00 PM - 7:30 PM", "Board & Catering", 1),
        ("hours", "Starbucks Hours", "Monday - Friday: 7:00 AM - 10:00 PM\nSaturday - Sunday: 8:00 AM - 8:00 PM", "Starbucks", 1),
        ("hours", "Qdoba Hours", "Monday - Friday: 11:00 AM - 9:00 PM\nSaturday: 11:00 AM - 8:00 PM\nSunday: Closed", "Qdoba", 1),
        ("hours", "Retail & Mac's Grill Hours", "Monday - Friday: 7:00 AM - 2:00 PM", "Retail & Mac's Grill", 1),
        ("emergency", "Fire Emergency", "Call 911 immediately\nEvacuate all guests\nMeet at designated assembly point\nNotify Director", None, 2),
        ("emergency", "Medical Emergency", "Call 911\nDo not move the injured person\nProvide first aid if trained\nNotify Director immediately", None, 2),
        ("emergency", "Power Outage", "Secure all food items immediately\nCheck freezer and cooler temps\nContact Facilities: ext 4100\nFollow food safety hold procedures", None, 2),
        ("policy", "Food Allergy Protocol", "Always ask about allergies\nUse separate prep tools\nLabel all allergens clearly\nWhen in doubt, check with manager", None, 1),
        ("policy", "Cash Handling", "Count drawer at start and end of shift\nTwo-person verification for drops\nNever leave register unattended\nReport discrepancies immediately", None, 1),
    ]
    for ki in key_info_seeds:
        c.execute("""
            INSERT OR IGNORE INTO key_info (category, title, content, department, priority)
            VALUES (?, ?, ?, ?, ?)
        """, ki)

    conn.commit()
    conn.close()
    print("Database initialized at {}".format(DB_PATH))
    print("Sample users created:")
    for u in users:
        print("  {:12s} | {:8s} | {}".format(u[0], u[2], u[3] or "All departments"))




if __name__ == "__main__":
    init_database()
