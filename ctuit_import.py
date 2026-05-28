"""
CTUIT auto-import — pulls Ops Statement PDFs from Gmail / imports/ folder,
parses them, and writes into weekly_financials so the dashboard updates automatically.
"""

import io
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import db
from config import CTUIT_REPORT_GROUP_MAP

BASE_DIR = Path(__file__).parent
IMPORTS_DIR = BASE_DIR / "imports"

# Filename hints for department when Report Group line is missing
_FILENAME_DEPT_HINTS = [
    ("consolidat", "Consolidated"),
    ("qdoba", "Qdoba"),
    ("starbucks", "Starbucks"),
    ("board", "Board & Catering"),
    ("catering", "Board & Catering"),
    ("hamilton", "Board & Catering"),
    ("retail", "Retail & Mac's Grill"),
    ("mac", "Retail & Mac's Grill"),
]


def init_ctuit_tables(conn):
    """Ensure import log table exists."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ctuit_import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            department TEXT,
            week_start DATE,
            records INTEGER DEFAULT 0,
            status TEXT,
            message TEXT,
            imported_at DATETIME,
            imported_by TEXT
        )
        """
    )
    conn.commit()


def fetch_last_ctuit_sync(conn):
    """Return metadata for the most recent successful CTUIT import."""
    init_ctuit_tables(conn)
    row = conn.execute(
        """
        SELECT imported_at, department, week_start, records, filename
        FROM ctuit_import_log
        WHERE status = 'success'
        ORDER BY imported_at DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None


def _already_imported(conn, filename):
    row = conn.execute(
        "SELECT id FROM ctuit_import_log WHERE filename = ?", (filename,)
    ).fetchone()
    return row is not None


def _log_import(conn, filename, department, week_start, records, status, message, username):
    conn.execute(
        """
        INSERT OR REPLACE INTO ctuit_import_log
        (filename, department, week_start, records, status, message, imported_at, imported_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            department,
            week_start,
            records,
            status,
            message,
            datetime.now().isoformat(),
            username,
        ),
    )
    conn.commit()


def parse_week_start_from_result(result):
    """Derive fiscal week_start (Sunday) from CTUIT Date Range header."""
    date_range = (result or {}).get("date_range", "") or ""
    match = re.search(r"to\s+(\d{1,2}/\d{1,2}/\d{4})", date_range, re.IGNORECASE)
    if match:
        try:
            end = datetime.strptime(match.group(1), "%m/%d/%Y").date()
            return db.get_week_start(end).isoformat()
        except ValueError:
            pass
    return db.get_week_start(date.today() - timedelta(weeks=1)).isoformat()


def detect_department_from_filename(filename):
    """Guess department from attachment filename."""
    name = (filename or "").lower()
    for hint, dept in _FILENAME_DEPT_HINTS:
        if hint in name:
            return dept
    return None


def detect_department_from_text(text):
    """Match Report Group line to a department."""
    report_group = ""
    for line in (text or "").split("\n"):
        if "Report Group:" in line:
            report_group = line.split("Report Group:")[-1].strip()
            break
    if not report_group:
        return None
    rg_lower = report_group.lower()
    for keyword, dept in CTUIT_REPORT_GROUP_MAP.items():
        if keyword in rg_lower:
            return dept
    return None


def _looks_like_odyssey_pdf(filename):
    name = (filename or "").lower()
    return any(
        k in name
        for k in (
            "odyssey",
            "plan_membership",
            "plan membership",
            "transaction_counts",
            "transaction counts",
            "tender_totals",
            "tender totals",
        )
    )


def is_ctuit_ops_pdf(path):
    """Return True if PDF appears to be a CTUIT / Compeat Ops Statement."""
    path = Path(path)
    if _looks_like_odyssey_pdf(path.name):
        return False
    name = path.name.lower()
    if any(k in name for k in ("ctuit", "compeat", "ops_statement", "ops statement")):
        return True
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                return False
            text = (pdf.pages[0].extract_text() or "")[:3000]
        return (
            "Ops Statement" in text
            or "Compeat" in text
            or "Report Group:" in text
        )
    except Exception:
        return False


