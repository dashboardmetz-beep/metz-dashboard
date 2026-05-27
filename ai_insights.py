"""
AI Insights — uses Claude to analyze weekly operational data
and generate manager commentary, observations, and recommendations.
"""

import json
from datetime import date, timedelta
import streamlit as st

from config import COPILOT_MODEL
from copilot import get_anthropic_client, api_key_status_message


def _build_context(conn, week_start, last_year_week=None):
    """Build a structured snapshot of the week's data for Claude."""
    from views.operations_dashboard_view import (
        _fetch_dept_totals, _fetch_consolidated, _fetch_8wk_history,
        _get_targets,
    )
    from config import DEPARTMENTS

    # This week consolidated
    this_week = _fetch_consolidated(conn, week_start)
    last_week = _fetch_consolidated(conn, last_year_week) if last_year_week else None

    # Per-dept this week
    dept_data = {}
    for d in DEPARTMENTS:
        t = _fetch_dept_totals(conn, week_start, d)
        targets = _get_targets(conn, d)
        rev = t.get("revenue", 0) or 0
        dept_data[d] = {
            "revenue": rev,
            "cos": t.get("cos", 0) or 0,
            "labor_d": t.get("labor_d", 0) or 0,
            "labor_h": t.get("labor_h", 0) or 0,
            "fc_pct": (t.get("cos", 0) / rev * 100) if rev > 0 else 0,
            "labor_pct": (t.get("labor_d", 0) / rev * 100) if rev > 0 else 0,
            "target_labor_pct": targets.get("target_labor_pct") or 0,
            "target_fc_pct": targets.get("target_food_cost_pct") or 0,
        }

    # 8-week history
    history = _fetch_8wk_history(conn, "_consolidated", week_start, weeks=8)
    revs = [h["revenue"] for h in history]
    avg_rev = sum(revs) / len(revs) if revs else 0
    last_3_avg = sum(revs[-3:]) / 3 if len(revs) >= 3 else avg_rev

    # Variance flags
    rev = this_week["revenue"]
    fc_pct = (this_week["cos"] / rev * 100) if rev > 0 else 0
    lp_pct = (this_week["labor_d"] / rev * 100) if rev > 0 else 0

    flags = []
    for d, data in dept_data.items():
        if data["revenue"] > 0:
            if data["target_labor_pct"] and data["labor_pct"] > data["target_labor_pct"] + 2:
                flags.append("{}: labor {:.1f}% vs target {:.1f}%".format(
                    d, data["labor_pct"], data["target_labor_pct"]))
            if data["target_fc_pct"] and data["fc_pct"] > data["target_fc_pct"] + 2:
                flags.append("{}: food cost {:.1f}% vs target {:.1f}%".format(
                    d, data["fc_pct"], data["target_fc_pct"]))

    return {
        "week_of": week_start.isoformat(),
        "consolidated": {
            "revenue": round(rev),
            "food_cost_pct": round(fc_pct, 1),
            "labor_pct": round(lp_pct, 1),
            "covers": int(this_week.get("covers", 0)),
        },
        "vs_last_year": {
            "revenue": round(last_week["revenue"]) if last_week else None,
            "covers": int(last_week.get("covers", 0)) if last_week else None,
        },
        "departments": {d: {k: round(v, 1) for k, v in data.items()}
                        for d, data in dept_data.items()},
        "history": {
            "8_week_avg_revenue": round(avg_rev),
            "last_3_week_avg_revenue": round(last_3_avg),
            "trend_direction": "up" if last_3_avg > avg_rev else "down",
        },
        "automated_flags": flags,
    }


@st.cache_data(ttl=300)  # Cache 5 min
def generate_insights(_conn_id, week_start_iso, last_year_iso=None):
    """Get Claude commentary for the week. Cached 5 min."""
    import sqlite3
    conn = sqlite3.connect("budget.db")
    conn.row_factory = sqlite3.Row

    week_start = date.fromisoformat(week_start_iso)
    last_year = date.fromisoformat(last_year_iso) if last_year_iso else None

    context = _build_context(conn, week_start, last_year)

    client = get_anthropic_client()
    if not client:
        return {
            "available": False,
            "message": api_key_status_message().replace("**", ""),
        }

    prompt = """You are an executive analyst for Metz Culinary Management. Analyze this week's data \
and write a brief (3-4 paragraph) executive summary for the general manager.

Focus on:
1. Lead with the headline — revenue and the single most important variance
2. What is performing well
3. What requires attention (specific department, metric, and recommended action)
4. One forward-looking note (forecast, scheduling, or ordering)

Use a professional, corporate tone. Be direct and specific with numbers. No bullet points, \
no casual language, no emoji. Reference departments by name.

DATA:
{}""".format(json.dumps(context, indent=2))

    try:
        msg = client.messages.create(
            model=COPILOT_MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text if msg.content else ""
        return {
            "available": True,
            "commentary": text,
            "context": context,
        }
    except Exception as e:
        return {
            "available": False,
            "message": "AI error: {}".format(str(e)[:200]),
            "context": context,
        }


def render_insights_panel(conn, week_start, last_year_week=None):
    """Render the AI Insights panel in Streamlit."""
    last_year_iso = last_year_week.isoformat() if last_year_week else None
    result = generate_insights("default", week_start.isoformat(), last_year_iso)

    import html as _html

    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E4E7EC;'
        'border-top:3px solid #C7A462;border-radius:10px;padding:28px 32px;">'
        '<p style="margin:0 0 6px;font-size:10px;font-weight:600;'
        'letter-spacing:0.16em;text-transform:uppercase;color:#C7A462;">'
        'Executive Insights</p>'
        '<h3 style="margin:0;font-size:18px;font-weight:600;color:#0F172A;'
        'letter-spacing:-0.02em;">Weekly commentary</h3>'
        '<p style="margin:6px 0 0;font-size:12px;color:#94A3B8;">'
        'AI-generated summary · verify before distribution</p>',
        unsafe_allow_html=True,
    )

    if not result.get("available"):
        st.markdown(
            '<p style="font-size:13px;color:#64748B;line-height:1.6;margin:16px 0 0;">'
            '{}</p></div>'.format(_html.escape(result.get("message", "Unavailable"))),
            unsafe_allow_html=True,
        )
        return

    text = result.get("commentary", "").strip()
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    body_html = "".join(
        '<p style="font-size:14px;line-height:1.65;color:#334155;'
        'margin:16px 0 0 0;">{}</p>'.format(_html.escape(p))
        for p in paragraphs
    )

    st.markdown(body_html + "</div>", unsafe_allow_html=True)
