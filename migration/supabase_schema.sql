-- Auto-generated Postgres schema for Supabase.
-- Source: budget.db (SQLite). Built by migration/build_supabase_schema.py.
-- Safe to re-run: every statement is IF NOT EXISTS.

-- ─── adp_sync_log ───
CREATE TABLE IF NOT EXISTS adp_sync_log (
            id BIGSERIAL PRIMARY KEY,
            sync_timestamp TIMESTAMPTZ NOT NULL,
            sync_type TEXT NOT NULL,
            status TEXT NOT NULL,
            records_synced BIGINT DEFAULT 0,
            error_message TEXT,
            triggered_by TEXT
        );

-- ─── ar_invoices ───
CREATE TABLE IF NOT EXISTS ar_invoices (
            id BIGSERIAL PRIMARY KEY,
            invoice_number TEXT NOT NULL,
            due_date TEXT,
            total DOUBLE PRECISION DEFAULT 0,
            current_amount DOUBLE PRECISION DEFAULT 0,
            days_0_30 DOUBLE PRECISION DEFAULT 0,
            days_31_60 DOUBLE PRECISION DEFAULT 0,
            days_61_90 DOUBLE PRECISION DEFAULT 0,
            days_91_120 DOUBLE PRECISION DEFAULT 0,
            days_121_150 DOUBLE PRECISION DEFAULT 0,
            days_151_plus DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(invoice_number)
        );

-- ─── area_assignments ───
CREATE TABLE IF NOT EXISTS area_assignments (
            id BIGSERIAL PRIMARY KEY,
            area_name TEXT NOT NULL,
            department TEXT NOT NULL,
            assigned_to TEXT,
            shift TEXT DEFAULT 'All Day',
            responsibilities TEXT,
            notes TEXT,
            effective_date DATE,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(area_name, department, shift)
        );

-- ─── budget_attachments ───
CREATE TABLE IF NOT EXISTS budget_attachments (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size BIGINT DEFAULT 0,
            uploaded_by TEXT NOT NULL,
            uploaded_at TIMESTAMPTZ NOT NULL,
            updated_by TEXT,
            updated_at TIMESTAMPTZ
        );

-- ─── budgets ───
CREATE TABLE IF NOT EXISTS budgets (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            revenue DOUBLE PRECISION DEFAULT 0,
            labor_dollars DOUBLE PRECISION DEFAULT 0,
            labor_hours DOUBLE PRECISION DEFAULT 0,
            status TEXT DEFAULT 'Draft',
            version BIGINT DEFAULT 1,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            submitted_by TEXT,
            submitted_at TIMESTAMPTZ,
            approved_by TEXT,
            approved_at TIMESTAMPTZ,
            UNIQUE(week_start, department)
        );

-- ─── calendar_events ───
CREATE TABLE IF NOT EXISTS calendar_events (
        id BIGSERIAL PRIMARY KEY,
        event_date DATE NOT NULL,
        end_date DATE,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL DEFAULT 'other',
        affects_dining BIGINT DEFAULT 0,
        dining_impact TEXT,
        created_by TEXT DEFAULT 'system',
        created_at TIMESTAMPTZ,
        UNIQUE(event_date, title)
    );

-- ─── catering_event_items ───
CREATE TABLE IF NOT EXISTS catering_event_items (
        id BIGSERIAL PRIMARY KEY,
        event_id BIGINT NOT NULL,
        item_name TEXT NOT NULL,
        quantity BIGINT DEFAULT 1,
        unit_cost DOUBLE PRECISION DEFAULT 0,
        total_cost DOUBLE PRECISION DEFAULT 0,
        category TEXT DEFAULT 'food',
        notes TEXT
    );

-- ─── catering_events ───
CREATE TABLE IF NOT EXISTS catering_events (
        id BIGSERIAL PRIMARY KEY,
        event_date DATE NOT NULL,
        event_name TEXT NOT NULL,
        client_name TEXT,
        department TEXT DEFAULT 'Board & Catering',
        event_type TEXT DEFAULT 'catering',
        location TEXT,
        start_time TEXT,
        end_time TEXT,
        guest_count BIGINT DEFAULT 0,
        setup_style TEXT,
        menu_notes TEXT,
        special_requests TEXT,
        dietary_notes TEXT,
        equipment_needed TEXT,
        staffing_notes TEXT,
        status TEXT DEFAULT 'Pending',
        total_cost DOUBLE PRECISION DEFAULT 0,
        billed_amount DOUBLE PRECISION DEFAULT 0,
        created_by TEXT,
        created_at TIMESTAMPTZ,
        updated_by TEXT,
        updated_at TIMESTAMPTZ,
        UNIQUE(event_date, event_name)
    );

