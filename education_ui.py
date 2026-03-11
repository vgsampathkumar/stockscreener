import streamlit as st

# ── YouTube video helper ──────────────────────────────────────────────────────
def _yt(video_id: str, caption: str = ""):
    """Embed a YouTube video responsively using an iframe."""
    st.markdown(
        f"""
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                    border-radius:12px;margin:12px 0 4px 0;box-shadow:0 4px 16px rgba(0,0,0,0.12);">
          <iframe src="https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1"
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
    labels = ["🟢 Simple (Beginner)", "🟡 Medium (Intermediate)", "🔴 Complex (Advanced)"]
    texts  = [simple, medium, complex_]
    colors = ["#d1fae5", "#fef9c3", "#fee2e2"]
    border = ["#10b981", "#f59e0b", "#ef4444"]
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


# ══════════════════════════════════════════════════════════════════════════════
# Main render function
# ══════════════════════════════════════════════════════════════════════════════
def render_education():
    st.header("📚 Stock Market Education Center")
    st.markdown(
        "Your beginner-friendly guide to understanding the stock market. "
        "Each section has a **video**, **real-world examples** (simple → complex), "
        "and there's a **live AI Tutor** at the bottom you can chat with! 🤖"
    )

    # ── 1. Basics of Stock Market ─────────────────────────────────────────────
    with st.expander("🏛️ 1. Basics of the Stock Market", expanded=True):
        _yt("p7HKvqRI_Bo", "TED-Ed — How does the stock market work?")
        st.markdown("""
### What is the Stock Market?
The **stock market** is a marketplace where buyers and sellers trade **shares** (tiny pieces of ownership) of companies.
When a company wants to raise money, it sells shares to the public through an **IPO**. Those shares then trade on exchanges like the **NYSE** or **NASDAQ**.

| Term | Kid-Friendly Definition |
|---|---|
| **Stock / Share** | A tiny ownership piece of a company 🍕 |
| **Exchange** | The marketplace where stocks trade (NYSE, NASDAQ) |
| **Market Cap** | Total value of a company = Price × Total Shares |
| **Bull Market** 🐂 | Prices going UP — happy optimistic market |
| **Bear Market** 🐻 | Prices going DOWN — scared pessimistic market |
| **Index** | A scorecard tracking a group of stocks (e.g. S&P 500) |
| **Dividend** | Cash a company pays you just for owning its stock 💸 |
| **IPO** | A company's first day selling shares to the public 🎉 |
| **Broker** | The middleman app/person who executes your trades 📱 |
        """)
        _examples(
            "You own 1 share of your school's pizza club for $5. The club does well and your share becomes worth $8. You made $3 just by owning a piece! 🍕",
            "You buy 10 shares of Apple (AAPL) at $170 each ($1,700 total). Apple launches a hit product and shares rise to $200. Your investment is now worth $2,000 — a $300 gain! 📱",
            "You invest $10,000 across 5 stocks in different sectors. A bear market hits — tech falls 30% but healthcare rises 10%. Your diversified portfolio only falls 12% instead of 30%, because you spread the risk. 📊",
        )

    # ── 2. Buying & Selling ───────────────────────────────────────────────────
    with st.expander("💱 2. Buying & Selling Stocks"):
        _yt("ZCFkWDdmXG8", "How to Buy Stocks for Beginners — Step by Step")
        st.markdown("""
### How to Buy a Stock
1. **Open a brokerage account** (Robinhood, Fidelity, Schwab, Zerodha)
2. **Deposit money** into your account
3. **Search the ticker** — e.g. `AAPL` for Apple, `TSLA` for Tesla
4. **Place an order** — choose quantity and order type
5. **Monitor** your position in the portfolio section

### How to Sell
Reverse process: find the stock in your holdings → choose Sell → enter quantity → confirm. Cash arrives in **T+1** (next business day).

### Long vs. Short
| | Long 📈 | Short 📉 |
|---|---|---|
| You believe | Price will **rise** | Price will **fall** |
| Open position | **Buy** shares | Borrow & sell shares |
| Close position | **Sell** shares | Buy shares back |
| Profit when | Price goes UP | Price goes DOWN |
| Max loss | Amount invested | Unlimited ⚠️ |

### Key Costs
- **Commission:** Often $0 at modern brokers
- **Bid-Ask Spread:** Tiny hidden cost between buy/sell prices
- **Capital Gains Tax:** Profits are taxed — short-term (< 1 yr) at higher rate, long-term (> 1 yr) at lower rate
        """)
        _examples(
            "Emma has $50. She buys 1 share of a toy company at $50. A year later it's worth $65. She sells and makes $15 profit. That's investing! 🧸",
            "Jake buys 20 shares of Nike at $100 = $2,000. Nike reports bad earnings, shares drop to $90. He sells for $1,800 — a $200 realized loss that can offset other gains at tax time. 👟",
            "Sarah buys 50 Tesla shares at $200 ($10,000). After 2 years it hits $350. She sells 25 shares ($8,750) to lock in profit, holding 25 shares for more potential upside. She pays long-term capital gains tax only on the sold portion. ⚡",
        )

    # ── 3. Orders ────────────────────────────────────────────────────────────
    with st.expander("📋 3. Orders — What They Are"):
        _yt("bBiKjdY_Smc", "How to Buy Stocks — Understanding Orders (Step by Step)")
        st.markdown("""
### What is an Order?
An **order** is the instruction you send to your broker: *"Buy X shares of company Y."*
Every single trade starts as an order.

### Anatomy of an Order
| Component | Description |
|---|---|
| **Symbol** | Which stock (e.g. `MSFT` for Microsoft) |
| **Side** | Buy or Sell |
| **Quantity** | Number of shares |
| **Order Type** | How to execute (Market, Limit, Stop…) |
| **Time-in-Force** | How long to keep trying (Day, GTC…) |

### Order Lifecycle
```
Submitted → Pending → Working (live on exchange)
                            ↓               ↓           ↓
                         Filled ✅   Partially Filled 🟠   Cancelled / Rejected ⚪🔴
```
        """)
        _examples(
            "You tell your broker: 'Buy 5 shares of Disney.' That's your order! When it's matched on the exchange, it's filled — you now own 5 shares of Disney! 🏰",
            "You place a Day order to buy 100 shares of Ford at $12.00. The stock never drops that low today. At 4pm ET the order expires automatically — no shares bought, no money spent. 🚗",
            "A hedge fund needs to buy 500,000 shares without spiking the price. They use an algorithm to split it into 50 smaller orders of 10,000 each, spread over hours — this is called an algorithmic execution strategy. 🤖",
        )

    # ── 4. Order Types ────────────────────────────────────────────────────────
    with st.expander("🔀 4. Order Types"):
        _yt("Tiyystl8x40", "Market vs Limit vs Stop Orders — All Order Types Explained")
        st.markdown("""
### The 5 Main Order Types

| Type | Executes When | Price Guaranteed? | Best For |
|---|---|---|---|
| **Market** | Immediately | ❌ No | Fast fills on liquid stocks |
| **Limit** | At your price or better | ✅ Yes | Precise buy/sell price |
| **Stop-Loss** | Stock hits stop price → triggers Market order | ❌ No | Downside protection |
| **Stop-Limit** | Stock hits stop price → triggers Limit order | ✅ Yes | Controlled stop |
| **Trailing Stop** | Auto-moves stop as stock rises; fires if price drops by set % | ❌ No | Protecting gains |

#### 🔹 Market Order — "Buy NOW at any price"
Executes immediately at the best available price. Fastest but no price guarantee.

#### 🔹 Limit Order — "Only buy if the price is right"
Only fills at your specified price or better. May not fill at all if price never reaches your level.

#### 🔹 Stop-Loss — "Sell if things go bad"
A dormant order that activates when a stock reaches your stop price, then converts to a Market sell.

#### 🔹 Stop-Limit — "Sell if bad, but not below my floor"
Like Stop-Loss but converts to a Limit order. More control, but risks not filling if price gaps past the limit.

#### 🔹 Trailing Stop — "Protect my gains automatically"
The stop price follows the stock UP automatically as it rises, but never moves back down.
        """)
        _examples(
            "You want to buy 3 shares of Google right now, no matter the price. You place a Market order — done in 1 second at whatever the current price is. ✅",
            "Amazon is at $180 but you think it's fair value at $170. You place a Limit Buy at $170. It only executes if Amazon drops to $170 or below. If it never dips, you don't buy. 📦",
            "You own Netflix at $400. You set a 15% Trailing Stop. When Netflix rises to $500, the stop automatically moves to $425. If Netflix then crashes from $500 to $425, it auto-sells — locking in a $25/share profit over your $400 cost. 🎬",
        )

    # ── 5. Order Status ───────────────────────────────────────────────────────
    with st.expander("🚦 5. Order Status"):
        _yt("AQLVCFqkFbA", "Understanding Order Statuses — Pending, Filled, Cancelled Explained")
        st.markdown("""
### Every Order Passes Through States

| Status | Icon | Meaning |
|---|---|---|
| **Pending** | 🟡 | Submitted but not yet sent to the exchange |
| **Working / Open** | 🔵 | Live on the exchange, waiting to be matched |
| **Filled** | 🟢 | Fully executed — trade is complete! |
| **Partially Filled** | 🟠 | Some shares traded; rest still open |
| **Cancelled** | ⚪ | Removed before filling (by you or via Time-in-Force expiry) |
| **Rejected** | 🔴 | Refused (insufficient funds, invalid ticker, etc.) |
| **Expired** | 🕒 | Time limit hit without filling |

### Time-in-Force Options
| Option | Meaning |
|---|---|
| **DAY** | Valid today only; auto-cancels at 4pm ET |
| **GTC** (Good Till Cancelled) | Active until you cancel it or it fills |
| **IOC** (Immediate or Cancel) | Fill what's available now; cancel the rest |
| **FOK** (Fill or Kill) | Must fill entirely and instantly, or cancel |
| **GTD** (Good Till Date) | Active until your chosen date |
        """)
        _examples(
            "You place a Market order for Apple shares. It shows 'Working' for 1 second, then 'Filled'. Done — you're an Apple shareholder! 🍎",
            "You place a Limit order to sell 200 shares of a thinly traded stock. After an hour, only 120 shares found buyers. Status = 'Partially Filled'. The remaining 80 shares are still 'Working' on the exchange.",
            "You set a GTC Limit Buy for a biotech stock at $45 (currently $60). Three weeks later, bad news drops the stock to $44.95 briefly. Your order fills at $45 exactly — the patient entry you planned months ago. 🧬",
        )

    # ── 6. Position ───────────────────────────────────────────────────────────
    with st.expander("📌 6. Positions"):
        _yt("bMnKtXkDTbE", "Long Position vs Short Position — Trading for Beginners")
        st.markdown("""
### What is a Position?
A **position** is your current holding — how many shares you own and at what average cost.

### Position Metrics
| Metric | Formula | What it tells you |
|---|---|---|
| **Quantity** | Shares held | Size of your holding |
| **Avg Cost** | Total paid ÷ Shares | Your personal break-even price |
| **Market Value** | Current Price × Qty | What it's worth right now |
| **Unrealized P&L** | (Price − Avg Cost) × Qty | Gain/loss if you sold right now |
| **Realized P&L** | From closed trades | Profit/loss you've already locked in |
| **P&L %** | (Price − Cost) ÷ Cost × 100 | Percentage gain or loss |
| **Day Change** | Today's price move × Qty | How much value changed today |

### Position Types
| | Meaning |
|---|---|
| **Long** | You own shares — profit if price rises 📈 |
| **Flat** | No position in that stock |
| **Short** | Borrowed & sold shares — profit if price falls 📉 |
        """)
        _examples(
            "You buy 5 shares of McDonald's at $280. Your position = 5 shares, avg cost = $280. If it goes to $300 you have an unrealized profit of $100. You haven't actually made money until you SELL! 🍔",
            "You buy 50 shares of Microsoft at $300. Then you buy 50 more at $280. Your new avg cost = $290. Now you need the price above $290 just to break even — this is called 'averaging down'. 💻",
            "A fund manager holds 2,000 shares of Nvidia long (+$1.8M) and is short 1,000 shares of AMD. If Nvidia rises and AMD falls, BOTH positions profit simultaneously. This 'long/short pair trade' is used to capture relative value while hedging market risk. 🖥️",
        )

    # ── 7. Balance ───────────────────────────────────────────────────────────
    with st.expander("💰 7. Balance"):
        _yt("0SGGSqOZhps", "Brokerage Account Balance — Cash, Buying Power, Margin Explained")
        st.markdown("""
### Your Account Balance Breakdown
| Term | Definition |
|---|---|
| **Cash Balance** | Uninvested cash sitting in your account |
| **Buying Power** | Cash available for new trades (may include margin) |
| **Portfolio Value** | Current market value of all open positions |
| **Total Account Value** | Cash + Portfolio Value |
| **Equity** | Total Value − Margin borrowed |

### Paper Trading Balance (This App)
You start with **virtual cash** (e.g. $100,000). Buying reduces cash and adds shares. Selling does the reverse. Zero real risk — perfect for learning! 🎮

### Key Balance Rules
- **Settlement (T+1):** After selling, cash arrives the next business day
- **Margin:** Borrowed money from broker — amplifies gains AND losses equally
- **Maintenance Margin:** Minimum equity required; falling below triggers a **Margin Call** 🚨
- **PDT Rule:** 4+ day trades in 5 days with < $25,000 account = restrictions ⚠️
        """)
        _examples(
            "You deposit $1,000 into your paper trading account. Cash = $1,000. You buy $400 of stock. Now cash = $600, portfolio value = $400, total = $1,000. Nothing was gained or lost yet! 🏦",
            "You have $10,000 in a margin account. Broker gives 2× leverage = $20,000 buying power. You buy $15,000 of stock. If it rises 10%, you gain $1,500 on your $10k equity = 15% return (better than 10% without margin). But losses are amplified the same way! ⚡",
            "A trader uses 4× leverage on a $50,000 account ($200,000 position). The market crashes 25% overnight. Position drops $50,000 in value — wiping out ALL the trader's equity. A margin call forces immediate deposit or force-liquidation at the worst possible price. 🚨",
        )

    # ── 8. Performance ────────────────────────────────────────────────────────
    with st.expander("📊 8. Performance"):
        _yt("ezFzCcAoeBs", "How to Check Your Portfolio Performance — Beginners Guide")
        st.markdown("""
### Measuring How Well You're Doing

#### Absolute Returns
| Metric | Formula |
|---|---|
| **Total Return %** | (Current Value − Cost) ÷ Cost × 100 |
| **Day's P&L** | Sum of (Today's price change × Qty) across all positions |

