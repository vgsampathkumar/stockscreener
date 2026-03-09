import yfinance as yf
from yahooquery import Screener
import pandas as pd
from langchain_core.tools import tool
import json

@tool
def screen_market(asset_class: str = "Stocks", valuation: str = "Undervalued", sector: str = "Technology") -> str:
    """Screens the market based on asset class, valuation category, and sector.
    Args:
        asset_class (str): 'Stocks', 'ETFs', or 'Mutual Funds'
        valuation (str): 'Undervalued', 'Overvalued', 'Equal Valued', or 'Any' (primarily for stocks)
        sector (str): The specific sector to screen (e.g. 'Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer Cyclical', etc.)
    """
    try:
        s = Screener()
        # Map user friendly sectors to yahooquery endpoints (most sectors map directly to their lowercase names)
        sector_mapping = {
            "Technology": "ms_technology", "Healthcare": "ms_healthcare", "Financial": "ms_financial_services",
            "Energy": "ms_energy", "Consumer Cyclical": "ms_consumer_cyclical",
            "Basic Materials": "ms_basic_materials", "Communication Services": "ms_communication_services",
            "Industrials": "ms_industrials", "Consumer Defensive": "ms_consumer_defensive",
            "Real Estate": "ms_real_estate", "Utilities": "ms_utilities", "All Stocks": "day_gainers"
        }
        
        # Determine the endpoint
        if asset_class == "ETFs":
            endpoint = "top_etfs_us"
        elif asset_class == "Mutual Funds":
            endpoint = "top_mutual_funds"
        else:
            endpoint = sector_mapping.get(sector, "technology")
            
        # Get more results to increase chances of finding stocks fitting the valuation criteria
        data = s.get_screeners(endpoint, count=250)
        
        if endpoint in data and 'quotes' in data[endpoint] and data[endpoint]['quotes']:
            quotes = data[endpoint]['quotes']
            df = pd.DataFrame(quotes)
            if df.empty:
                return f"No results found for {sector} {asset_class} at this time."
                
            cols_to_keep = ['symbol', 'shortName', 'regularMarketPrice', 'marketCap', 'trailingPE', 'forwardPE', 'priceToBook', 'epsTrailingTwelveMonths', 'dividendYield', 'yield', 'ytdReturn', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'beta']
            available_cols = [c for c in cols_to_keep if c in df.columns]
            
            # Filter by valuation if it's Stocks
            if asset_class == "Stocks" and "trailingPE" in df.columns and valuation != "Any":
                df['trailingPE'] = pd.to_numeric(df['trailingPE'], errors='coerce')
                
                # Dynamic heuristic for high-growth sectors
                low_pe = 20 if sector in ["Technology", "Healthcare"] else 15
                high_pe = 35 if sector in ["Technology", "Healthcare"] else 25
                
                if valuation == "Undervalued":
                    df = df[df['trailingPE'] < low_pe].sort_values('trailingPE')
                elif valuation == "Overvalued":
                    df = df[df['trailingPE'] > high_pe].sort_values('trailingPE', ascending=False)
                elif valuation == "Equal Valued":
                    df = df[(df['trailingPE'] >= low_pe) & (df['trailingPE'] <= high_pe)]
                    
            if df.empty:
                return f"No {valuation} results found in {sector} {asset_class} based on P/E ratio criteria."
                
            # Limit the final output to 15
            df = df.head(15)
            
            if 'marketCap' in df.columns:
                df['marketCap'] = df['marketCap'].apply(lambda x: f"${x/1e9:.2f}B" if pd.notnull(x) else x)
            if 'beta' in df.columns:
                df['beta'] = df['beta'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else x)
            if 'dividendYield' in df.columns:
                df['dividendYield'] = df['dividendYield'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)
                
            # Rename columns for better readability in the UI
            rename_map = {
                'symbol': 'Ticker',
                'shortName': 'Company',
                'regularMarketPrice': 'Price',
                'marketCap': 'Market Cap',
                'trailingPE': 'P/E Ratio',
                'forwardPE': 'Fwd P/E',
                'priceToBook': 'P/B Ratio',
                'epsTrailingTwelveMonths': 'EPS (TTM)',
                'dividendYield': 'Div Yield',
                'yield': 'Yield',
                'ytdReturn': 'YTD Return',
                'fiftyTwoWeekLow': '52 Wk Low',
                'fiftyTwoWeekHigh': '52 Wk High',
                'beta': 'Beta'
            }
            df = df.rename(columns=rename_map)
            # Filter available cols based on the ones we kept and then renamed
            display_cols = [rename_map.get(c, c) for c in available_cols]
                
            res = df[display_cols].to_markdown(index=False)
            return f"### {valuation} {sector} {asset_class} Screener Results\n\n{res}"
            
        return f"No results found for {sector} {asset_class} at this time."
    except Exception as e:
        return f"Error screening market: {str(e)}"

@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Fetches fundamental data and key valuation metrics for a specific stock ticker.
    Use this to get P/E ratios, P/B ratios, ROE, debt-to-equity, and company information.
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL', 'MSFT').
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key metrics
        metrics = {
            "Company": info.get("longName", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "Market Cap": info.get("marketCap", "N/A"),
            "Current Price": info.get("currentPrice", "N/A"),
            "52 Week High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52 Week Low": info.get("fiftyTwoWeekLow", "N/A"),
            "Trailing P/E": info.get("trailingPE", "N/A"),
            "Forward P/E": info.get("forwardPE", "N/A"),
            "PEG Ratio": info.get("pegRatio", "N/A"),
            "Price to Book": info.get("priceToBook", "N/A"),
            "Return on Equity (ROE)": info.get("returnOnEquity", "N/A"),
            "Return on Assets (ROA)": info.get("returnOnAssets", "N/A"),
            "Debt to Equity": info.get("debtToEquity", "N/A"),
            "Current Ratio": info.get("currentRatio", "N/A"),
            "Dividend Yield": info.get("dividendYield", "N/A"),
            "Analyst Target Price": info.get("targetMeanPrice", "N/A"),
            "Analyst Recommendation": info.get("recommendationKey", "N/A")
        }
        
        # Format the output as a readable string
        formatted_metrics = "\n".join([f"- **{k}**: {v}" for k, v in metrics.items()])
        return f"### Fundamentals for {ticker}\n\n{formatted_metrics}\n\n**Business Summary:**\n{info.get('longBusinessSummary', 'N/A')}"
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
def get_macro_economic_data() -> str:
    """Fetches recent macroeconomic news, Federal Reserve policy statements, and interest rate chatter.
    Use this to correlate market conditions (rates, inflation, Fed meetings) with portfolio holdings.
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