-- ─── checklist_entries ───
CREATE TABLE IF NOT EXISTS checklist_entries (
            id BIGSERIAL PRIMARY KEY,
            template_id BIGINT NOT NULL,
            entry_date TEXT NOT NULL,
            department TEXT DEFAULT 'Board & Catering',
            completed_items TEXT DEFAULT '[]',
            total_items BIGINT DEFAULT 0,
            completed_count BIGINT DEFAULT 0,
            completed_by TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (now()),
            UNIQUE(template_id, entry_date, department)
        );

-- ─── checklist_items ───
CREATE TABLE IF NOT EXISTS checklist_items (
            id BIGSERIAL PRIMARY KEY,
            template_id BIGINT NOT NULL,
            item_text TEXT NOT NULL,
            sort_order BIGINT DEFAULT 0
        );

-- ─── checklist_templates ───
CREATE TABLE IF NOT EXISTS checklist_templates (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            checklist_type TEXT DEFAULT 'daily',
            department TEXT DEFAULT 'Board & Catering',
            active BIGINT DEFAULT 1,
            created_at TEXT DEFAULT (now()),
            UNIQUE(name, department)
        );

-- ─── comments ───
CREATE TABLE IF NOT EXISTS comments (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            field TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            is_open BIGINT DEFAULT 1
        );

-- ─── contacts ───
CREATE TABLE IF NOT EXISTS contacts (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT,
            department TEXT,
            phone TEXT,
            email TEXT,
            is_emergency BIGINT DEFAULT 0,
            category TEXT DEFAULT 'staff',
            notes TEXT,
            created_by TEXT,
            updated_at TIMESTAMPTZ
        );

-- ─── contract_areas ───
CREATE TABLE IF NOT EXISTS contract_areas (
        id BIGSERIAL PRIMARY KEY,
        department TEXT NOT NULL UNIQUE,
        contract_type TEXT DEFAULT 'Managed',
        operator TEXT DEFAULT 'Metz Culinary Management',
        revenue_share_pct DOUBLE PRECISION DEFAULT 0,
        commission_structure TEXT,
        contract_start DATE,
        contract_end DATE,
        renewal_date DATE,
        operating_hours TEXT,
        operating_days TEXT,
        meal_periods TEXT,
        seating_capacity BIGINT DEFAULT 0,
        square_footage BIGINT DEFAULT 0,
        key_contact_name TEXT,
        key_contact_phone TEXT,
        key_contact_email TEXT,
        performance_kpis TEXT,
        special_terms TEXT,
        notes TEXT,
        updated_by TEXT,
        updated_at TIMESTAMPTZ
    );

-- ─── ctuit_detail_items ───
CREATE TABLE IF NOT EXISTS ctuit_detail_items (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL,
            line_item TEXT NOT NULL,
            amount DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department, section, line_item)
        );

-- ─── ctuit_import_log ───
CREATE TABLE IF NOT EXISTS ctuit_import_log (
            id BIGSERIAL PRIMARY KEY,
            filename TEXT UNIQUE NOT NULL,
            department TEXT,
            week_start DATE,
            records BIGINT DEFAULT 0,
            status TEXT,
            message TEXT,
            imported_at TIMESTAMPTZ,
            imported_by TEXT
        );

-- ─── daily_labor ───
CREATE TABLE IF NOT EXISTS daily_labor (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            labor_hours DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(entry_date, department)
        );

-- ─── daily_notes ───
CREATE TABLE IF NOT EXISTS daily_notes (
    id BIGSERIAL PRIMARY KEY,
    entry_date DATE NOT NULL,
    department TEXT NOT NULL,
    category TEXT NOT NULL,
    notes TEXT,
    updated_by TEXT,
    updated_at TIMESTAMPTZ,
    UNIQUE(entry_date, department, category)
);

-- ─── daily_sales ───
CREATE TABLE IF NOT EXISTS daily_sales (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            board_revenue DOUBLE PRECISION DEFAULT 0,
            retail_revenue DOUBLE PRECISION DEFAULT 0,
            flex_revenue DOUBLE PRECISION DEFAULT 0,
            catering_revenue DOUBLE PRECISION DEFAULT 0,
            other_revenue DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(entry_date, department)
        );

