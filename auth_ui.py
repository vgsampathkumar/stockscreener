import streamlit as st # Session refresh enabled
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

    import base64
    import os

    # Load and encode the background image
    bg_img_path = os.path.join("assets", "login_bg.png")
    if os.path.exists(bg_img_path):
        with open(bg_img_path, "rb") as f:
            data = f.read()
            encoded_img = base64.b64encode(data).decode()
    else:
        encoded_img = ""

    st.markdown(f"""
    <style>
    /* Apply background to the absolute main container */
    [data-testid="stAppViewContainer"] {{
        background: url("data:image/png;base64,{encoded_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    
    /* Ensure the header and other parts don't block the background */
    [data-testid="stHeader"], [data-testid="stToolbar"] {{
        background: rgba(0,0,0,0) !important;
    }}

    .auth-container {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(25px) saturate(180%);
        -webkit-backdrop-filter: blur(25px) saturate(180%);
        padding: 40px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.4);
        width: 100%;
        margin: 40px 0;
        color: white;
        text-align: center;
    }}
    
    h1, h2, p {{
        color: white !important;
        text-shadow: 2px 2px 10px rgba(0,0,0,0.8);
        font-family: 'Inter', sans-serif;
    }}

    /* Tab styling for Dark/Transparent background */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent !important;
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: rgba(255,255,255,0.7) !important;
        background-color: rgba(255,255,255,0.05) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: white !important;
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-bottom: 3px solid #FF0000 !important;
    }}
    
    /* Input fields visibility */
    .stTextInput input {{
        background-color: rgba(255,255,255,0.9) !important;
        color: black !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col2:
        st.markdown("""
        <div class="auth-container">
            <div style="margin-bottom:20px;">
                <h1 style="font-size:2.2em; margin:0; line-height: 1.1;">📈 Trade Fox</h1>
                <h2 style="color:white; font-size:1.3em; opacity:0.9;">AI Financial Academy</h2>
                <p style="margin-top:12px; font-weight: 500; font-size:1.05em;">Empowering the next generation of investor</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_in, tab_up, tab_guest = st.tabs(["🔑 Sign In", "📝 Sign Up", "🕵️ Guest"])

        # ── Sign In ─────────────────────────────────────────────────────────
        with tab_in:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Google OAuth Sign In ---
            try:
                # Ask supabase to generate the oauth link
                # We need to explicitly pass the redirect URL to where the streamlit app lives
                redirect_uri = "https://papermoneytrading.streamlit.app"
                res_oauth = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": redirect_uri}})
                if hasattr(res_oauth, 'url'):
                    st.link_button("🌐 Continue with Google", res_oauth.url, type="secondary", use_container_width=True)
                    st.markdown("<div style='text-align:center; padding: 10px 0;'>&mdash; or &mdash;</div>", unsafe_allow_html=True)
            except Exception as e:
                pass # Fallback to password only if OAuth is not configured
                
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
                                
        # ── Guest Login ──────────────────────────────────────────────────────
        with tab_guest:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("Try out the TradeFox: AI Paper Trading Academy without creating an account. Portfolios will not be permanently saved.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Continue as Guest", key="btn_guest", use_container_width=True):
                # We use a dummy guest fallback in portfolio_engine
                st.session_state["user_id"] = "guest_user"
                st.session_state["user_email"] = "Guest Explorer"
                st.session_state["access_token"] = "guest_token_123"
                st.rerun()

def render_user_header():
    # Renders the logged-in user badge using fixed CSS, and places Sign Out in sidebar if active.
    email = st.session_state.get("user_email", "Guest")
    st.markdown(f"""
        <style>
        .user-badge-fixed {{
            position: fixed;
            top: 6px;
            right: 80px;
            z-index: 1000002;
            background: rgba(255, 255, 255, 0.95);
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: #111827;
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        </style>
        <div class='user-badge-fixed'>👤 {email}</div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("""
            <style>
            .stButton>button[key="btn_signout"] {
                background-color: #FF0000 !important;
                color: white !important;
            }
            .stButton>button[key="btn_signout"]:hover {
                background-color: #CC0000 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Sign Out", key="btn_signout", use_container_width=True):
            try:
                if st.session_state.get("user_id") != "guest_user":
                    supabase = get_supabase()
                    supabase.auth.sign_out()
            except Exception:
                pass
            for key in ["user_id", "user_email", "access_token", "selected_account",
                        "show_order_ticket", "show_quote_modal", "guest_db"]:
                st.session_state.pop(key, None)
            st.rerun()


def sync_supabase_session():
    """
    Checks the Supabase session and updates st.session_state if refreshed.
    Call this on every app rerun to ensure the access_token is valid.
    """
    if st.session_state.get("user_id") and st.session_state.get("user_id") != "guest_user":
        supabase = get_supabase()
        try:
            # get_session() returns current session if valid, or refreshes if expired/near-expiry
            # provided the refresh_token is available in the client's auth state.
            res = supabase.auth.get_session()
            if res and res.session:
                new_token = res.session.access_token
                if st.session_state.get("access_token") != new_token:
                    st.session_state["access_token"] = new_token
        except Exception as e:
            # If session is invalid/expired and can't be refreshed, sign out
            st.warning(f"Session expired. Please sign in again. ({e})")
            for key in ["user_id", "user_email", "access_token", "selected_account"]:
                st.session_state.pop(key, None)
            st.rerun()

def is_authenticated() -> bool:
    """Returns True if a valid user session exists in session_state."""
    return bool(st.session_state.get("user_id"))
