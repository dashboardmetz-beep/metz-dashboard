"""
ADP API client for syncing labor schedule data.
Fetches scheduled shifts and actual time cards from ADP Workforce Now.

Required environment variables:
  ADP_API_BASE_URL    (e.g., https://api.adp.com)
  ADP_CLIENT_ID
  ADP_CLIENT_SECRET
  ADP_CERT_PATH       (optional, for mutual TLS)
"""

import os
from datetime import datetime


def _get_adp_token():
    """Acquire an OAuth2 access token from ADP."""
    import requests

    base_url = os.environ.get("ADP_API_BASE_URL", "https://api.adp.com")
    client_id = os.environ.get("ADP_CLIENT_ID", "")
    client_secret = os.environ.get("ADP_CLIENT_SECRET", "")
    cert_path = os.environ.get("ADP_CERT_PATH")

    if not all([client_id, client_secret]):
        raise ValueError("ADP API credentials not configured.")

    token_url = "{}/auth/oauth/v2/token".format(base_url)

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    kwargs = {}
    if cert_path and os.path.exists(cert_path):
        kwargs["cert"] = cert_path

    response = requests.post(token_url, data=data, **kwargs)
    response.raise_for_status()

    result = response.json()
    if "access_token" in result:
        return result["access_token"]
    else:
        raise ValueError("Failed to acquire ADP token: {}".format(result))


def sync_schedules(conn, start_date, end_date):
    """
    Sync labor schedules from ADP for the given date range.
    Updates the labor_schedule table in the database.

    Returns: {"success": bool, "records": int, "error": str}
    """
    try:
        import requests
        from config import DEPARTMENTS

        token = _get_adp_token()
        base_url = os.environ.get("ADP_API_BASE_URL", "https://api.adp.com")

        headers = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json",
        }

        # Fetch scheduled shifts
        schedule_url = "{}/time/v2/workers/schedules".format(base_url)
        params = {
            "startDate": start_date,
            "endDate": end_date,
        }

        cert_path = os.environ.get("ADP_CERT_PATH")
        kwargs = {}
        if cert_path and os.path.exists(cert_path):
            kwargs["cert"] = cert_path

        response = requests.get(schedule_url, headers=headers, params=params, **kwargs)
        response.raise_for_status()

        schedule_data = response.json()

        # Fetch actual time cards
        timecard_url = "{}/time/v2/workers/time-cards".format(base_url)
        tc_response = requests.get(timecard_url, headers=headers, params=params, **kwargs)
        tc_response.raise_for_status()
        timecard_data = tc_response.json()

        # Process and aggregate by department and date
        # NOTE: The actual structure depends on your ADP configuration.
        # This is a template that should be adapted to your specific ADP setup.
        records = _process_adp_data(conn, schedule_data, timecard_data)

        return {"success": True, "records": records}

    except Exception as e:
        return {"success": False, "records": 0, "error": str(e)}


def _process_adp_data(conn, schedule_data, timecard_data):
    """
    Process ADP API responses and insert/update labor_schedule records.
    This is a template - adapt the field mapping to your ADP configuration.
    """
    import db

    records = 0

    # Template: process schedule entries
    # ADP response format varies by configuration.
    # Typically: scheduleEntries -> [{ worker, scheduledShifts: [{ date, hours }] }]
    schedule_entries = schedule_data.get("scheduleEntries", [])
    timecard_entries = timecard_data.get("timeCards", [])

    # Build a lookup: (date, department) -> scheduled_hours
    scheduled = {}
    for entry in schedule_entries:
        dept = entry.get("department", "")
        for shift in entry.get("shifts", []):
            d = shift.get("date", "")
            hrs = float(shift.get("hours", 0) or 0)
            key = (d, dept)
            scheduled[key] = scheduled.get(key, 0) + hrs

    # Build a lookup: (date, department) -> actual_hours
    actuals = {}
    for entry in timecard_entries:
        dept = entry.get("department", "")
        d = entry.get("date", "")
        hrs = float(entry.get("hours", 0) or 0)
        key = (d, dept)
        actuals[key] = actuals.get(key, 0) + hrs

    # Merge and save
    all_keys = set(list(scheduled.keys()) + list(actuals.keys()))
    for (d, dept) in all_keys:
        sched_hrs = scheduled.get((d, dept), 0)
        actual_hrs = actuals.get((d, dept), 0)
        db.upsert_labor_schedule(conn, d, dept, sched_hrs, actual_hrs, "adp_api")
        records += 1

    return records
