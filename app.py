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
    page_title="Agentic Stock Screener Analyst & Papertrader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
        color: #e11d48 !important;
        border-bottom: 2px solid #e11d48 !important;
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
        border-left: 4px solid #e11d48;
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
    div[data-testid="stMetricValue"] { color: #e11d48; }

    /* ── Primary Buttons ─────────────────────────────── */
    .stButton>button {
        background: #e11d48;
        color: #ffffff;
        border-radius: 8px;
        border: none;
        padding: 0.55rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(225,29,72,0.30);
    }
    .stButton>button:hover {
        background: #be123c;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(225,29,72,0.45);
    }

    /* ── Inputs / Selects ────────────────────────────── */
    .stTextInput>div>div>input, .stSelectbox>div>div {
        border: 1px solid #d1d5db;
        border-radius: 8px;
        color: #111827;
        background: #ffffff;
    }

    /* ── Spinners / Info Boxes ───────────────────────── */
    .stSpinner > div { border-top-color: #e11d48 !important; }
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
</style>
""", unsafe_allow_html=True)

# ── Auth Gate ────────────────────────────────────────────────────────────────
if not is_authenticated():
    render_auth_page()
    st.stop()

# ── App Header (shown when authenticated) ────────────────────────────────────
render_user_header()

header_title_html = """
<div style="background: white; padding-bottom: 2px;">
    <h1 style="margin-bottom: 0;"> Agentic Stock Screener Analyst & Papertrader</h1>
    <p style="color: #6b7280; margin-top: 4px; margin-bottom: 8px;">An AI-powered financial analyst that screens for undervalued stocks, analyzes fundamentals, and provides actionable insights.</p>
</div>
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
                color = "#ffffff" if chg >= 0 else "#fca5a5"
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
    for sym in ["^GSPC", "^IXIC", "GC=F", "CL=F", "BTC-USD"]:
        try:
            news = yf_ribbon.Ticker(sym).news or []
            for n in news[:4]:
                title = n.get('content', {}).get('title', '') or n.get('title', '')
                if title and title not in seen:
                    seen.add(title)
                    items.append(f'<span class="news-item">📰 {title}</span>')
        except Exception: pass
    return items

def render_ribbon_html(items, bg_color, speed="40s", ribbon_id="ribbon"):
    if not items: return ""
    track = "".join(items * 2)
    return f"""
<style>
.ribbon-wrap-{ribbon_id} {{
    overflow: hidden;
    background: {bg_color};
    padding: 6px 12px;
    border-radius: 6px;
    margin-bottom: 6px;
    white-space: nowrap;
    position: relative;
}}
.ribbon-track-{ribbon_id} {{
    display: inline-block;
    white-space: nowrap;
    animation: ticker-{ribbon_id} {speed} linear infinite;
    font-size: 0.82rem;
    color: #f3f4f6;
}}
@keyframes ticker-{ribbon_id} {{
    0%   {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
}}
.idx-item  {{ margin-right: 48px; }}
.news-item {{ margin-right: 60px; }}
</style>
<div class="ribbon-wrap-{ribbon_id}">
  <div class="ribbon-track-{ribbon_id}">{track}</div>
</div>
"""

with st.spinner("Loading market data..."):
    index_items = get_index_ribbon_html()
    news_items  = get_news_ribbon_html()

idx_html = render_ribbon_html(index_items, bg_color="#111827", speed="60s", ribbon_id="idx")
news_html = render_ribbon_html(news_items, bg_color="#374151", speed="120s", ribbon_id="news")

sticky_header_html = f"""
<div class="header-sticky-wrapper">
    {header_title_html}
    {idx_html}
    {news_html}
</div>
<style>
    div[data-testid="stVerticalBlock"] > div:has(.header-sticky-wrapper) {{
        position: sticky;
        top: 2.875rem;
        z-index: 999;
        background: white;
        padding-bottom: 2px;
        margin-top: -1.5rem;
    }}
    .header-sticky-wrapper {{
        width: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
</style>
"""
st.markdown(sticky_header_html, unsafe_allow_html=True)

# ── Navigation Logic ────────────────────────────────────────────────────────
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

if 'active_page' not in st.session_state:
    st.session_state.active_page = "🎓 Education"

def set_page(page_name):
    st.session_state.active_page = page_name

with st.sidebar:
    st.markdown("### 🏠 Navigation")
    page_options = [
        "🎓 Education",
        "1️⃣ Stock Screener",
        "2️⃣ Single Stock Analyst",
        "3️⃣ Macro Portfolio Analyst",
        "4️⃣ Paper Trader"
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
5. 💰 Practice risk-free with **Paper Trader**
6. 🤖 **Ask Finley** in any tab for help!
    """)
    st.markdown("---")
    for sec_name, sec_icon, sec_desc in [
        ("🎓 Education", "🎓", "Interactive stock market school for all levels."),
        ("1️⃣ Stock Screener", "📊", "Scan global markets for undervalued stocks."),
        ("2️⃣ Single Stock Analyst", "🔍", "AI-powered deep-dive on any stock ticker."),
        ("3️⃣ Macro Portfolio Analyst", "🌐", "Personalized macro risk analysis for your holdings."),
        ("4️⃣ Paper Trader", "💰", "Simulated trading with virtual cash.")
    ]:
        with st.expander(f"{sec_icon} {sec_name}"):
            st.markdown(sec_desc)
    st.markdown("---")
    st.caption("🤖 AI powered by Llama 3.3 via Groq")

# ── Portfolio Engine Setup ────────────────────────────────────────────────
user_id = st.session_state.get("user_id")
is_guest = (user_id == "guest_user")
portfolio = None

if user_id and not is_guest:
    sync_supabase_session()
    access_token = st.session_state.get("access_token")
    if 'portfolio' not in st.session_state or st.session_state.get('portfolio_user_id') != user_id:
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

elif active_page == "1️⃣ Stock Screener":
    st.header("1️⃣ Market Screener")
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
                    st.success(f"Ready! Switch to '4️⃣ Paper Trader' tab.")
            
            pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
            if pcol1.button("◀ Prev", disabled=(page == 0)):
                st.session_state['screener_page'] -= 1
                st.rerun()
            pcol2.markdown(f"<p style='text-align:center;color:#94a3b8;'>Showing {start+1}–{end} of {total_rows}</p>", unsafe_allow_html=True)
            if pcol3.button("Next ▶", disabled=(page >= total_pages - 1)):
                st.session_state['screener_page'] += 1
                st.rerun()

    render_chat(groq_api_key, tab_context="screener")

elif active_page == "2️⃣ Single Stock Analyst":
    st.header("2️⃣ Single Stock Analyst")
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

elif active_page == "3️⃣ Macro Portfolio Analyst":
    st.header("3️⃣ Macro Portfolio Analyst")
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

elif active_page == "4️⃣ Paper Trader":
    if is_guest:
        st.warning("⚠️ **Guest Mode**")
        st.markdown("Create an account to save portfolio data.")
        if st.button("🏠 Back to Home"):
            set_page("🎓 Education")
            st.rerun()
    else:
        if st.button("⬅️ Back to Home"):
            set_page("🎓 Education")
            st.rerun()
        st.markdown("---")
        render_paper_trader(portfolio)
        render_chat(groq_api_key, tab_context="paper_trader")
