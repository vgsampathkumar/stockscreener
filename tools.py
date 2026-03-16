import yfinance as yf
from yahooquery import Screener as YQScreener
import pandas as pd
from langchain_core.tools import tool
import json

REGION_CODE_MAP = {
    "United States": "us", "India": "in", "United Kingdom": "gb",
    "Germany": "de", "France": "fr", "Canada": "ca", "Australia": "au",
    "Taiwan": "tw", "Singapore": "sg", "Brazil": "br",
    "Japan": "jp", "China": "cn", "South Korea": "kr", "Hong Kong": "hk"
}

SECTOR_YF_MAP = {
    "Technology": "Technology", "Healthcare": "Healthcare",
    "Financial": "Financial Services", "Energy": "Energy",
    "Consumer Cyclical": "Consumer Cyclical", "Basic Materials": "Basic Materials",
    "Communication Services": "Communication Services", "Industrials": "Industrials",
    "Consumer Defensive": "Consumer Defensive", "Real Estate": "Real Estate",
    "Utilities": "Utilities", "All Stocks": None
}

RENAME_MAP = {
    'symbol': 'Ticker', 'shortName': 'Company', 'regularMarketPrice': 'Price',
    'marketCap': 'Market Cap', 'trailingPE': 'P/E Ratio', 'forwardPE': 'Fwd P/E',
    'priceToBook': 'P/B Ratio', 'epsTrailingTwelveMonths': 'EPS (TTM)',
    'dividendYield': 'Div Yield', 'fiftyTwoWeekLow': '52 Wk Low',
    'fiftyTwoWeekHigh': '52 Wk High', 'beta': 'Beta'
}

def fetch_screener_df(asset_class: str = "Stocks", valuation: str = "Undervalued",
                      sector: str = "Technology", region: str = "United States"):
    """Returns a (pd.DataFrame, title_str) for the given screener parameters.
    Used by both the AI tool and the Streamlit UI directly."""
    region_code = REGION_CODE_MAP.get(region, "us")

    # ETFs / Mutual Funds from yahooquery (US-only)
    if asset_class in ["ETFs", "Mutual Funds"]:
        s = YQScreener()
        endpoint = "top_etfs_us" if asset_class == "ETFs" else "top_mutual_funds"
        data = s.get_screeners(endpoint, count=100)
        if endpoint in data and 'quotes' in data[endpoint] and data[endpoint]['quotes']:
            df = pd.DataFrame(data[endpoint]['quotes'])
            cols = ['symbol', 'shortName', 'regularMarketPrice', 'marketCap', 'yield', 'ytdReturn', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh']
            avail = [c for c in cols if c in df.columns]
            df = df[avail].rename(columns={'symbol': 'Ticker', 'shortName': 'Company', 'regularMarketPrice': 'Price', 'marketCap': 'Market Cap', 'yield': 'Yield', 'ytdReturn': 'YTD Return', 'fiftyTwoWeekLow': '52 Wk Low', 'fiftyTwoWeekHigh': '52 Wk High'})
            return df, f"Top {asset_class} (US)"
        return pd.DataFrame(), f"No data for {asset_class}."

    # Stocks via yfinance EquityQuery (lazy import for Streamlit Cloud compatibility)
    from yfinance.screener.screener import EquityQuery, screen
    sector_name = SECTOR_YF_MAP.get(sector)
    operands = [
        EquityQuery('eq', ['region', region_code]),
        EquityQuery('gt', ['intradaymarketcap', 50000000])  # min $50M
    ]
    if sector_name:
        operands.append(EquityQuery('eq', ['sector', sector_name]))

    query = EquityQuery('and', operands)
    res = screen(query, size=250)
    quotes = res.get('quotes', [])
    if not quotes:
        return pd.DataFrame(), f"No results for {sector} in {region}."

    df = pd.DataFrame(quotes)
    cols_to_keep = ['symbol', 'shortName', 'regularMarketPrice', 'marketCap', 'trailingPE', 'forwardPE', 'priceToBook', 'epsTrailingTwelveMonths', 'dividendYield', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'beta']
    available_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[available_cols].copy()

    # Numeric conversion
    for num_col in ['trailingPE', 'forwardPE', 'priceToBook', 'marketCap', 'dividendYield', 'beta', 'regularMarketPrice', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'epsTrailingTwelveMonths']:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors='coerce')

    # Valuation filter
    if "trailingPE" in df.columns and valuation != "Any":
        low_pe = 20 if sector in ["Technology", "Healthcare"] else 15
        high_pe = 35 if sector in ["Technology", "Healthcare"] else 25
        if valuation == "Undervalued":
            df = df[df['trailingPE'] < low_pe].sort_values('trailingPE', ascending=True)
        elif valuation == "Overvalued":
            df = df[df['trailingPE'] > high_pe].sort_values('trailingPE', ascending=False)
        elif valuation == "Equal Valued":
            df = df[(df['trailingPE'] >= low_pe) & (df['trailingPE'] <= high_pe)].sort_values('trailingPE')
    elif "trailingPE" in df.columns:
        df = df.sort_values('trailingPE', ascending=True)

    df = df.rename(columns=RENAME_MAP)
    title = f"{valuation} {sector} Stocks — {region} ({len(df)} results)"
    return df, title


