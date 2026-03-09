import sys
import re

try:
    from yahooquery import Screener
    s = Screener(country='invalid_country')
except ValueError as e:
    err_str = str(e)
    # The error looks like: "invalid_country is not a valid country. One of united states, ... is required"
    match = re.search(r"One of (.*) is required", err_str)
    if match:
        print(match.group(1))
    else:
        print(err_str)
except Exception as e:
    print(f"Other error: {e}")
