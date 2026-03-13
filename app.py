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
    page_title="Agentic Stock Screener & Analyst",
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

    /* ── Freeze Header and Tabs ────────────────────── */
    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.95);
    }
    /* We keep the sticky tabs/ribbon wrapper in front */
    .stApp > header {
        z-index: 10;
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

# Define the Title and Description elements separately
header_title_html = """
<div style="background: white; padding-bottom: 2px;">
    <h1 style="margin-bottom: 0;">📈 Agentic Stock Screener & Analyst</h1>
    <p style="color: #6b7280; margin-top: 4px; margin-bottom: 8px;">An AI-powered financial analyst that screens for undervalued stocks, analyzes fundamentals, and provides actionable insights.</p>
</div>
"""

# ── Scrolling Ribbons ────────────────────────────────────────────────────────
import yfinance as yf_ribbon
import time

@st.cache_data(ttl=300)  # cache for 5 minutes
def get_index_ribbon_html():
    """Fetch live global index prices and format as scrolling ribbon HTML."""
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
        except Exception:
            pass
    return items

@st.cache_data(ttl=300)
def get_news_ribbon_html():
    """Fetch latest market news headlines and format as scrolling ribbon HTML."""
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
        except Exception:
            pass
    return items

def render_ribbon_html(items, bg_color, speed="40s", ribbon_id="ribbon"):
    if not items:
        return ""
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
    font-family: 'Inter', sans-serif;
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

# Combine both ribbons into a single sticky wrapper
with st.spinner("Loading market data..."):
    index_items = get_index_ribbon_html()
    news_items  = get_news_ribbon_html()

idx_html = render_ribbon_html(index_items, bg_color="#111827", speed="60s", ribbon_id="idx")
news_html = render_ribbon_html(news_items, bg_color="#374151", speed="120s", ribbon_id="news")

# Combine Title, Description, and both ribbons into a single sticky wrapper
# top: 2.875rem (approx 46px) is roughly where it sits under the native Streamlit header
sticky_header_html = f"""
<div class="header-sticky-wrapper">
    {header_title_html}
    {idx_html}
    {news_html}
</div>

<style>
    /* 1. Target the outer Streamlit element container that holds our wrapper */
    div[data-testid="stVerticalBlock"] > div:has(.header-sticky-wrapper) {{
        position: sticky;
        top: 2.875rem; /* Native Streamlit header height */
        z-index: 999;
        background: white;
        padding-bottom: 2px;
        margin-top: -1.5rem;
    }}

    /* Ensure the wrapper itself doesn't cause extra spacing */
    .header-sticky-wrapper {{
        width: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
</style>
"""
st.markdown(sticky_header_html, unsafe_allow_html=True)


# Groq API key from secrets for AI agents
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

# Sidebar with How it works + Tab descriptions
with st.sidebar:
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

    with st.expander("🎓 Education"):
        st.markdown("""
Interactive stock market school for all levels. Covers market basics, buying/selling, order types,
order status, positions, account balance, and performance metrics. Each section includes a
**YouTube video**, **3 tiered examples** (beginner to advanced), and a
**live AI chatbot** for Q&A.
        """)

    with st.expander("1️⃣ Stock Screener"):
        st.markdown("""
Scan global markets for **undervalued**, **overvalued**, or **equal-valued** stocks. Filter by
asset class (Stocks, ETFs, Mutual Funds), sector, and 14 market regions worldwide.
Results can be directly sent to Paper Trader.
        """)

    with st.expander("2️⃣ Single Stock Analyst"):
        st.markdown("""
AI-powered deep-dive on any stock ticker. The agent uses financial tools to fetch fundamentals,
financials, news, and analyst consensus, then generates a professional **Buy / Hold / Sell**
report with a 1-year price chart.
        """)

    with st.expander("3️⃣ Macro Portfolio Analyst"):
        st.markdown("""
Enter your real portfolio tickers and get a personalized macro risk analysis. The AI agent
correlates your holdings with Fed policy, interest rates, tariffs, and global events to produce
a **5-year rebalancing plan** benchmarked against Wall Street analyst consensus.
        """)

    with st.expander("4️⃣ Paper Trader"):
        st.markdown("""
Fidelity-style simulated trading with virtual cash. Place market/limit orders, manage positions,
track P&L, and view portfolio performance — all risk-free. Data is saved to the cloud via
Supabase so your portfolio persists across sessions.
        """)

    st.markdown("---")
    st.caption("🤖 AI powered by Llama 3.3 via Groq")

# Layout using Tabs for better organization
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🎓 Education",
    "1️⃣ Stock Screener",
    "2️⃣ Single Stock Analyst",
    "3️⃣ Macro Portfolio Analyst",
    "4️⃣ Paper Trader"
])

