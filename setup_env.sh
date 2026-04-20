#!/bin/bash
# ═══════════════════════════════════════════════════════
# Campus Dining Budget App — Environment Setup
# ═══════════════════════════════════════════════════════
#
# INSTRUCTIONS:
# 1. Fill in your real values below (replace the placeholder text)
# 2. Save this file
# 3. Run: source setup_env.sh
# 4. Then start the app: python3 -m streamlit run app.py
#
# HOW TO GET THESE VALUES:
#   Go to https://portal.azure.com → Microsoft Entra ID
#   → App registrations → your app → Overview page
# ═══════════════════════════════════════════════════════

# ── Microsoft Graph API (Outlook Email Integration) ──
# Used for: US Foods invoices, CTUIT ops statements, Odyssey meal plan data
export MS_GRAPH_TENANT_ID="PASTE_YOUR_TENANT_ID_HERE"
export MS_GRAPH_CLIENT_ID="PASTE_YOUR_CLIENT_ID_HERE"
export MS_GRAPH_CLIENT_SECRET="PASTE_YOUR_CLIENT_SECRET_HERE"
export MS_GRAPH_MAILBOX="your-email@yourdomain.edu"

# ── ADP Integration (Optional — for labor schedule sync) ──
# Leave these blank if you don't use ADP
export ADP_API_BASE_URL=""
export ADP_CLIENT_ID=""
export ADP_CLIENT_SECRET=""
export ADP_CERT_PATH=""

echo "Environment variables set successfully!"
echo "MS_GRAPH_MAILBOX = $MS_GRAPH_MAILBOX"
echo ""
echo "Now run: python3 -m streamlit run app.py"