-- ─── daily_weather ───
CREATE TABLE IF NOT EXISTS daily_weather (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            condition TEXT NOT NULL,
            weather_affected_staffing BIGINT DEFAULT 0,
            notes TEXT,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(entry_date)
        );

-- ─── digital_meal_counts ───
CREATE TABLE IF NOT EXISTS digital_meal_counts (
            id BIGSERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            day_name TEXT,
            sheet_name TEXT,
            location TEXT DEFAULT 'Board',
            py_breakfast BIGINT DEFAULT 0,
            py_lunch BIGINT DEFAULT 0,
            py_dinner BIGINT DEFAULT 0,
            fc_breakfast BIGINT DEFAULT 0,
            fc_lunch BIGINT DEFAULT 0,
            fc_dinner BIGINT DEFAULT 0,
            greeter_breakfast BIGINT DEFAULT 0,
            nonmeal_breakfast BIGINT DEFAULT 0,
            student_breakfast BIGINT DEFAULT 0,
            total_breakfast BIGINT DEFAULT 0,
            greeter_lunch BIGINT DEFAULT 0,
            nonmeal_lunch BIGINT DEFAULT 0,
            student_lunch BIGINT DEFAULT 0,
            total_lunch BIGINT DEFAULT 0,
            greeter_dinner BIGINT DEFAULT 0,
            fulltime_dinner BIGINT DEFAULT 0,
            student_dinner BIGINT DEFAULT 0,
            total_dinner BIGINT DEFAULT 0,
            total_day BIGINT DEFAULT 0,
            admission BIGINT DEFAULT 0,
            special_groups BIGINT DEFAULT 0,
            weather TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            imported_at TEXT DEFAULT (now()),
            UNIQUE(date, location)
        );

-- ─── door_counts ───
CREATE TABLE IF NOT EXISTS door_counts (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            hour_of_day BIGINT,
            count BIGINT DEFAULT 0,
            updated_at TIMESTAMPTZ, meal_period TEXT NOT NULL DEFAULT 'lunch', updated_by TEXT,
            UNIQUE(entry_date, department, hour_of_day)
        );

-- ─── email_import_log ───
CREATE TABLE IF NOT EXISTS email_import_log (
            id BIGSERIAL PRIMARY KEY,
            import_timestamp TIMESTAMPTZ NOT NULL,
            email_subject TEXT,
            email_sender TEXT,
            email_date TIMESTAMPTZ,
            import_type TEXT NOT NULL,
            status TEXT NOT NULL,
            records_imported BIGINT DEFAULT 0,
            error_message TEXT,
            triggered_by TEXT
        );

-- ─── employees ───
CREATE TABLE IF NOT EXISTS employees (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'Staff',
            department TEXT DEFAULT 'Board & Catering',
            hourly_rate DOUBLE PRECISION DEFAULT 0.0,
            max_hours DOUBLE PRECISION DEFAULT 40.0,
            active BIGINT DEFAULT 1,
            created_at TEXT DEFAULT (now()),
            UNIQUE(name, department)
        );

-- ─── flash_explanations ───
CREATE TABLE IF NOT EXISTS flash_explanations (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            line_item TEXT NOT NULL,
            variance_type TEXT NOT NULL,
            explanation TEXT NOT NULL,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department, line_item, variance_type)
        );

-- ─── food_cost ───
CREATE TABLE IF NOT EXISTS food_cost (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            invoice_total DOUBLE PRECISION DEFAULT 0,
            inventory_start DOUBLE PRECISION DEFAULT 0,
            inventory_end DOUBLE PRECISION DEFAULT 0,
            adjustments DOUBLE PRECISION DEFAULT 0,
            notes TEXT,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department)
        );

-- ─── inventory_counts ───
CREATE TABLE IF NOT EXISTS inventory_counts (
            id BIGSERIAL PRIMARY KEY,
            item_id BIGINT NOT NULL,
            count_date TEXT NOT NULL,
            quantity DOUBLE PRECISION DEFAULT 0.0,
            counted_by TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (now()),
            UNIQUE(item_id, count_date)
        );

-- ─── inventory_items ───
CREATE TABLE IF NOT EXISTS inventory_items (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            unit TEXT DEFAULT 'each',
            unit_cost DOUBLE PRECISION DEFAULT 0.0,
            par_level DOUBLE PRECISION DEFAULT 0.0,
            supplier TEXT DEFAULT '',
            department TEXT DEFAULT 'Board & Catering',
            active BIGINT DEFAULT 1,
            created_at TEXT DEFAULT (now()),
            UNIQUE(name, department)
        );

