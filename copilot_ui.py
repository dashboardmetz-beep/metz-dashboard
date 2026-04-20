"""
AI Copilot UI — Draggable floating button using components.html + side panel.
The button is a real HTML element with JavaScript drag support.
"""

import streamlit as st
import streamlit.components.v1 as components
from streamlit_float import float_init, float_css_helper

from copilot import (
    get_anthropic_client,
    get_suggested_questions,
    run_copilot_turn,
)


# Draggable button HTML — runs in iframe with full JS support
_DRAGGABLE_BUTTON_HTML = """
<div id="dragBtn" style="
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 999999;
    cursor: grab;
    user-select: none;
    touch-action: none;
">
    <button onclick="window.parent.postMessage({type:'copilot_open'}, '*')" style="
        background: #FFFFFF;
        color: #1E293B;
        border: 1px solid #E5E7EB;
        border-radius: 28px;
        padding: 12px 22px;
        font-size: 14px;
        font-weight: 600;
        font-family: 'Inter', -apple-system, sans-serif;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        cursor: pointer;
        transition: box-shadow 0.2s, transform 0.2s;
        letter-spacing: 0.2px;
        white-space: nowrap;
    " onmouseover="this.style.boxShadow='0 6px 28px rgba(0,0,0,0.12)';this.style.borderColor='#C7A462'"
      onmouseout="this.style.boxShadow='0 4px 20px rgba(0,0,0,0.08)';this.style.borderColor='#E5E7EB'"
    >💬 Ask Help</button>
</div>

<script>
(function() {
    var el = document.getElementById('dragBtn');
    var isDragging = false;
    var wasDragged = false;
    var startX, startY, startLeft, startTop;

    el.addEventListener('mousedown', function(e) {
        isDragging = true;
        wasDragged = false;
        startX = e.clientX;
        startY = e.clientY;
        var rect = el.getBoundingClientRect();
        startLeft = rect.left;
        startTop = rect.top;
        el.style.cursor = 'grabbing';
        el.style.transition = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        var dx = e.clientX - startX;
        var dy = e.clientY - startY;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) wasDragged = true;
        el.style.right = 'auto';
        el.style.bottom = 'auto';
        el.style.left = (startLeft + dx) + 'px';
        el.style.top = (startTop + dy) + 'px';
        e.preventDefault();
    });

    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            el.style.cursor = 'grab';
            el.style.transition = '';
        }
    });

    // Touch support for mobile
    el.addEventListener('touchstart', function(e) {
        isDragging = true;
        wasDragged = false;
        var touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        var rect = el.getBoundingClientRect();
        startLeft = rect.left;
        startTop = rect.top;
        el.style.transition = 'none';
    }, {passive: false});

    document.addEventListener('touchmove', function(e) {
        if (!isDragging) return;
        var touch = e.touches[0];
        var dx = touch.clientX - startX;
        var dy = touch.clientY - startY;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) wasDragged = true;
        el.style.right = 'auto';
        el.style.bottom = 'auto';
        el.style.left = (startLeft + dx) + 'px';
        el.style.top = (startTop + dy) + 'px';
        e.preventDefault();
    }, {passive: false});

    document.addEventListener('touchend', function() {
        isDragging = false;
        el.style.transition = '';
    });

    // Prevent click after drag
    el.querySelector('button').addEventListener('click', function(e) {
        if (wasDragged) {
            e.stopPropagation();
            e.preventDefault();
            wasDragged = false;
        }
    }, true);
})();
</script>

<style>
body { margin: 0; padding: 0; overflow: hidden; background: transparent; }
</style>
"""

# Panel CSS
_PANEL_STYLE = """
<style>
.copilot-panel-container button[kind="secondary"] {
    background: #F8F9FB !important;
    border: 1px solid #E8EAF0 !important;
    border-radius: 16px !important;
    color: #374151 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
    text-align: left !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
}
.copilot-panel-container button[kind="secondary"]:hover {
    background: #F1F3F7 !important;
    border-color: #C7A462 !important;
}
</style>
"""


def _init_session_state():
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
    if "copilot_client" not in st.session_state:
        st.session_state.copilot_client = None
    if "copilot_pending_question" not in st.session_state:
        st.session_state.copilot_pending_question = None
    if "copilot_open" not in st.session_state:
        st.session_state.copilot_open = False


