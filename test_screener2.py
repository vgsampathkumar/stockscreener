from yahooquery import Screener

s = Screener()
url = 'https://query2.finance.yahoo.com/v1/finance/screener'
payload = {
    "offset": 0,
    "size": 5,
    "sortField": "intradaymarketcap",
    "sortType": "DESC",
    "quoteType": "EQUITY",
    "query": {
        "operator": "AND",
        "operands": [
            {
                "operator": "eq",
                "operands": [
                    "region",
                    "in"
                ]
            },
            {
                "operator": "eq",
                "operands": [
                    "sector",
                    "Technology"
                ]
            }
        ]
    }
}

try:
    # Use the session from yahooquery which handles the crumb
    res = s.session.post(url, json=payload)
    if res.status_code == 200:
        data = res.json()
        quotes = data['finance']['result'][0]['quotes']
        print(f"Found {len(quotes)} quotes.")
        for q in quotes:
            print(q.get('symbol'), q.get('shortName'), q.get('region'))
    else:
        print(f"Error: {res.status_code}", res.text)
except Exception as e:
    print(f"Exception: {e}")
