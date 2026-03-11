import streamlit as st
from supabase import create_client, Client

def get_supabase() -> Client:
    """Get the Supabase client, initialized from st.secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def render_auth_page():
    """
    Renders the Sign In / Sign Up page.
    On success, stores user_id and access_token in st.session_state.
    Returns True if user is authenticated, False otherwise.
    """
    supabase = get_supabase()

    st.markdown("""
    <div style="max-width:420px; margin:60px auto 0 auto;">
        <div style="text-align:center; margin-bottom:32px;">
            <h1 style="color:#008a00; font-size:2.4em; margin:0;">📈 Paper Trader</h1>
            <p style="color:#6b7280; margin-top:8px;">Powered by Fidelity-style simulated trading</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_in, tab_up = st.tabs(["🔑 Sign In", "📝 Sign Up"])

        # ── Sign In ─────────────────────────────────────────────────────────
        with tab_in:
            st.markdown("<br>", unsafe_allow_html=True)
            email_in = st.text_input("Email", key="signin_email", placeholder="you@example.com")
            pass_in = st.text_input("Password", key="signin_pass", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In", key="btn_signin", use_container_width=True):
                if not email_in or not pass_in:
                    st.error("Please enter both email and password.")
                else:
                    with st.spinner("Signing in..."):
                        try:
                            res = supabase.auth.sign_in_with_password({
                                "email": email_in,
                                "password": pass_in
                            })
                            st.session_state["user_id"] = res.user.id
                            st.session_state["user_email"] = res.user.email
                            st.session_state["access_token"] = res.session.access_token
                            st.rerun()
                        except Exception as e:
                            err = str(e)
                            if "Invalid login" in err or "invalid_grant" in err.lower():
                                st.error("❌ Invalid email or password.")
                            else:
                                st.error(f"❌ Sign in failed: {err}")

        # ── Sign Up ─────────────────────────────────────────────────────────
        with tab_up:
            st.markdown("<br>", unsafe_allow_html=True)
            email_up = st.text_input("Email", key="signup_email", placeholder="you@example.com")
            pass_up = st.text_input("Password (min 8 chars)", key="signup_pass", type="password", placeholder="••••••••")
            pass_up2 = st.text_input("Confirm Password", key="signup_pass2", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account", key="btn_signup", use_container_width=True):
                if not email_up or not pass_up:
                    st.error("Please fill in all fields.")
                elif len(pass_up) < 8:
                    st.error("Password must be at least 8 characters.")
                elif pass_up != pass_up2:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating account..."):
                        try:
                            res = supabase.auth.sign_up({
                                "email": email_up,
                                "password": pass_up
                            })
                            if res.user:
                                # Check if email confirmation is required
                                if res.session:
                                    st.session_state["user_id"] = res.user.id
                                    st.session_state["user_email"] = res.user.email
                                    st.session_state["access_token"] = res.session.access_token
                                    st.success("✅ Account created! Welcome to Paper Trader.")
                                    st.rerun()
                                else:
                                    st.success("✅ Account created! Please check your email to confirm your address, then Sign In.")
                        except Exception as e:
                            err = str(e)
                            if "already registered" in err.lower():
                                st.error("❌ This email is already registered. Please Sign In instead.")
                            else:
                                st.error(f"❌ Sign up failed: {err}")


def render_user_header():
    """Renders the logged-in user badge and Sign Out button in top-right."""
    email = st.session_state.get("user_email", "User")
    col_l, col_r = st.columns([5, 1])
    with col_r:
        st.markdown(f"<div style='text-align:right; color:#6b7280; font-size:0.85em; padding-top:4px;'>👤 {email}</div>", unsafe_allow_html=True)
        if st.button("Sign Out", key="btn_signout"):
            try:
                supabase = get_supabase()
                supabase.auth.sign_out()
            except Exception:
                pass
            for key in ["user_id", "user_email", "access_token", "selected_account",
                        "show_order_ticket", "show_quote_modal"]:
                st.session_state.pop(key, None)
            st.rerun()


def is_authenticated() -> bool:
    """Returns True if a valid user session exists in session_state."""
    return bool(st.session_state.get("user_id"))
