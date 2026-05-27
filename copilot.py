"""
AI Copilot — Text-to-SQL engine powered by Anthropic Claude.
Users ask natural language questions; Claude generates read-only SQL,
the app executes it, and Claude interprets the results.
"""

import os
import re
import json
import sqlite3
import streamlit as st
from datetime import date, timedelta

from config import (
    DB_PATH,
    DEPARTMENTS,
    REVENUE_STREAMS,
    COPILOT_MODEL,
    COPILOT_MAX_TOKENS,
    COPILOT_MAX_QUERY_ROWS,
)

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ABS_DB_PATH = DB_PATH if os.path.isabs(DB_PATH) else os.path.join(_PROJECT_ROOT, DB_PATH)

# ─── Blocked SQL keywords (defense-in-depth) ──────────────────────

_BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX", "REPLACE",
]

_BLOCKED_PATTERN = re.compile(
    r"\b(?:{})\b".format("|".join(_BLOCKED_KEYWORDS)),
    re.IGNORECASE,
)

_NAV_PAGES = [
    "Daily Entry",
    "Weekly Budget",
    "Flash Report",
    "Dashboard",
    "Forecast & Allowable",
    "YoY & Alerts",
    "Inventory",
    "Checklists",
    "Scheduling",
    "Training",
    "Planning",
    "Communication",
    "Data Import",
]