-- ─── inventory_waste ───
CREATE TABLE IF NOT EXISTS inventory_waste (
            id BIGSERIAL PRIMARY KEY,
            item_id BIGINT,
            waste_date TEXT NOT NULL,
            quantity DOUBLE PRECISION DEFAULT 0.0,
            reason TEXT DEFAULT '',
            cost DOUBLE PRECISION DEFAULT 0.0,
            department TEXT DEFAULT 'Board & Catering',
            logged_by TEXT DEFAULT '',
            created_at TEXT DEFAULT (now())
        );

-- ─── invoice_tracker ───
CREATE TABLE IF NOT EXISTS invoice_tracker (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            vendor TEXT NOT NULL,
            sun DOUBLE PRECISION DEFAULT 0,
            mon DOUBLE PRECISION DEFAULT 0,
            tue DOUBLE PRECISION DEFAULT 0,
            wed DOUBLE PRECISION DEFAULT 0,
            thu DOUBLE PRECISION DEFAULT 0,
            fri DOUBLE PRECISION DEFAULT 0,
            sat DOUBLE PRECISION DEFAULT 0,
            weekly_total DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department, section, vendor)
        );

-- ─── key_info ───
CREATE TABLE IF NOT EXISTS key_info (
            id BIGSERIAL PRIMARY KEY,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            department TEXT,
            priority BIGINT DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(category, title, department)
        );

-- ─── labor_schedule ───
CREATE TABLE IF NOT EXISTS labor_schedule (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            department TEXT NOT NULL,
            scheduled_hours DOUBLE PRECISION DEFAULT 0,
            actual_hours DOUBLE PRECISION DEFAULT 0,
            variance_hours DOUBLE PRECISION DEFAULT 0,
            source TEXT DEFAULT 'manual',
            updated_at TIMESTAMPTZ,
            UNIQUE(entry_date, department)
        );

-- ─── last_year_actuals ───
CREATE TABLE IF NOT EXISTS last_year_actuals (
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            revenue DOUBLE PRECISION DEFAULT 0,
            labor_dollars DOUBLE PRECISION DEFAULT 0,
            labor_hours DOUBLE PRECISION DEFAULT 0,
            PRIMARY KEY(week_start, department)
        );

-- ─── meal_exchange ───
CREATE TABLE IF NOT EXISTS meal_exchange (
    id BIGSERIAL PRIMARY KEY,
    entry_date DATE NOT NULL,
    department TEXT NOT NULL,
    exchange_count BIGINT DEFAULT 0,
    dollar_amount DOUBLE PRECISION DEFAULT 0,
    updated_by TEXT,
    updated_at TIMESTAMPTZ,
    UNIQUE(entry_date, department)
);

-- ─── meal_plan_participation ───
CREATE TABLE IF NOT EXISTS meal_plan_participation (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            plan_type TEXT NOT NULL,
            enrolled_count BIGINT DEFAULT 0,
            meals_used BIGINT DEFAULT 0,
            billing_days BIGINT DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(entry_date, plan_type)
        );

-- ─── meal_plan_tracker ───
CREATE TABLE IF NOT EXISTS meal_plan_tracker (
            id BIGSERIAL PRIMARY KEY,
            semester TEXT NOT NULL,
            section TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            budgeted_daily_rate DOUBLE PRECISION DEFAULT 0,
            actual_daily_rate DOUBLE PRECISION DEFAULT 0,
            flex_amount DOUBLE PRECISION DEFAULT 0,
            budgeted_plans BIGINT DEFAULT 0,
            actual_plans BIGINT DEFAULT 0,
            budgeted_revenue DOUBLE PRECISION DEFAULT 0,
            actual_revenue DOUBLE PRECISION DEFAULT 0,
            budgeted_flex DOUBLE PRECISION DEFAULT 0,
            actual_flex DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(semester, section, plan_name)
        );

-- ─── odyssey_import_log ───
CREATE TABLE IF NOT EXISTS odyssey_import_log (
            id BIGSERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            report_type TEXT NOT NULL,
            report_date TEXT,
            records_imported BIGINT DEFAULT 0,
            imported_at TEXT DEFAULT (now()),
            UNIQUE(filename)
        );

-- ─── odyssey_plan_membership ───
CREATE TABLE IF NOT EXISTS odyssey_plan_membership (
            id BIGSERIAL PRIMARY KEY,
            report_date TEXT NOT NULL,
            plan_id BIGINT NOT NULL,
            plan_name TEXT NOT NULL,
            member_count BIGINT DEFAULT 0,
            percentage DOUBLE PRECISION DEFAULT 0.0,
            imported_at TEXT DEFAULT (now()),
            UNIQUE(report_date, plan_id)
        );