#### Risk-Adjusted Returns
| Metric | Meaning | Target |
|---|---|---|
| **Sharpe Ratio** | Return per unit of risk taken | > 1.0 good, > 2.0 excellent |
| **Max Drawdown** | Biggest peak-to-valley drop in portfolio value | Smaller = better |
| **Win Rate** | % of trades that were profitable | > 50% is helpful |
| **Profit Factor** | Gross profit ÷ Gross loss | > 1.5 is solid |

#### Benchmarking
Always compare against the **S&P 500**. If the S&P gained 20% and you gained 12%, you *underperformed* — even though you made money.

#### Key Principles
- 📅 Review performance weekly/monthly — catch bad habits early
- 🎯 Define your maximum loss **before** entering any trade
- 🔄 Rebalance periodically to control risk drift
- 📈 **Rule of 72:** Divide 72 by your annual return % to find how many years to double your money (10% return → doubles in 7.2 years!)
        """)
        _examples(
            "You invested $1,000 in an S&P 500 ETF a year ago — now worth $1,120. Your return = 12%. The S&P itself returned 12%. You matched the benchmark perfectly! 🏆",
            "Your portfolio returned 18% — but it dropped 22% in March before recovering. High return but HIGH pain. Sharpe ratio = 0.8. A smoother strategy earning 14% with a Sharpe of 1.6 is actually better on a risk-adjusted basis. 📊",
            "A quant fund wins only 45% of trades, but averages a $3,000 gain per winner and only $1,000 loss per loser. Profit Factor = (0.45 × $3,000) ÷ (0.55 × $1,000) = 2.45 — hugely profitable despite losing more often than winning! Risk/reward ratio beats win rate. 🧮",
        )

    # ══════════════════════════════════════════════════════════════════════════
    # AI Tutor Chatbot
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🤖 Ask the AI Finance Tutor")
    st.markdown(
        "Chat with an AI tutor powered by **Llama 3 via Groq** (free & fast ⚡). "
        "Ask anything about stocks, trading, investing, or any concept above!"
    )

    # ── Groq API key handling ─────────────────────────────────────────────────
    groq_key = None
    try:
        groq_key = st.secrets.get("GROQ_API_KEY", None)
    except Exception:
        pass

    if not groq_key:
        st.info(
            "💡 **To activate the AI Tutor:** Add your free Groq API key to `.streamlit/secrets.toml`:\n\n"
            "```\nGROQ_API_KEY = \"your-key-here\"\n```\n\n"
            "Get a **free key** (no credit card) at 👉 [console.groq.com](https://console.groq.com) in under 1 minute!"
        )
        # Still render a limited chatbot with canned Q&A when no key is present
        _render_basic_chatbot()
        return

    _render_ai_chatbot(groq_key)


# ── Suggested question chips helper ──────────────────────────────────────────
_SUGGESTED = [
    "What is a stock? Explain like I'm 10 🍎",
    "How does a limit order work? Give me an example",
    "What is the difference between unrealized and realized profit?",
    "Why does the stock market go up and down?",
    "What is the S&P 500 index?",
    "How does short selling work?",
    "What is a margin call? Is it scary?",
    "What is the Sharpe ratio and why does it matter?",
    "How can a kid start investing?",
    "What is the Rule of 72?",
    "What is a bull market vs bear market?",
    "Explain dividends with a simple example",
]

def _render_ai_chatbot(groq_key: str):
    """Full AI chatbot powered by Groq Llama-3."""
    try:
        from groq import Groq
    except ImportError:
        st.error("⚠️ The `groq` package is not installed. Run `pip install groq` and restart the app.")
        return

    # Initialise session state
    if "edu_chat" not in st.session_state:
        st.session_state["edu_chat"] = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hi! I'm your **AI Finance Tutor** powered by Llama 3! 🚀\n\n"
                    "I make stock market concepts fun and easy to understand — whether you're 10 years old or 100! "
                    "Ask me *anything* about stocks, trading, investing, or any topic from the sections above.\n\n"
                    "**Try clicking one of the suggested questions below, or type your own!** ⬇️"
                ),
            }
        ]

    # Render chat history
    for msg in st.session_state["edu_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Suggested question chips ──────────────────────────────────────────────
    st.markdown("**💬 Suggested questions — click to ask:**")
    cols = st.columns(3)
    for i, suggestion in enumerate(_SUGGESTED):
        with cols[i % 3]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state["edu_pending_q"] = suggestion

    # ── Chat input ────────────────────────────────────────────────────────────
    typed_q = st.chat_input("Ask me anything about stocks and investing…")

    # Resolve which question to process (typed or clicked suggestion)
    question = typed_q or st.session_state.pop("edu_pending_q", None)

    if question:
        # Show user message immediately
        st.session_state["edu_chat"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Call Groq with a strong educational system prompt
        system_prompt = """You are an enthusiastic, friendly AI Finance Tutor named "Finley" 🦊.
