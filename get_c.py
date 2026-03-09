import sys
try:
    from yahooquery import Screener
    s = Screener(country='invalid_country')
except ValueError as e:
    with open("countries.txt", "w") as f:
        f.write(str(e))
except Exception as e:
    with open("countries.txt", "w") as f:
        f.write(f"Other error: {e}")