-- ─── odyssey_tender_totals ───
CREATE TABLE IF NOT EXISTS odyssey_tender_totals (
            id BIGSERIAL PRIMARY KEY,
            report_date TEXT NOT NULL,
            terminal TEXT NOT NULL,
            service_period TEXT NOT NULL,
            board_count BIGINT DEFAULT 0,
            points_count BIGINT DEFAULT 0,
            bonpts_count BIGINT DEFAULT 0,
            board_total DOUBLE PRECISION DEFAULT 0.0,
            points_total DOUBLE PRECISION DEFAULT 0.0,
            bonpts_total DOUBLE PRECISION DEFAULT 0.0,
            board_avg DOUBLE PRECISION DEFAULT 0.0,
            points_avg DOUBLE PRECISION DEFAULT 0.0,
            bonpts_avg DOUBLE PRECISION DEFAULT 0.0,
            imported_at TEXT DEFAULT (now()),
            UNIQUE(report_date, terminal, service_period)
        );

-- ─── odyssey_transaction_counts ───
CREATE TABLE IF NOT EXISTS odyssey_transaction_counts (
            id BIGSERIAL PRIMARY KEY,
            week_start TEXT NOT NULL,
            week_end TEXT NOT NULL,
            unit TEXT NOT NULL,
            plan_id BIGINT NOT NULL,
            plan_name TEXT NOT NULL,
            bfast BIGINT DEFAULT 0,
            cbfast BIGINT DEFAULT 0,
            brunch BIGINT DEFAULT 0,
            lunch BIGINT DEFAULT 0,
            dinner BIGINT DEFAULT 0,
            late BIGINT DEFAULT 0,
            total BIGINT DEFAULT 0,
            imported_at TEXT DEFAULT (now()),
            UNIQUE(week_start, plan_id)
        );

-- ─── operation_cost ───
CREATE TABLE IF NOT EXISTS operation_cost (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            amount DOUBLE PRECISION DEFAULT 0,
            description TEXT,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department, category)
        );

-- ─── po_items ───
CREATE TABLE IF NOT EXISTS po_items (
            id BIGSERIAL PRIMARY KEY,
            po_id BIGINT NOT NULL,
            item_id BIGINT,
            item_name TEXT NOT NULL,
            quantity DOUBLE PRECISION DEFAULT 0.0,
            unit_cost DOUBLE PRECISION DEFAULT 0.0,
            total_cost DOUBLE PRECISION DEFAULT 0.0
        );

-- ─── preservice_meetings ───
CREATE TABLE IF NOT EXISTS preservice_meetings (
            id BIGSERIAL PRIMARY KEY,
            meeting_date DATE NOT NULL,
            department TEXT NOT NULL,
            meal_period TEXT NOT NULL DEFAULT 'lunch',
            led_by TEXT,
            attendee_count BIGINT DEFAULT 0,
            menu_highlights TEXT,
            items_86d TEXT,
            vip_info TEXT,
            event_notes TEXT,
            safety_reminders TEXT,
            general_notes TEXT,
            action_items TEXT,
            created_by TEXT,
            created_at TIMESTAMPTZ,
            UNIQUE(meeting_date, department, meal_period)
        );

-- ─── purchase_orders ───
CREATE TABLE IF NOT EXISTS purchase_orders (
            id BIGSERIAL PRIMARY KEY,
            supplier TEXT NOT NULL,
            order_date TEXT NOT NULL,
            delivery_date TEXT,
            department TEXT DEFAULT 'Board & Catering',
            status TEXT DEFAULT 'draft',
            total_cost DOUBLE PRECISION DEFAULT 0.0,
            notes TEXT DEFAULT '',
            created_by TEXT DEFAULT '',
            created_at TEXT DEFAULT (now())
        );

-- ─── safety_checklist_items ───
CREATE TABLE IF NOT EXISTS safety_checklist_items (
        id BIGSERIAL PRIMARY KEY,
        checklist_id BIGINT NOT NULL,
        item_name TEXT NOT NULL,
        is_checked BIGINT DEFAULT 0,
        value TEXT,
        notes TEXT,
        checked_by TEXT,
        checked_at TIMESTAMPTZ
    );

