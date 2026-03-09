import requests

url = 'https://query2.finance.yahoo.com/v1/finance/screener'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}
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
    res = requests.post(url, headers=headers, json=payload)
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
