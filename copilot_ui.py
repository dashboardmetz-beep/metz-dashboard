"""
AI Copilot UI — corporate sidebar launcher + executive dialog.
"""

import html

import streamlit as st

from config import APP_FULL_NAME, COPILOT_SUBTITLE, COPILOT_TITLE, PLATFORM_TITLE
from copilot import (
    api_key_status_message,
    get_anthropic_client,
    get_suggested_questions,
    run_copilot_turn,
)

_CORPORATE_COPILOT_CSS = """
<style>
/* Sidebar — Insights launcher */
section[data-testid="stSidebar"] .copilot-launch-wrap {
    padding: 4px 12px 12px;
}
section[data-testid="stSidebar"] .copilot-launch-wrap + div .stButton > button {
    background: rgba(199, 164, 98, 0.12) !important;
    border: 1px solid rgba(199, 164, 98, 0.35) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    height: 44px !important;
    min-height: 44px !important;
    box-shadow: none !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}
section[data-testid="stSidebar"] .copilot-launch-wrap + div .stButton > button:hover {
    background: rgba(199, 164, 98, 0.2) !important;
    border-color: #C7A462 !important;
    transform: none !important;
}

/* Dialog shell */
[data-testid="stDialog"] {
    border-radius: 12px !important;
    border: 1px solid #E4E7EC !important;
    box-shadow: 0 24px 64px rgba(15, 23, 42, 0.14) !important;
    overflow: hidden !important;
}
[data-testid="stDialog"] > div {
    background: #FAFBFC !important;
}
[data-testid="stDialog"] header {
    background: #FFFFFF !important;
    border-bottom: 1px solid #E4E7EC !important;
    padding: 0 !important;
}
[data-testid="stDialog"] header h2 {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #0F172A !important;
    letter-spacing: -0.02em !important;
}

.copilot-shell {
    font-family: 'Inter', -apple-system, sans-serif;
}
.copilot-header {
    background: #FFFFFF;
    border-bottom: 1px solid #E4E7EC;
    padding: 0 0 20px 0;
    margin: -8px 0 20px 0;
}
.copilot-header::before {
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(90deg, #1F2A44 0%, #C7A462 50%, #1F2A44 100%);
    margin: 0 -1rem 20px -1rem;
}
.copilot-eyebrow {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #C7A462;
    margin: 0 0 6px 0;
}
.copilot-title {
    font-size: 22px;
    font-weight: 600;
    color: #0F172A;
    letter-spacing: -0.03em;
    margin: 0;
    line-height: 1.25;
}
.copilot-sub {
    font-size: 13px;
    color: #64748B;
    margin: 8px 0 0 0;
    line-height: 1.5;
}
.copilot-context {
    display: inline-block;
    margin-top: 12px;
    padding: 6px 12px;
    background: #F1F3F6;
    border: 1px solid #E4E7EC;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    color: #475569;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.copilot-disclaimer {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 14px;
    line-height: 1.45;
    border-top: 1px solid #EEF0F3;
    padding-top: 12px;
}

.copilot-prompt-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #94A3B8;
    margin: 0 0 10px 0;
}

.copilot-setup {
    background: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-left: 3px solid #C7A462;
    border-radius: 8px;
    padding: 20px 22px;
    margin: 8px 0;
}
.copilot-setup h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    font-weight: 600;
    color: #0F172A;
}

/* Dialog buttons */
[data-testid="stDialog"] .stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #475569 !important;
    -webkit-text-fill-color: #475569 !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    height: 36px !important;
    min-height: 36px !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
[data-testid="stDialog"] .copilot-prompts .stButton > button {
    background: #FFFFFF !important;
    border: 1px solid #E4E7EC !important;
    color: #1F2A44 !important;
    -webkit-text-fill-color: #1F2A44 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 12px 16px !important;
    height: auto !important;
    min-height: 44px !important;
    line-height: 1.45 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    white-space: normal !important;
}
[data-testid="stDialog"] .copilot-prompts .stButton > button:hover {
    border-color: #C7A462 !important;
    background: #FFFBF7 !important;
}

/* Chat */
[data-testid="stDialog"] [data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 8px 0 !important;
}
[data-testid="stDialog"] [data-testid="stChatMessageAvatarIcon"] {
    background: #1F2A44 !important;
    color: #C7A462 !important;
    border: 1px solid rgba(199, 164, 98, 0.4) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
}
[data-testid="stDialog"] [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarIcon"]) 
    + div [data-testid="stMarkdownContainer"] {
    background: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stDialog"] [data-testid="stChatInput"] textarea {
    border: 1px solid #E4E7EC !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    background: #FFFFFF !important;
}
[data-testid="stDialog"] [data-testid="stChatInput"] textarea:focus {
    border-color: #C7A462 !important;
    box-shadow: 0 0 0 3px rgba(199, 164, 98, 0.12) !important;
}
</style>
"""