-- ─── safety_checklists ───
CREATE TABLE IF NOT EXISTS safety_checklists (
        id BIGSERIAL PRIMARY KEY,
        checklist_date DATE NOT NULL,
        department TEXT NOT NULL,
        checklist_type TEXT NOT NULL,
        completed_by TEXT,
        completed_at TIMESTAMPTZ,
        status TEXT DEFAULT 'Incomplete',
        notes TEXT,
        UNIQUE(checklist_date, department, checklist_type)
    );

-- ─── schedule_shifts ───
CREATE TABLE IF NOT EXISTS schedule_shifts (
            id BIGSERIAL PRIMARY KEY,
            employee_id BIGINT NOT NULL,
            shift_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            hours DOUBLE PRECISION DEFAULT 0.0,
            department TEXT DEFAULT 'Board & Catering',
            position TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (now()),
            UNIQUE(employee_id, shift_date)
        );

-- ─── shift_communications ───
CREATE TABLE IF NOT EXISTS shift_communications (
            id BIGSERIAL PRIMARY KEY,
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
            urgent_flag BIGINT DEFAULT 0,
            read_by TEXT,
            created_by TEXT,
            created_at TIMESTAMPTZ,
            UNIQUE(comm_date, department, shift_type)
        );

-- ─── split_transactions ───
CREATE TABLE IF NOT EXISTS split_transactions (
            id BIGSERIAL PRIMARY KEY,
            transaction_date DATE NOT NULL,
            department TEXT NOT NULL,
            transaction_id TEXT,
            tender_type_1 TEXT,
            amount_1 DOUBLE PRECISION DEFAULT 0,
            tender_type_2 TEXT,
            amount_2 DOUBLE PRECISION DEFAULT 0,
            tender_type_3 TEXT,
            amount_3 DOUBLE PRECISION DEFAULT 0,
            total_amount DOUBLE PRECISION DEFAULT 0,
            updated_at TIMESTAMPTZ
        );

-- ─── targets ───
CREATE TABLE IF NOT EXISTS targets (
            department TEXT PRIMARY KEY,
            target_labor_pct DOUBLE PRECISION,
            target_splh DOUBLE PRECISION
        , target_food_cost_pct DOUBLE PRECISION DEFAULT 30.0, salaries_dollars DOUBLE PRECISION DEFAULT 0.0, office_labor_dollars DOUBLE PRECISION DEFAULT 0.0, avg_hourly_wage DOUBLE PRECISION DEFAULT 17.0);

-- ─── temp_logs ───
CREATE TABLE IF NOT EXISTS temp_logs (
        id BIGSERIAL PRIMARY KEY,
        log_date DATE NOT NULL,
        department TEXT NOT NULL,
        equipment_name TEXT NOT NULL,
        temp_reading DOUBLE PRECISION,
        temp_unit TEXT DEFAULT 'F',
        in_range BIGINT DEFAULT 1,
        corrective_action TEXT,
        logged_by TEXT,
        logged_at TIMESTAMPTZ,
        UNIQUE(log_date, department, equipment_name, logged_at)
    );

-- ─── training_modules ───
CREATE TABLE IF NOT EXISTS training_modules (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            required BIGINT DEFAULT 0,
            description TEXT DEFAULT '',
            duration_hours DOUBLE PRECISION DEFAULT 1.0,
            created_at TEXT DEFAULT (now()),
            UNIQUE(name)
        );

-- ─── training_progress ───
CREATE TABLE IF NOT EXISTS training_progress (
            id BIGSERIAL PRIMARY KEY,
            employee_id BIGINT NOT NULL,
            module_id BIGINT NOT NULL,
            status TEXT DEFAULT 'not_started',
            started_date TEXT,
            completed_date TEXT,
            score DOUBLE PRECISION,
            notes TEXT DEFAULT '',
            UNIQUE(employee_id, module_id)
        );

-- ─── users ───
CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT
        , password_hash TEXT);

-- ─── waste_log ───
CREATE TABLE IF NOT EXISTS waste_log (
        id BIGSERIAL PRIMARY KEY,
        log_date DATE NOT NULL,
        department TEXT NOT NULL,
        category TEXT NOT NULL,
        item_description TEXT,
        weight_lbs DOUBLE PRECISION DEFAULT 0,
        estimated_cost DOUBLE PRECISION DEFAULT 0,
        reason TEXT,
        meal_period TEXT,
        corrective_action TEXT,
        logged_by TEXT,
        logged_at TIMESTAMPTZ
    );