Your mission is to make stock market and investing concepts fun, clear, and exciting for everyone — especially kids and teenagers.

Rules:
- Use simple, everyday language. Avoid jargon unless you immediately explain it.
- Use emojis, analogies, and real-world comparisons (pizza 🍕, candy 🍬, sports, games) to explain concepts.
- Always give a concrete example after explaining any concept.
- If a beginner asks, explain from scratch. If an advanced question is asked, match the sophistication.
- Keep responses concise — 3 to 6 paragraphs max.
- End every response with a fun follow-up question or a "did you know?" fact to keep the learner engaged.
- Never give actual financial advice or tell anyone what to buy/sell. You are educational only.
- If asked something outside finance/investing, kindly redirect to finance topics.
"""

        with st.chat_message("assistant"):
            with st.spinner("Finley is thinking… 🦊"):
                try:
                    client = Groq(api_key=groq_key)
                    # Build message history (last 10 messages to stay within context limit)
                    history = st.session_state["edu_chat"][-10:]
                    messages = [{"role": "system", "content": system_prompt}] + [
                        {"role": m["role"], "content": m["content"]} for m in history
                    ]
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        max_tokens=600,
                        temperature=0.7,
                    )
                    answer = response.choices[0].message.content
                except Exception as e:
                    answer = (
                        f"⚠️ Oops! Couldn't connect to the AI tutor right now. Error: `{e}`\n\n"
                        "Please check your Groq API key in `.streamlit/secrets.toml` and try again!"
                    )

            st.markdown(answer)

        st.session_state["edu_chat"].append({"role": "assistant", "content": answer})
        st.rerun()


def _render_basic_chatbot():
    """Simple keyword-based fallback chatbot when no API key is configured."""
    KB = {
        "stock": "A **stock** (or share) is a tiny piece of ownership in a company! 🍕 If a company has 1 million shares and you own 1, you own one-millionth of that company. When the company does well, your share becomes more valuable!",
        "market": "The **stock market** is like a giant online store where people buy and sell ownership pieces of companies. Popular exchanges include the NYSE and NASDAQ in the US. 🏛️",
        "buy": "To **buy a stock**: open a brokerage account → deposit money → search for the ticker symbol (e.g. AAPL for Apple) → place a Buy order → done! The shares appear in your portfolio. 📱",
        "sell": "To **sell a stock**: find it in your portfolio → place a Sell order → choose how many shares → confirm. The cash arrives in your account by the next business day (T+1). 💵",
        "limit": "A **limit order** only executes at your specified price or better. If you want Apple at $170 but it's trading at $180, you set a Limit Buy at $170. It only fills if Apple drops to $170 or below. 🎯",
        "market order": "A **market order** executes immediately at whatever the current price is. It's the fastest way to buy or sell, but you don't control the exact price. Best for very popular stocks! ⚡",
        "stop": "A **stop-loss order** is a safety net 🛡️. You pick a price — if the stock falls to that level, it automatically sells to prevent bigger losses. E.g. buy at $100, set stop at $90.",
        "order": "An **order** is the instruction you send to your broker to buy or sell shares. You specify the stock, quantity, and price type. Every trade starts as an order! 📋",
        "position": "A **position** is how many shares you currently own of a stock. If you own 50 Tesla shares, you have a 'position' of 50 shares in TSLA. The P&L shows how much you've gained or lost. 📌",
        "profit": "**Profit (P&L)** = Current Value − What You Paid. If you paid $1,000 and it's worth $1,200, your profit is $200 (20% gain). Unrealized P&L = on paper; Realized P&L = actually sold. 💰",
        "loss": "A **loss** happens when your stock is worth less than you paid. E.g. bought at $100, now at $80 = $20 unrealized loss per share. Losses become 'realized' (and tax-deductible) only when you sell. 📉",
        "balance": "Your **account balance** = Cash + Portfolio Value. Cash is money not yet invested. Portfolio value is the current worth of your stocks. Buying power is how much you can still invest. 🏦",
        "dividend": "A **dividend** is money a company shares with shareholders! E.g. you own 100 shares and the company pays $1/share dividend — you receive $100 cash just for holding the stock. 💸",
        "etf": "An **ETF** (Exchange-Traded Fund) is a basket of stocks in one investment. SPY tracks the S&P 500 — buying 1 SPY share gives exposure to 500 companies! Great for beginners. 🧺",
        "index": "An **index** like the S&P 500 tracks 500 large US companies. If the S&P rises, most of those stocks went up. It's like a report card for the overall stock market! 📊",
        "bull": "A **bull market** 🐂 means stocks are rising and investors are optimistic. Historically bull markets last longer than bear markets — the market generally goes UP over the long run!",
        "bear": "A **bear market** 🐻 means stocks are falling — typically a 20%+ drop from recent highs. They're scary but temporary! Every bear market in history has eventually ended with a recovery.",
        "ipo": "An **IPO** (Initial Public Offering) is when a private company sells shares to the public for the first time. It's like the company's stock market birthday! 🎂",
        "broker": "A **broker** is the middleman who places your trades on the exchange. Modern brokers are apps like Robinhood, Fidelity, Schwab, or Zerodha. Many now offer $0 commission! 📱",
        "sharpe": "The **Sharpe Ratio** measures how much return you earn per unit of risk. Higher is better — above 1.0 is good, above 2.0 is excellent. It tells you if your gains are worth the stress! 🎯",
        "drawdown": "**Max Drawdown** is the biggest drop from peak to bottom before recovering. E.g. if your portfolio went from $10k → $7k → $15k, the max drawdown was -30%. Lower drawdown = smoother ride. 📉",
        "margin": "**Margin** means borrowing money from your broker to invest more. It amplifies BOTH gains and losses. Risky for beginners — stick to cash accounts while learning! ⚠️",
        "short": "**Short selling** means borrowing shares and selling them, hoping to buy them back cheaper later. You profit if the price FALLS. Risk is theoretically unlimited since prices can rise forever. 🎲",
        "paper": "**Paper trading** is practicing with fake virtual money — all the realism of trading with zero financial risk! Use the Paper Trader tab in this app to practice before risking real money. 🎮",
    }

    if "edu_chat_basic" not in st.session_state:
        st.session_state["edu_chat_basic"] = [
            {"role": "assistant", "content": "👋 Hi! I'm a basic Finance Tutor Bot (add a **free Groq API key** above to unlock the full AI tutor!). Ask me basic stock market questions — like *'what is a stock?'* or *'what is a limit order?'*"}
        ]

    for msg in st.session_state["edu_chat_basic"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Suggested chips
    st.markdown("**💬 Try asking:**")
    basic_suggestions = ["What is a stock?", "What is a limit order?", "What is a dividend?",
                         "What is a bull market?", "What is paper trading?", "What is a position?"]
    cols = st.columns(3)
    for i, s in enumerate(basic_suggestions):
        with cols[i % 3]:
            if st.button(s, key=f"bsug_{i}", use_container_width=True):
                st.session_state["edu_basic_pending"] = s

    user_q = st.chat_input("Ask a basic finance question…")
    question = user_q or st.session_state.pop("edu_basic_pending", None)

    if question:
        st.session_state["edu_chat_basic"].append({"role": "user", "content": question})
        q_lower = question.lower()
        answer = None
        for keyword, resp in KB.items():
            if keyword in q_lower:
                answer = resp
                break
        if not answer:
            answer = (
                "Good question! 🤔 I'm a basic bot so my knowledge is limited. "
                "**Add a free Groq API key** (see above) to unlock the full AI tutor that can answer anything! "
                "Try asking about: *stock, buy, sell, limit, stop, position, dividend, ETF, index, bull, bear, margin, or paper trading.*"
            )
        st.session_state["edu_chat_basic"].append({"role": "assistant", "content": answer})
        st.rerun()
