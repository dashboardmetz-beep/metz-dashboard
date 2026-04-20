"""
Odyssey PDF Parser — Parses Plan Membership and Transaction Counts PDFs
from CBORD Odyssey PCS and stores data in the database.
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pdfplumber


def _extract_date_from_pdf(text):
    """Extract the 'As of MM/DD/YYYY' date from PDF text."""
    match = re.search(r'As of (\d{2}/\d{2}/\d{4})', text)
    if match:
        return datetime.strptime(match.group(1), "%m/%d/%Y").strftime("%Y-%m-%d")
    # Try date range for transaction counts
    match = re.search(r'(\d{2}/\d{2}/\d{4}) at .* through (\d{2}/\d{2}/\d{4})', text)
    if match:
        return datetime.strptime(match.group(2), "%m/%d/%Y").strftime("%Y-%m-%d")
    return None


def _extract_week_range(text):
    """Extract week start/end from transaction counts PDF."""
    match = re.search(
        r'(\d{2}/\d{2}/\d{4}) at .* through (\d{2}/\d{2}/\d{4})', text
    )
    if match:
        start = datetime.strptime(match.group(1), "%m/%d/%Y").strftime("%Y-%m-%d")
        end = datetime.strptime(match.group(2), "%m/%d/%Y").strftime("%Y-%m-%d")
        return start, end
    return None, None


def parse_plan_membership(pdf_path):
    """
    Parse Plan Membership Summary PDF.
    Returns: {
        'report_date': '2026-03-30',
        'total_plans': 39,
        'total_members': 8636,
        'plans': [
            {'plan_id': 1, 'plan_name': '19 Meal Plan', 'count': 87, 'pct': 1.01},
            ...
        ]
    }
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        tables = page.extract_tables()

    report_date = _extract_date_from_pdf(text)

    plans = []
    if tables:
        for table in tables:
            for row in table:
                if not row or len(row) < 4:
                    continue
                # Skip header rows
                if row[0] and 'Plan ID' in str(row[0]):
                    continue
                if row[0] and 'Count Totals' in str(row[0]):
                    continue
                try:
                    plan_id = int(str(row[0]).strip())
                    plan_name = str(row[1]).strip()
                    count_str = str(row[2]).strip().replace(',', '')
                    count = int(float(count_str))
                    pct = float(str(row[3]).strip())
                    plans.append({
                        'plan_id': plan_id,
                        'plan_name': plan_name,
                        'count': count,
                        'pct': pct,
                    })
                except (ValueError, IndexError):
                    continue

    # Fallback: parse from text if table extraction failed
    if not plans:
        lines = text.split('\n')
        for line in lines:
            match = re.match(
                r'\s*(\d+)\s+(.+?)\s+([\d,]+)\s+([\d.]+)\s*$', line
            )
            if match:
                plans.append({
                    'plan_id': int(match.group(1)),
                    'plan_name': match.group(2).strip(),
                    'count': int(match.group(3).replace(',', '')),
                    'pct': float(match.group(4)),
                })

    total_members = sum(p['count'] for p in plans)

    return {
        'report_date': report_date,
        'total_plans': len(plans),
        'total_members': total_members,
        'plans': plans,
    }


