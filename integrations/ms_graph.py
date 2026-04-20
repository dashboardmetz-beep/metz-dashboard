"""
Microsoft Graph API email client.
Fetches unread emails from a Microsoft 365 mailbox using client credentials flow.

Required environment variables:
  MS_GRAPH_TENANT_ID
  MS_GRAPH_CLIENT_ID
  MS_GRAPH_CLIENT_SECRET
  MS_GRAPH_MAILBOX  (email address to read from)
"""

import os

# NOTE: msal and requests must be installed (pip install msal requests)
# These are conditionally imported to avoid errors when not configured.


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

# Known sender patterns for auto-detection
EMAIL_TYPE_PATTERNS = {
    "usfoods_invoice": {
        "senders": ["usfoods.com", "us foods"],
        "subjects": ["invoice", "order confirmation", "us foods"],
    },
    "inventory": {
        "senders": ["inventory"],
        "subjects": ["inventory report", "weekly inventory", "stock count"],
    },
    "ctuit": {
        "senders": ["ctuit.com", "ctuit"],
        "subjects": ["ctuit", "operational statement", "ops statement"],
    },
    "odyssey": {
        "senders": ["odyssey"],
        "subjects": ["odyssey", "communication", "meal plan"],
    },
}


def _get_access_token():
    """Acquire an access token using MSAL client credentials flow."""
    import msal

    tenant_id = os.environ.get("MS_GRAPH_TENANT_ID", "")
    client_id = os.environ.get("MS_GRAPH_CLIENT_ID", "")
    client_secret = os.environ.get("MS_GRAPH_CLIENT_SECRET", "")

    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Microsoft Graph credentials not configured.")

    authority = "https://login.microsoftonline.com/{}".format(tenant_id)
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )

    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" in result:
        return result["access_token"]
    else:
        raise ValueError("Failed to acquire token: {}".format(result.get("error_description", "Unknown error")))


def fetch_unread_emails(max_results=20):
    """
    Fetch unread emails from the configured mailbox.
    Returns a list of dicts with: id, subject, from, date, body, attachments.
    """
    import requests

    token = _get_access_token()
    mailbox = os.environ.get("MS_GRAPH_MAILBOX", "")

    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }

    url = "{}/users/{}/messages".format(GRAPH_BASE_URL, mailbox)
    params = {
        "$filter": "isRead eq false",
        "$top": max_results,
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,receivedDateTime,body,hasAttachments",
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    emails = []

    for msg in data.get("value", []):
        email = {
            "id": msg["id"],
            "subject": msg.get("subject", ""),
            "from": msg.get("from", {}).get("emailAddress", {}).get("address", ""),
            "date": msg.get("receivedDateTime", ""),
            "body": msg.get("body", {}).get("content", ""),
            "has_attachments": msg.get("hasAttachments", False),
        }

        # Fetch attachments if present
        if email["has_attachments"]:
            att_url = "{}/users/{}/messages/{}/attachments".format(
                GRAPH_BASE_URL, mailbox, msg["id"])
            att_response = requests.get(att_url, headers=headers)
            if att_response.status_code == 200:
                email["attachments"] = att_response.json().get("value", [])
            else:
                email["attachments"] = []
        else:
            email["attachments"] = []

        emails.append(email)

    return emails


def detect_email_type(email):
    """
    Auto-detect the import type based on sender and subject patterns.
    Returns: 'usfoods_invoice', 'inventory', 'ctuit', 'odyssey', or None.
    """
    sender = (email.get("from", "") or "").lower()
    subject = (email.get("subject", "") or "").lower()

    for import_type, patterns in EMAIL_TYPE_PATTERNS.items():
        for s in patterns["senders"]:
            if s in sender:
                return import_type
        for s in patterns["subjects"]:
            if s in subject:
                return import_type

    return None


def mark_email_read(email_id):
    """Mark an email as read after successful import."""
    import requests

    token = _get_access_token()
    mailbox = os.environ.get("MS_GRAPH_MAILBOX", "")

    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }

    url = "{}/users/{}/messages/{}".format(GRAPH_BASE_URL, mailbox, email_id)
    response = requests.patch(url, headers=headers, json={"isRead": True})
    response.raise_for_status()