@tool
def screen_market(asset_class: str = "Stocks", valuation: str = "Undervalued", sector: str = "Technology", region: str = "United States") -> str:
    """Screens the market based on asset class, valuation category, sector, and global region.
    Args:
        asset_class (str): 'Stocks', 'ETFs', or 'Mutual Funds'
        valuation (str): 'Undervalued', 'Overvalued', 'Equal Valued', or 'Any'
        sector (str): Sector to screen (e.g. 'Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer Cyclical', etc.)
        region (str): Market region (e.g., 'United States', 'India', 'Japan', 'China', 'South Korea', etc.)
    """
    try:
        df, title = fetch_screener_df(asset_class, valuation, sector, region)
        if df.empty:
            return title
        display_cols = [c for c in df.columns if c in RENAME_MAP.values()]
        return f"### {title}\n\n{df.head(20).to_markdown(index=False)}"
    except Exception as e:
        return f"Error screening market: {str(e)}"


import yfinance as yf
@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Fetches fundamental data and key valuation metrics for a specific stock ticker.
    Use this to get P/E ratios, P/B ratios, ROE, debt-to-equity, and company information.
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL', 'MSFT').
    """
    try:
        stock = yf.Ticker(ticker)
        info = {}
        try:
            info = stock.info
        except:
            pass
            
        # Robust price fallback
        cp = info.get("currentPrice") or info.get("regularMarketPrice")
        if cp is None:
            try:
                if hasattr(stock, 'fast_info') and 'last_price' in stock.fast_info:
                    cp = stock.fast_info['last_price']
                if cp is None:
                    cp = stock.history(period="1d")['Close'].iloc[-1]
            except:
                cp = "N/A"
        
        # Extract key metrics
        metrics = {
            "Company": info.get("longName", "N/A") if info else ticker,
            "Sector": info.get("sector", "N/A") if info else "N/A",
            "Industry": info.get("industry", "N/A") if info else "N/A",
            "Market Cap": info.get("marketCap", "N/A") if info else "N/A",
            "Current Price": cp,
            "52 Week High": info.get("fiftyTwoWeekHigh", "N/A") if info else "N/A",
            "52 Week Low": info.get("fiftyTwoWeekLow", "N/A") if info else "N/A",
            "Trailing P/E": info.get("trailingPE", "N/A") if info else "N/A",
            "Forward P/E": info.get("forwardPE", "N/A") if info else "N/A",
            "PEG Ratio": info.get("pegRatio", "N/A") if info else "N/A",
            "Price to Book": info.get("priceToBook", "N/A") if info else "N/A",
            "Return on Equity (ROE)": info.get("returnOnEquity", "N/A") if info else "N/A",
            "Return on Assets (ROA)": info.get("returnOnAssets", "N/A") if info else "N/A",
            "Debt to Equity": info.get("debtToEquity", "N/A") if info else "N/A",
            "Current Ratio": info.get("currentRatio", "N/A") if info else "N/A",
            "Dividend Yield": info.get("dividendYield", "N/A") if info else "N/A",
            "Analyst Target Price": info.get("targetMeanPrice", "N/A") if info else "N/A",
            "Analyst Recommendation": info.get("recommendationKey", "N/A") if info else "N/A"
        }
        
        # Format the output as a readable string
        formatted_metrics = "\n".join([f"- **{k}**: {v}" for k, v in metrics.items()])
        summary = info.get('longBusinessSummary', 'N/A') if info else "Detailed fundamentals currently unavailable via Yahoo Finance API."
        return f"### Fundamentals for {ticker}\n\n{formatted_metrics}\n\n**Business Summary:**\n{summary}"
    except Exception as e:
        return f"Error fetching fundamentals for {ticker}: {str(e)}"

@tool
def get_stock_financials(ticker: str) -> str:
    """Fetches recent financial statements (Income Statement, Balance Sheet, Cash Flow) for a specific stock ticker.
    Use this to analyze revenue growth, profitability, margins, and cash generation.
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get last 3 years of annual financials, convert to string (markdown)
        inc_stmt = stock.financials.head(10) # Get top rows containing key items like Total Revenue, Net Income
        bal_sheet = stock.balance_sheet.head(10)
        cash_flow = stock.cashflow.head(10)
        
        if inc_stmt.empty:
            return f"No financial statements available for {ticker}."
            
        result = f"### Financial Statements for {ticker} (Last 3-4 Years)\n\n"
        result += "#### Income Statement (Key Items)\n"
        result += inc_stmt.to_markdown() + "\n\n"
        
        result += "#### Balance Sheet (Key Items)\n"
        result += bal_sheet.to_markdown() + "\n\n"
        
        result += "#### Cash Flow (Key Items)\n"
        result += cash_flow.to_markdown() + "\n"
        
        return result
    except Exception as e:
        return f"Error fetching financials for {ticker}: {str(e)}"