def _load_dotenv():
    """Load .env from project root into os.environ (does not override existing)."""
    env_path = os.path.join(_PROJECT_ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


def get_api_key():
    """Return Anthropic API key from secrets, environment, or .env file."""
    _load_dotenv()
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key.strip()
    except Exception:
        pass
    key = os.environ.get("ANTHROPIC_API_KEY")
    return key.strip() if key else None


def get_anthropic_client():
    """Return an Anthropic client, or None if no API key is configured."""
    api_key = get_api_key()
    if not api_key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def api_key_status_message():
    """Human-readable setup instructions when the API key is missing."""
    return (
        "The AI assistant needs an **Anthropic API key**.\n\n"
        "1. Create a key at [console.anthropic.com](https://console.anthropic.com)\n"
        "2. Add to project `.env`:\n"
        "   `ANTHROPIC_API_KEY=sk-ant-...`\n"
        "3. Or add to `.streamlit/secrets.toml`:\n"
        "   `ANTHROPIC_API_KEY = \"sk-ant-...\"`\n"
        "4. Restart the app"
    )


# ─── Schema extraction ────────────────────────────────────────────


@st.cache_data(ttl=600)
def get_schema_text(_conn_id="default"):
    """Extract all CREATE TABLE statements, redacting password_hash."""
    ro_conn = sqlite3.connect(
        "file:{}?mode=ro".format(_ABS_DB_PATH), uri=True, timeout=5
    )
    rows = ro_conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    ro_conn.close()
    parts = []
    for row in rows:
        ddl = row[0]
        ddl = re.sub(
            r",?\s*password_hash\s+TEXT[^,\)]*", "", ddl, flags=re.IGNORECASE
        )
        parts.append(ddl + ";")
    return "\n\n".join(parts)


# ─── System prompt ─────────────────────────────────────────────────


def _current_week_start():
    """Sunday of the current fiscal week."""
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


def build_system_prompt(conn, user, current_page, current_department):
    """Assemble the full system prompt with schema + domain knowledge + context."""
    schema = get_schema_text()
    week_start = _current_week_start().isoformat()
    today_str = date.today().isoformat()

    user_name = user.get("display_name", "Unknown") if user else "Unknown"
    user_role = user.get("role", "staff") if user else "staff"
    user_dept = current_department or "All departments"

    dept_list = ", ".join(DEPARTMENTS)
    stream_list = ", ".join(REVENUE_STREAMS)

    return """You are an executive operations analyst for the Metz Operations Platform (Metz Culinary Management). You support general managers and directors with clear, professional briefings on budgets, labor, food cost, sales, and operations.

## Database Schema
{schema}

## Domain Knowledge
- Departments: {dept_list}
- Revenue streams: {stream_list} (daily_sales columns: board, retail, flex, catering, other)
- Fiscal week: Sunday through Saturday. `week_start` is always a Sunday date.
- Budget statuses: Draft, Submitted, Returned, Approved
- Key metrics (calculate when needed):
  - Labor % = (total_labor_dollars / total_revenue) * 100
  - SPLH = total_revenue / total_labor_hours
  - COS % = (cos_dollars / total_revenue) * 100
  - Food cost = invoice_total + inventory_start - inventory_end + adjustments
  - Total revenue = sum of all revenue stream columns in weekly_financials

## Current Context
- Today: {today_str}
- Current fiscal week starts: {week_start}
- User: {user_name} ({user_role})
- Department scope: {user_dept}
- Current page: {current_page}

## Instructions
1. Generate ONLY SELECT queries. Never modify data.
2. Use exact table and column names from the schema.
3. "This week" means week_start = '{week_start}'.
4. Use exact department names: {dept_list}
5. If the user is not admin/approver, scope to their department ({user_dept}) unless they ask for all.
6. Format answers clearly — dollars, percentages, readable dates.
7. If no rows returned, explain likely reasons (no data entered yet).
8. Use ISO date strings for SQLite comparisons.
9. Use NULLIF() for division to avoid divide-by-zero.
10. Never query password_hash.
11. Call query_database multiple times when needed for complex questions.
12. Write in a professional, corporate tone — concise, factual, and actionable. No casual language or emoji.
13. Structure longer answers with short paragraphs. Lead with the headline finding, then supporting detail.
14. Give concise, actionable answers with interpretation — not just raw numbers.
15. Use navigate_to when the user wants to open a page or when directing them to enter data.

## App Pages
- Daily Entry: daily sales and labor
- Weekly Budget: Revenue, Food Cost, Labor, Financials & Costs, Targets, Invoice Tracker
- Flash Report: Financial Summary, Operational Metrics, Budget & Projections
- Dashboard: Operations Dashboard, Overview, KPIs
- Forecast & Allowable, YoY & Alerts
- Planning: Calendar, Pre-Service Meeting, Catering & Events, Waste Tracking
- Communication: Shift Communication, Contract Areas, Safety
- Inventory, Checklists, Scheduling, Training
- Data Import: CTUIT, Odyssey, labor, inventory imports""".format(
        schema=schema,
        dept_list=dept_list,
        stream_list=stream_list,
        today_str=today_str,
        week_start=week_start,
        user_name=user_name,
        user_role=user_role,
        user_dept=user_dept,
        current_page=current_page,
    )


# ─── Tool definition ──────────────────────────────────────────────

COPILOT_TOOLS = [
    {
        "name": "query_database",
        "description": (
            "Execute a read-only SQL SELECT query against the Metz operations "
            "SQLite database. Returns up to {max_rows} rows as JSON."
        ).format(max_rows=COPILOT_MAX_QUERY_ROWS),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A SQLite SELECT query.",
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of what this query retrieves.",
                },
            },
            "required": ["sql", "explanation"],
        },
    },
    {
        "name": "navigate_to",
        "description": (
            "Navigate the user to a page (and optional subsection) in the app."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "enum": _NAV_PAGES,
                },
                "subsection": {
                    "type": "string",
                    "description": "Optional subsection within the page.",
                },
            },
            "required": ["page"],
        },
    },
]


# ─── Query validation & execution ─────────────────────────────────