def parse_transaction_counts(pdf_path):
    """
    Parse Weekly Transaction Counts Board PDF.
    Returns: {
        'week_start': '2026-03-23',
        'week_end': '2026-03-30',
        'report_date': '2026-03-30',
        'unit': 'HAMILTON COMMONS UNIT',
        'plans': [
            {'plan_id': 1, 'plan_name': '19 Meal Plan',
             'bfast': 172, 'cbfast': 0, 'brunch': 110,
             'lunch': 247, 'dinner': 304, 'late': 0, 'total': 833},
            ...
        ],
        'period_totals': {
            'bfast': 1271, 'cbfast': 0, 'brunch': 814,
            'lunch': 2308, 'dinner': 2543, 'late': 0, 'total': 6936
        }
    }
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        tables = page.extract_tables()

    week_start, week_end = _extract_week_range(text)
    report_date = _extract_date_from_pdf(text)

    # Extract unit name
    unit = "HAMILTON COMMONS UNIT"
    unit_match = re.search(r'Unit ID:\s*\d+,\s*(.+)', text)
    if unit_match:
        unit = unit_match.group(1).strip()

    plans = []
    period_totals = None

    # Try table extraction first
    if tables:
        for table in tables:
            for row in table:
                if not row or len(row) < 7:
                    continue
                name_col = str(row[0] or '').strip()
                if name_col.startswith('Plan #'):
                    plan_match = re.match(r'Plan #(\d+)\s*-\s*(.+)', name_col)
                    if plan_match:
                        try:
                            vals = []
                            for i in range(1, 7):
                                v = str(row[i] or '0').strip().replace(',', '')
                                v = v.split('\n')[0]
                                vals.append(int(float(v)))
                            total_str = str(row[-1] or '0').strip().replace(',', '')
                            total_str = total_str.split('\n')[0]
                            plans.append({
                                'plan_id': int(plan_match.group(1)),
                                'plan_name': plan_match.group(2).strip(),
                                'bfast': vals[0], 'cbfast': vals[1],
                                'brunch': vals[2], 'lunch': vals[3],
                                'dinner': vals[4], 'late': vals[5],
                                'total': int(float(total_str)),
                            })
                        except (ValueError, IndexError):
                            continue

    # Fallback: parse from raw text lines
    if not plans:
        lines = text.split('\n')
        for line in lines:
            m = re.match(
                r'\s*Plan\s*#(\d+)\s*-\s*(.+?)\s+'
                r'([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)',
                line,
            )
            if m:
                def _int(s):
                    return int(s.replace(',', ''))
                plans.append({
                    'plan_id': int(m.group(1)),
                    'plan_name': m.group(2).strip(),
                    'bfast': _int(m.group(3)), 'cbfast': _int(m.group(4)),
                    'brunch': _int(m.group(5)), 'lunch': _int(m.group(6)),
                    'dinner': _int(m.group(7)), 'late': _int(m.group(8)),
                    'total': _int(m.group(9)),
                })
            # Period totals line
            if 'Period Totals' in line:
                nums = re.findall(r'[\d,]+', line.split('Period Totals')[1])
                if len(nums) >= 7:
                    nums = [int(n.replace(',', '')) for n in nums[:7]]
                    period_totals = {
                        'bfast': nums[0], 'cbfast': nums[1],
                        'brunch': nums[2], 'lunch': nums[3],
                        'dinner': nums[4], 'late': nums[5],
                        'total': nums[6],
                    }

    # Second fallback: match number blocks per plan from extracted text
    if not plans:
        # Find plan lines and their associated numbers
        plan_blocks = re.findall(
            r'Plan #(\d+)\s*-\s*(.+?)(?=Plan #|\nPeriod Totals|\Z)',
            text, re.DOTALL
        )
        for pid, block in plan_blocks:
            nums = re.findall(r'[\d,]+\.?\d*', block)
            # Filter to integers, take first row of numbers (counts, not decimals)
            int_nums = []
            for n in nums:
                try:
                    int_nums.append(int(n.replace(',', '').split('.')[0]))
                except ValueError:
                    continue
            if len(int_nums) >= 7:
                name = block.split('\n')[0].strip()
                plans.append({
                    'plan_id': int(pid),
                    'plan_name': name,
                    'bfast': int_nums[0], 'cbfast': int_nums[1],
                    'brunch': int_nums[2], 'lunch': int_nums[3],
                    'dinner': int_nums[4], 'late': int_nums[5],
                    'total': int_nums[6],
                })

    # Calculate totals from plans if not extracted
    if not period_totals and plans:
        period_totals = {
            'bfast': sum(p['bfast'] for p in plans),
            'cbfast': sum(p['cbfast'] for p in plans),
            'brunch': sum(p['brunch'] for p in plans),
            'lunch': sum(p['lunch'] for p in plans),
            'dinner': sum(p['dinner'] for p in plans),
            'late': sum(p['late'] for p in plans),
            'total': sum(p['total'] for p in plans),
        }

    return {
        'week_start': week_start,
        'week_end': week_end,
        'report_date': report_date,
        'unit': unit,
        'plans': plans,
        'period_totals': period_totals or {},
    }


def parse_tender_totals(pdf_path):
    """
    Parse Tender Totals by Terminal - On Campus Daily PDF.
    Returns: {
        'report_date': '2026-04-14',
        'service_category': 'Hamilton Commons',
        'terminals': [
            {'name': 'Hamilton 04', 'periods': [
                {'period': 'Breakfast', 'board_count': 168, 'points_count': 0,
                 'bonpts_count': 0, 'board_total': 168.00, ...},
                ...
            ]},
            ...
        ],
        'grand_totals': {...},
    }
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

    # Extract report date from "MM/DD/YYYY at ... through MM/DD/YYYY"
    # The report_date is the START date (the day the data is for)
    report_date = None
    m = re.search(r'(\d{2}/\d{2}/\d{4}) at .* through \d{2}/\d{2}/\d{4}', text)
    if m:
        report_date = datetime.strptime(m.group(1), "%m/%d/%Y").strftime("%Y-%m-%d")

    # Service category
    service_cat = "Hamilton Commons"
    m = re.search(r'Service Category:\s*(.+)', text)
    if m:
        service_cat = m.group(1).strip()

    # Parse terminals by splitting on "Terminal:" markers
    # Each terminal section has: header, period rows, Terminal Totals row
    # Periods can be: Breakfast, Lunch, Dinner, Late, Brunch, CBfast

    _VALID_PERIODS = ["Breakfast", "Brunch", "CBfast", "Lunch", "Dinner", "Late"]

    terminals = []
    # Find all terminals
    term_pattern = re.compile(r'Terminal:\s*([^\n]+?)(?:\s*\(\d+\))?\s*\n')
    term_matches = list(term_pattern.finditer(text))

    # Get positions where each terminal section starts
    positions = [(m.group(1).strip(), m.end()) for m in term_matches]
    positions.append(("__END__", len(text)))

    for i in range(len(positions) - 1):
        term_name, start = positions[i]
        end = positions[i + 1][1]
        section = text[start:end]

        # Clean terminal name (strip count suffix)
        term_name = re.sub(r'\s*\(\d+\)\s*$', '', term_name).strip()

        # Parse lines in this section, looking for period rows
        periods = []
        lines = [l.strip() for l in section.split('\n') if l.strip()]
        for line in lines:
            # Check if line starts with a known service period
            for period in _VALID_PERIODS:
                if line.startswith(period + ' ') or line == period:
                    # Extract 3 numbers after the period name
                    rest = line[len(period):].strip()
                    # First 3 numbers are counts: board, points, bonpts
                    nums = re.findall(r'-?[\d,]+\.?\d*', rest)
                    if len(nums) >= 3:
                        def _to_num(s):
                            try:
                                return float(s.replace(',', ''))
                            except ValueError:
                                return 0
                        periods.append({
                            "period": period,
                            "board_count": int(_to_num(nums[0])),
                            "points_count": int(_to_num(nums[1])),
                            "bonpts_count": int(_to_num(nums[2])),
                        })
                    break

        if periods:
            terminals.append({
                "name": term_name,
                "periods": periods,
            })

    return {
        "report_date": report_date,
        "service_category": service_cat,
        "terminals": terminals,
    }