def render_copilot_panel(conn, user, current_page, current_department):
    _init_session_state()
    float_init()
    st.markdown(_PANEL_STYLE, unsafe_allow_html=True)

    # ── Draggable floating button (when panel is closed) ──
    if not st.session_state.copilot_open:
        # Render draggable button via components.html (supports JS)
        components.html(_DRAGGABLE_BUTTON_HTML, height=0, scrolling=False)

        # Hidden Streamlit button to receive the open command
        # The JS postMessage triggers this via query params
        open_col = st.container()
        with open_col:
            if st.button("Open Ask Help", key="copilot_open_btn"):
                if st.session_state.copilot_client is None:
                    st.session_state.copilot_client = get_anthropic_client()
                st.session_state.copilot_open = True
                st.rerun()
        # Hide this button visually
        open_col.float(float_css_helper(
            bottom="-100px",
            right="-100px",
            css="opacity: 0 !important; pointer-events: none !important;"
        ))

        # Also provide a visible fallback button in case postMessage doesn't work
        fallback = st.container()
        with fallback:
            if st.button("💬", key="copilot_fallback_btn", help="Open Ask Help"):
                if st.session_state.copilot_client is None:
                    st.session_state.copilot_client = get_anthropic_client()
                st.session_state.copilot_open = True
                st.rerun()
        fallback.float(float_css_helper(
            bottom="28px",
            left="240px",
            css="""
                z-index: 999998;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                button {
                    background: #FFFFFF !important;
                    color: #1E293B !important;
                    border: 1px solid #E5E7EB !important;
                    border-radius: 50% !important;
                    width: 44px !important;
                    height: 44px !important;
                    padding: 0 !important;
                    font-size: 20px !important;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
                    cursor: pointer !important;
                }
                button:hover {
                    border-color: #C7A462 !important;
                }
            """
        ))
        return

    # ── Side panel (open) ──
    panel = st.container()
    with panel:
        st.markdown('<div class="copilot-panel-container">', unsafe_allow_html=True)

        user_name = user.get("display_name", "there") if user else "there"
        first_name = user_name.split()[0] if user_name else "there"
        messages = st.session_state.copilot_messages
        display_messages = _get_display_messages(messages)

        if st.button("✕", key="copilot_close"):
            st.session_state.copilot_open = False
            st.rerun()

        st.markdown(
            '<div style="padding:8px 0 16px;">'
            '<h2 style="margin:0;font-size:24px;font-weight:600;'
            'background:linear-gradient(135deg,#C7A462,#B8943F);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            'line-height:1.3;">Hello, {name}</h2>'
            '<p style="margin:2px 0 0;font-size:17px;color:#1E293B;'
            'font-weight:500;line-height:1.3;">How can I help you today?</p>'
            '<p style="margin:8px 0 0;font-size:11px;color:#94A3B8;'
            'letter-spacing:0.3px;text-transform:uppercase;">{page}</p>'
            '</div>'.format(name=first_name, page=current_page),
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="height:1px;background:linear-gradient(90deg,'
            'transparent,#E5E7EB,transparent);margin:0 0 16px;"></div>',
            unsafe_allow_html=True,
        )

        if display_messages:
            if st.button("↺ New conversation", key="copilot_clear"):
                st.session_state.copilot_messages = []
                st.rerun()
            for msg in display_messages:
                with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "✨"):
                    st.markdown(msg["content"])

        if not display_messages:
            suggestions = get_suggested_questions(current_page)
            icons = ["📊", "📈", "🔍"]
            for i, q in enumerate(suggestions):
                icon = icons[i] if i < len(icons) else "💡"
                if st.button(
                    "{} {}".format(icon, q),
                    key="copilot_s_{}".format(i),
                    use_container_width=True,
                ):
                    st.session_state.copilot_pending_question = q
                    st.rerun()

        user_input = st.chat_input("Ask a question...", key="copilot_input")
        st.markdown('</div>', unsafe_allow_html=True)

        question = user_input or st.session_state.copilot_pending_question
        if st.session_state.copilot_pending_question and question == st.session_state.copilot_pending_question:
            st.session_state.copilot_pending_question = None

        if question:
            messages.append({"role": "user", "content": question})
            with st.chat_message("user", avatar="👤"):
                st.markdown(question)
            with st.chat_message("assistant", avatar="✨"):
                with st.spinner(""):
                    try:
                        answer, updated_messages = run_copilot_turn(
                            client=st.session_state.copilot_client,
                            conn=conn,
                            messages=messages,
                            user=user,
                            current_page=current_page,
                            current_department=current_department,
                        )
                        st.session_state.copilot_messages = updated_messages
                        st.markdown(answer)
                    except Exception as e:
                        st.error("Error: {}".format(str(e)))
                        messages.append({
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Error: {}".format(str(e))}],
                        })
                        st.session_state.copilot_messages = messages

        nav = st.session_state.pop("copilot_navigate", None)
        if nav:
            page = nav.get("page")
            subsection = nav.get("subsection")
            if page:
                st.session_state.current_page = page
                if subsection:
                    st.session_state.current_subsection = subsection
                st.session_state.copilot_open = False
                st.rerun()

    panel.float(float_css_helper(
        top="0px",
        right="0px",
        css="""
            z-index: 999998;
            position: fixed !important;
            width: 360px !important;
            height: 100vh !important;
            background: rgba(255, 255, 255, 0.92) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-left: 1px solid rgba(229, 231, 235, 0.6) !important;
            box-shadow: -8px 0 40px rgba(0, 0, 0, 0.06) !important;
            padding: 24px 20px !important;
            overflow-y: auto !important;
            border-radius: 0 !important;
        """
    ))


def _get_display_messages(messages):
    display = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user" and isinstance(content, str):
            display.append({"role": "user", "content": content})
        elif role == "assistant":
            if isinstance(content, str):
                display.append({"role": "assistant", "content": content})
            elif isinstance(content, list):
                text_parts = []
                for block in content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                    elif isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                if text_parts:
                    display.append({"role": "assistant", "content": "\n".join(text_parts)})
    return display
