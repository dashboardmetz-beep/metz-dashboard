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

# Gmail read + send scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

BASE_DIR = Path(__file__).parent
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
IMPORTS_DIR = BASE_DIR / "imports"


def _load_token_from_secrets():
    """Try to load token JSON from Streamlit secrets (for cloud deployment)."""
    try:
        import streamlit as st
        if "gmail_token" in st.secrets:
            return json.loads(st.secrets["gmail_token"])
    except Exception:
        pass
    return None


def _save_token(creds):
    """Save token to local file (only when running locally — cloud is read-only)."""
    try:
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    except Exception:
        # On cloud (read-only filesystem), token persists via st.secrets only
        pass


def _get_gmail_service():
    """Authenticate and return a Gmail API service.
    Tries (in order):
      1. Streamlit secrets (cloud deployment)
      2. Local token.json file
      3. Fresh OAuth flow (only works locally)
    """
    creds = None
    token_data = _load_token_from_secrets()

    if token_data:
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                _save_token(creds)
            except Exception as e:
                raise RuntimeError(
                    "Gmail token expired and refresh failed. "
                    "Re-authenticate locally and update Streamlit secret 'gmail_token'. "
                    "Error: {}".format(e)
                )
        elif CREDS_FILE.exists():
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
            _save_token(creds)
        else:
            raise RuntimeError(
                "No Gmail credentials available. "
                "Set 'gmail_token' in Streamlit secrets, or place credentials.json locally."
            )

    return build("gmail", "v1", credentials=creds)


def get_token_status():
    """Inspect token.json + try to refresh.

    Returns dict with: state ('linked', 'expired', 'not_linked', 'no_creds'),
    account (best-effort email or client_id snippet), expiry, error (if any).
    """
    info = {
        "state": "not_linked",
        "account": None,
        "expiry": None,
        "scopes": [],
        "error": None,
    }

    if not CREDS_FILE.exists():
        info["state"] = "no_creds"
        info["error"] = "credentials.json missing — OAuth app config not found."
        return info

    token_data = _load_token_from_secrets()
    creds = None
    if token_data:
        try:
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            info["error"] = "Could not load token from secrets: {}".format(e)
    elif TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            info["error"] = "Could not read token.json: {}".format(e)

    if creds is None:
        return info  # state stays "not_linked"

    info["scopes"] = list(getattr(creds, "scopes", []) or [])
    info["expiry"] = creds.expiry.isoformat() if creds.expiry else None
    cid = getattr(creds, "client_id", "") or ""
    info["account"] = cid[:30] + "..." if cid else None

    if creds.valid:
        info["state"] = "linked"
        return info

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            info["state"] = "linked"
            info["expiry"] = creds.expiry.isoformat() if creds.expiry else None
            return info
        except Exception as e:
            info["state"] = "expired"
            info["error"] = "Refresh failed: {}".format(str(e)[:200])
            return info

    info["state"] = "expired"
    info["error"] = "Token invalid and no refresh_token available."
    return info


def force_reauth():
    """Wipe the local token and run a fresh OAuth flow.

    Opens a browser tab for the user to sign in. Blocks until they approve.
    Returns dict: {ok: bool, account: str|None, error: str|None}.

    Only works when the app is running locally (the OAuth callback hits
    localhost). On hosted Streamlit Cloud this raises.
    """
    if not CREDS_FILE.exists():
        return {
            "ok": False,
            "account": None,
            "error": "credentials.json missing — cannot start OAuth flow.",
        }

    # Delete stale token first so the flow always prompts.
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
    except Exception:
        pass

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
        creds = flow.run_local_server(
            port=0,
            prompt="consent",
            authorization_prompt_message="",
            success_message="Gmail reconnected. You can close this tab and return to the app.",
            open_browser=True,
        )
        _save_token(creds)
        # Best-effort account email lookup
        account_email = None
        try:
            service = build("gmail", "v1", credentials=creds)
            profile = service.users().getProfile(userId="me").execute()
            account_email = profile.get("emailAddress")
        except Exception:
            pass
        return {"ok": True, "account": account_email, "error": None}
    except Exception as e:
        return {"ok": False, "account": None, "error": str(e)[:300]}


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


# ─── CTUIT / Compeat Ops Statement ─────────────────────────────────

CTUIT_GMAIL_QUERY = (
    "(from:ctuit OR from:compeat OR subject:ctuit OR subject:\"ops statement\") "
    "has:attachment filename:pdf"
)


def _download_pdf_attachments(service, messages, prefix="ctuit"):
    """Download PDF attachments from a list of Gmail message refs."""
    saved_files = []

    for msg_info in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_info["id"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "unknown")
        date_str = headers.get("Date", "")

        try:
            import re as _re
            from email.utils import parsedate_to_datetime

            clean_date = _re.sub(r"\s*\([A-Z]{2,5}\)\s*$", "", date_str.strip())
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
                try:
                    dt = parsedate_to_datetime(date_str)
                    date_prefix = dt.strftime("%Y-%m-%d")
                except Exception:
                    date_prefix = datetime.now().strftime("%Y-%m-%d")
        except Exception:
            date_prefix = datetime.now().strftime("%Y-%m-%d")

        parts = msg["payload"].get("parts", [])
        for part in parts:
            filename = part.get("filename", "")
            if not filename or not filename.lower().endswith(".pdf"):
                continue

            safe_name = "{}__{}__{}".format(
                prefix, date_prefix, filename.replace(" ", "_")
            )
            save_path = IMPORTS_DIR / safe_name

            if save_path.exists():
                continue

            att_id = part["body"].get("attachmentId")
            if not att_id:
                continue

            att = service.users().messages().attachments().get(
                userId="me", messageId=msg_info["id"], id=att_id
            ).execute()

            data = base64.urlsafe_b64decode(att["data"])
            with open(save_path, "wb") as fh:
                fh.write(data)

            saved_files.append({
                "path": str(save_path),
                "filename": filename,
                "subject": subject,
                "date": date_prefix,
            })

    return saved_files


def fetch_ctuit_attachments(max_results=20):
    """Download CTUIT / Compeat Ops Statement PDFs from Gmail."""
    IMPORTS_DIR.mkdir(exist_ok=True)
    service = _get_gmail_service()

    results = service.users().messages().list(
        userId="me", q=CTUIT_GMAIL_QUERY, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    return _download_pdf_attachments(service, messages, prefix="ctuit")


def check_new_ctuit_emails():
    """Download unread CTUIT PDF attachments from Gmail."""
    IMPORTS_DIR.mkdir(exist_ok=True)
    try:
        service = _get_gmail_service()
    except Exception:
        return []

    query = CTUIT_GMAIL_QUERY + " is:unread"
    results = service.users().messages().list(
        userId="me", q=query, maxResults=25
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    return _download_pdf_attachments(service, messages, prefix="ctuit")


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
