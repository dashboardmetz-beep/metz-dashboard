"""
Gmail Auto-Import — Fetches PDF attachments from dashboardmetz@gmail.com
and saves them to the imports/ folder for processing.
"""

import os
import base64
import json
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail read-only scope
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = Path(__file__).parent
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
IMPORTS_DIR = BASE_DIR / "imports"


def _get_gmail_service():
    """Authenticate and return a Gmail API service."""
    creds = None

    # Load saved token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or re-auth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save token for future use
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_odyssey_attachments(max_results=10):
    """
    Fetch PDF attachments from NoReplyOdyssey emails.
    Returns list of saved file paths.
    """
    IMPORTS_DIR.mkdir(exist_ok=True)
    service = _get_gmail_service()

    # Search for emails from Odyssey with attachments
    query = "from:NoReplyOdyssey has:attachment"
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    saved_files = []

    for msg_info in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_info["id"]
        ).execute()

        # Get subject and date
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "unknown")
        date_str = headers.get("Date", "")

        # Parse date for filename — strip (TZ) suffix like "(EDT)"
        try:
            import re as _re
            clean_date = _re.sub(r'\s*\([A-Z]{2,5}\)\s*$', '', date_str.strip())
            date_prefix = None
            for fmt in [
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%d %b %Y %H:%M:%S %z",
            ]:
                try:
                    dt = datetime.strptime(clean_date, fmt)
                    date_prefix = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            if not date_prefix:
                # Fallback: use email.utils parser (handles more formats)
                from email.utils import parsedate_to_datetime
                try:
                    dt = parsedate_to_datetime(date_str)
                    date_prefix = dt.strftime("%Y-%m-%d")
                except Exception:
                    date_prefix = datetime.now().strftime("%Y-%m-%d")
        except Exception:
            date_prefix = datetime.now().strftime("%Y-%m-%d")

        # Find attachments
        parts = msg["payload"].get("parts", [])
        for part in parts:
            filename = part.get("filename", "")
            if not filename or not filename.lower().endswith(".pdf"):
                continue

            # Check if already downloaded
            safe_name = "{}__{}".format(date_prefix, filename.replace(" ", "_"))
            save_path = IMPORTS_DIR / safe_name

            if save_path.exists():
                continue  # Skip already downloaded

            # Download attachment
            att_id = part["body"].get("attachmentId")
            if not att_id:
                continue

            att = service.users().messages().attachments().get(
                userId="me", messageId=msg_info["id"], id=att_id
            ).execute()

            data = base64.urlsafe_b64decode(att["data"])
            with open(save_path, "wb") as f:
                f.write(data)

            saved_files.append({
                "path": str(save_path),
                "filename": filename,
                "subject": subject,
                "date": date_prefix,
            })

    return saved_files


def check_new_emails():
    """
    Check for new unread emails from Odyssey and download attachments.
    Returns list of newly saved files.
    """
    IMPORTS_DIR.mkdir(exist_ok=True)
    service = _get_gmail_service()

    # Only unread emails from Odyssey
    query = "from:NoReplyOdyssey has:attachment is:unread"
    results = service.users().messages().list(
        userId="me", q=query, maxResults=20
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    return fetch_odyssey_attachments(max_results=20)


def get_import_status():
    """Get list of already imported files."""
    IMPORTS_DIR.mkdir(exist_ok=True)
    files = sorted(IMPORTS_DIR.glob("*.pdf"), reverse=True)
    return [
        {
            "filename": f.name,
            "size_kb": f.stat().st_size // 1024,
            "imported": f.stat().st_mtime,
        }
        for f in files
    ]


if __name__ == "__main__":
    # First run — will open browser for OAuth consent
    print("Authenticating with Gmail...")
    files = fetch_odyssey_attachments()
    if files:
        print("Downloaded {} file(s):".format(len(files)))
        for f in files:
            print("  - {} ({})".format(f["filename"], f["date"]))
    else:
        print("No new attachments found.")
