import streamlit as st # Session refresh enabled
import os
import json
from tools import screen_market, fetch_screener_df
from agent import create_financial_agent, run_analysis
from portfolio_engine import PaperPortfolio
from paper_trade_ui import render_paper_trader
from auth_ui import render_auth_page, render_user_header, is_authenticated, sync_supabase_session
from education_ui import render_education
from chat_ui import render_chat

st.set_page_config(
    page_title="TradeFox: AI Paper Money Trading Academy!",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Navigation Logic & State Setup ───────────────────────────────────────────
if 'active_page' not in st.session_state:
    st.session_state.active_page = "🎓 Education"

def set_page(page_name):
    st.session_state.active_page = page_name

with st.sidebar:
    st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
    if not is_authenticated():
        st.markdown("### 🏠 Welcome to TradeFox")
        st.info("Sign In or Continue as Guest to begin.")
    
    st.markdown("### 🏠 Navigation")
    page_options = [
        "🎓 Education",
        "📊 Stock Screener",
        "🔍 Single Stock Analyst",
        "🌐 Macro Portfolio Analyst",
        "💰 Paper Money Trading"
    ]
    
    current_idx = page_options.index(st.session_state.active_page) if st.session_state.active_page in page_options else 0
    selected_page = st.radio("Select Section", page_options, index=current_idx, label_visibility="collapsed")
    
    if selected_page != st.session_state.active_page:
        st.session_state.active_page = selected_page
        st.rerun()

    if st.button("🏠 Back to Home", use_container_width=True):
        set_page("🎓 Education")
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ How it works")
    st.markdown("""
1. 🎓 Learn the basics in **Education**
2. 📊 Screen the market for opportunities
3. 🔍 Deep-dive any stock with **AI Analyst**
4. 🌐 Evaluate macro risks for your portfolio
5. 💰 Practice risk-free with **Paper Money Trading**
6. 🤖 **Ask Finley** in any tab for help!
    """)
    st.markdown("---")
    for sec_name, sec_icon, sec_desc in [
        ("🎓 Education", "🎓", "Interactive stock market school for all levels."),
        ("📊 Stock Screener", "📊", "Scan global markets for undervalued stocks."),
        ("🔍 Single Stock Analyst", "🔍", "AI-powered deep-dive on any stock ticker."),
        ("🌐 Macro Portfolio Analyst", "🌐", "Personalized macro risk analysis for your holdings."),
        ("💰 Paper Money Trading", "💰", "Simulated trading with virtual cash.")
    ]:
        with st.expander(f"{sec_icon} {sec_name}"):
            st.markdown(sec_desc)
    st.markdown("---")
    st.caption("🤖 AI powered by Llama 3.3 via Groq")
    st.caption("🚀 Build v1.1.2 - March 16")

# ── Force Expand Script (Aggressive fallback) ────────────────────────────────
st.markdown("""
<script>
    (function() {
        const pdoc = window.parent.document;
        const forceExpand = () => {
            const sidebar = pdoc.querySelector('section[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {
                const expandBtn = pdoc.querySelector('[data-testid="collapsedControl"]') ||
                                  pdoc.querySelector('[data-testid="stSidebarCollapsedControl"]') || 
                                  pdoc.querySelector('button[aria-label="Expand sidebar"]');
                if (expandBtn) {
                    expandBtn.click();
                    // Also dispatch native event to be sure
                    expandBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    return true;
                }
            }
            return false;
        };
        // Run repeatedly for 5s to override internal Streamlit state
        const expandInterval = setInterval(forceExpand, 500);
        setTimeout(() => clearInterval(expandInterval), 5000);
    })();
</script>
""", unsafe_allow_html=True)

# Custom CSS — White / Red / Black / Grey palette
st.markdown("""
<style>
    /* ── Core Layout ───────────────────────────────── */
    .stApp {
        background: #ffffff;
        color: #111827;
        font-family: 'Inter', sans-serif;
    }

    /* ── Sidebar ────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #f3f4f6;
        border-right: 2px solid #e5e7eb;
    }
    /* Darken and Resize Sidebar Labels */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    /* Ensure Sign Out and Back to Home button text is WHITE */
    [data-testid="stSidebar"] button p {
        color: #ffffff !important;
    }
    /* Ensure "How it works" list items are also black/larger */
    [data-testid="stSidebar"] li {
        color: #000000 !important;
        font-size: 1.05rem !important;
        font-weight: 500;
    }

    /* ── Headers ────────────────────────────────────── */
    h1, h2, h3, h4 {
        color: #111827;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* ── Tab Bar ────────────────────────────────────── */
    [data-testid="stTabs"] button {
        color: #6b7280;
        font-weight: 600;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #FF0000 !important;
        border-bottom: 2px solid #FF0000 !important;
    }

    /* ── Freeze Header ────────────────────────────── */
    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.95);
        z-index: 1000 !important;
    }
    
    /* ── Result Card ─────────────────────────────────── */
    .result-card {
        background: #f9fafb;
        padding: 24px;
        border-radius: 12px;
        border-left: 4px solid #FF0000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-top: 16px;
        color: #111827;
    }

    /* ── Tables ─────────────────────────────────────── */
    table { width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; }
    th {
        background-color: #111827;
        color: #ffffff;
        font-weight: 600;
        text-align: left;
        padding: 11px 14px;
    }
    td { padding: 10px 14px; border-bottom: 1px solid #e5e7eb; color: #111827; }
    tr:hover td { background-color: #fef2f2; }

    /* ── Metric Values ───────────────────────────────── */
    div[data-testid="stMetricValue"] { color: #FF0000; }

    /* ── Primary Buttons ─────────────────────────────── */
    .stButton>button {
        background: #FF0000;
        color: #ffffff;
        border-radius: 8px;
        border: none;
        padding: 0.55rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(255,0,0,0.30);
    }
    .stButton>button:hover {
        background: #CC0000;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(255,0,0,0.45);
    }

    /* ── Inputs / Selects ────────────────────────────── */
    .stTextInput>div>div>input, .stSelectbox>div>div {
        border: 1px solid #d1d5db;
        border-radius: 8px;
        color: #111827;
        background: #ffffff;
    }

    /* ── Spinners / Info Boxes ───────────────────────── */
    .stSpinner > div { border-top-color: #FF0000 !important; }
    .stAlert { border-radius: 8px; }

    /* ── Dataframe / Table header ────────────────────── */
    [data-testid="stDataFrame"] th {
        background-color: #111827 !important;
        color: #ffffff !important;
    }
    [data-testid="stDataFrame"] tr:hover td { background-color: #fef2f2 !important; }

    /* ── Scrollbar ───────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f3f4f6; }
    ::-webkit-scrollbar-thumb { background: #9ca3af; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #e11d48; }

    /* ── Hide Radio Button Circles and Style Labels ── */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        display: none;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: transparent !important;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 4px 8px !important;
        margin-bottom: 4px;
        transition: all 0.2s;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #fef2f2 !important;
    }
    /* Hide the actual radio circle */
    div[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stRadioButtonDot"] {
        display: none !important;
    }
    /* Style the selected label */
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {
        background: #fef2f2 !important;
        border: 1px solid #FF0000 !important;
        color: #FF0000 !important;
    }

    /* ── Hide Developer Tools ── */
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    .stDeployButton, .stAppDeployButton {display: none !important;}
    
    /* 5. Reposition and Style Native Sidebar Controls to Middle-Left Edge */
    
    /* Expand Button (when collapsed) */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 50% !important;
        left: 0 !important;
        transform: translateY(-50%) !important;
        z-index: 10000005 !important; /* Higher than stHeader (10000001) */
        display: flex !important;
        visibility: visible !important;
        background: white !important;
        border: 1.5px solid #d1d5db !important;
        border-radius: 0 10px 10px 0 !important;
        width: 32px !important;
        height: 56px !important;
        box-shadow: 4px 0 12px rgba(0,0,0,0.18) !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="collapsedControl"]:hover {
        background: #FF0000 !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: #374151 !important;
        pointer-events: auto !important;
        visibility: visible !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover button,
    [data-testid="collapsedControl"]:hover button {
        color: white !important;
    }
    /* Replace SVG with Arrow Icon */
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] button::after,
    [data-testid="collapsedControl"] button::after {
        content: "»" !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
    }

    /* Collapse Button (when expanded) */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="sidebarCollapseButton"] {
        position: absolute !important;
        top: 50% !important;
        right: -16px !important;
        transform: translateY(-50%) !important;
        z-index: 10000000 !important;
        display: flex !important;
        visibility: visible !important;
        background: white !important;
        border: 1.5px solid #d1d5db !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.15) !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="sidebarCollapseButton"]:hover {
        background: #FF0000 !important;
    }
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="sidebarCollapseButton"] button {
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: #374151 !important;
        pointer-events: auto !important;
        visibility: visible !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover button,
    [data-testid="sidebarCollapseButton"]:hover button {
        color: white !important;
    }
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="sidebarCollapseButton"] svg {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"] button::after,
    [data-testid="sidebarCollapseButton"] button::after {
        content: "«" !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
    }

    /* Global Visibility and Layering Fixes */
    [data-testid="stSidebarHeader"] {
        background: transparent !important;
        padding: 0 !important;
        min-height: 0 !important;
        overflow: visible !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important; 
        z-index: 10000001 !important; /* Higher than Ribbons (999999) */
    }
    header[data-testid="stHeader"] button {
        pointer-events: auto !important;
    }
    
    /* ── Main Content Area ─────────────────────────── */
    .block-container {
        padding-top: 0.1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Offset main content — Header ribbons occupy ~40-50px */
    div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: 0px !important; 
    }
</style>
""", unsafe_allow_html=True)

# ── App Header (shown when authenticated) ────────────────────────────────────
render_user_header()

header_title_html = """
<div class="ultra-compact-header">
    <span class="title-text">📈 TradeFox: AI Paper Money Trading Academy!</span>
    <span class="desc-text"> | AI-powered analysis & insights</span>
</div>

<style>
    .ultra-compact-header {
        display: flex;
        align-items: center;
        background: transparent;
        height: 28px;
    }
    .title-text {
        font-size: 0.9rem;
        font-weight: 800;
        color: #111827;
        margin-right: 8px;
    }
    .desc-text {
        font-size: 0.68rem;
        color: #6b7280;
    }
</style>
"""

# ── Scrolling Ribbons ────────────────────────────────────────────────────────
import yfinance as yf_ribbon

@st.cache_data(ttl=300)
def get_index_ribbon_html():
    indices = {
        "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "Dow Jones": "^DJI",
        "FTSE 100": "^FTSE", "Nikkei 225": "^N225", "Hang Seng": "^HSI",
        "BSE Sensex": "^BSESN", "Shanghai": "000001.SS", "KOSPI": "^KS11",
        "DAX": "^GDAXI", "CAC 40": "^FCHI", "ASX 200": "^AXJO",
        "Russell 2000": "^RUT", "VIX": "^VIX"
    }
    items = []
    for name, sym in indices.items():
        try:
            t = yf_ribbon.Ticker(sym)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev  = hist['Close'].iloc[-2]
                chg   = (price - prev) / prev * 100
                arrow = "▲" if chg >= 0 else "▼"
                color = "#FF0000" if chg < 0 else "#22c55e" # Bright Red for negative
                items.append(
                    f'<span class="idx-item"><b>{name}</b> &nbsp;'
                    f'<span style="color:#f9fafb">{price:,.2f}</span>&nbsp;'
                    f'<span style="color:{color}">{arrow} {abs(chg):.2f}%</span></span>'
                )
        except Exception: pass
    return items

@st.cache_data(ttl=300)
def get_news_ribbon_html():
    items = []
    seen = set()
    # Diversify news sources: US, Europe, Asia, India, Crypto, Commodities
    global_tickers = [
        "^GSPC", "^IXIC",          # US
        "^FTSE", "^GDAXI", "^FCHI", # Europe (UK, Germany, France)
        "^N225", "^HSI",           # Asia (Japan, HK)
        "^BSESN",                  # India
        "^AXJO",                   # Australia
        "GC=F", "CL=F",            # Commodities (Gold, Oil)
        "BTC-USD"                  # Crypto
    ]
    for sym in global_tickers:
        try:
            news = yf_ribbon.Ticker(sym).news or []
            # Take only top 2 from each to ensure diversity across the ribbon
            for n in news[:2]:
                title = n.get('content', {}).get('title', '') or n.get('title', '')
                # Handle deeply nested yfinance news structure
                link = n.get('link')
                if not link and 'content' in n:
                    link = n['content'].get('canonicalUrl', {}).get('url')
                if not link:
                    link = "#"
                
                if title and title not in seen:
                    seen.add(title)
                    items.append(f'<span class="news-item">📰 <a href="{link}" target="_blank" style="color: inherit; text-decoration: none;">{title}</a></span>')
        except Exception: pass
    return items

def render_ribbon_html(items, bg_color, ribbon_id="ribbon"):
    if not items: return ""
    track = "".join(items * 2)
    # Return JUST the container; CSS will be consolidated at the end
    return f'<div class="ribbon-wrap-{ribbon_id}"><div class="ribbon-track-{ribbon_id}">{track}</div></div>'

with st.spinner("Loading market data..."):
    index_items = get_index_ribbon_html()
    news_items  = get_news_ribbon_html()

idx_html = render_ribbon_html(index_items, bg_color="#111827", ribbon_id="idx")
news_html = render_ribbon_html(news_items, bg_color="#374151", ribbon_id="news")

# Consolidate all Header CSS and HTML into one clean block to prevent rendering bugs
sticky_header_html = f"""
<style>
    /* 1. Global Header Wrapper */
    .header-sticky-wrapper {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background: white;
        border-bottom: 1px solid #e5e7eb;
        pointer-events: auto;
        display: flex;
        flex-direction: column;
        align-items: center; /* Center horizontally */
        padding-top: 4px;
        padding-bottom: 2px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    }}
    
    /* 2. Centered Title Section */
    .ultra-compact-title {{
        text-align: center;
        margin-bottom: 4px;
        padding: 0 4rem; /* Space for sidebar and guest badge */
    }}
    .title-text {{
        font-size: 1.4rem;
        font-weight: 800;
        color: #111827;
        display: block;
    }}
    .desc-text-hide {{ display: none; }}
    
    /* 3. Ribbons Stacked Vertically */
    .ribbons-container {{
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 2px;
        padding: 0 12px;
    }}
    .ribbons-container > div {{
        width: 100%;
        height: 18px;
        border-radius: 3px;
        overflow: hidden;
        position: relative;
    }}
    
    .ribbon-track-idx, .ribbon-track-news {{
        display: flex;
        align-items: center;
        white-space: nowrap;
        font-size: 0.68rem;
        color: #f3f4f6;
        height: 100%;
        width: fit-content; /* Ensure track spans content */
    }}
    .ribbon-track-idx {{ animation: ticker-idx 20s linear infinite; background: #111827; }}
    .ribbon-track-news {{ animation: ticker-news 120s linear infinite; background: #374151; }}
    
    @keyframes ticker-idx {{ 
        0% {{ transform: translateX(0); }} 
        100% {{ transform: translateX(-50%); }} 
    }}
    @keyframes ticker-news {{ 
        0% {{ transform: translateX(0); }} 
        100% {{ transform: translateX(-50%); }} 
    }}
    
    .idx-item {{ margin-right: 40px; }}
    .news-item {{ margin-right: 50px; }}
    .news-item a:hover {{ text-decoration: underline !important; color: #FF0000 !important; }}
</style>

<div class="header-sticky-wrapper">
    <div class="ultra-compact-title">
        <span class="title-text">📈 TradeFox: AI Paper Money Trading Academy!</span>
    </div>
    <div class="ribbons-container">
        {idx_html}
        {news_html}
    </div>
</div>

<script>
    // Robust anchor to top to combat Streamlit's chat_input auto-scroll
    const anchorTop = () => {{
        try {{
            window.parent.scrollTo(0, 0);
            const view = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
            const main = window.parent.document.querySelector('.main');
            if (view) view.scrollTop = 0;
            if (main) main.scrollTop = 0;
        }} catch(e) {{}}
    }};
    anchorTop();
    const anchorInterval = setInterval(anchorTop, 50);
    setTimeout(() => clearInterval(anchorInterval), 4000); // give it 4 seconds to override the chatbot init
</script>
"""
st.markdown(sticky_header_html, unsafe_allow_html=True)

# ── Auth Gate ────────────────────────────────────────────────────────────────
if not is_authenticated():
    render_auth_page()
    st.stop()

# Load API Key for the modules below
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

# ── Portfolio Engine Setup ────────────────────────────────────────────────
from portfolio_engine import PaperPortfolio, GuestPortfolio

user_id = st.session_state.get("user_id")
is_guest = (user_id == "guest_user")
portfolio = None

if is_guest:
    if 'portfolio' not in st.session_state or not isinstance(st.session_state.get('portfolio'), GuestPortfolio):
        st.session_state['portfolio'] = GuestPortfolio()
    portfolio = st.session_state['portfolio']
elif user_id:
    sync_supabase_session()
    access_token = st.session_state.get("access_token")
    if 'portfolio' not in st.session_state or not isinstance(st.session_state.get('portfolio'), PaperPortfolio) or st.session_state.get('portfolio_user_id') != user_id:
        st.session_state['portfolio'] = PaperPortfolio(user_id=user_id, access_token=access_token)
        st.session_state['portfolio_user_id'] = user_id
    else:
        st.session_state['portfolio'].refresh_client(access_token)
    portfolio = st.session_state['portfolio']

# ── Page Rendering ──────────────────────────────────────────────────────────
active_page = st.session_state.active_page

if active_page == "🎓 Education":
    render_education()
    render_chat(groq_api_key, tab_context="education")

elif active_page == "📊 Stock Screener":
    st.markdown("<h3 style='font-size: 1.1rem; margin-top: 0;'>📊 Market Screener</h3>", unsafe_allow_html=True)
    st.markdown("Scan the market for potentially undervalued, overvalued, or equal valued stocks.")
    
    col1a, col1b, col1c, col1d = st.columns(4)
    with col1a: asset_class = st.selectbox("Asset Class", ["Stocks", "ETFs", "Mutual Funds"])
    with col1b: valuation = st.selectbox("Valuation Category", ["Undervalued", "Equal Valued", "Overvalued", "Any"], disabled=(asset_class != "Stocks"))
    with col1c:
        sec_options = ["Technology", "Healthcare", "Financial", "Energy", "Consumer Cyclical", "Basic Materials", "Communication Services", "Industrials", "Consumer Defensive", "Real Estate", "Utilities", "All Stocks"]
        sector = st.selectbox("Sector", sec_options if asset_class == "Stocks" else ["N/A"], disabled=(asset_class != "Stocks"))
    with col1d:
        regions = ["United States", "India", "United Kingdom", "Germany", "France", "Canada", "Australia", "Taiwan", "Singapore", "Brazil", "Japan", "China", "South Korea", "Hong Kong"]
        region_choice = st.selectbox("Market Region", regions)
            
    if st.button("Run Screener", type="primary"):
        with st.spinner(f"Scanning {asset_class}..."):
            try:
                df_result, result_title = fetch_screener_df(asset_class, valuation, sector, region_choice)
                st.session_state['screener_df'] = df_result
                st.session_state['screener_title'] = result_title
                st.session_state['screener_page'] = 0
            except Exception as e:
                st.error(f"⚠️ Screener error: {e}")

    if 'screener_df' in st.session_state and st.session_state['screener_df'] is not None:
        df_all = st.session_state['screener_df']
        title = st.session_state.get('screener_title', 'Screener Results')
        st.markdown("---")
        if df_all.empty:
            st.warning(f"⚠️ {title}")
        else:
            PAGE_SIZE = 10
            total_rows = len(df_all)
            total_pages = max(1, (total_rows + PAGE_SIZE - 1) // PAGE_SIZE)
            page = st.session_state.get('screener_page', 0)
            
            hcol1, hcol2 = st.columns([3, 1])
            with hcol1: st.markdown(f"### {title}")
            with hcol2: st.markdown(f"<p style='text-align:right;color:#94a3b8;padding-top:0.6rem;'>Page {page+1} of {total_pages}</p>", unsafe_allow_html=True)
            
            start = page * PAGE_SIZE
            end = min(start + PAGE_SIZE, total_rows)
            df_page = df_all.iloc[start:end].copy()
            
            if "Market Cap" in df_page.columns:
                df_page["Market Cap"] = df_page["Market Cap"].apply(lambda x: x / 1e9 if isinstance(x, (int, float)) and x > 0 else x)
            
            st.dataframe(df_page, use_container_width=True, hide_index=True, column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Market Cap": st.column_config.NumberColumn("Mkt Cap ($B)", format="%.2fB"),
                "Price": st.column_config.NumberColumn("Price", format="%.2f"),
                "Div Yield": st.column_config.NumberColumn("Div Yield", format="%.2f%%"),
            })
            
            st.markdown("---")
            invest_col1, invest_col2 = st.columns([1, 2])
            with invest_col1: sel_ticker = st.selectbox("Select ticker to Paper Trade", df_page['Ticker'].tolist())
            with invest_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📥 Paper Trade Selected", type="primary"):
                    st.session_state['paper_trade_ticker'] = sel_ticker
                    st.session_state['paper_trade_notes'] = "Found via Screener"
                    st.session_state['show_order_ticket'] = True
                    st.success(f"Ready! Switch to '💰 Paper Trader' tab.")
            
            pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
            if pcol1.button("◀ Prev", disabled=(page == 0)):
                st.session_state['screener_page'] -= 1
                st.rerun()
            pcol2.markdown(f"<p style='text-align:center;color:#94a3b8;'>Showing {start+1}–{end} of {total_rows}</p>", unsafe_allow_html=True)
            if pcol3.button("Next ▶", disabled=(page >= total_pages - 1)):
                st.session_state['screener_page'] += 1
                st.rerun()

    render_chat(groq_api_key, tab_context="screener")

elif active_page == "🔍 Single Stock Analyst":
    st.markdown("<h3 style='font-size: 1.1rem; margin-top: 0;'>🔍 Single Stock Analyst</h3>", unsafe_allow_html=True)
    st.markdown("Deep dive into stock financials and AI-powered analysis.")
    ticker_input = st.text_input("Enter Ticker (e.g., AAPL)").upper()
    
    if st.button("Run AI Analysis", type="primary"):
        if not groq_api_key: st.error("⚠️ API key missing.")
        elif not ticker_input: st.error("⚠️ Enter a ticker.")
        else:
            try:
                agent = create_financial_agent(groq_api_key)
                st.markdown(f"### Analyzing {ticker_input}...")
                
                col_chart, col_broker = st.columns([2, 1])
                with col_chart:
                    with st.expander("📈 Price Chart", expanded=True):
                        try:
                            hist = yf_ribbon.Ticker(ticker_input).history(period="1y")
                            if not hist.empty: st.line_chart(hist['Close'])
                        except: st.info("Chart unavailable.")
                with col_broker:
                    with st.expander("🏦 Wall Street Consensus", expanded=True):
                        from tools import get_analyst_recommendations
                        st.markdown(get_analyst_recommendations.invoke({"ticker": ticker_input}))
                
                st.markdown("### 🤖 Agent Analysis")
                status = st.empty()
                report = st.empty()
                
                with st.spinner("Analyzing..."):
                    query = f"Deep dive analysis on {ticker_input}. Conclude with Buy/Hold/Sell."
                    for msg in run_analysis(agent, query):
                        if msg.type == "ai" and msg.content:
                            status.success("Complete!")
                            report.markdown(f"<div class='result-card'>{msg.content}</div>", unsafe_allow_html=True)
                            if st.button("📥 Paper Trade This Stock"):
                                st.session_state['paper_trade_ticker'] = ticker_input
                                st.session_state['paper_trade_notes'] = f"AI Analyst: {msg.content[:100]}..."
                                st.session_state['show_order_ticket'] = True
                                st.success("Ready! Switch to Paper Trader.")
            except Exception as e: st.error(f"Error: {e}")

    render_chat(groq_api_key, tab_context="analyst")

elif active_page == "🌐 Macro Portfolio Analyst":
    st.markdown("<h3 style='font-size: 1.1rem; margin-top: 0;'>🌐 Macro Portfolio Analyst</h3>", unsafe_allow_html=True)
    st.markdown("Analyze your holdings against Fed policy and global trends.")
    
    uploaded_file = st.file_uploader("📥 Optional: Upload Positions (CSV)", type=["csv"])
    if uploaded_file:
        import pandas as pd
        try:
            df = pd.read_csv(uploaded_file, on_bad_lines='skip')
            for col in df.columns:
                if str(col).strip().lower() in ['symbol', 'ticker']:
                    symbols = ", ".join(df[col].dropna().astype(str).unique())
                    st.session_state['portfolio_input'] = symbols
                    st.success("✅ Portfolio loaded!")
                    break
        except Exception as e: st.error(f"Error: {e}")
            
    portfolio_input = st.text_area("Portfolio Tickers (comma separated)", value=st.session_state.get('portfolio_input', "NVDA, AMD"))
    horizon = st.selectbox("Horizon", ["5 Years", "3 Years", "10 Years"])
    
    if st.button("Generate Macro Plan", type="primary"):
        if not groq_api_key: st.error("⚠️ Key missing.")
        else:
            try:
                from agent import create_macro_analyst_agent
                macro_agent = create_macro_analyst_agent(groq_api_key)
                status = st.empty()
                report = st.empty()
                with st.spinner("Analyzing macro environment..."):
                    query = f"Portfolio: {portfolio_input}. Horizon: {horizon}. Analyze risks vs Fed policy."
                    for msg in run_analysis(macro_agent, query):
                        if msg.type == "ai" and msg.content:
                            status.success("Complete!")
                            report.markdown(f"<div class='result-card'>{msg.content}</div>", unsafe_allow_html=True)
                            if st.button("📥 Execute Plan in Paper Trader"):
                                first = [t.strip() for t in portfolio_input.split(",") if t.strip()][0]
                                st.session_state['paper_trade_ticker'] = first
                                st.session_state['show_order_ticket'] = True
                                st.success("Ready! Switch to Paper Trader.")
            except Exception as e: st.error(f"Error: {e}")

    render_chat(groq_api_key, tab_context="macro")

elif active_page == "💰 Paper Money Trading":
    if is_guest:
        st.markdown("<h3 style='font-size: 1.1rem; margin-top: 0;'>💰 Paper Money Trading</h3>", unsafe_allow_html=True)
        st.warning("⚠️ **Guest Mode:** Trades will not be permanently saved. Create an account for a persistent portfolio.")
    
    # We now pass the local GuestPortfolio so the UI renders fully
    render_paper_trader(portfolio)
    render_chat(groq_api_key, tab_context="paper_trader")