def save_tender_totals(conn, data, filename):
    """Save parsed tender totals to database."""
    init_odyssey_tables(conn)

    existing = conn.execute(
        "SELECT id FROM odyssey_import_log WHERE filename = ?",
        (filename,)
    ).fetchone()
    if existing:
        return 0

    count = 0
    for term in data.get("terminals", []):
        for period in term.get("periods", []):
            conn.execute(
                """INSERT OR REPLACE INTO odyssey_tender_totals
                   (report_date, terminal, service_period,
                    board_count, points_count, bonpts_count,
                    board_total, points_total, bonpts_total,
                    board_avg, points_avg, bonpts_avg)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["report_date"], term["name"], period["period"],
                 period["board_count"], period["points_count"],
                 period["bonpts_count"],
                 0, 0, 0, 0, 0, 0),  # totals/avgs optional for now
            )
            count += 1

    conn.execute(
        """INSERT OR IGNORE INTO odyssey_import_log
           (filename, report_type, report_date, records_imported)
           VALUES (?, ?, ?, ?)""",
        (filename, 'tender_totals', data['report_date'], count),
    )
    conn.commit()
    return count


# ─── Database Storage ───

def init_odyssey_tables(conn):
    """Create tables for Odyssey data if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS odyssey_plan_membership (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            plan_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            member_count INTEGER DEFAULT 0,
            percentage REAL DEFAULT 0.0,
            imported_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(report_date, plan_id)
        );

        CREATE TABLE IF NOT EXISTS odyssey_transaction_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL,
            week_end TEXT NOT NULL,
            unit TEXT NOT NULL,
            plan_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            bfast INTEGER DEFAULT 0,
            cbfast INTEGER DEFAULT 0,
            brunch INTEGER DEFAULT 0,
            lunch INTEGER DEFAULT 0,
            dinner INTEGER DEFAULT 0,
            late INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            imported_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(week_start, plan_id)
        );

        CREATE TABLE IF NOT EXISTS odyssey_tender_totals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            terminal TEXT NOT NULL,
            service_period TEXT NOT NULL,
            board_count INTEGER DEFAULT 0,
            points_count INTEGER DEFAULT 0,
            bonpts_count INTEGER DEFAULT 0,
            board_total REAL DEFAULT 0.0,
            points_total REAL DEFAULT 0.0,
            bonpts_total REAL DEFAULT 0.0,
            board_avg REAL DEFAULT 0.0,
            points_avg REAL DEFAULT 0.0,
            bonpts_avg REAL DEFAULT 0.0,
            imported_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(report_date, terminal, service_period)
        );

        CREATE TABLE IF NOT EXISTS odyssey_import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            report_type TEXT NOT NULL,
            report_date TEXT,
            records_imported INTEGER DEFAULT 0,
            imported_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(filename)
        );
    """)
    conn.commit()


def save_plan_membership(conn, data, filename):
    """Save parsed plan membership data to database."""
    init_odyssey_tables(conn)

    # Check if already imported
    existing = conn.execute(
        "SELECT id FROM odyssey_import_log WHERE filename = ?",
        (filename,)
    ).fetchone()
    if existing:
        return 0  # Already imported

    count = 0
    for plan in data['plans']:
        conn.execute(
            """INSERT OR REPLACE INTO odyssey_plan_membership
               (report_date, plan_id, plan_name, member_count, percentage)
               VALUES (?, ?, ?, ?, ?)""",
            (data['report_date'], plan['plan_id'],
             plan['plan_name'], plan['count'], plan['pct']),
        )
        count += 1

    conn.execute(
        """INSERT OR IGNORE INTO odyssey_import_log
           (filename, report_type, report_date, records_imported)
           VALUES (?, ?, ?, ?)""",
        (filename, 'plan_membership', data['report_date'], count),
    )
    conn.commit()
    return count


def save_transaction_counts(conn, data, filename):
    """Save parsed transaction counts data to database."""
    init_odyssey_tables(conn)

    existing = conn.execute(
        "SELECT id FROM odyssey_import_log WHERE filename = ?",
        (filename,)
    ).fetchone()
    if existing:
        return 0

    count = 0
    for plan in data['plans']:
        conn.execute(
            """INSERT OR REPLACE INTO odyssey_transaction_counts
               (week_start, week_end, unit, plan_id, plan_name,
                bfast, cbfast, brunch, lunch, dinner, late, total)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data['week_start'], data['week_end'], data['unit'],
             plan['plan_id'], plan['plan_name'],
             plan['bfast'], plan['cbfast'], plan['brunch'],
             plan['lunch'], plan['dinner'], plan['late'], plan['total']),
        )
        count += 1

    conn.execute(
        """INSERT OR IGNORE INTO odyssey_import_log
           (filename, report_type, report_date, records_imported)
           VALUES (?, ?, ?, ?)""",
        (filename, 'transaction_counts', data['report_date'], count),
    )
    conn.commit()
    return count


