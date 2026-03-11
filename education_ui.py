import streamlit as st

# ── YouTube video helper ──────────────────────────────────────────────────────
def _yt(video_id: str, caption: str = ""):
    """Embed a YouTube video responsively using an iframe."""
    st.markdown(
        f"""
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                    border-radius:12px;margin:12px 0 4px 0;box-shadow:0 4px 16px rgba(0,0,0,0.12);">
          <iframe src="https://www.youtube.com/embed/{video_id}?rel=0"
            style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
            allowfullscreen loading="lazy">
          </iframe>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(f"📺 {caption}")


# ── Example block helper ──────────────────────────────────────────────────────
def _examples(simple: str, medium: str, complex_: str):
    """Render three tiered real-world examples with colour-coded labels."""
    st.markdown("#### 💡 Real-World Examples")
    cols = st.columns(3)
    labels = ["🟢 Simple", "🟡 Medium", "🔴 Complex"]
    texts  = [simple, medium, complex_]
    colors = ["#d1fae5", "#fef9c3", "#fee2e2"]
    border = ["#10b981",  "#f59e0b", "#ef4444"]
    for col, label, text, bg, bd in zip(cols, labels, texts, colors, border):
        with col:
            st.markdown(
                f"""
                <div style="background:{bg};border-left:4px solid {bd};
                            padding:14px 16px;border-radius:10px;min-height:160px;">
                  <b style="font-size:0.85rem;">{label}</b>
                  <p style="margin:8px 0 0 0;font-size:0.88rem;color:#111827;">{text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── Chatbot knowledge base ────────────────────────────────────────────────────
_KB = {
    # Stock market basics
    "stock market":     "The stock market is a marketplace where people buy and sell ownership pieces of companies called shares. When you own a share, you own a tiny piece of that company! 🏢",
    "what is stock":    "A stock (or share) is a small piece of ownership in a company. If Apple has 1 billion shares and you own 1, you own 1 billionth of Apple! 🍎",
    "share":            "A share represents one unit of ownership in a company. Companies issue millions of shares — owning even one makes you a shareholder!",
    "index":            "An index tracks a group of stocks to show how the market is doing overall. The S&P 500 tracks 500 large US companies. If the index goes up, most of those stocks went up! 📊",
    "bull market":      "A bull market means stock prices are rising — investors are optimistic about the economy. 🐂 Think of it as a 'happy' market!",
    "bear market":      "A bear market means stock prices are falling — investors are scared or pessimistic. 🐻 It's when the market feels 'grumpy'. Historically, bull markets last longer than bear markets!",
    "dividend":         "A dividend is money a company shares with its stockholders — like getting a bonus just for owning the stock! For example, if you own 100 shares and the dividend is $1 per share, you get $100 cash. 💰",
    "ipo":              "IPO stands for Initial Public Offering. It's when a private company sells its shares to the public for the very first time. Like a grand opening for a stock! 🎉",
    "broker":           "A broker is a middleman (person or app) that places your buy/sell orders on the stock exchange. Apps like Robinhood, Fidelity, and Schwab are modern brokers. 📱",
    "exchange":         "A stock exchange is the marketplace where stocks are listed and traded. The NYSE (New York Stock Exchange) and NASDAQ are the two biggest in the US. Think of it like eBay, but for stocks!",
    # Buying & Selling
    "how to buy":       "To buy a stock: 1️⃣ Open a brokerage account, 2️⃣ Add money (deposit), 3️⃣ Search for the company's ticker (e.g. AAPL for Apple), 4️⃣ Choose how many shares, 5️⃣ Place a Market order and confirm!",
    "how to sell":      "To sell a stock: Open your brokerage app, find the stock in your portfolio, select 'Sell', enter the number of shares, pick an order type, and confirm. The cash lands in your account after settlement (T+1). 💵",
    "long":             "Going long means you BUY a stock because you believe the price will RISE. You profit when the stock goes up. This is the most common way people invest! 📈",
    "short":            "Short selling means you BORROW shares and sell them, hoping to buy them back cheaper later. You profit if the price FALLS. It's riskier because losses can be unlimited if the price keeps rising. ⚠️",
    "bid ask":          "The bid price is the highest price buyers are willing to pay. The ask price is the lowest sellers will accept. The difference is called the 'spread' — it's a tiny hidden cost of trading.",
    "spread":           "The bid-ask spread is the gap between what buyers offer and sellers want. A stock with bid $99.95 and ask $100.00 has a $0.05 spread. Tighter spreads mean lower trading costs. 💹",
    "commission":       "A trading commission is a fee brokers charge per trade. Many US brokers now offer $0 commissions on stocks and ETFs. Always check your broker's fee schedule! 📋",
    "capital gains":    "Capital gains tax is the tax you pay on profits from selling investments. Short-term gains (held < 1 year) are taxed at your normal income rate. Long-term gains (held > 1 year) get lower tax rates. 🧾",
    "settlement":       "After you sell, the cash doesn't arrive instantly. US stocks settle T+1 — meaning the next business day. During this period the funds are 'pending'. 🕐",
    # Orders
    "order":            "An order is the instruction you send to your broker to buy or sell shares. Every trade is an order! Key parts: what stock, buy or sell, how many shares, and what price you'll accept. 📩",
    "market order":     "A market order buys or sells immediately at the best available price. It's FAST ✅ but the exact price isn't guaranteed ❌. Best for popular stocks where prices barely move between clicking and filling.",
    "limit order":      "A limit order only executes at your specified price or better. You set the maximum you'll pay (buy) or minimum you'll accept (sell). It might not fill if the price never reaches your limit. 🎯",
    "stop":             "A stop order (stop-loss) is like a safety net 🛡️. You set a trigger price — if the stock falls to that price, it automatically sells to prevent bigger losses. Example: You own a stock at $100. Set stop at $90. If it drops to $90, it sells. ",
    "stop limit":       "A stop-limit order combines a stop price (trigger) and a limit price (minimum to accept). More control than a plain stop — but won't fill if the stock gaps past your limit. ⚙️",
    "trailing stop":    "A trailing stop automatically moves your stop price up as the stock rises, locking in gains! If a stock goes from $100 → $120 with a 10% trailing stop, the stop moves from $90 → $108. 🔄",
    # Order status
    "pending":          "Pending means your order has been submitted but hasn't reached the exchange yet. It's like mailing a letter — it's sent but not delivered yet. 🟡",
    "working":          "Working (or Open) means your order is live on the exchange, waiting to be matched with a buyer or seller. Like raising your hand at an auction! 🔵",
    "filled":           "Filled means your order was fully executed — the trade is complete! Check your portfolio to see your new position (buy) or cash (sell). 🟢✅",
    "partially filled": "Partial fill means only some of your shares were traded. Common on less-liquid stocks. The rest stays open unless you cancel. 🟠",
    "cancelled":        "Cancelled means your order was removed before it could fill — either you cancelled it or it expired (e.g., a Day order after market close). ⚪",
    "rejected":         "Rejected means the broker or exchange refused your order — usually due to insufficient funds, invalid ticker, or exceeding margin limits. 🔴 Fix the issue and resubmit.",
    "expired":          "Expired means your order's time limit ran out without filling. A Day order expires at 4pm ET. A GTD order expires on the date you chose. 🕒",
    "gtc":              "GTC (Good Till Cancelled) keeps your order active until it fills OR you cancel it. Useful for limit orders where you're patient about the price. ♾️",
    "day order":        "A Day order is active only during the current trading session (9:30 AM – 4:00 PM ET). If it doesn't fill by close, it's automatically cancelled. 📅",
    # Position
    "position":         "A position is how many shares you currently own of a stock. If you bought 50 shares of Tesla, you have a 'position' of 50 shares in TSLA. 📌",
    "average cost":     "Average cost (avg cost) is the average price you paid per share across all your purchases. If you bought 1 share at $100 and another at $120, your avg cost is $110. Break-even is at $110. ⚖️",
    "unrealized":       "Unrealized P&L is your gain or loss on paper — it only becomes REAL when you sell. Think of it as 'what you'd make if you sold right now'. 📝",
    "realized":         "Realized P&L is the profit or loss you've already locked in by selling. This is what you actually made (or lost) and what gets taxed. 💯",
    "p&l":              "P&L stands for Profit & Loss — how much money you've made or lost on a trade or overall portfolio. Positive = 🟢 profit, Negative = 🔴 loss.",
    "pnl":              "P&L (Profit & Loss) shows how much money you've made or lost. Unrealized P&L = current value vs what you paid. Realized P&L = what you locked in by selling.💹",
    # Balance
    "balance":          "Your brokerage balance shows how much cash you have. 'Buying power' is how much you can invest right now. 'Portfolio value' is the current worth of your open positions. Total value = Cash + Portfolio. 💰",
    "buying power":     "Buying power is the cash available to place new trades. In a cash account it equals your deposited cash. In a margin account it could be 2x your cash (borrowed money from the broker). 💪",
    "margin":           "Margin means borrowing money from your broker to buy more stock than your cash allows. Powerful, but risky — losses are amplified and you pay interest on the loan. ⚠️",
    "margin call":      "A margin call is when your broker demands you deposit more money or sell positions because your account value fell below the required minimum. It's the broker saying 'pay up or we sell your stocks'. 🚨",
    "cash account":     "A cash account only lets you trade with money you've deposited — no borrowing. Safer for beginners. You can only lose what you put in. 🏦",
    "pdt":              "PDT (Pattern Day Trader) is a US rule: if you make 4+ day trades in 5 business days in an account under $25,000, your account gets restricted. Day trading requires $25k+ minimum in the US. 📏",
    # Performance
    "performance":      "Performance measures how well your investments are doing. Key metrics: Total Return %, Sharpe Ratio (risk-adjusted return), Max Drawdown (worst loss from peak), and Win Rate (% of profitable trades). 📊",
    "sharpe ratio":     "The Sharpe Ratio measures return per unit of risk. Formula: (Return − Risk-Free Rate) ÷ Standard Deviation. A Sharpe of 1.0 = good, 2.0+ = excellent. Higher = better risk-adjusted returns. 🎯",
    "max drawdown":     "Max Drawdown is the biggest drop from a portfolio's peak to its lowest point before recovering. E.g., if your portfolio went $10k → $6k → $12k, the max drawdown was -40%. Lower is better! 📉",
    "win rate":         "Win rate is the % of your closed trades that were profitable. A 60% win rate means 6 of every 10 trades made money. A high win rate WITH good risk/reward = excellent trading! ✅",
    "benchmark":        "A benchmark is a standard to compare your returns against — usually the S&P 500. If the S&P gained 20% and you gained 15%, you underperformed the benchmark even though you made money. 🏁",
    "rebalancing":      "Rebalancing is adjusting your portfolio back to your target mix. If stocks go up a lot, you sell some stocks and buy bonds to restore your desired allocation. Keeps risk in check! ⚖️",
    # General
    "etf":              "An ETF (Exchange-Traded Fund) is a basket of stocks bundled into one investment. SPY tracks the S&P 500 — buying 1 share of SPY gives you exposure to 500 companies! Great for diversification. 🧺",
    "mutual fund":      "A mutual fund pools money from many investors to buy a diversified portfolio, managed by a professional. Unlike ETFs, they trade once per day at closing price (NAV). Often used in 401(k) plans. 🤝",
    "diversification":  "Diversification = 'don't put all your eggs in one basket'. Owning many different stocks/sectors reduces risk — if one stock crashes, others may hold up. 🥚🐣",
    "volatility":       "Volatility measures how much a stock's price swings up and down. High volatility = bigger moves (more risk AND more opportunity). Low volatility = steady, predictable price. 🎢",
    "beta":             "Beta measures how much a stock moves relative to the market. Beta 1.0 = moves with market. Beta 2.0 = moves twice as much. Beta 0.5 = half as much. High beta = more risk/reward. 📐",
    "pe ratio":         "P/E ratio (Price-to-Earnings) tells you how much investors pay for $1 of earnings. A P/E of 20 means investors pay $20 per $1 of annual earnings. Lower P/E = potentially cheaper stock, but context matters! 🔢",
    "market cap":       "Market cap = Share Price × Total Shares Outstanding. It's the total value of a company. Large-cap (>$10B) are stable giants like Apple. Small-cap (<$2B) are smaller, potentially faster-growing companies. 🏗️",
    "paper trading":    "Paper trading (or virtual trading) means practising with FAKE money. You get all the experience of real trading — placing orders, tracking P&L, managing positions — with zero financial risk. Perfect for beginners! 🎮",
}

def _chatbot_answer(question: str) -> str:
    """Simple keyword-matching chatbot engine."""
    q = question.lower().strip()

    # Exact & substring keyword matching
    best_key   = None
    best_score = 0
    for keyword, answer in _KB.items():
        kw_words = keyword.lower().split()
        score    = sum(1 for w in kw_words if w in q)
        if score > best_score:
            best_score = score
            best_key   = keyword

    if best_score > 0 and best_key:
        return _KB[best_key]

    # Fallback
    return (
        "Great question! 🤔 I don't have a specific answer for that yet. "
        "Try asking about: **stocks, orders, limit order, stop loss, position, "
        "balance, margin, P&L, Sharpe ratio, ETF, dividend, IPO, bull/bear market**, or **paper trading**. "
        "You can also explore the sections above for detailed explanations!"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Main render function
# ══════════════════════════════════════════════════════════════════════════════
def render_education():
    st.header("📚 Stock Market Education Center")
    st.markdown(
        "Your beginner-friendly guide to understanding the stock market. "
        "Includes **videos**, **real-world examples** (simple → complex), "
        "and a **chatbot** at the bottom you can ask any question! 🤖"
    )

    # ── 1. Basics of Stock Market ─────────────────────────────────────────────
    with st.expander("🏛️ 1. Basics of the Stock Market", expanded=True):
        _yt("p7HKvqRI_Bo", "TED-Ed — How does the stock market work?")
        st.markdown("""
### What is the Stock Market?
The **stock market** is a marketplace where buyers and sellers trade **shares** (ownership stakes) of publicly listed companies.
When a company wants to raise money, it sells shares to the public through an **IPO**. Those shares then trade on exchanges like the **NYSE** or **NASDAQ**.

| Term | Kid-Friendly Definition |
|---|---|
| **Stock / Share** | A tiny ownership piece of a company 🍕 |
| **Exchange** | The marketplace where stocks trade (NYSE, NASDAQ) |
| **Market Cap** | The total value of a company = Price × Total Shares |
| **Bull Market** 🐂 | Prices going UP — happy, optimistic market |
| **Bear Market** 🐻 | Prices going DOWN — scared, pessimistic market |
| **Index** | A scorecard tracking a group of stocks (e.g. S&P 500) |
| **Dividend** | Cash a company pays you just for owning its stock |
| **IPO** | A company's first day selling shares to the public |
| **Broker** | The middleman app/person who executes your trades |
        """)
        _examples(
            "You own 1 share of your school's pizza club for $5. If the club does well, the share is worth $8. You made $3! 🍕",
            "You buy 10 shares of Apple (AAPL) at $170 each ($1,700 total). Apple launches a hit product, shares hit $200. Your investment is now $2,000 — a $300 gain! 📱",
            "You invest $10,000 across 5 stocks in different sectors (tech, healthcare, energy). A bear market hits — tech falls 30% but healthcare rises 10%. Your diversified portfolio only falls 12% instead of 30%. 📊",
        )

    # ── 2. Buying & Selling ───────────────────────────────────────────────────
    with st.expander("💱 2. Buying & Selling Stocks"):
        _yt("ZCFkWDdmXG8", "Intro to Buying and Selling Stocks for Beginners")
        st.markdown("""
### How to Buy a Stock
1. **Open a brokerage account** (Robinhood, Fidelity, Schwab, Zerodha)
2. **Deposit money** into the account
3. **Search the ticker** (e.g. `AAPL` for Apple, `TSLA` for Tesla)
4. **Place an order** — pick quantity and type
5. **Monitor** — check your portfolio for the filled position

### How to Sell
Same steps in reverse: find the stock in your holdings → choose Sell → enter quantity → confirm.

### Long vs. Short
| | Long 📈 | Short 📉 |
|---|---|---|
| You believe | Price will rise | Price will fall |
| Action to open | **Buy** shares | Borrow & **sell** shares |
| Action to close | **Sell** shares | **Buy** shares back |
| Max loss | What you invested | Unlimited ⚠️ |

### Key Costs
- **Commission:** Often $0 at modern brokers
- **Bid-Ask Spread:** Tiny hidden cost between buy/sell prices
- **Capital Gains Tax:** Short-term < 1 yr = ordinary income rate; Long-term > 1 yr = lower rate
        """)
        _examples(
            "Emma has $50. She buys 1 share of a toy company for $50. A year later the shares are $65. She sells and makes $15 profit (minus any taxes)! 🧸",
            "Jake buys 20 shares of Nike (NKE) at $100 = $2,000. Nike releases bad earnings and he sells at $90 = $1,800. He has a realized loss of $200 that can offset other gains at tax time. 👟",
            "Sarah buys 50 shares of Tesla at $200 ($10,000). After 2 years Tesla hits $350. She sells 25 shares ($8,750) to lock in profit, holding 25 shares to let gains run. She pays long-term capital gains tax only on the sold portion. ⚡",
        )

    # ── 3. Orders ────────────────────────────────────────────────────────────
    with st.expander("📋 3. Orders — What They Are"):
        _yt("mFNbY7FMKzY", "Stock Market Orders Explained for Beginners")
        st.markdown("""
### What is an Order?
An **order** is an instruction you send to your broker: *"Buy X shares of company Y at price Z."*

### Anatomy of an Order
| Component | Description |
|---|---|
| **Symbol** | Which stock (e.g. `MSFT`) |
| **Side** | Buy or Sell |
| **Quantity** | Number of shares |
| **Order Type** | How to execute (Market, Limit, Stop…) |
| **Time-in-Force** | How long to keep trying (Day, GTC…) |

### Order Lifecycle
```
Placed → Pending → Working (live on exchange) → Filled ✅
                                               → Partially Filled 🟠
                                               → Cancelled ⚪
                                               → Rejected 🔴
```
        """)
        _examples(
            "You tell your broker: 'Buy 5 shares of Disney.' That instruction is your order. When it's matched on the exchange, it's filled — you now own 5 shares of Disney! 🏰",
            "You place a Day order to buy 100 shares of Ford at $12.00. The stock never drops that low today. At 4pm the order expires automatically — no shares bought, no money spent. 🚗",
            "A hedge fund places a large buy order for 500,000 shares. To avoid moving the market price with one big order, they split it into 50 smaller orders of 10,000 each, executed over several hours using an algorithm. 🤖",
        )

    # ── 4. Order Types ────────────────────────────────────────────────────────
    with st.expander("🔀 4. Order Types"):
        _yt("xT5jd3DdYIs", "Market vs Limit vs Stop Orders — Full Explanation")
        st.markdown("""
### The 5 Main Order Types

| Type | Executes When | Price Guaranteed? | Best For |
|---|---|---|---|
| **Market** | Immediately | ❌ No | Fast fills on liquid stocks |
| **Limit** | At your price or better | ✅ Yes | Precise buy/sell price |
| **Stop-Loss** | When stop price is hit → Market order | ❌ No | Downside protection |
| **Stop-Limit** | When stop triggered → Limit order | ✅ Yes | Controlled stop |
| **Trailing Stop** | Follows price up; sells if price drops set % | ❌ No | Protecting gains |

#### 🔹 Market Order
Buys/sells **right now** at the best price. Fastest but no price guarantee.

#### 🔹 Limit Order
Only fills at **your price or better**. You won't overpay. May not fill at all.

#### 🔹 Stop-Loss
A dormant order that **wakes up** when the stock hits your stop price, then sells at market. Protects you from big losses.

#### 🔹 Stop-Limit
Like Stop-Loss but converts to a **Limit** order instead of Market. More control but risk of not filling if stock gaps.

#### 🔹 Trailing Stop
The stop price **moves up automatically** as the stock rises, preserving profits while giving room to grow.
        """)
        _examples(
            "You want to buy 3 shares of Google right now for whatever price it is. You place a Market order — done in seconds at the current price. Simple! 🔍",
            "Amazon is trading at $180 but you only want it at $170. You place a Limit Buy at $170. It only executes if Amazon drops to $170 or below. If it never dips that far, you don't buy. 📦",
            "You own Netflix at $400. You set a 15% Trailing Stop. When Netflix rises to $500, the stop trail moves to $425 ($500 × 0.85). If Netflix then drops from $500 to $425, it automatically sells — locking in a $25/share gain over your original $400 cost. 🎬",
        )

    # ── 5. Order Status ───────────────────────────────────────────────────────
    with st.expander("🚦 5. Order Status"):
        _yt("lNdOtlpmH5M", "Understanding Order Status in Stock Trading")
        st.markdown("""
### Every Order Passes Through States

| Status | Icon | Meaning |
|---|---|---|
| **Pending** | 🟡 | Submitted but not yet on the exchange |
| **Working / Open** | 🔵 | Live on exchange, waiting for a match |
| **Filled** | 🟢 | Fully executed — trade complete! |
| **Partially Filled** | 🟠 | Some shares traded; rest still open |
| **Cancelled** | ⚪ | Removed before filling |
| **Rejected** | 🔴 | Refused (insufficient funds, bad ticker…) |
| **Expired** | 🕒 | Time limit hit without filling |

### Time-in-Force Options
| Option | Meaning |
|---|---|
| **DAY** | Valid today only; auto-cancels at 4pm ET |
| **GTC** | Good Till Cancelled — stays open until you cancel |
| **IOC** | Immediate or Cancel — fill now or cancel remainder |
| **FOK** | Fill or Kill — all-or-nothing, must fill instantly |
| **GTD** | Good Till Date — active until your chosen date |
        """)
        _examples(
            "You place a Market order for Apple. It shows 'Working' for 1 second, then 'Filled' — you own the shares. Easy! 🍎",
            "You place a Limit order to sell 200 shares of a slow-moving stock. After an hour only 120 shares found buyers — status shows 'Partially Filled'. The remaining 80 are still Working.",
            "You set a GTC Limit Buy for a biotech stock at $45 (currently $60). Three weeks later, bad news drops it to $45.10 — your order is Working but not filled. If it dips to exactly $45, it fills and you get the bargain entry you planned. 🧬",
        )

    # ── 6. Position ───────────────────────────────────────────────────────────
    with st.expander("📌 6. Positions"):
        _yt("86rPxqPRgJY", "What is a Stock Position? Beginners Guide to Portfolio Holdings")
        st.markdown("""
### What is a Position?
A **position** is your current holding in a security — how many shares you own and at what average cost.

### Position Metrics
| Metric | Formula | What it tells you |
|---|---|---|
| **Quantity** | Shares held | Size of holding |
| **Avg Cost** | Total paid ÷ Shares | Your break-even price |
| **Market Value** | Current Price × Qty | What it's worth NOW |
| **Unrealized P&L** | (Price - Avg Cost) × Qty | Gain/loss if you sold now |
| **Realized P&L** | From closed trades | Locked-in profit or loss |
| **P&L %** | (Price - Cost) ÷ Cost × 100 | % gain or loss |
| **Day Change** | Today's price move × Qty | Today's value change |

### Position Types
| | Meaning |
|---|---|
| **Long** | You own shares — profit if price rises 📈 |
| **Flat** | No position |
| **Short** | Borrowed & sold shares — profit if price falls 📉 |
        """)
        _examples(
            "You buy 5 shares of McDonald's at $280. Your position = 5 shares, avg cost = $280. If it goes to $300, your unrealized P&L = $100. You haven't made money yet until you sell! 🍔",
            "You buy 50 shares of Microsoft at $300 (avg cost). Then you buy 50 more at $280 — your new avg cost is $290. Now you need the price to be above $290 to be in profit.",
            "A portfolio manager holds 2,000 shares of Nvidia (long), worth $1.8M, and is also short 1,000 shares of AMD (short). If Nvidia rises and AMD falls, BOTH positions profit. This is a 'pair trade' strategy to hedge sector risk. 🖥️",
        )

    # ── 7. Balance ───────────────────────────────────────────────────────────
    with st.expander("💰 7. Balance"):
        _yt("Efq6C7oWFkM", "Stock Brokerage Account Balance Types Explained")
        st.markdown("""
### Your Account Balance Breakdown
| Term | Definition |
|---|---|
| **Cash Balance** | Uninvested cash in your account |
| **Buying Power** | Cash available for new trades (+ margin if applicable) |
| **Portfolio Value** | Current market value of all open positions |
| **Total Account Value** | Cash + Portfolio Value |
| **Equity** | Total Value − Any Margin Borrowed |

### Paper Trading Balance (This App)
You start with **virtual cash** (e.g. $100,000). Buying reduces cash and adds shares. Selling removes shares and returns cash. Zero real risk — perfect for learning! 🎮

### Key Balance Rules
- **Settlement (T+1):** After selling, cash arrives the next business day
- **Margin:** Borrowed money from broker — amplifies gains AND losses
- **Maintenance Margin:** Minimum equity% required; falling below triggers a **Margin Call** 🚨
- **PDT Rule:** 4+ day trades in 5 days in US with < $25,000 = account restricted ⚠️
        """)
        _examples(
            "You deposit $1,000 into your paper trading account. Your cash balance = $1,000, portfolio value = $0, total value = $1,000. You buy $400 of stock — now cash = $600, portfolio = $400. 🏦",
            "You have $10,000 in a margin account. Your broker gives you 2× leverage = $20,000 buying power. You buy $15,000 of stock. If it rises 10%, you gain $1,500 on your $10k equity = 15% return. But if it falls 10%, you lose $1,500 = 15% loss on your own money. ⚡",
            "A trader has $50,000 equity and uses 4× leverage ($200,000 position). The market crashes 25% overnight. Position value = $150,000 (−$50,000). Equity wiped out. Broker issues a margin call — the trader must deposit more cash or all positions are force-liquidated at a catastrophic loss. 🚨",
        )

    # ── 8. Performance ────────────────────────────────────────────────────────
    with st.expander("📊 8. Performance"):
        _yt("KEbTHYScBzU", "How to Measure Your Investment Portfolio Performance")
        st.markdown("""
### Measuring How Well You're Doing

#### Absolute Returns
| Metric | Formula |
|---|---|
| **Total Return %** | (Current Value − Cost) ÷ Cost × 100 |
| **Day's P&L** | Sum of (Price Change Today × Qty) |

#### Risk-Adjusted Returns
| Metric | What it means | Target |
|---|---|---|
| **Sharpe Ratio** | Return per unit of risk | > 1.0 good, > 2.0 excellent |
| **Max Drawdown** | Biggest peak-to-valley drop | Smaller = better |
| **Win Rate** | % of trades that were profitable | > 50% helpful |
| **Profit Factor** | Gross profit ÷ Gross loss | > 1.5 solid |

#### Benchmarking
Always compare against the **S&P 500**. If the S&P gained 20% and you gained 12%, you underperformed — even though you made money.

#### Key Principles
- 📅 Review performance **weekly/monthly** — catch bad habits early
- 🎯 **Risk management first** — define max loss before entering a trade
- 🔄 **Rebalance** periodically to restore target allocations
- 📈 **Compounding** is powerful — 10% annual return doubles money in ~7 years (Rule of 72)
        """)
        _examples(
            "You invested $1,000 in an S&P 500 ETF one year ago. It's now worth $1,120. Your return = 12%. The S&P itself returned 12% — you matched the benchmark perfectly! 🏆",
            "Your portfolio of 5 stocks returned 18% this year, but the ride was bumpy — it dropped 22% in March before recovering. High return but high drawdown. Your Sharpe ratio of 0.8 suggests you took a lot of risk for that return. A smoother strategy might score 1.5. 📊",
            "A quantitative fund runs a strategy with: Win Rate 45%, but average win = $3,000 and average loss = $1,000. Profit Factor = (0.45 × $3,000) ÷ (0.55 × $1,000) = $1,350 ÷ $550 = 2.45 — highly profitable despite losing more trades than winning! This demonstrates how risk/reward ratio matters more than simply winning often. 🧮",
        )

    # ── Chatbot ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🤖 Ask the Finance Tutor Bot")
    st.markdown(
        "Got a question? Type anything below — about stocks, orders, positions, "
        "performance, or any concept from above!"
    )

    # Initialise history
    if "edu_chat" not in st.session_state:
        st.session_state["edu_chat"] = [
            {
                "role": "assistant",
                "text": "👋 Hi! I'm your Finance Tutor Bot. Ask me anything about stocks, "
                        "orders, positions, balance, or trading! For example: *'What is a limit order?'* "
                        "or *'What does filled mean?'*",
            }
        ]

    # Render chat history
    for msg in st.session_state["edu_chat"]:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["text"])
        else:
            st.chat_message("assistant").markdown(msg["text"])

    # Input
    user_q = st.chat_input("Type your question here…")
    if user_q and user_q.strip():
        # Show user message
        st.session_state["edu_chat"].append({"role": "user", "text": user_q.strip()})
        # Generate answer
        answer = _chatbot_answer(user_q)
        st.session_state["edu_chat"].append({"role": "assistant", "text": answer})
        st.rerun()
