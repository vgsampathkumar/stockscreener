from yfinance.screener.screener import EquityQuery, screen
from yahooquery import Screener as YQScreener
import pandas as pd
from langchain_core.tools import tool
import json

@tool
def screen_market(asset_class: str = "Stocks", valuation: str = "Undervalued", sector: str = "Technology", region: str = "United States") -> str:
    """Screens the market based on asset class, valuation category, sector, and global region.
    Args:
        asset_class (str): 'Stocks', 'ETFs', or 'Mutual Funds'
        valuation (str): 'Undervalued', 'Overvalued', 'Equal Valued', or 'Any'
        sector (str): Sector to screen (e.g. 'Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer Cyclical', etc.)
        region (str): Market region (e.g., 'United States', 'India', 'United Kingdom', 'Germany', 'France', 'Canada', 'Australia', 'Taiwan', 'Singapore', 'Brazil')
    """
    try:
        region_code_map = {
            "United States": "us", "India": "in", "United Kingdom": "gb",
            "Germany": "de", "France": "fr", "Canada": "ca", "Australia": "au",
            "Taiwan": "tw", "Singapore": "sg", "Brazil": "br"
        }
        sector_yf_map = {
            "Technology": "Technology", "Healthcare": "Healthcare",
            "Financial": "Financial Services", "Energy": "Energy",
            "Consumer Cyclical": "Consumer Cyclical", "Basic Materials": "Basic Materials",
            "Communication Services": "Communication Services", "Industrials": "Industrials",
            "Consumer Defensive": "Consumer Defensive", "Real Estate": "Real Estate",
            "Utilities": "Utilities", "All Stocks": None
        }
        region_code = region_code_map.get(region, "us")

        # ETFs and Mutual Funds: fall back to yahooquery (US-only sources)
        if asset_class in ["ETFs", "Mutual Funds"]:
            s = YQScreener()
            endpoint = "top_etfs_us" if asset_class == "ETFs" else "top_mutual_funds"
            data = s.get_screeners(endpoint, count=50)
            if endpoint in data and 'quotes' in data[endpoint] and data[endpoint]['quotes']:
                df = pd.DataFrame(data[endpoint]['quotes'])
                cols = ['symbol', 'shortName', 'regularMarketPrice', 'marketCap', 'yield', 'ytdReturn', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh']
                avail = [c for c in cols if c in df.columns]
                df = df[avail].head(15)
                rmap = {'symbol': 'Ticker', 'shortName': 'Company', 'regularMarketPrice': 'Price', 'marketCap': 'Market Cap', 'yield': 'Yield', 'ytdReturn': 'YTD Return', 'fiftyTwoWeekLow': '52 Wk Low', 'fiftyTwoWeekHigh': '52 Wk High'}
                df = df.rename(columns=rmap)
                dcols = [rmap.get(c, c) for c in avail]
                return f"### Top {asset_class} Screener Results (US)\n\n{df[dcols].to_markdown(index=False)}"
            return f"No data for {asset_class} at this time."

        # --- Stocks: use yfinance EquityQuery to filter by REAL region + sector ---
        sector_name = sector_yf_map.get(sector, None)

        operands = [
            EquityQuery('eq', ['region', region_code]),
            EquityQuery('gt', ['intradaymarketcap', 100000000])  # min $100M marketcap
        ]
        if sector_name:
            operands.append(EquityQuery('eq', ['sector', sector_name]))

        query = EquityQuery('and', operands)
        res = screen(query, size=200, sortField='intradaymarketcap', sortType='DESC')
        quotes = res.get('quotes', [])

        if not quotes:
            return f"No results found for {sector} stocks in {region}. The exchange may not have data available."

        df = pd.DataFrame(quotes)
        cols_to_keep = ['symbol', 'shortName', 'regularMarketPrice', 'marketCap', 'trailingPE', 'forwardPE', 'priceToBook', 'epsTrailingTwelveMonths', 'dividendYield', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'beta']
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols].copy()

        # Post-filter by valuation via P/E heuristic
        if "trailingPE" in df.columns and valuation != "Any":
            df['trailingPE'] = pd.to_numeric(df['trailingPE'], errors='coerce')
            low_pe = 20 if sector in ["Technology", "Healthcare"] else 15
            high_pe = 35 if sector in ["Technology", "Healthcare"] else 25
            if valuation == "Undervalued":
                df = df[df['trailingPE'] < low_pe].sort_values('trailingPE')
            elif valuation == "Overvalued":
                df = df[df['trailingPE'] > high_pe].sort_values('trailingPE', ascending=False)
            elif valuation == "Equal Valued":
                df = df[(df['trailingPE'] >= low_pe) & (df['trailingPE'] <= high_pe)]

        if df.empty:
            return f"No {valuation} {sector} stocks found in {region}. Try 'Any' valuation for broader results."

        df = df.head(20)

        if 'marketCap' in df.columns:
            df['marketCap'] = df['marketCap'].apply(lambda x: f"${x/1e9:.2f}B" if pd.notnull(x) else "N/A")
        if 'beta' in df.columns:
            df['beta'] = df['beta'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
        if 'dividendYield' in df.columns:
            df['dividendYield'] = df['dividendYield'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")

        rename_map = {
            'symbol': 'Ticker', 'shortName': 'Company', 'regularMarketPrice': 'Price',
            'marketCap': 'Market Cap', 'trailingPE': 'P/E Ratio', 'forwardPE': 'Fwd P/E',
            'priceToBook': 'P/B Ratio', 'epsTrailingTwelveMonths': 'EPS (TTM)',
            'dividendYield': 'Div Yield', 'fiftyTwoWeekLow': '52 Wk Low',
            'fiftyTwoWeekHigh': '52 Wk High', 'beta': 'Beta'
        }
        df = df.rename(columns=rename_map)
        display_cols = [rename_map.get(c, c) for c in available_cols]
        return f"### {valuation} {sector} Stocks — {region}\n\n{df[display_cols].to_markdown(index=False)}"

    except Exception as e:
        return f"Error screening market: {str(e)}"