def auto_import_all(conn, imports_dir=None):
    """
    Scan imports/ folder, parse all PDFs, and save to database.
    Returns summary of what was imported.
    """
    if imports_dir is None:
        imports_dir = Path(__file__).parent / "imports"

    imports_dir = Path(imports_dir)
    if not imports_dir.exists():
        return []

    init_odyssey_tables(conn)
    results = []

    for pdf_file in sorted(imports_dir.glob("*.pdf")):
        filename = pdf_file.name

        # Skip already imported
        existing = conn.execute(
            "SELECT id FROM odyssey_import_log WHERE filename = ?",
            (filename,)
        ).fetchone()
        if existing:
            continue

        try:
            if 'Plan_Membership' in filename or 'Plan Membership' in filename:
                data = parse_plan_membership(str(pdf_file))
                count = save_plan_membership(conn, data, filename)
                results.append({
                    'filename': filename,
                    'type': 'Plan Membership',
                    'date': data['report_date'],
                    'records': count,
                })
            elif 'Transaction_Counts' in filename or 'Transaction Counts' in filename:
                data = parse_transaction_counts(str(pdf_file))
                count = save_transaction_counts(conn, data, filename)
                results.append({
                    'filename': filename,
                    'type': 'Transaction Counts',
                    'date': data.get('week_end', data.get('report_date')),
                    'records': count,
                })
            elif 'Tender_Totals' in filename or 'Tender Totals' in filename:
                data = parse_tender_totals(str(pdf_file))
                count = save_tender_totals(conn, data, filename)
                results.append({
                    'filename': filename,
                    'type': 'Tender Totals',
                    'date': data.get('report_date'),
                    'records': count,
                })
        except Exception as e:
            results.append({
                'filename': filename,
                'type': 'error',
                'date': None,
                'records': 0,
                'error': str(e),
            })

    return results


