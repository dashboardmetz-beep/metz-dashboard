"""
Email attachment parsers for different import types.
Each parser extracts structured data from email attachments (CSV/Excel).

Supported types:
  - usfoods_invoice: US Foods invoice totals
  - inventory: Weekly inventory reports
  - ctuit: CTUIT operational statements
  - odyssey: Odyssey communication / meal plan data
"""

import io
import pandas as pd


def parse_email(email, email_type):
    """
    Route email to the appropriate parser based on type.
    Returns: {"success": bool, "records": int, "data": list, "error": str}
    """
    parsers = {
        "usfoods_invoice": parse_usfoods_invoice,
        "inventory": parse_inventory_report,
        "ctuit": parse_ctuit_statement,
        "odyssey": parse_odyssey_data,
    }

    parser = parsers.get(email_type)
    if not parser:
        return {"success": False, "records": 0, "error": "Unknown import type: {}".format(email_type)}

    try:
        return parser(email)
    except Exception as e:
        return {"success": False, "records": 0, "error": str(e)}


def _get_attachment_df(email):
    """Extract a DataFrame from the first CSV/Excel attachment."""
    attachments = email.get("attachments", [])
    if not attachments:
        return None

    for att in attachments:
        name = (att.get("name", "") or "").lower()
        content_bytes = att.get("contentBytes")
        if not content_bytes:
            continue

        import base64
        raw = base64.b64decode(content_bytes)

        if name.endswith(".csv"):
            return pd.read_csv(io.BytesIO(raw))
        elif name.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw))

    return None


# ═══════════════════════════════════════════════════════
# US FOODS INVOICE PARSER
# ═══════════════════════════════════════════════════════


def parse_usfoods_invoice(email):
    """
    Parse US Foods invoice attachment.
    Expected columns: date, department, invoice_total, description
    Fallback: parse from email body if no attachment.
    """
    df = _get_attachment_df(email)

    if df is not None:
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": str(row.get("date", "")),
                "department": str(row.get("department", "")),
                "invoice_total": float(row.get("invoice_total", 0) or 0),
                "description": str(row.get("description", "")),
            })
        return {"success": True, "records": len(records), "data": records}

    # Fallback: could parse email body for invoice totals
    return {"success": False, "records": 0,
            "error": "No parseable attachment found in US Foods email."}


# ═══════════════════════════════════════════════════════
# INVENTORY REPORT PARSER
# ═══════════════════════════════════════════════════════


def parse_inventory_report(email):
    """
    Parse inventory report attachment.
    Expected columns: week_start, department, inventory_start, inventory_end
    """
    df = _get_attachment_df(email)

    if df is not None:
        records = []
        for _, row in df.iterrows():
            records.append({
                "week_start": str(row.get("week_start", "")),
                "department": str(row.get("department", "")),
                "inventory_start": float(row.get("inventory_start", 0) or 0),
                "inventory_end": float(row.get("inventory_end", 0) or 0),
            })
        return {"success": True, "records": len(records), "data": records}

    return {"success": False, "records": 0,
            "error": "No parseable attachment found in inventory email."}


# ═══════════════════════════════════════════════════════
# CTUIT STATEMENT PARSER
# ═══════════════════════════════════════════════════════


def parse_ctuit_statement(email):
    """
    Parse CTUIT operational statement attachment.
    Expected columns will vary; this parser extracts what's available.
    """
    df = _get_attachment_df(email)

    if df is not None:
        records = df.to_dict(orient="records")
        return {"success": True, "records": len(records), "data": records}

    return {"success": False, "records": 0,
            "error": "No parseable attachment found in CTUIT email."}


# ═══════════════════════════════════════════════════════
# ODYSSEY PARSER
# ═══════════════════════════════════════════════════════


def parse_odyssey_data(email):
    """
    Parse Odyssey communication / meal plan data attachment.
    Expected columns: entry_date, plan_type, enrolled_count, meals_used
    """
    df = _get_attachment_df(email)

    if df is not None:
        records = []
        for _, row in df.iterrows():
            records.append({
                "entry_date": str(row.get("entry_date", "")),
                "plan_type": str(row.get("plan_type", "")),
                "enrolled_count": int(row.get("enrolled_count", 0) or 0),
                "meals_used": int(row.get("meals_used", 0) or 0),
            })
        return {"success": True, "records": len(records), "data": records}

    return {"success": False, "records": 0,
            "error": "No parseable attachment found in Odyssey email."}
