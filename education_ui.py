import streamlit as st


def render_education():
    st.header("📚 Stock Market Education Center")
    st.markdown("Your beginner-friendly guide to understanding the stock market, trading mechanics, and portfolio management.")

    # ── Sub-sections using expanders ─────────────────────────────────────────────

    # 1. Basics of the Stock Market
    with st.expander("🏛️ Basics of the Stock Market", expanded=True):
        st.markdown("""
### What is the Stock Market?
The **stock market** is a marketplace where buyers and sellers trade shares (ownership stakes) of publicly listed companies.
When a company wants to raise money, it sells shares to the public through an **Initial Public Offering (IPO)**. Those
shares then trade on an exchange such as the **NYSE** or **NASDAQ**.

### Key Concepts
| Term | Definition |
|---|---|
| **Stock / Share** | A unit of ownership in a company |
| **Exchange** | Marketplace where stocks are listed & traded (NYSE, NASDAQ, BSE, NSE) |
| **Market Cap** | Total market value of a company = Share Price × Total Shares |
| **Bull Market** | Extended period of rising prices (optimism) |
| **Bear Market** | Extended period of declining prices (pessimism) |
| **Index** | Benchmark tracking a group of stocks (S&P 500, Dow Jones, Nifty 50) |
| **Dividend** | Portion of company profit paid to shareholders |
| **IPO** | Initial Public Offering — first time a company sells shares to the public |
| **Broker** | Intermediary who executes trades on your behalf |

### How Prices Move
Prices are driven by **supply and demand**. If more investors want to buy a stock than sell it, the price rises. News, earnings reports,
interest rates, and economic data all influence investor sentiment and, therefore, prices.

### Market Hours (US)
- **Pre-market:** 4:00 AM – 9:30 AM ET
- **Regular session:** 9:30 AM – 4:00 PM ET
- **After-hours:** 4:00 PM – 8:00 PM ET
        """)

    # 2. Buying and Selling Stocks
    with st.expander("💱 Buying & Selling Stocks"):
        st.markdown("""
### How to Buy a Stock
1. **Open a brokerage account** (Robinhood, Fidelity, Schwab, Zerodha, etc.)
2. **Fund your account** (deposit cash)
3. **Search for the stock** using its ticker symbol (e.g., AAPL for Apple)
4. **Place an order** — specify quantity and order type
5. **Monitor your position** after execution

### How to Sell a Stock
The process mirrors buying. You select the stock you hold, choose a quantity to sell, pick an order type, and submit. Proceeds
(minus fees/taxes) are credited to your account balance.

### Long vs. Short
| | Long | Short |
|---|---|---|
| **You believe** | Price will go **UP** | Price will go **DOWN** |
| **Action to open** | Buy shares | Borrow & sell shares |
| **Action to close** | Sell shares | Buy shares back |
| **Profit if** | Price rises | Price falls |
| **Max loss** | Amount invested | Unlimited (price can rise indefinitely) |

### Key Fees to Know
- **Commission:** Fee per trade (many brokers now offer $0 commissions)
- **Bid-Ask Spread:** Difference between the best buy price and best sell price — a hidden cost
- **Capital Gains Tax:** Tax on profits — short-term (< 1 year) taxed as ordinary income; long-term (> 1 year) at lower rates
        """)

    # 3. Orders
    with st.expander("📋 Orders — What They Are"):
        st.markdown("""
### What is an Order?
An **order** is an instruction you send to your broker to **buy or sell** a security. Every trade begins with an order.

### Anatomy of an Order
| Component | Description |
|---|---|
| **Symbol / Ticker** | Which stock you want to trade (e.g., TSLA) |
| **Side** | Buy or Sell |
| **Quantity** | Number of shares |
| **Order Type** | How the order should be executed (Market, Limit, etc.) |
| **Time-in-Force** | How long the order stays active (Day, GTC, IOC, etc.) |

### Order Lifecycle
```
Order Placed → Pending → Working (sent to exchange) → Filled / Partially Filled / Cancelled / Rejected
```
        """)

    # 4. Order Types
    with st.expander("🔀 Order Types"):
        st.markdown("""
### Common Order Types

#### 1. Market Order
Executes **immediately at the best available price**.
- ✅ Guaranteed to fill
- ❌ Price is not guaranteed (can slip in volatile markets)
- **Best for:** Highly liquid stocks when speed matters

#### 2. Limit Order
Executes **only at your specified price or better**.
- ✅ Price is guaranteed (you won't pay more to buy / receive less to sell)
- ❌ Not guaranteed to fill if the price never reaches your limit
- **Buy Limit:** Below current price (you want a bargain)
- **Sell Limit:** Above current price (you want to lock in profit)

#### 3. Stop (Stop-Loss) Order
A dormant order that **activates when a stop price is reached**, then converts to a Market order.
- ✅ Automates loss protection
- ❌ In a fast-moving market, the fill price may be worse than the stop price (slippage)
- **Example:** You own AAPL at $180. You set a Stop-Loss at $165. If AAPL drops to $165, the order fires and sells at market.

#### 4. Stop-Limit Order
Like a Stop order, but converts to a **Limit order** instead of a Market order when triggered.
- ✅ Prevents slippage
- ❌ May not fill if price gaps past the limit

#### 5. Trailing Stop Order
Stop price **trails** the market price by a fixed amount or percentage.
- ✅ Locks in gains automatically as price rises
- ❌ Normal volatility can trigger the stop prematurely

### Quick Comparison
| Type | Execution Guaranteed? | Price Guaranteed? | Best Use Case |
|---|---|---|---|
| Market | ✅ Yes | ❌ No | Fast execution on liquid stocks |
| Limit | ❌ No | ✅ Yes | Precision entry/exit |
| Stop-Loss | ❌ No (market) | ❌ No | Downside protection |
| Stop-Limit | ❌ No | ✅ Yes | Controlled stop with price floor |
| Trailing Stop | ❌ No | ❌ No | Protecting profits in uptrend |
        """)

    # 5. Order Status
    with st.expander("🚦 Order Status"):
        st.markdown("""
### Order Status Definitions
After placing an order, it moves through several states:

| Status | Meaning |
|---|---|
| 🟡 **Pending** | Order submitted but not yet sent to the exchange |
| 🔵 **Working / Open** | Order is live on the exchange, waiting to be matched |
| 🟢 **Filled** | Order fully executed — shares have been bought/sold |
| 🟠 **Partially Filled** | Only a portion of the order has been executed so far |
| ⚪ **Cancelled** | Order was cancelled before it could fill (by you or expired) |
| 🔴 **Rejected** | Order was rejected by the broker/exchange (e.g., insufficient funds, invalid ticker) |
| 🕒 **Expired** | Order reached its Time-in-Force limit without filling |

### Time-in-Force Options
| Option | Meaning |
|---|---|
| **DAY** | Valid for the current trading session only; auto-cancels at market close |
| **GTC** (Good Till Cancelled) | Stays open until you cancel it or it fills |
| **IOC** (Immediate or Cancel) | Fill whatever quantity is available immediately; cancel the rest |
| **FOK** (Fill or Kill) | Must fill the entire quantity immediately, or cancel the whole order |
| **GTD** (Good Till Date) | Active until a specific date you choose |
        """)

    # 6. Position
    with st.expander("📌 Positions"):
        st.markdown("""
### What is a Position?
A **position** represents your current holding in a particular security — how many shares you own and at what average cost.

### Position Metrics
| Metric | Formula | What it tells you |
|---|---|---|
| **Quantity** | # shares held | Size of the position |
| **Avg Cost / Entry Price** | Total cost ÷ Shares | Your break-even price |
| **Current Price** | Live market price | What it's worth now |
| **Market Value** | Current Price × Quantity | Total current worth |
| **Unrealized P&L** | (Current Price − Avg Cost) × Qty | Gain/Loss if you sold right now |
| **Realized P&L** | Profit/Loss from closed trades | Locked-in gain or loss |
| **P&L %** | (Current − Cost) ÷ Cost × 100 | Percentage gain or loss |
| **Day's Change** | Today's price move × Qty | How much value changed today |

### Long vs. Flat vs. Short Position
| | Meaning |
|---|---|
| **Long** | You own shares; profit if price rises |
| **Flat** | No position in the stock |
| **Short** | You've borrowed and sold shares; profit if price falls |

### How to Manage a Position
- **Add to a position (Average Down/Up):** Buy more shares to change your average cost
- **Trim a position:** Sell a portion to reduce exposure or lock in partial profits
- **Close a position:** Sell all shares (long) or buy back all shares (short)
        """)

    # 7. Balance
    with st.expander("💰 Balance"):
        st.markdown("""
### Account Balance Explained
Your brokerage account balance consists of several components:

| Balance Type | Definition |
|---|---|
| **Cash Balance** | Uninvested cash sitting in your account |
| **Buying Power** | Cash available to place new trades (may include margin) |
| **Portfolio Value** | Market value of all open positions |
| **Total Account Value** | Cash Balance + Portfolio Value |
| **Margin Balance** | Amount borrowed from broker (margin accounts only) |
| **Equity** | Total Account Value − Margin Balance |

### Paper Trading Balance (This App)
In the Paper Trader, you start with a **virtual cash balance** (e.g., $100,000). Each buy reduces your cash and adds shares;
each sell removes shares and credits cash. No real money is ever at risk.

### Important Balance Terms
- **Settlement:** After a trade fills, cash/shares don't settle instantly. US equities settle **T+1** (next business day).
- **Margin:** Borrowed funds from your broker to trade larger positions. Amplifies both gains *and* losses.
- **Maintenance Margin:** Minimum equity % required to hold a margin position; falling below triggers a **margin call**.
- **Pattern Day Trader (PDT):** US rule — making 4+ day trades in 5 business days requires a $25,000+ account.
        """)

    # 8. Performance
    with st.expander("📊 Performance"):
        st.markdown("""
### Measuring Portfolio Performance

#### Absolute Returns
| Metric | Formula |
|---|---|
| **Total P&L** | Current Value − Total Cost Basis |
| **Total Return %** | (Total P&L ÷ Total Cost Basis) × 100 |
| **Day's P&L** | Sum of (Price Change Today × Qty) for all positions |

#### Risk-Adjusted Returns
| Metric | What it means |
|---|---|
| **Sharpe Ratio** | Return per unit of risk. Higher = better. Above 1.0 is good; above 2.0 is excellent |
| **Max Drawdown** | Largest peak-to-trough decline in portfolio value — measures worst loss |
| **Win Rate** | % of closed trades that were profitable |
| **Profit Factor** | Gross profit ÷ Gross loss. Above 1.5 is solid |

#### Benchmarking
Always compare your returns against a **benchmark** (e.g., S&P 500). If the S&P returned 15% and you returned 10%,
you **underperformed** even though your absolute return was positive.

#### Key Takeaways
- 📈 **Consistency beats big wins** — steady positive returns with managed drawdowns outperforms "moonshots"
- 🎯 **Risk management first** — define your maximum loss per trade *before* entering
- 📅 **Review regularly** — weekly/monthly performance reviews help identify patterns in your trading
- 🔄 **Rebalance** — periodically restore your target allocation to control drift and manage risk

---
> 💡 **Tip:** Use the **Paper Trader** tab to practice all of these concepts with virtual money before risking real capital!
        """)
