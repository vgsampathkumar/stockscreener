import yfinance as yf
# Let's inspect the exact path
import sys

try:
    from yfinance.screener.screener import Screener
    from yfinance.screener.screener import EquityQuery

    q = EquityQuery('and', [
        EquityQuery('eq', ['region', 'in']),
        EquityQuery('eq', ['sector', 'Technology'])
    ])

    s = Screener()
    s.set_query(q)
    res = s.response
    quotes = res.get('quotes', [])
    print(f"Found {len(quotes)} quotes.")
    for q in quotes[:5]:
        print(q.get('symbol'))
except Exception as e:
    print(e)