def _inject_copilot_styles():
    st.markdown(_CORPORATE_COPILOT_CSS, unsafe_allow_html=True)


def _init_session_state():
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
    if "copilot_pending_question" not in st.session_state:
        st.session_state.copilot_pending_question = None


def _display_turns(messages):
    """Render conversation history."""
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user" and isinstance(content, str):
            with st.chat_message("user", avatar="You"):
                st.markdown(content)
        elif role == "assistant":
            text = _extract_assistant_text(content)
            if text:
                with st.chat_message("assistant", avatar="AI"):
                    st.markdown(text)


def _extract_assistant_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(p for p in parts if p)


def _render_header(user, current_page):
    user_name = user.get("display_name", "") if user else ""
    first_name = user_name.split()[0] if user_name else "there"
    page_safe = html.escape(str(current_page or "Dashboard"))

    st.markdown(
        '<div class="copilot-shell"><div class="copilot-header">'
        '<p class="copilot-eyebrow">{} · {}</p>'
        '<h1 class="copilot-title">{}, {}</h1>'
        '<p class="copilot-sub">{}</p>'
        '<span class="copilot-context">Viewing · {}</span>'
        '<p class="copilot-disclaimer">'
        'Responses are generated from your operational database. '
        'Verify figures before financial decisions. '
        'Data is read-only and scoped to your access level.'
        '</p></div></div>'.format(
            html.escape(APP_FULL_NAME),
            html.escape(PLATFORM_TITLE),
            html.escape(COPILOT_TITLE),
            html.escape(first_name),
            html.escape(COPILOT_SUBTITLE),
            page_safe,
        ),
        unsafe_allow_html=True,
    )


def _render_setup_notice():
    st.markdown(
        '<div class="copilot-setup">'
        '<h4>Configuration required</h4></div>',
        unsafe_allow_html=True,
    )
    st.markdown(api_key_status_message())


@st.dialog(COPILOT_TITLE, width="large")
def _copilot_dialog(conn, user, current_page, current_department):
    """Executive modal for AI operations intelligence."""
    _inject_copilot_styles()

    client = get_anthropic_client()
    _render_header(user, current_page)

    if not client:
        _render_setup_notice()
        return

    messages = st.session_state.copilot_messages

    toolbar_l, toolbar_r = st.columns([1, 1])
    with toolbar_l:
        if messages:
            if st.button("Start new session", key="copilot_clear", type="secondary"):
                st.session_state.copilot_messages = []
                st.rerun()
    with toolbar_r:
        st.markdown(
            '<p style="text-align:right;font-size:11px;color:#94A3B8;'
            'margin:8px 0 0;padding:0;">Powered by Claude</p>',
            unsafe_allow_html=True,
        )

    if messages:
        st.markdown("---")
        _display_turns(messages)

    if not messages:
        st.markdown(
            '<p class="copilot-prompt-label">Suggested inquiries</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="copilot-prompts">', unsafe_allow_html=True)
        for i, q in enumerate(get_suggested_questions(current_page)):
            if st.button(q, key="copilot_s_{}".format(i), use_container_width=True):
                st.session_state.copilot_pending_question = q
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    question = st.chat_input(
        "Enter your question — revenue, labor, food cost, budgets…",
        key="copilot_input",
    )
    pending = st.session_state.copilot_pending_question
    if pending:
        question = pending
        st.session_state.copilot_pending_question = None

    if question:
        messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="You"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="AI"):
            with st.spinner("Retrieving and analyzing operational data…"):
                try:
                    answer, updated = run_copilot_turn(
                        client=client,
                        conn=conn,
                        messages=messages,
                        user=user,
                        current_page=current_page,
                        current_department=current_department,
                    )
                    st.session_state.copilot_messages = updated
                    st.markdown(answer)
                except Exception as e:
                    st.error(
                        "Unable to complete this request. "
                        "Please try again or rephrase your question.\n\n"
                        "_{}_".format(html.escape(str(e)))
                    )
                    if messages and messages[-1].get("role") == "user":
                        messages.pop()


def render_copilot_panel(conn, user, current_page, current_department):
    """Sidebar launcher and post-chat navigation."""
    _init_session_state()

    nav = st.session_state.pop("copilot_navigate", None)
    if nav and nav.get("page"):
        st.session_state.current_page = nav["page"]
        if nav.get("subsection"):
            st.session_state.current_subsection = nav["subsection"]
        st.rerun()

    _inject_copilot_styles()

    st.sidebar.markdown(
        '<div class="copilot-launch-wrap">'
        '<div class="nav-group-label" style="padding:16px 8px 8px !important;">'
        'Intelligence</div></div>',
        unsafe_allow_html=True,
    )
    if st.sidebar.button(
        COPILOT_TITLE,
        use_container_width=True,
        key="copilot_open_dialog",
        help="Executive AI assistant for operations, budgets, and labor data",
    ):
        _copilot_dialog(conn, user, current_page, current_department)
