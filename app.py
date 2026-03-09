import streamlit as st
import os
import json
from tools import screen_market
from agent import create_financial_agent, run_analysis

st.set_page_config(
    page_title="Agentic Stock Screener & Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a premium "Facelift" look
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Custom Card for Results - Glassmorphism */
    .result-card {
        background: rgba(30, 35, 41, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-top: 16px;
    }
    
    /* Tables Styling */
    table {
        width: 100%;
        border-collapse: collapse;
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background-color: rgba(255, 255, 255, 0.05);
        color: #94a3b8;
        font-weight: 600;
        text-align: left;
        padding: 12px;
    }
    td {
        padding: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    tr:hover {
        background-color: rgba(255, 255, 255, 0.02);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #10b981; /* Bullish Green */
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.title("📈 Agentic Stock Screener & Analyst")
st.markdown("An AI-powered financial analyst that screens for undervalued stocks, analyzes fundamentals, and provides actionable insights.")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required to run the AI Analyst")
    model_choice = st.selectbox("Model", ["gpt-4o", "gpt-3.5-turbo"])
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("1. Provide your API Key.")
    st.markdown("2. Use the **Screener** to find undervalued growth stocks.")
    st.markdown("3. Enter a **Ticker** to run a comprehensive fundamental analysis and get a Buy/Hold/Sell recommendation.")

# Layout using Tabs for better organization
tab1, tab2, tab3 = st.tabs(["1️⃣ Stock Screener", "2️⃣ Single Stock Analyst", "3️⃣ Macro Portfolio Analyst"])

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
            "France", "Canada", "Australia", "Taiwan", "Singapore", "Brazil"
        ]
        region_choice = st.selectbox("Market Region", supported_regions)
            
    if st.button("Run Screener"):
        with st.spinner(f"Scanning {asset_class} in {region_choice}..."):
            results = screen_market.invoke({
                "asset_class": asset_class, 
                "valuation": valuation, 
                "sector": sector,
                "region": region_choice
            })
            # Remove the HTML div wrapper so Streamlit's markdown parser properly renders the table
            st.markdown("---")
            st.markdown(results)

with tab2:
    st.header("Single Stock Analyst")
    st.markdown("Deep dive into a specific stock's financials, fundamentals, and recent news.")
    ticker_input = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, TSLA)").upper()
    
    if st.button("Run AI Analysis", type="primary"):
        if not api_key:
            st.error("⚠️ Please provide an OpenAI API Key in the sidebar.")
        elif not ticker_input:
            st.error("⚠️ Please enter a stock ticker.")
        else:
            try:
                # Initialize Agent
                agent = create_financial_agent(api_key, model_choice)
                
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
                    except Exception as e:
                        st.error(f"Error during agent execution: {str(e)}")
                        
            except Exception as e:
                st.error(f"Failed to initialize agent. Check your API key. Error: {str(e)}")

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
        if not api_key:
            st.error("⚠️ Please provide an OpenAI API Key.")
        elif not portfolio_input:
            st.error("⚠️ Please enter at least one ticker.")
        else:
            try:
                from agent import create_macro_analyst_agent
                macro_agent = create_macro_analyst_agent(api_key, model_choice)
                
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
                    except Exception as e:
                        st.error(f"Error during agent execution: {str(e)}")
            except Exception as e:
                st.error(f"Failed to initialize macro agent: {str(e)}")
