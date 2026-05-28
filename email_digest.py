"""
Email Weekly Digest — sends a beautifully formatted summary of the
operations dashboard to specified recipients via Gmail API.
"""

import base64
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _build_html_digest(context, ai_commentary=""):
    """Build a clean HTML email body from the dashboard context."""
    cons = context["consolidated"]
    depts = context["departments"]
    history = context["history"]
    flags = context.get("automated_flags", [])

    # Header card
    header_html = """
    <div style="background:linear-gradient(135deg,#1F2A44 0%,#2E3A59 100%);
                border-radius:12px;padding:32px 28px;color:#FFFFFF;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.10em;
                  text-transform:uppercase;color:#C7A462;margin-bottom:6px;">
        WEEKLY DIGEST
      </div>
      <div style="font-size:24px;font-weight:700;letter-spacing:-.02em;">
        Operations Dashboard
      </div>
      <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-top:4px;">
        Week of {wk}
      </div>
    </div>
    """.format(wk=context["week_of"])

    # KPI grid
    kpi_html = """
    <div style="display:flex;gap:12px;margin-top:20px;flex-wrap:wrap;">
      <div style="flex:1;min-width:140px;background:#FFFFFF;border:1px solid #E5E7EB;
                  border-radius:10px;padding:18px;">
        <div style="font-size:10px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;">REVENUE</div>
        <div style="font-size:24px;font-weight:700;color:#1E293B;margin-top:4px;">
          ${rev:,}
        </div>
      </div>
      <div style="flex:1;min-width:140px;background:#FFFFFF;border:1px solid #E5E7EB;
                  border-radius:10px;padding:18px;">
        <div style="font-size:10px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;">FOOD COST %</div>
        <div style="font-size:24px;font-weight:700;color:#1E293B;margin-top:4px;">
          {fc}%
        </div>
      </div>
      <div style="flex:1;min-width:140px;background:#FFFFFF;border:1px solid #E5E7EB;
                  border-radius:10px;padding:18px;">
        <div style="font-size:10px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;">LABOR %</div>
        <div style="font-size:24px;font-weight:700;color:#1E293B;margin-top:4px;">
          {lp}%
        </div>
      </div>
      <div style="flex:1;min-width:140px;background:#FFFFFF;border:1px solid #E5E7EB;
                  border-radius:10px;padding:18px;">
        <div style="font-size:10px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;">COVERS</div>
        <div style="font-size:24px;font-weight:700;color:#1E293B;margin-top:4px;">
          {cv:,}
        </div>
      </div>
    </div>
    """.format(rev=cons["revenue"], fc=cons["food_cost_pct"],
               lp=cons["labor_pct"], cv=cons["covers"])

    # Department breakdown
    rows = []
    for dept_name, data in depts.items():
        if not data.get("revenue"):
            continue
        rows.append("""
        <tr style="border-bottom:1px solid #F1F5F9;">
          <td style="padding:12px 14px;font-size:13px;color:#1E293B;font-weight:500;">{}</td>
          <td style="padding:12px 14px;font-size:13px;color:#1E293B;text-align:right;">${:,.0f}</td>
          <td style="padding:12px 14px;font-size:13px;color:#1E293B;text-align:right;">{:.1f}%</td>
          <td style="padding:12px 14px;font-size:13px;color:#1E293B;text-align:right;">{:.1f}%</td>
        </tr>
        """.format(dept_name, data["revenue"], data["fc_pct"], data["labor_pct"]))

    dept_html = """
    <div style="margin-top:24px;">
      <div style="font-size:11px;font-weight:700;color:#94A3B8;
                  text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">
        BY DEPARTMENT
      </div>
      <table style="width:100%;background:#FFFFFF;border:1px solid #E5E7EB;
                    border-radius:10px;border-collapse:separate;border-spacing:0;
                    overflow:hidden;">
        <thead>
          <tr style="background:#F8FAFC;">
            <th style="padding:11px 14px;font-size:10px;color:#94A3B8;
                       text-transform:uppercase;letter-spacing:.06em;
                       text-align:left;font-weight:600;">DEPARTMENT</th>
            <th style="padding:11px 14px;font-size:10px;color:#94A3B8;
                       text-transform:uppercase;letter-spacing:.06em;
                       text-align:right;font-weight:600;">REVENUE</th>
            <th style="padding:11px 14px;font-size:10px;color:#94A3B8;
                       text-transform:uppercase;letter-spacing:.06em;
                       text-align:right;font-weight:600;">FC %</th>
            <th style="padding:11px 14px;font-size:10px;color:#94A3B8;
                       text-transform:uppercase;letter-spacing:.06em;
                       text-align:right;font-weight:600;">LABOR %</th>
          </tr>
        </thead>
        <tbody>{}</tbody>
      </table>
    </div>
    """.format("".join(rows))

    # Flags / alerts
    flags_html = ""
    if flags:
        flag_items = "".join(
            '<li style="font-size:13px;color:#1E293B;margin-bottom:6px;">{}</li>'.format(f)
            for f in flags
        )
        flags_html = """
        <div style="margin-top:24px;background:#FEF3C7;border:1px solid #FDE68A;
                    border-radius:10px;padding:16px 20px;">
          <div style="font-size:11px;font-weight:700;color:#92400E;
                      text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">
            ⚠ AUTOMATED FLAGS
          </div>
          <ul style="margin:0;padding-left:18px;">{}</ul>
        </div>
        """.format(flag_items)

    # AI commentary
    ai_html = ""
    if ai_commentary:
        paragraphs = [p.strip() for p in ai_commentary.split("\n\n") if p.strip()]
        body = "".join(
            '<p style="font-size:14px;line-height:1.6;color:#FFFFFF;'
            'margin:0 0 12px 0;">{}</p>'.format(p)
            for p in paragraphs
        )
        ai_html = """
        <div style="margin-top:24px;background:linear-gradient(135deg,#1F2A44,#2E3A59);
                    border-radius:12px;padding:24px;color:#FFFFFF;">
          <div style="font-size:11px;font-weight:700;letter-spacing:.10em;
                      text-transform:uppercase;color:#C7A462;margin-bottom:12px;">
            ✦ AI INSIGHTS
          </div>
          {}
        </div>
        """.format(body)

    # Footer
    footer_html = """
    <div style="margin-top:32px;text-align:center;font-size:11px;color:#94A3B8;">
      Campus Dining Operations Platform · Metz Culinary Management
    </div>
    """

    full = """
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',
                       sans-serif;background:#F7F8FA;padding:24px;">
      <div style="max-width:680px;margin:0 auto;">
        {h}{k}{d}{f}{a}{ft}
      </div>
    </body></html>
    """.format(h=header_html, k=kpi_html, d=dept_html, f=flags_html,
               a=ai_html, ft=footer_html)

    return full


def send_digest(recipients, subject, html_body):
    """Send digest via Gmail API. Recipients = list of emails."""
    from gmail_import import _get_gmail_service

    service = _get_gmail_service()

    # Need send scope — but we only have readonly. Need to upgrade scope.
    # For now, try and report what we get
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "dashboardmetz@gmail.com"
    msg["To"] = ", ".join(recipients) if isinstance(recipients, list) else recipients

    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}