-- ─── weekly_financials ───
CREATE TABLE IF NOT EXISTS weekly_financials (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            board_revenue DOUBLE PRECISION DEFAULT 0,
            retail_revenue DOUBLE PRECISION DEFAULT 0,
            flex_revenue DOUBLE PRECISION DEFAULT 0,
            catering_revenue DOUBLE PRECISION DEFAULT 0,
            other_revenue DOUBLE PRECISION DEFAULT 0,
            cos_dollars DOUBLE PRECISION DEFAULT 0,
            total_labor_dollars DOUBLE PRECISION DEFAULT 0,
            total_labor_hours DOUBLE PRECISION DEFAULT 0,
            overtime_dollars DOUBLE PRECISION DEFAULT 0,
            direct_expenses DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ, gross_profit DOUBLE PRECISION DEFAULT 0, total_payroll DOUBLE PRECISION DEFAULT 0, tax_fringe DOUBLE PRECISION DEFAULT 0, after_prime_costs DOUBLE PRECISION DEFAULT 0, pace DOUBLE PRECISION DEFAULT 0, non_cont_expenses DOUBLE PRECISION DEFAULT 0, insurance DOUBLE PRECISION DEFAULT 0, profit_fee DOUBLE PRECISION DEFAULT 0, royalties DOUBLE PRECISION DEFAULT 0, net_income DOUBLE PRECISION DEFAULT 0, management_fees DOUBLE PRECISION DEFAULT 0,
            UNIQUE(week_start, department)
        );

-- ─── weekly_flash_targets ───
CREATE TABLE IF NOT EXISTS weekly_flash_targets (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            budget_board_revenue DOUBLE PRECISION DEFAULT 0,
            budget_retail_revenue DOUBLE PRECISION DEFAULT 0,
            budget_flex_revenue DOUBLE PRECISION DEFAULT 0,
            budget_catering_revenue DOUBLE PRECISION DEFAULT 0,
            budget_other_revenue DOUBLE PRECISION DEFAULT 0,
            projection_board_revenue DOUBLE PRECISION DEFAULT 0,
            projection_retail_revenue DOUBLE PRECISION DEFAULT 0,
            projection_flex_revenue DOUBLE PRECISION DEFAULT 0,
            projection_catering_revenue DOUBLE PRECISION DEFAULT 0,
            projection_other_revenue DOUBLE PRECISION DEFAULT 0,
            budget_cos_dollars DOUBLE PRECISION DEFAULT 0,
            projection_cos_dollars DOUBLE PRECISION DEFAULT 0,
            budget_labor_dollars DOUBLE PRECISION DEFAULT 0,
            budget_labor_hours DOUBLE PRECISION DEFAULT 0,
            projection_labor_dollars DOUBLE PRECISION DEFAULT 0,
            projection_labor_hours DOUBLE PRECISION DEFAULT 0,
            budget_overtime_dollars DOUBLE PRECISION DEFAULT 0,
            projection_overtime_dollars DOUBLE PRECISION DEFAULT 0,
            budget_direct_expenses DOUBLE PRECISION DEFAULT 0,
            projection_direct_expenses DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department)
        );

-- ─── weekly_operational ───
CREATE TABLE IF NOT EXISTS weekly_operational (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            students_resident_plan BIGINT DEFAULT 0,
            students_commuter_plan BIGINT DEFAULT 0,
            meals_used_participation_pct DOUBLE PRECISION DEFAULT 0,
            board_plan_billing_days BIGINT DEFAULT 0,
            board_plan_labor_hours DOUBLE PRECISION DEFAULT 0,
            retail_labor_hours DOUBLE PRECISION DEFAULT 0,
            catering_labor_hours DOUBLE PRECISION DEFAULT 0,
            concession_labor_hours DOUBLE PRECISION DEFAULT 0,
            conference_labor_hours DOUBLE PRECISION DEFAULT 0,
            ot_hours_included_above DOUBLE PRECISION DEFAULT 0,
            ot_dollars_paid DOUBLE PRECISION DEFAULT 0,
            temp_hours_included_above DOUBLE PRECISION DEFAULT 0,
            temp_dollars_paid DOUBLE PRECISION DEFAULT 0,
            management_wages DOUBLE PRECISION DEFAULT 0,
            hourly_wages DOUBLE PRECISION DEFAULT 0,
            average_hourly_wage DOUBLE PRECISION DEFAULT 0,
            fee_account_fee DOUBLE PRECISION DEFAULT 0,
            total_inventory DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department)
        );

