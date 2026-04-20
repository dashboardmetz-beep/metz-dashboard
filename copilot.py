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
    DB_PATH, DEPARTMENTS, REVENUE_STREAMS, REVENUE_STREAM_LABELS,
    COPILOT_MODEL, COPILOT_MAX_TOKENS, COPILOT_MAX_QUERY_ROWS,
)


# ─── Blocked SQL keywords (defense-in-depth) ──────────────────────

_BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX", "REPLACE",
]

_BLOCKED_PATTERN = re.compile(
    r"\b(?:{})\b".format("|".join(_BLOCKED_KEYWORDS)),
    re.IGNORECASE,
)


# ─── Anthropic client ─────────────────────────────────────────────


def get_anthropic_client():
    """Return an Anthropic client, or None if no API key is configured."""
    api_key = None
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


# ─── Schema extraction ────────────────────────────────────────────


@st.cache_data(ttl=600)
def get_schema_text(_conn_id="default"):
    """Extract all CREATE TABLE statements, redacting password_hash. Cached for 10 min."""
    import sqlite3
    ro_conn = sqlite3.connect("file:{}?mode=ro".format(DB_PATH), uri=True, timeout=5)
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

    return """You are a data analyst assistant for the Campus Dining Operations Platform at Alma College, managed by Metz Culinary Management. You help dining staff answer questions about their operational data.

## Database Schema
{schema}

## Domain Knowledge
- Departments: {dept_list}
- Revenue Streams: {stream_list} (column names in daily_sales: board, retail, flex, catering, other)
- Fiscal week: Sunday through Saturday. The `week_start` column is always a Sunday date.
- Use `get_week_start()` logic: week_start = date - ((weekday + 1) % 7) days. In SQL: date(d, '-' || ((strftime('%w', d) + 0) ) || ' days') gives Sunday.
- Budget workflow statuses: Draft, Submitted, Returned, Approved
- Key Metrics (calculated, not stored):
  - Labor % = (total_labor_dollars / total_revenue) * 100
  - SPLH (Sales Per Labor Hour) = total_revenue / total_labor_hours
  - COS % = (cos_dollars / total_revenue) * 100
  - CPM (Cost Per Meal, Board only) = cos_dollars / meals_served
  - MPLH (Meals Per Labor Hour, Board only) = meals_served / total_labor_hours
  - Food Cost = invoice_total + inventory_start - inventory_end + adjustments
  - Total Revenue = board_revenue + retail_revenue + flex_revenue + catering_revenue + other_revenue

## Current Context
- Today: {today_str}
- Current fiscal week starts: {week_start}
- Current user: {user_name} ({user_role})
- User department: {user_dept}
- Current page: {current_page}

## Instructions
1. Generate ONLY SELECT queries. Never modify data.
2. Use exact table and column names from the schema above.
3. When the user says "this week", use week_start = '{week_start}'.
4. Use exact department names from the list: {dept_list}
5. If the user's role is not admin/approver, scope queries to their department ({user_dept}) unless they ask about all departments.
6. Format your answers clearly — use dollar signs for money, percentages where appropriate, and readable dates.
7. If a query returns no results, explain what that likely means (e.g., no data entered yet).
8. For SQLite date comparisons use ISO strings like '{today_str}'.
9. Keep SQL efficient — select only needed columns, use appropriate WHERE clauses.
10. NEVER query or reveal password_hash values.
11. When asked about trends, order results chronologically and explain the pattern.
12. For daily data, the date column is usually named `date`. For weekly data, use `week_start`.
13. When calculating metrics that involve division, handle zero denominators gracefully with NULLIF().
14. You may call the query_database tool multiple times if you need data from different tables to answer a complex question.
15. Always provide a clear, conversational answer — not just raw numbers. Add context and interpretation.
16. If the user asks to go to a page or needs to be directed somewhere, use the navigate_to tool. For example: "take me to labor", "go to food cost", "show me the dashboard".
17. You can also proactively suggest navigation when it would help the user. For example, if they ask about entering revenue, navigate them to Weekly Budget > Revenue.

## App Pages & Subsections
- Daily Entry: daily sales and labor entry
- Weekly Budget: Revenue, Food Cost, Labor, Financials & Costs, Targets, Invoice Tracker
- Flash Report: Financial Summary, Operational Metrics, Budget & Projections
- Dashboard: overview with KPIs and charts
- Calendar: academic and dining events
- Pre-Service Meeting: meeting notes
- Shift Communication: shift logs
- Contacts: staff directory
- Data Import: CTUIT imports, projections, meal plans""".format(
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
            "Execute a read-only SQL SELECT query against the campus dining "
            "SQLite database. Returns up to {max_rows} rows as JSON. Use this "
            "to answer questions about budgets, sales, labor, food cost, "
            "safety, catering, and other dining operations data."
        ).format(max_rows=COPILOT_MAX_QUERY_ROWS),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A SQLite SELECT query. Only SELECT statements are allowed.",
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
            "Navigate the user to a specific page and subsection in the app. "
            "Use this when the user asks to go somewhere, or when directing "
            "them to a relevant page based on their question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "description": "The page to navigate to.",
                    "enum": [
                        "Daily Entry", "Weekly Budget", "Flash Report",
                        "Dashboard", "Calendar", "Pre-Service Meeting",
                        "Shift Communication", "Contacts", "Data Import",
                    ],
                },
                "subsection": {
                    "type": "string",
                    "description": (
                        "Optional subsection within the page. "
                        "Weekly Budget: Revenue, Food Cost, Labor, Financials & Costs, Targets, Invoice Tracker. "
                        "Flash Report: Financial Summary, Operational Metrics, Budget & Projections. "
                        "Data Import: various import types."
                    ),
                },
            },
            "required": ["page"],
        },
    },
]