def validate_query(sql):
    """Validate that sql is a safe SELECT statement."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    if _BLOCKED_PATTERN.search(stripped):
        return False, "Query contains a blocked keyword."
    if re.search(r"\bpassword_hash\b", stripped, re.IGNORECASE):
        return False, "Access to password_hash is not allowed."
    return True, ""


def execute_readonly_query(sql, max_rows=None):
    """Execute SELECT on read-only connection. Returns (results, error)."""
    if max_rows is None:
        max_rows = COPILOT_MAX_QUERY_ROWS

    sql_upper = sql.strip().upper()
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";").strip() + " LIMIT {}".format(max_rows)

    try:
        ro_conn = sqlite3.connect(
            "file:{}?mode=ro".format(_ABS_DB_PATH), uri=True, timeout=5
        )
        ro_conn.row_factory = sqlite3.Row
        cursor = ro_conn.execute(sql)
        rows = cursor.fetchmany(max_rows)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        results = [dict(zip(columns, row)) for row in rows]
        ro_conn.close()
        return results, None
    except Exception as e:
        return None, "Query error: {}".format(str(e))


def _serialize_content(content):
    """Convert SDK content blocks to JSON-serializable dicts for session storage."""
    if isinstance(content, str):
        return content
    out = []
    for block in content:
        if isinstance(block, dict):
            out.append(block)
        elif hasattr(block, "model_dump"):
            out.append(block.model_dump(exclude_none=True))
        elif hasattr(block, "text"):
            out.append({"type": "text", "text": block.text})
        else:
            out.append({"type": "text", "text": str(block)})
    return out


# ─── Claude conversation loop ─────────────────────────────────────


def run_copilot_turn(client, conn, messages, user, current_page, current_department):
    """
    Run one conversational turn with Claude (tool-use loop).
    Returns (assistant_text, updated_messages).
    """
    if client is None:
        raise ValueError("AI client is not configured. Set ANTHROPIC_API_KEY.")

    system_prompt = build_system_prompt(conn, user, current_page, current_department)

    response = client.messages.create(
        model=COPILOT_MODEL,
        max_tokens=COPILOT_MAX_TOKENS,
        system=system_prompt,
        tools=COPILOT_TOOLS,
        messages=messages,
    )

    for _ in range(5):
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            break

        tool_results = []
        for tool_block in tool_uses:
            if tool_block.name == "query_database":
                sql = tool_block.input.get("sql", "")
                is_valid, err = validate_query(sql)
                if not is_valid:
                    payload = {"error": err}
                else:
                    results, query_err = execute_readonly_query(sql)
                    payload = (
                        {"error": query_err}
                        if query_err
                        else {"row_count": len(results), "data": results}
                    )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps(payload),
                })
            elif tool_block.name == "navigate_to":
                page = tool_block.input.get("page", "")
                subsection = tool_block.input.get("subsection")
                st.session_state["copilot_navigate"] = {
                    "page": page,
                    "subsection": subsection,
                }
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps({
                        "status": "navigating",
                        "page": page,
                        "subsection": subsection,
                    }),
                })
            else:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps({"error": "Unknown tool."}),
                })

        messages.append({
            "role": "assistant",
            "content": _serialize_content(response.content),
        })
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=COPILOT_MODEL,
            max_tokens=COPILOT_MAX_TOKENS,
            system=system_prompt,
            tools=COPILOT_TOOLS,
            messages=messages,
        )

    text_parts = [b.text for b in response.content if hasattr(b, "text")]
    answer = (
        "\n".join(text_parts)
        if text_parts
        else "I couldn't generate an answer. Please try rephrasing your question."
    )

    messages.append({
        "role": "assistant",
        "content": _serialize_content(response.content),
    })

    return answer, messages


def get_suggested_questions(current_page):
    """Return contextual starter questions based on the current page."""
    suggestions = {
        "Daily Entry": [
            "What were total sales across all departments yesterday?",
            "Compare this week's labor hours to last week",
            "Which department had the highest revenue this week?",
        ],
        "Weekly Budget": [
            "Which departments have approved budgets this week?",
            "Show labor % trends for the last 4 weeks",
            "What is food cost for Board & Catering this week?",
        ],
        "Flash Report": [
            "Summarize this week's financial performance",
            "Which metrics are over budget this week?",
            "Compare COS % across all departments",
        ],
        "Dashboard": [
            "What is total revenue for the current week?",
            "Which department has the highest labor percentage?",
            "How many budgets are still in Draft status?",
        ],
        "Operations Dashboard": [
            "How does this week compare to last year?",
            "Which department is over labor target?",
            "Summarize consolidated revenue for this week",
        ],
        "Forecast & Allowable": [
            "What is projected revenue for this week?",
            "Show allowable spend vs actual food cost",
        ],
        "Data Import": [
            "When was the last successful import?",
            "List recent import history",
        ],
    }
    return suggestions.get(current_page, [
        "What is total revenue this week?",
        "Show labor % for the last 4 weeks",
        "Which department has the highest revenue?",
    ])