-- ─── weekly_operational_targets ───
CREATE TABLE IF NOT EXISTS weekly_operational_targets (
            id BIGSERIAL PRIMARY KEY,
            week_start DATE NOT NULL,
            department TEXT NOT NULL,
            budget_students_resident BIGINT DEFAULT 0,
            budget_students_commuter BIGINT DEFAULT 0,
            budget_participation_pct DOUBLE PRECISION DEFAULT 0,
            budget_billing_days BIGINT DEFAULT 0,
            budget_board_labor_hours DOUBLE PRECISION DEFAULT 0,
            budget_retail_labor_hours DOUBLE PRECISION DEFAULT 0,
            budget_catering_labor_hours DOUBLE PRECISION DEFAULT 0,
            budget_concession_labor_hours DOUBLE PRECISION DEFAULT 0,
            budget_conference_labor_hours DOUBLE PRECISION DEFAULT 0,
            budget_ot_hours DOUBLE PRECISION DEFAULT 0,
            budget_ot_dollars DOUBLE PRECISION DEFAULT 0,
            budget_temp_hours DOUBLE PRECISION DEFAULT 0,
            budget_temp_dollars DOUBLE PRECISION DEFAULT 0,
            budget_management_wages DOUBLE PRECISION DEFAULT 0,
            budget_hourly_wages DOUBLE PRECISION DEFAULT 0,
            budget_avg_hourly_wage DOUBLE PRECISION DEFAULT 0,
            budget_fee_account_fee DOUBLE PRECISION DEFAULT 0,
            budget_total_inventory DOUBLE PRECISION DEFAULT 0,
            projection_students_resident BIGINT DEFAULT 0,
            projection_students_commuter BIGINT DEFAULT 0,
            projection_participation_pct DOUBLE PRECISION DEFAULT 0,
            projection_billing_days BIGINT DEFAULT 0,
            projection_board_labor_hours DOUBLE PRECISION DEFAULT 0,
            projection_retail_labor_hours DOUBLE PRECISION DEFAULT 0,
            projection_catering_labor_hours DOUBLE PRECISION DEFAULT 0,
            projection_concession_labor_hours DOUBLE PRECISION DEFAULT 0,
            projection_conference_labor_hours DOUBLE PRECISION DEFAULT 0,
            projection_ot_hours DOUBLE PRECISION DEFAULT 0,
            projection_ot_dollars DOUBLE PRECISION DEFAULT 0,
            projection_temp_hours DOUBLE PRECISION DEFAULT 0,
            projection_temp_dollars DOUBLE PRECISION DEFAULT 0,
            projection_management_wages DOUBLE PRECISION DEFAULT 0,
            projection_hourly_wages DOUBLE PRECISION DEFAULT 0,
            projection_avg_hourly_wage DOUBLE PRECISION DEFAULT 0,
            projection_fee_account_fee DOUBLE PRECISION DEFAULT 0,
            projection_total_inventory DOUBLE PRECISION DEFAULT 0,
            updated_by TEXT,
            updated_at TIMESTAMPTZ,
            UNIQUE(week_start, department)
        );


-- ═══ Foreign keys (added after all tables exist) ═══

DO $$ BEGIN
  ALTER TABLE "catering_event_items" ADD CONSTRAINT "fk_catering_event_items_event_id" FOREIGN KEY (event_id) REFERENCES "catering_events"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "checklist_items" ADD CONSTRAINT "fk_checklist_items_template_id" FOREIGN KEY (template_id) REFERENCES "checklist_templates"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "inventory_counts" ADD CONSTRAINT "fk_inventory_counts_item_id" FOREIGN KEY (item_id) REFERENCES "inventory_items"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "po_items" ADD CONSTRAINT "fk_po_items_po_id" FOREIGN KEY (po_id) REFERENCES "purchase_orders"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "po_items" ADD CONSTRAINT "fk_po_items_item_id" FOREIGN KEY (item_id) REFERENCES "inventory_items"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "safety_checklist_items" ADD CONSTRAINT "fk_safety_checklist_items_checklist_id" FOREIGN KEY (checklist_id) REFERENCES "safety_checklists"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "schedule_shifts" ADD CONSTRAINT "fk_schedule_shifts_employee_id" FOREIGN KEY (employee_id) REFERENCES "employees"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "training_progress" ADD CONSTRAINT "fk_training_progress_employee_id" FOREIGN KEY (employee_id) REFERENCES "employees"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE "training_progress" ADD CONSTRAINT "fk_training_progress_module_id" FOREIGN KEY (module_id) REFERENCES "training_modules"(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