# ── Sticky Tabs via CSS ─────────────────────────────────────────────────────
# `position: sticky` is broken by Streamlit's CSS `contain: content` on parent
# divs. Using `position: fixed` instead, which positions relative to the
# viewport and bypasses containment entirely.
st.markdown("""
<style>
    /* Target the tab buttons row (the [role="tablist"] container).
       Use position:fixed to break out of containment. */
    [data-testid="stTabs"] [role="tablist"] {
        position: fixed !important;
        top: 0px !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        z-index: 999 !important;
        background: white !important;
        padding: 8px 1rem 4px 5rem !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
        border-bottom: 2px solid #f3f4f6 !important;
    }

    /* Push the content down so it does not hide behind the fixed tab bar */
    [data-testid="stTabs"] > div:nth-child(2) {
        padding-top: 52px !important;
    }

    /* Hide the native Streamlit header to avoid stacking */
    header[data-testid="stHeader"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Portfolio Engine scoped to the logged-in user
user_id = st.session_state.get("user_id")

# For guest users, we bypass the portfolio engine entirely
is_guest = user_id == "guest_user"
portfolio = None

if user_id and not is_guest:
    # 1. Sync session at the start of every rerun to refresh JWT if needed
    sync_supabase_session()
    
    # 2. Get the latest token from session state
    access_token = st.session_state.get("access_token")
    
    # 3. Handle Portfolio instance persistence and token refreshing
    if 'portfolio' not in st.session_state or st.session_state.get('portfolio_user_id') != user_id:
        st.session_state['portfolio'] = PaperPortfolio(user_id=user_id, access_token=access_token)
        st.session_state['portfolio_user_id'] = user_id
    else:
        # Update the existing instance with the (possibly refreshed) token
        st.session_state['portfolio'].refresh_client(access_token)
        
    portfolio = st.session_state['portfolio']

with tab0:
    render_education()
    render_chat(groq_api_key, tab_context="education")

with tab1:
    st.header("Market Screener")
    st.markdown("Scan the market for potentially undervalued, overvalued, or equal valued stocks, along with top ETFs and Mutual Funds across all sectors.")
    
    col1a, col1b, col1c, col1d = st.columns(4)
    with col1a:
        asset_class = st.selectbox("Asset Class", ["Stocks", "ETFs", "Mutual Funds"])
    with col1b:
        if asset_class == "Stocks":
            valuation = st.selectbox("Valuation Category", ["Undervalued", "Equal Valued", "Overvalued", "Any"])
        else:
            valuation = st.selectbox("Valuation Category", ["Any"], disabled=True)
    with col1c:
        if asset_class == "Stocks":
            sec_options = ["Technology", "Healthcare", "Financial", "Energy", "Consumer Cyclical", 
                           "Basic Materials", "Communication Services", "Industrials", "Consumer Defensive", 
                           "Real Estate", "Utilities", "All Stocks"]
            sector = st.selectbox("Sector", sec_options)
        else:
            sector = st.selectbox("Sector", ["N/A"], disabled=True)
            
    with col1d:
        supported_regions = [
            "United States", "India", "United Kingdom", "Germany", 
            "France", "Canada", "Australia", "Taiwan", "Singapore", "Brazil",
            "Japan", "China", "South Korea", "Hong Kong"
        ]
        region_choice = st.selectbox("Market Region", supported_regions)
            
    if st.button("Run Screener", type="primary"):
        with st.spinner(f"Scanning {asset_class} in {region_choice}..."):
            try:
                df_result, result_title = fetch_screener_df(asset_class, valuation, sector, region_choice)
                st.session_state['screener_df'] = df_result
                st.session_state['screener_title'] = result_title
                st.session_state['screener_page'] = 0  # reset to first page
            except Exception as e:
                err_msg = str(e).lower()
                if "rate" in err_msg or "limit" in err_msg or "429" in err_msg:
                    st.error("⚠️ **Yahoo Finance rate limit reached.** Too many requests — please wait 30 seconds and try again.")
                else:
                    st.error(f"⚠️ Screener error: {e}")

    # Display results (persisted in session state, survives reruns from page buttons)
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
            
            # Header row: title on left, record count on right
            hcol1, hcol2 = st.columns([3, 1])
            with hcol1:
                st.markdown(f"### {title}")
            with hcol2:
                st.markdown(f"<p style='text-align:right;color:#94a3b8;padding-top:0.6rem;'>Page {page+1} of {total_pages} &nbsp;|&nbsp; {total_rows} records</p>", unsafe_allow_html=True)
            
            # Slice page
            start = page * PAGE_SIZE
            end = min(start + PAGE_SIZE, total_rows)
            df_page = df_all.iloc[start:end].copy()
            
            # Convert Market Cap from raw dollars to billions
            if "Market Cap" in df_page.columns:
                df_page["Market Cap"] = df_page["Market Cap"].apply(
                    lambda x: x / 1e9 if isinstance(x, (int, float)) and x > 0 else x
                )
            
            # Native st.dataframe — has built-in column sort on click
            st.dataframe(
                df_page,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ticker":       st.column_config.TextColumn("Ticker", width="small"),
                    "Company":      st.column_config.TextColumn("Company", width="medium"),
                    "Price":        st.column_config.NumberColumn("Price", format="%.2f"),
                    "Market Cap":   st.column_config.NumberColumn("Mkt Cap ($B)", format="%.2fB"),
                    "P/E Ratio":    st.column_config.NumberColumn("P/E Ratio", format="%.2f"),
                    "Fwd P/E":      st.column_config.NumberColumn("Fwd P/E", format="%.2f"),
                    "P/B Ratio":    st.column_config.NumberColumn("P/B Ratio", format="%.2f"),
                    "EPS (TTM)":    st.column_config.NumberColumn("EPS (TTM)", format="%.2f"),
                    "Div Yield":    st.column_config.NumberColumn("Div Yield", format="%.2f%%"),
                    "52 Wk Low":   st.column_config.NumberColumn("52 Wk Low", format="%.2f"),
                    "52 Wk High":  st.column_config.NumberColumn("52 Wk High", format="%.2f"),
                    "Beta":         st.column_config.NumberColumn("Beta", format="%.2f"),
                }
            )
            
            st.markdown("---")
            invest_col1, invest_col2 = st.columns([1, 2])
            with invest_col1:
                sel_ticker = st.selectbox("Select ticker from above to Paper Trade", df_page['Ticker'].tolist())
            with invest_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📥 Paper Trade Selected", type="primary", use_container_width=False):
                    st.session_state['paper_trade_ticker'] = sel_ticker
                    st.session_state['paper_trade_notes'] = "Found via Screener"
                    st.session_state['show_order_ticket'] = True
                    st.success(f"Ready! Switch to the '4️⃣ Paper Trader' tab to buy {sel_ticker}.")
            
            st.markdown("---")
            pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
            with pcol1:
                if st.button("◀ Prev", disabled=(page == 0), key="prev_page"):
                    st.session_state['screener_page'] -= 1
                    st.rerun()
            with pcol2:
                st.markdown(f"<p style='text-align:center;color:#94a3b8;'>Showing rows {start+1}–{end} of {total_rows} &nbsp;·&nbsp; Click any column header to sort</p>", unsafe_allow_html=True)
            with pcol3:
                if st.button("Next ▶", disabled=(page >= total_pages - 1), key="next_page"):
                    st.session_state['screener_page'] += 1
                    st.rerun()

    render_chat(groq_api_key, tab_context="screener")


with tab2:
    st.header("Single Stock Analyst")
    st.markdown("Deep dive into a specific stock's financials, fundamentals, and recent news.")
    ticker_input = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, TSLA)").upper()
    
    if st.button("Run AI Analysis", type="primary"):
        if not groq_api_key:
            st.error("⚠️ Groq API key not found. Please add `GROQ_API_KEY` to `.streamlit/secrets.toml`.")
        elif not ticker_input:
            st.error("⚠️ Please enter a stock ticker.")
        else:
            try:
                # Initialize Agent with Groq
                agent = create_financial_agent(groq_api_key)
                
                st.markdown(f"### Analyzing {ticker_input}...")
                
                # Show Price Chart and Broker Consensus side-by-side
                col_chart, col_broker = st.columns([2, 1])
                
                with col_chart:
                    with st.expander(f"📈 {ticker_input} 1-Year Price Chart", expanded=True):
                        try:
                            import yfinance as yf
                            hist = yf.Ticker(ticker_input).history(period="1y")
                            if not hist.empty and 'Close' in hist.columns:
                                st.line_chart(hist['Close'])
                            else:
                                st.info("No historical price data available.")
                        except Exception as e:
                            st.warning(f"Could not load chart: {e}")
                            
                with col_broker:
                    with st.expander("🏦 Wall Street Broker Consensus", expanded=True):
                        from tools import get_analyst_recommendations
                        with st.spinner("Fetching broker targets..."):
                            broker_data = get_analyst_recommendations.invoke({"ticker": ticker_input})
                            st.markdown(broker_data)
                
                # Create empty containers for streaming output
                st.markdown("### 🤖 AI Agent Analysis")
                status_container = st.empty()
                report_container = st.empty()
                
                query = f"Please do a deep dive analysis on {ticker_input}. Look at its fundamentals, recent financials, and recent news. Conclude with a detailed report and a definitive Buy/Hold/Sell recommendation."
                
                with st.spinner(f"Agent is analyzing {ticker_input}..."):
                    try:
                        # Iterate through the LangGraph stream
                        for msg in run_analysis(agent, query):
                            # Check if the message is from a tool call (Agent Action)
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    status_container.info(f"🛠️ Agent using tool: `{tool_call['name']}`")
                            
                            # Check if it's the final AI response
                            if msg.type == "ai" and not hasattr(msg, 'tool_calls') or (hasattr(msg, 'tool_calls') and not msg.tool_calls) and msg.content:
                                status_container.success("Analysis Complete!")
                                report_container.markdown(f"<div class='result-card'>{msg.content}</div>", unsafe_allow_html=True)
                                
                                # Inject Paper Trade button with AI notes
                                st.markdown("---")
                                if st.button("📥 Paper Trade This Stock", type="primary"):
                                    st.session_state['paper_trade_ticker'] = ticker_input
                                    st.session_state['paper_trade_notes'] = "AI Analyst Recommendation: " + msg.content[:200] + "..."
                                    st.session_state['show_order_ticket'] = True
                                    st.success(f"Ready! Switch to '4️⃣ Paper Trader' tab to place order for {ticker_input}.")
                    except Exception as e:
                        st.error(f"Error during agent execution: {str(e)}")
                        
            except Exception as e:
                st.error(f"Failed to initialize agent. Check your API key. Error: {str(e)}")

    render_chat(groq_api_key, tab_context="analyst")

with tab3:
    st.header("Macro Portfolio Analyst")
    st.markdown("Analyze your specific holdings against current Fed policy and macroeconomic trends to generate a 5-year risk mitigation and rebalancing plan.")
    
    # Optional Brokerage CSV Upload
    uploaded_file = st.file_uploader("📥 Optional: Upload Brokerage Positions (CSV) to auto-fill portfolio", type=["csv"], help="Export 'Positions' from Fidelity, E-Trade, or Schwab as a CSV. This happens 100% locally and securely.")
    
    if uploaded_file is not None:
        import pandas as pd
        try:
            # Some brokerages have a few lines of summary at the top before the actual table header.
            # We explicitly skip bad lines or look for the 'Symbol' column.
            df = pd.read_csv(uploaded_file, on_bad_lines='skip')
            
            # Simple heuristic: find the column that looks like stock symbols
            symbol_col = None
            for col in df.columns:
                # Most brokers export with exactly 'Symbol' or 'Ticker'
                if str(col).strip().lower() in ['symbol', 'ticker']:
                    symbol_col = col
                    break
                    
            if symbol_col:
                # Extract symbols, drop NAs, unique them, strip whitespace, ignore Cash/Core positions usually named 'Pending' or 'Account'
                symbols = df[symbol_col].dropna().astype(str).tolist()
                valid_symbols = []
                for s in symbols:
                    clean_s = str(s).strip().upper()
                    # Filter out obvious non-stock rows that brokerages sometimes include
                    if clean_s and not clean_s.startswith('ACCOUNT') and clean_s != 'PENDING ACTIVITY' and clean_s != 'CORE':
                        valid_symbols.append(clean_s)
                        
                valid_symbols = sorted(list(set(valid_symbols)))
                if valid_symbols:
                    st.session_state['portfolio_input'] = ", ".join(valid_symbols)
                    st.success(f"✅ Successfully extracted {len(valid_symbols)} positions!")
                else:
                    st.warning("Found the Symbol column but couldn't extract any valid stock tickers.")
            else:
                st.warning("⚠️ Could not find a 'Symbol' or 'Ticker' column in the uploaded file.")
        except Exception as e:
            st.error(f"Error parsing file: {e}")
            
    default_portfolio = st.session_state.get('portfolio_input', "NVDA, AMD, TSM")
    portfolio_input = st.text_area("Enter your portfolio tickers (comma separated)", value=default_portfolio)
    horizon = st.selectbox("Investment Horizon", ["5 Years", "3 Years", "10 Years"])
    
    if st.button("Generate Rebalancing Plan", type="primary"):
        if not groq_api_key:
            st.error("⚠️ Groq API key not found. Please add `GROQ_API_KEY` to `.streamlit/secrets.toml`.")
        elif not portfolio_input:
            st.error("⚠️ Please enter at least one ticker.")
        else:
            try:
                from agent import create_macro_analyst_agent
                macro_agent = create_macro_analyst_agent(groq_api_key)
                
                st.markdown(f"### Evaluating Macro Risks for: {portfolio_input}")
                
                status_container_macro = st.empty()
                report_container_macro = st.empty()
                
                query_macro = f"My portfolio consists of: {portfolio_input}. My investment horizon is {horizon}. Please pull the latest earnings calls for these companies, and correlate them with current macroeconomic data and Fed policy. Provide a highly personalized risk mitigation and rebalancing plan."
                
                with st.spinner("Analyzing macro environment and portfolio correlation..."):
                    try:
                        for msg in run_analysis(macro_agent, query_macro):
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    status_container_macro.info(f"🛠️ Agent using tool: `{tool_call['name']}`")
                            
                            if msg.type == "ai" and not hasattr(msg, 'tool_calls') or (hasattr(msg, 'tool_calls') and not msg.tool_calls) and msg.content:
                                status_container_macro.success("Macro Analysis Complete!")
                                report_container_macro.markdown(f"<div class='result-card'>{msg.content}</div>", unsafe_allow_html=True)
                                
                                st.markdown("---")
                                if st.button("📥 Execute Plan in Paper Trader", type="primary"):
                                    # Just takes the first ticker as a quick-start, user can loop
                                    first_tick = [t.strip() for t in portfolio_input.split(",") if t.strip()][0]
                                    st.session_state['paper_trade_ticker'] = first_tick
                                    st.session_state['paper_trade_notes'] = "Macro Plan: " + msg.content[:200] + "..."
                                    st.session_state['show_order_ticket'] = True
                                    st.success("Ready! Switch to '4️⃣ Paper Trader' tab to begin executing the plan.")
                    except Exception as e:
                        st.error(f"Error during agent execution: {str(e)}")
            except Exception as e:
                st.error(f"Failed to initialize macro agent: {str(e)}")

    render_chat(groq_api_key, tab_context="macro")

with tab4:
    if st.session_state.get("user_id") == "guest_user":
        st.warning("⚠️ **Guest Mode**")
        st.markdown("Paper Trading requires an account to securely save and track your portfolio data. Please Sign Out and create a free account to use this feature.")
    else:
        render_paper_trader(portfolio)
        render_chat(groq_api_key, tab_context="paper_trader")

