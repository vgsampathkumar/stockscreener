from yfinance.screener import Screener
from yfinance.query import EquityQuery

# Eq(region, in) AND Eq(sector, Technology)
q = EquityQuery('and', [
    EquityQuery('eq', ['region', 'in']),
    EquityQuery('eq', ['sector', 'Technology'])
])

s = Screener()
s.set_query(q)

try:
    res = s.response
    quotes = res.get('quotes', [])
    print(f"Found {len(quotes)} quotes.")
    for q in quotes[:5]:
        print(q.get('symbol'), q.get('shortName'), q.get('region'))
except Exception as e:
    print(e)
