import streamlit as st

USERS = {
    "admin": "5881",
    "Grace": "GraceOunh",
    "Patrick": "PatrickNdukwe",
}

def login():
    st.markdown("""
    <style>
    .login-box {
        max-width: 380px;
        margin: 80px auto;
        padding: 40px;
        background: #0d1117;
        border: 1px solid #21262d;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔐 Stock Dashboard Login")

    with st.form("login_form"):
        user = st.text_input("Username")
        pw   = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if user in USERS and USERS[user] == pw:
            st.session_state.logged_in = True
            st.session_state.username  = user
            st.rerun()
        else:
            st.error("❌ Wrong credentials — try again.")