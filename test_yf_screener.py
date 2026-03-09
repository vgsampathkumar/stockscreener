import yfinance as yf
try:
    if hasattr(yf, 'Screener'):
        print("Screener exists")
    if hasattr(yf, 'EquityQuery'):
        print("EquityQuery exists")
        q = yf.EquityQuery('and', [
            yf.EquityQuery('eq', ['region', 'in']),
            yf.EquityQuery('eq', ['sector', 'Technology'])
        ])
        s = yf.Screener()
        s.set_query(q)
        res = s.response
        print(len(res['quotes']))
        print([(x['symbol'], x['shortName']) for x in res['quotes'][:5]])
except Exception as e:
    print("Error:", e)