@tool
def get_stock_news(ticker: str) -> str:
    """Fetches recent news articles and headlines for a specific stock ticker.
    Use this to gather qualitative context, sentiment, and recent catalysts for the stock.
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            return f"No recent news found for {ticker}."
            
        formatted_news = []
        for item in news[:5]: # Top 5 news items
            title = item.get('title', 'No Title')
            publisher = item.get('publisher', 'Unknown')
            link = item.get('link', '#')
            # The 'providerPublishTime' is a timestamp
            formatted_news.append(f"- **{title}** ({publisher}) - [Link]({link})")
            
        return f"### Recent News for {ticker}\n\n" + "\n".join(formatted_news)
    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"

@tool
def get_analyst_recommendations(ticker: str) -> str:
    """Fetches aggregate analyst recommendations and recent firm upgrades/downgrades.
    Use this to see what Wall Street analysts (similar to TipRanks/Morningstar) are saying.
    Args:
        ticker (str): The stock ticker symbol.
    """
    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations
        up_down = stock.upgrades_downgrades
        
        result = f"### Analyst Recommendations for {ticker}\n\n"
        
        has_data = False
        if recs is not None and not recs.empty:
            result += "#### Current Aggregate Consensus\n"
            result += recs.head(5).to_markdown() + "\n\n"
            has_data = True
            
        if up_down is not None and not up_down.empty:
            result += "#### Recent Firm Upgrades/Downgrades\n"
            result += up_down.head(10).to_markdown() + "\n\n"
            has_data = True
            
        if not has_data:
            return f"No analyst recommendations or upgrades/downgrades found for {ticker}."
            
        return result
    except Exception as e:
        return f"Error fetching analyst recommendations for {ticker}: {str(e)}"

@tool
def get_earnings_transcripts(ticker: str) -> str:
    """Fetches recent earnings call summaries, press releases, and guidance for a given ticker.
    Use this to understand management sentiment and forward-looking statements.
    Args:
        ticker (str): The stock ticker symbol.
    """
    try:
        stock = yf.Ticker(ticker)
        # Use recent news and calendar items as a proxy for earnings summaries
        cal = stock.calendar
        news = stock.news
        
        result = f"### Recent Earnings Context for {ticker}\n\n"
        if cal is not None and not cal.empty and 'Earnings Date' in cal.index:
            result += f"**Next/Recent Earnings Date:** {cal.loc['Earnings Date'][0]}\n\n"
        
        if news:
            result += "#### Earnings & Management News Mentions\n"
            for item in news[:5]:
                title = item.get('title', '')
                # Filter heuristically for earnings/management related news
                if any(word in title.lower() for word in ['earn', 'quarter', 'q1', 'q2', 'q3', 'q4', 'guidance', 'ceo', 'cfo', 'call', 'report']):
                    result += f"- {title}\n"
            
        return result if len(result) > 50 else f"No specific earnings call summaries found for {ticker} recently, but refer to general news."
    except Exception as e:
        return f"Error fetching earnings data for {ticker}: {str(e)}"

@tool
def get_macro_economic_data(query: str = "latest macro economic news") -> str:
    """Fetches recent macroeconomic news, Federal Reserve policy statements, and interest rate chatter.
    Use this to correlate market conditions (rates, inflation, Fed meetings) with portfolio holdings.
    Args:
        query (str): Optional focus area for the macro data lookup (e.g. 'interest rates', 'inflation', 'Fed policy'). Defaults to general macro news.
    """
    try:
        # We can use the 10-Year Treasury Yield (^TNX) and SPY as proxies to get macro news
        tnx = yf.Ticker("^TNX")
        spy = yf.Ticker("SPY")
        
        result = "### Recent Macroeconomic & Fed Policy Indicators\n\n"
        
        # Get current 10-year yield
        if tnx.info and 'previousClose' in tnx.info:
            result += f"- **10-Year Treasury Yield (Proxy for interest rates):** {tnx.info['previousClose']}%\n\n"
            
        result += "#### Macro & Geopolitical News Headlines\n"
        seen_titles = set()
        
        # Expanded keywords to capture war, tariffs, elections, and general macro
        macro_keywords = ['fed', 'rate', 'inflation', 'cpi', 'powell', 'macro', 'economy', 'tariff', 'war', 'election', 'policy', 'trump', 'geopolitical', 'trade']
        
        # We also check the SPY news to capture broader market impacting events
        for stock in [tnx, spy]:
            for item in stock.news[:10]: # Check more news items to find matches
                title = item.get('title', '')
                if title not in seen_titles and any(word in title.lower() for word in macro_keywords):
                    seen_titles.add(title)
                    result += f"- {title}\n"
                    
        return result
    except Exception as e:
        return f"Error fetching macro economic data: {str(e)}"

# List of all tools to be imported by the agent
FINANCIAL_TOOLS = [
    screen_market,
    get_stock_fundamentals,
    get_stock_financials,
    get_stock_news,
    get_analyst_recommendations,
    get_earnings_transcripts,
    get_macro_economic_data
]


# ─────────────────────────────────────────────────────────────────────────────
# Web search tool for the agentic chatbot (uses DuckDuckGo – free, no key)
# ─────────────────────────────────────────────────────────────────────────────
import requests as _req

@tool
def web_search_news(query: str) -> str:
    """Search the web for the latest news, market trends, economic data, or any topic.
    Uses Tavily Search API for highly accurate, real-time results tailored for LLMs.
    Args:
        query (str): The search query, e.g. 'latest Federal Reserve interest rate decision 2026'
    """
    try:
        api_key = st.secrets.get("TAVILY_API_KEY")
        if not api_key:
            return "⚠️ Tavily API key missing. Please ensure `TAVILY_API_KEY` is in `.streamlit/secrets.toml`."

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 5
        }
        
        resp = _req.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return f"No search results found for '{query}'. Try a different search query."

        formatted = f"### Web Search Results for: {query}\n\n"
        
        # Include the AI-generated answer from Tavily if available
        if data.get("answer"):
            formatted += f"**Key Summary:** {data['answer']}\n\n"

        for i, r in enumerate(results, 1):
            title = r.get("title", r.get("url", "No title"))
            url = r.get("url", "#")
            content = r.get("content", "No description available.")
            formatted += f"**{i}. [{title}]({url})**\n"
            formatted += f"   {content}\n\n"
            
        return formatted
    except Exception as e:
        return f"Error performing web search with Tavily: {str(e)}"


# All tools available to the agentic chatbot (finance + web search)
CHAT_TOOLS = [
    get_stock_fundamentals,
    get_stock_financials,
    get_stock_news,
    get_analyst_recommendations,
    get_earnings_transcripts,
    get_macro_economic_data,
    web_search_news,
]

