import sqlite3
import hashlib
import os
import streamlit as st

# ── Database setup ────────────────────────────────────────────────────────────
DB_PATH = "users.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Create the users table if it doesn't exist yet."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    UNIQUE NOT NULL COLLATE NOCASE,
                email       TEXT    UNIQUE NOT NULL COLLATE NOCASE,
                password    TEXT    NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# ── Password hashing (sha-256 + per-user salt, no extra libraries) ────────────

def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Return (hashed, salt). If salt is None, a new one is generated."""
    if salt is None:
        salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    hashed, _ = _hash_password(password, salt)
    return hashed == stored_hash


# ── Auth actions ──────────────────────────────────────────────────────────────

def _register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Returns (success, message).
    Stores password as  hash:salt  in the password column.
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email or "." not in email:
        return False, "Enter a valid email address."

    hashed, salt = _hash_password(password)
    stored = f"{hashed}:{salt}"

    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username.strip(), email.strip().lower(), stored),
            )
            conn.commit()
        return True, "Account created! You can now log in."
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        if "email" in str(e):
            return False, "Email already registered."
        return False, "Registration failed."


def _login_user(username: str, password: str) -> tuple[bool, str]:
    """Returns (success, message). Sets session state on success."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT username, password FROM users WHERE username = ?",
            (username.strip(),)
        ).fetchone()

    if row is None:
        return False, "No account found with that username."

    stored = row["password"]
    try:
        hashed, salt = stored.split(":", 1)
    except ValueError:
        return False, "Account error — please contact support."

    if _verify_password(password, hashed, salt):
        return True, row["username"]
    return False, "Incorrect password."


# ── Login / Register UI ───────────────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #080c10;
}
#MainMenu, footer, header { visibility: hidden; }

.auth-wrap {
    max-width: 400px;
    margin: 60px auto 0;
}
.auth-logo {
    text-align: center;
    font-size: 2rem;
    margin-bottom: 6px;
}
.auth-title {
    text-align: center;
    font-size: 1.35rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 2px;
    letter-spacing: -0.02em;
}
.auth-sub {
    text-align: center;
    font-size: 0.78rem;
    color: #2d3748;
    margin-bottom: 28px;
    font-family: 'JetBrains Mono', monospace;
}

/* Input fields */
.stTextInput input {
    background: #0d1520 !important;
    border: 1px solid #1a2030 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.85rem !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}
.stTextInput label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #4a5568 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

/* Submit button */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    border: none !important;
    border-radius: 9px !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 11px !important;
    width: 100% !important;
    letter-spacing: 0.03em !important;
    transition: opacity 0.2s !important;
    margin-top: 6px !important;
}
[data-testid="stFormSubmitButton"] button:hover { opacity: 0.88 !important; }

/* Tab switcher */
[data-baseweb="tab-list"] {
    background: #0d1520 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #1a2030 !important;
    margin-bottom: 24px !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 7px !important;
    color: #4a5568 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    flex: 1 !important;
    justify-content: center !important;
}
[aria-selected="true"] {
    background: #1a2030 !important;
    color: #e2e8f0 !important;
}

.stAlert { border-radius: 9px !important; font-size: 0.8rem !important; }
</style>
"""


def login():
    """Render the full login / register page."""
    _init_db()
    st.markdown(_CSS, unsafe_allow_html=True)

    # Centre the form
    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.markdown("""
        <div class="auth-logo">📈</div>
        <div class="auth-title">StockMarket Dashboard</div>
        <div class="auth-sub">sign in to your account</div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["  Sign In  ", "  Create Account  "])

        # ── Sign in ──────────────────────────────────────────────────────
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    ok, result = _login_user(username, password)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.username  = result
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")

        # ── Create account ───────────────────────────────────────────────
        with tab_register:
            with st.form("register_form"):
                new_user  = st.text_input("Username")
                new_email = st.text_input("Email")
                new_pw    = st.text_input("Password", type="password")
                new_pw2   = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not all([new_user, new_email, new_pw, new_pw2]):
                    st.error("Please fill in all fields.")
                elif new_pw != new_pw2:
                    st.error("❌ Passwords don't match.")
                else:
                    ok, msg = _register_user(new_user, new_email, new_pw)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")