# ─── Query validation ─────────────────────────────────────────────


def validate_query(sql):
    """
    Validate that sql is a safe SELECT statement.
    Returns (is_valid, error_message).
    """
    stripped = sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    if _BLOCKED_PATTERN.search(stripped):
        return False, "Query contains a blocked keyword."
    if re.search(r"\bpassword_hash\b", stripped, re.IGNORECASE):
        return False, "Access to password_hash is not allowed."
    return True, ""


# ─── Query execution ──────────────────────────────────────────────


def execute_readonly_query(sql, max_rows=None):
    """
    Execute a SELECT query on a read-only SQLite connection.
    Returns (results_list, error_string). One will be None.
    """
    if max_rows is None:
        max_rows = COPILOT_MAX_QUERY_ROWS

    # Auto-append LIMIT if not present
    sql_upper = sql.strip().upper()
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";").strip() + " LIMIT {}".format(max_rows)

    try:
        ro_conn = sqlite3.connect(
            "file:{}?mode=ro".format(DB_PATH), uri=True, timeout=5
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


# ─── Claude conversation loop ─────────────────────────────────────


def run_copilot_turn(client, conn, messages, user, current_page, current_department):
    """
    Run one conversational turn with Claude.
    Handles the tool-use loop (Claude may call query_database multiple times).
    Returns (assistant_text, updated_messages).
    """
    system_prompt = build_system_prompt(conn, user, current_page, current_department)

    # Initial API call
    response = client.messages.create(
        model=COPILOT_MODEL,
        max_tokens=COPILOT_MAX_TOKENS,
        system=system_prompt,
        tools=COPILOT_TOOLS,
        messages=messages,
    )

    # Tool-use loop — allow up to 5 rounds
    for _ in range(5):
        # Check if Claude wants to use a tool
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            break

        # Process each tool call
        tool_results = []
        for tool_block in tool_uses:
            if tool_block.name == "query_database":
                sql = tool_block.input.get("sql", "")
                is_valid, err = validate_query(sql)
                if not is_valid:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps({"error": err}),
                    })
                else:
                    results, query_err = execute_readonly_query(sql)
                    if query_err:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": json.dumps({"error": query_err}),
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": json.dumps({
                                "row_count": len(results),
                                "data": results,
                            }),
                        })
            elif tool_block.name == "navigate_to":
                page = tool_block.input.get("page", "")
                subsection = tool_block.input.get("subsection")
                # Store navigation request in session state for the UI to pick up
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

        # Append assistant message (with tool_use blocks) + tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # Call Claude again with the tool results
        response = client.messages.create(
            model=COPILOT_MODEL,
            max_tokens=COPILOT_MAX_TOKENS,
            system=system_prompt,
            tools=COPILOT_TOOLS,
            messages=messages,
        )

    # Extract final text answer
    text_parts = [b.text for b in response.content if hasattr(b, "text")]
    answer = "\n".join(text_parts) if text_parts else "I wasn't able to generate an answer. Please try rephrasing your question."

    # Append final assistant message
    messages.append({"role": "assistant", "content": response.content})

    return answer, messages


# ─── Suggested questions ───────────────────────────────────────────


def get_suggested_questions(current_page):
    """Return contextual starter questions based on the current page."""
    suggestions = {
        "Daily Entry": [
            "What were total sales across all departments yesterday?",
            "Compare today's labor hours to last week's average",
            "Which department had the highest revenue this week?",
        ],
        "Weekly Budget": [
            "Which departments have approved budgets this week?",
            "Show me labor % trends for the last 4 weeks",
            "What is the food cost for Board & Catering this week?",
        ],
        "Flash Report": [
            "Summarize this week's financial performance",
            "Which line items have the largest budget variance?",
            "Compare COS % across all departments",
        ],
        "Dashboard": [
            "What is total revenue for the current week?",
            "Which department has the highest labor percentage?",
            "How many budgets are still in Draft status?",
        ],
        "Calendar": [
            "What events are scheduled for this week?",
            "Are there any catering events coming up?",
        ],
        "Data Import": [
            "When was the last CTUIT import?",
            "Show me import history for the past month",
        ],
    }
    return suggestions.get(current_page, [
        "What were total sales yesterday?",
        "Show me labor % for the last 4 weeks",
        "Which department has the highest revenue this week?",
    ])