def parse_ctuit_pdf_file(pdf_path):
    """Parse CTUIT PDF using the same logic as Weekly Budget import."""
    from views.weekly_entry import _parse_ctuit_pdf

    with open(pdf_path, "rb") as fh:
        data = fh.read()
    return _parse_ctuit_pdf(io.BytesIO(data))


def import_ctuit_pdf(conn, pdf_path, username, department=None, week_start=None):
    """
    Parse one CTUIT PDF and write to the database.
    Returns a result dict with success, department, week_start, records, error.
    """
    init_ctuit_tables(conn)
    path = Path(pdf_path)
    filename = path.name

    if _already_imported(conn, filename):
        return {
            "success": False,
            "skipped": True,
            "filename": filename,
            "records": 0,
        }

    if not is_ctuit_ops_pdf(path):
        return {
            "success": False,
            "skipped": True,
            "filename": filename,
            "records": 0,
            "error": "Not a CTUIT Ops Statement",
        }

    try:
        result = parse_ctuit_pdf_file(str(path))
    except Exception as exc:
        _log_import(conn, filename, None, None, 0, "error", str(exc), username)
        return {"success": False, "filename": filename, "error": str(exc), "records": 0}

    if not result:
        _log_import(conn, filename, None, None, 0, "error", "Parse failed", username)
        return {
            "success": False,
            "filename": filename,
            "error": "Could not parse CTUIT PDF",
            "records": 0,
        }

    parsed_values = result.get("parsed_values") or {}
    detail_items = result.get("detail_items") or []
    budget_values = result.get("budget_values") or {}

    if not parsed_values and not detail_items:
        _log_import(conn, filename, None, None, 0, "error", "No values", username)
        return {
            "success": False,
            "filename": filename,
            "error": "No importable values in PDF",
            "records": 0,
        }

    dept = (
        department
        or result.get("department")
        or detect_department_from_filename(filename)
    )
    if not dept:
        # Sniff report group from raw file text
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages[:2])
        dept = detect_department_from_text(text)

    if not dept:
        _log_import(
            conn, filename, None, None, 0, "error", "Unknown department", username
        )
        return {
            "success": False,
            "filename": filename,
            "error": "Could not detect department from PDF",
            "records": 0,
        }

    ws = week_start or parse_week_start_from_result(result)
    user_stub = {"username": username}
    fin = db.fetch_weekly_financials(conn, ws, dept)

    try:
        from views.weekly_entry import _apply_ctuit_import

        _apply_ctuit_import(
            conn,
            user_stub,
            ws,
            dept,
            fin,
            parsed_values,
            detail_items,
            budget_values,
        )
        records = len(parsed_values) + len(
            [d for d in detail_items if d and len(d) > 2 and d[2]]
        )
    except Exception as exc:
        _log_import(conn, filename, dept, ws, 0, "error", str(exc), username)
        return {"success": False, "filename": filename, "error": str(exc), "records": 0}

    _log_import(conn, filename, dept, ws, records, "success", None, username)
    try:
        db.add_email_import_log(
            conn,
            "CTUIT auto-import: {}".format(filename),
            "auto",
            datetime.now().isoformat(),
            "ctuit",
            "success",
            records,
            "Department {} week {}".format(dept, ws),
            username,
        )
    except Exception:
        pass

    return {
        "success": True,
        "filename": filename,
        "department": dept,
        "week_start": ws,
        "records": records,
        "report_group": result.get("report_group"),
        "date_range": result.get("date_range"),
    }


def auto_import_ctuit(conn, username, imports_dir=None, download_from_gmail=True):
    """
    Download new CTUIT PDFs from Gmail (if configured) and import all new files
    from the imports/ folder.
    """
    init_ctuit_tables(conn)
    folder = Path(imports_dir) if imports_dir else IMPORTS_DIR
    folder.mkdir(exist_ok=True)

    if download_from_gmail:
        try:
            from gmail_import import check_new_ctuit_emails

            check_new_ctuit_emails()
        except Exception:
            pass

    results = []
    for pdf in sorted(folder.glob("*.pdf")):
        if not is_ctuit_ops_pdf(pdf):
            continue
        results.append(import_ctuit_pdf(conn, str(pdf), username))

    return results


def sync_ctuit_to_dashboard(conn, username):
    """Manual sync entry point — same as auto_import but always runs import pass."""
    return auto_import_ctuit(conn, username, download_from_gmail=True)