if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect("budget.db")
    conn.row_factory = sqlite3.Row

    # Test parsing
    imports = Path(__file__).parent / "imports"
    for pdf in imports.glob("*.pdf"):
        print("\n--- {} ---".format(pdf.name))
        if 'Membership' in pdf.name:
            data = parse_plan_membership(str(pdf))
            print("Date: {}".format(data['report_date']))
            print("Total members: {}".format(data['total_members']))
            print("Plans: {}".format(len(data['plans'])))
            for p in data['plans'][:5]:
                print("  #{}: {} → {}".format(p['plan_id'], p['plan_name'], p['count']))
        elif 'Transaction' in pdf.name:
            data = parse_transaction_counts(str(pdf))
            print("Week: {} to {}".format(data['week_start'], data['week_end']))
            print("Unit: {}".format(data['unit']))
            print("Plans: {}".format(len(data['plans'])))
            for p in data['plans'][:5]:
                print("  #{}: {} → {} total".format(
                    p['plan_id'], p['plan_name'], p['total']))
            if data['period_totals']:
                print("Period total: {}".format(data['period_totals']['total']))

    # Import to DB
    results = auto_import_all(conn)
    print("\n--- Import Results ---")
    for r in results:
        print("  {} → {} records ({})".format(r['filename'], r['records'], r['type']))
    if not results:
        print("  No new files to import.")
