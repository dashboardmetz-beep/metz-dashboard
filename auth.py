"""
Authentication and permission helpers.
Password-based login using Streamlit session state.
Supports persistent "Remember Me" via local session file.
"""

import hashlib
import json
import os
import streamlit as st

# Path to the persistent session file (same directory as this script)
_SESSION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".auth_session"
)


def _hash_password(password):
    """Hash a password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(conn, username, password):
    """Verify a username/password combo against the database."""
    cur = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    )
    row = cur.fetchone()
    if not row or not row[0]:
        return False
    return row[0] == _hash_password(password)


def _save_session(username):
    """Save the username to a local file for persistent login."""
    try:
        with open(_SESSION_FILE, "w") as fh:
            json.dump({"username": username}, fh)
    except Exception:
        pass  # silently fail — non-critical


def _load_saved_session():
    """Load a previously saved session. Returns username or None."""
    try:
        if os.path.exists(_SESSION_FILE):
            with open(_SESSION_FILE, "r") as fh:
                data = json.load(fh)
            return data.get("username")
    except Exception:
        pass
    return None


def _clear_saved_session():
    """Delete the saved session file."""
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except Exception:
        pass


def login_page(conn, fetch_user_fn):
    """
    Render split-screen login page in the main content area.
    Returns user dict if login succeeds, otherwise None.
    Supports auto-login from a saved session file.
    """
    if "user" not in st.session_state:
        st.session_state.user = None
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""

    if st.session_state.user:
        return st.session_state.user

    # ─── Auto-login from saved session ───
    if "auto_login_checked" not in st.session_state:
        st.session_state.auto_login_checked = True
        saved_username = _load_saved_session()
        if saved_username:
            user = fetch_user_fn(conn, saved_username)
            if user:
                st.session_state.user = user
                st.session_state.login_error = ""
                st.rerun()
            else:
                # Saved user no longer exists — clear stale session
                _clear_saved_session()

    if st.session_state.user:
        return st.session_state.user

    # ─── Clean centered login ───
    import base64, os

    # Load logo as base64
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "metz_logo.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    st.markdown(
        '<style>'
        '[data-testid="stMain"] > div:first-child {'
        '  background: #FFFFFF !important; min-height:100vh;'
        '}'
        '[data-testid="stMain"] .stTextInput input {'
        '  background: #FFFFFF !important;'
        '  border: 1.5px solid #E2E8F0 !important;'
        '  border-radius: 8px !important;'
        '  color: #1E293B !important;'
        '  padding: 14px 16px !important;'
        '  font-size: 14px !important;'
        '}'
        '[data-testid="stMain"] .stTextInput input::placeholder {'
        '  color: #94A3B8 !important;'
        '}'
        '[data-testid="stMain"] .stTextInput input:focus {'
        '  border-color: #D4A843 !important;'
        '  box-shadow: 0 0 0 3px rgba(212,168,67,0.1) !important;'
        '}'
        '[data-testid="stMain"] .stCheckbox label span {'
        '  color: #64748B !important; font-size:13px !important;'
        '}'
        '[data-testid="stMain"] button[kind="primary"] {'
        '  background: #3D2B1F !important;'
        '  border: none !important; border-radius:8px !important;'
        '  padding: 14px !important; font-size:15px !important;'
        '  font-weight:600 !important; color:#fff !important;'
        '  -webkit-text-fill-color:#fff !important;'
        '}'
        '[data-testid="stMain"] button[kind="primary"]:hover {'
        '  background: #2A1E15 !important;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:60px"></div>', unsafe_allow_html=True)

    _, center, _ = st.columns([1.2, 2, 1.2])

    with center:
        # Logo — save your Metz logo as assets/metz_logo.png
        from PIL import Image as PILImage
        try:
            if os.path.exists(logo_path):
                PILImage.open(logo_path)  # validate
                _, logo_col, _ = st.columns([1, 2, 1])
                with logo_col:
                    st.image(logo_path, use_container_width=True)
            else:
                raise FileNotFoundError
        except Exception:
            # Fallback: text logo
            st.markdown(
                '<div style="text-align:center;margin-bottom:8px;">'
                '<div style="font-size:28px;font-weight:800;color:#3D2B1F;'
                'font-family:Georgia,serif;letter-spacing:-.5px;">Metz</div>'
                '<div style="font-size:10px;font-weight:600;color:#94A3B8;'
                'text-transform:uppercase;letter-spacing:0.15em;">'
                'Culinary Management</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        # Card
        st.markdown(
            '<div style="text-align:center;margin-bottom:28px;">'
            '<div style="font-size:24px;font-weight:700;color:#1E293B;'
            'letter-spacing:-.3px;">Access your dashboard</div>'
            '<div style="font-size:14px;color:#94A3B8;margin-top:6px;">'
            'Monitor performance, budgets, and operations in one place</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        username_input = st.text_input(
            "Username",
            placeholder="Username",
            key="login_username",
            label_visibility="collapsed",
        )
        password_input = st.text_input(
            "Password",
            type="password",
            placeholder="Password",
            key="login_password",
            label_visibility="collapsed",
        )

        remember_me = st.checkbox("Remember me", value=True, key="login_remember")

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        if st.button("Sign In", type="primary", use_container_width=True):
            if not username_input.strip() or not password_input:
                st.session_state.login_error = (
                    "Please enter both username and password."
                )
                st.rerun()
            elif _verify_password(conn, username_input.strip(), password_input):
                user = fetch_user_fn(conn, username_input.strip())
                if user:
                    st.session_state.user = user
                    st.session_state.login_error = ""
                    if remember_me:
                        _save_session(username_input.strip())
                    st.rerun()
                else:
                    st.session_state.login_error = "User not found."
                    st.rerun()
            else:
                st.session_state.login_error = "Invalid username or password."
                st.rerun()

        st.markdown(
            '<div style="text-align:center;margin-top:48px;'
            'font-size:11px;color:#CBD5E1;">'
            'Metz Culinary Management &middot; Campus Dining</div>',
            unsafe_allow_html=True,
        )

    return None


def render_user_sidebar(user):
    """Render the logged-in user card at the bottom of the sidebar."""
    # Build initials from display name
    parts = user["display_name"].split()
    initials = parts[0][0].upper()
    if len(parts) > 1:
        initials += parts[-1][0].upper()

    role_label = user["role"].capitalize()

    st.sidebar.markdown(
        '<div style="display:flex;align-items:center;gap:12px;'
        'padding:14px 16px;margin:4px 0;'
        'border-top:1px solid rgba(255,255,255,0.06);">'
        # Avatar circle with initials
        '<div style="width:38px;height:38px;border-radius:50%;'
        'background:linear-gradient(135deg,#4F7DF3,#6C8FF8);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:14px;font-weight:700;color:#FFFFFF;'
        'font-family:Inter,sans-serif;flex-shrink:0;'
        'position:relative;">'
        '{initials}'
        '<span style="position:absolute;bottom:0;right:0;'
        'width:10px;height:10px;border-radius:50%;'
        'background:#22C55E;border:2px solid #1B2540;"></span>'
        '</div>'
        # Name and role
        '<div style="min-width:0;">'
        '<div style="font-size:13px;font-weight:600;color:#FFFFFF;'
        'font-family:Inter,sans-serif;white-space:nowrap;'
        'overflow:hidden;text-overflow:ellipsis;">{name}</div>'
        '<div style="font-size:11px;color:rgba(255,255,255,0.4);'
        'font-family:Inter,sans-serif;margin-top:1px;">'
        '● {role}</div>'
        '</div>'
        '</div>'.format(
            initials=initials,
            name=user["display_name"],
            role=role_label,
        ),
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state.user = None
        st.session_state.login_error = ""
        st.session_state.auto_login_checked = False
        _clear_saved_session()
        st.rerun()


# Legacy compatibility — kept so old code importing login_sidebar does not break
def login_sidebar(conn, fetch_all_users_fn, fetch_user_fn):
    """Legacy wrapper. Use login_page + render_user_sidebar instead."""
    if "user" not in st.session_state:
        st.session_state.user = None
    return st.session_state.user


# ─────────────────────── Permission Helpers ───────────────────────


def can_edit_budget(user, status):
    """Check if user can edit a budget entry given its current status."""
    if user["role"] == "admin":
        return True
    if user["role"] == "editor" and status in ("Draft", "Returned"):
        return True
    return False


def can_approve_budget(user, status):
    """Check if user can approve a budget."""
    return user["role"] in ("approver", "admin") and status == "Submitted"


def can_return_budget(user, status):
    """Check if user can return a budget."""
    return user["role"] in ("approver", "admin") and status == "Submitted"


def can_unlock_budget(user, status):
    """Check if user (admin only) can unlock an approved budget."""
    return user["role"] == "admin" and status == "Approved"


def can_edit_daily(user, department):
    """Check if user can edit daily entries for a department."""
    if user["role"] == "admin":
        return True
    if user["role"] == "approver":
        return True
    if user["role"] == "editor" and user["department"] == department:
        return True
    return False


def can_set_targets(user):
    """Check if user can set budget/projection targets."""
    return user["role"] in ("admin", "approver")


def can_access_imports(user):
    """Check if user can access the Data Import page."""
    return user["role"] in ("admin", "approver")


def get_user_departments(user, all_departments):
    """Return the list of departments the user can access."""
    if user["role"] in ("admin", "approver"):
        return all_departments
    return [user["department"]] if user["department"] else []
