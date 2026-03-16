import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import plotly.graph_objects as go
from portfolio_engine import PaperPortfolio

# ---- Cached helpers (called outside the class so st.cache_data works) ----

@st.cache_data(ttl=5) # Real-time-ish for trades
def get_price_robust(ticker: str) -> float:
    """Resilient one-off price fetcher for cloud environments."""
    if not ticker: return 0.0
    try:
        t = yf.Ticker(ticker)
        # 1. fast_info
        try:
            if hasattr(t, 'fast_info') and 'last_price' in t.fast_info:
                p = t.fast_info['last_price']
                if p and p > 0: return float(p)
        except: pass
        # 2. info
        try:
            info = t.info
            p = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            if p and p > 0: return float(p)
        except: pass
        # 3. history
        h = t.history(period="1d")
        if not h.empty:
            return float(h["Close"].iloc[-1])
        return 0.0
    except:
        return 0.0

@st.cache_data(ttl=60)  # Refresh prices at most once per minute
def fetch_live_prices(tickers: tuple) -> dict:
    """Batch-fetch prices for a list of tickers in ONE yfinance call."""
    if not tickers:
        return {}
    try:
        data = yf.download(list(tickers), period="1d", progress=False, auto_adjust=True)
        prices = {}
        if len(tickers) == 1:
            tick = tickers[0]
            if not data.empty and 'Close' in data.columns:
                prices[tick] = float(data['Close'].iloc[-1])
            else:
                prices[tick] = get_price_robust(tick) # Fallback
        else:
            for tick in tickers:
                try:
                    p = 0.0
                    if 'Close' in data.columns:
                        col = data['Close']
                        if tick in col.columns:
                            p = float(col[tick].dropna().iloc[-1])
                        else:
                            p = float(col.dropna().iloc[-1]) if not col.empty else 0.0
                    
                    if p <= 0: p = get_price_robust(tick)
                    prices[tick] = p
                except Exception:
                    prices[tick] = get_price_robust(tick)
        return prices
    except Exception:
        return {t: get_price_robust(t) for t in tickers}

@st.cache_data(ttl=300)  # Cache market status for 5 minutes
def get_cached_market_status() -> dict:
    """Thin wrapper so market calendar check is cached."""
    import pandas_market_calendars as mcal
    import datetime as dt
    now_et = datetime.now(pytz.timezone('US/Eastern'))
    try:
        nyse = mcal.get_calendar('NYSE')
        schedule = nyse.schedule(start_date=now_et.date(), end_date=now_et.date())
        is_trading_day = not schedule.empty
    except Exception:
        is_trading_day = now_et.weekday() < 5
    if not is_trading_day:
        return {"status": "CLOSED", "is_open": False}
    t = now_et.time()
    import datetime as _dt
    if _dt.time(9, 30) <= t <= _dt.time(16, 0):
        return {"status": "OPEN", "is_open": True}
    elif _dt.time(4, 0) <= t < _dt.time(9, 30):
        return {"status": "PRE-MARKET", "is_open": False}
    elif _dt.time(16, 0) < t <= _dt.time(20, 0):
        return {"status": "AFTER-HOURS", "is_open": False}
    return {"status": "CLOSED", "is_open": False}

def render_paper_trader(portfolio: PaperPortfolio):
    # Process any orders that can execute right now
    portfolio.process_pending_orders()

    # --- Fetch everything ONCE using the cached helpers ---
    cash = portfolio.get_cash_balance()
    pos_df_raw = portfolio.get_open_positions(include_live_prices=False)
    if not pos_df_raw.empty:
        tickers_tuple = tuple(pos_df_raw['ticker'].tolist())
        price_map = fetch_live_prices(tickers_tuple)
        pos_df_raw['current_price'] = pos_df_raw['ticker'].map(price_map)
        pos_df_raw['market_value'] = pos_df_raw['shares'] * pos_df_raw['current_price']
        pos_df_raw['total_cost'] = pos_df_raw['shares'] * pos_df_raw['avg_cost']
        pos_df_raw['unrealized_pnl'] = pos_df_raw['market_value'] - pos_df_raw['total_cost']
        pos_df_raw['return_pct'] = (pos_df_raw['unrealized_pnl'] / pos_df_raw['total_cost']).fillna(0) * 100
    pos_df = pos_df_raw
    pos_val = pos_df['market_value'].sum() if not pos_df.empty and 'market_value' in pos_df.columns else 0.0
    total_val = cash + pos_val

    start_val = 100000.0
    total_ret = ((total_val - start_val) / start_val) * 100
    ret_color = "#008a00" if total_ret >= 0 else "#d10000"
    sign = "+" if total_ret >= 0 else ""

    # --- Compact CSS for Paper Trading ---
    st.markdown("""
    <style>
        /* Compact Paper Trading header bar */
        .paper-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 0;
            margin-bottom: 4px;
            border-bottom: 2px solid #e5e7eb;
        }
        .paper-header h2 {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            color: #111827;
        }
        .paper-header .actions {
            display: flex;
            gap: 8px;
        }
        
        /* Smaller tabs for Paper Trading */
        .paper-tabs [data-baseweb="tab-list"] {
            gap: 0px !important;
        }
        .paper-tabs [data-baseweb="tab"] {
            font-size: 0.85rem !important;
            padding: 6px 16px !important;
            min-height: unset !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- Compact Title ---
    st.markdown("<h2 style='margin:0; font-size:1.15rem; font-weight:800;'>💰 Paper Money Trading</h2>", unsafe_allow_html=True)



    # --- Tabbed Content (Trade & Quote are part of the tab bar) ---
    st.markdown('<div class="paper-tabs">', unsafe_allow_html=True)
    tab_summary, tab_positions, tab_activity, tab_balances, tab_performance, tab_trade, tab_quote = st.tabs(
        ["📊 Summary", "📈 Positions", "📋 Activity & Orders", "💵 Balances", "🏆 Performance", "🔄 Trade", "🔍 Quote"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    with tab_summary:
        render_summary_tab(portfolio, cash, pos_df, total_val, start_val, total_ret, ret_color, sign)

    with tab_positions:
        render_positions_tab(pos_df, total_val)

    with tab_activity:
        render_activity_tab(portfolio)

    with tab_balances:
        render_balances_tab(cash, total_val, start_val, ret_color, sign)
        st.markdown("---")
        if st.button("🚨 Reset Academy Portfolio", help="Warning: Wipes all trades and positions, resets to $100K."):
            portfolio.reset_portfolio()
            st.rerun()

    with tab_performance:
        render_performance_tab(portfolio, cash, pos_df, total_val, start_val, total_ret, ret_color, sign)

    with tab_trade:
        render_order_ticket(portfolio)

    with tab_quote:
        render_quote_panel()


def render_quote_panel():
    with st.expander("🔍 Quote Lookup", expanded=True):
         cq1, cq2 = st.columns([3, 1])
         with cq1:
             q_ticker = st.text_input("Enter Symbol", key="quote_tick").upper()
         with cq2:
             st.markdown("<br>", unsafe_allow_html=True)
             if st.button("Close"):
                  st.session_state['show_quote_modal'] = False
                  st.rerun()
          if q_ticker:
             try:
                 t = yf.Ticker(q_ticker)
                 cp = get_price_robust(q_ticker)
                 
                 # info might still work for name even if inhibited for price
                 try:
                     name = t.info.get('longName', q_ticker)
                 except:
                     name = q_ticker

                 st.markdown(f"**{name} ({q_ticker})** | **${cp:.2f}**")
                 
                 # The functional Buy/Sell buttons from the requirement
                 qb1, qb2, _ = st.columns([1, 1, 4])
                 with qb1:
                      if st.button("Buy", type="primary", key="qb_buy"):
                           st.session_state['show_order_ticket'] = True
                           st.session_state['show_quote_modal'] = False
                           st.session_state['paper_trade_ticker'] = q_ticker
                           st.rerun()
                 with qb2:
                      if st.button("Sell", key="qb_sell"):
                           st.session_state['show_order_ticket'] = True
                           st.session_state['show_quote_modal'] = False
                           st.session_state['paper_trade_ticker'] = q_ticker
                           # We can't set action here easily without modifying render_ticket, but ticker helps
                           st.rerun()
                           
                 hist = t.history(period="1mo")
                 if not hist.empty:
                     st.line_chart(hist['Close'])
             except:
                 st.error("Could not fetch quote")
                 
    st.markdown("---")





def render_summary_tab(portfolio, cash, pos_df, total_val, start_val, total_ret, ret_color, sign):
    # Full-width layout for the balance card
    st.markdown("""
    <div style="border:1px solid #e5e7eb; border-radius:15px; padding:20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
    """, unsafe_allow_html=True)
    
    st.markdown(f"<p style='margin:0; font-size:1.4em; font-weight:bold; color:#111827'>Balance ⓘ</p><h1 style='margin:0; font-size:2.5em;'>${total_val:,.2f}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {ret_color}; font-weight: bold; margin-bottom: 25px;'>{sign}${total_val - start_val:,.2f} ({sign}{total_ret:.2f}%) <span style='font-weight:normal; color:#6b7280'>Today's gain/loss</span></p>", unsafe_allow_html=True)
    
    # Performance chart for the Balance card
    perf_df = portfolio.get_performance_history()
    fig_small = go.Figure()
    fig_small.add_trace(go.Scatter(x=perf_df['date'], y=perf_df['total_value'], mode='lines', line=dict(color='#3b82f6', width=2)))
    fig_small.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), 
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb', side='right', tickprefix='$'), 
        plot_bgcolor='white', 
        height=180, 
        showlegend=False
    )
    st.plotly_chart(fig_small, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_positions_tab(pos_df, total_val):
    st.markdown("### Positions")
    if pos_df.empty:
         st.info("No open positions. Click 'Trade' to get started!")
    else:
         # Format like Fidelity
         display_df = pd.DataFrame()
         display_df['Symbol'] = pos_df['ticker']
         display_df['Last Price'] = pos_df['current_price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
         
         # Gain formatting helper
         def fmt_gain(val, pct):
              if pd.isnull(val): return "N/A"
              color = "green" if val >= 0 else "red"
              s = "+" if val >= 0 else ""
              return f"<div><span style='color:{color}'>{s}${val:.2f}</span><br><span style='font-size:0.8em;color:{color}'>({s}{pct:.2f}%)</span></div>"
         
         display_df['Total Gain/Loss'] = pos_df.apply(lambda r: fmt_gain(r['unrealized_pnl'], r['return_pct']), axis=1)
         display_df['Current Value'] = pos_df['market_value'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
         display_df['% of Account'] = (pos_df['market_value'] / total_val * 100).apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
         display_df['Quantity'] = pos_df['shares']
         display_df['Cost Basis'] = pos_df['avg_cost'].apply(lambda x: f"${x:.2f}")

         # Use HTML table to allow colored multi-line cells
         st.markdown(display_df.to_html(escape=False, index=False, classes='positions-table'), unsafe_allow_html=True)
         
         # Add some CSS for the table
         st.markdown("""
         <style>
             .positions-table {
                 width: 100%;
                 border-collapse: collapse;
                 margin-top: 20px;
                 font-size: 0.95rem;
             }
             .positions-table th {
                 text-align: left;
                 border-bottom: 2px solid #e5e7eb;
                 padding: 12px 8px;
                 color: #6b7280;
                 font-weight: 600;
             }
             .positions-table td {
                 padding: 16px 8px;
                 border-bottom: 1px solid #f3f4f6;
                 vertical-align: middle;
             }
         </style>
         """, unsafe_allow_html=True)


def render_activity_tab(portfolio):
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px;'>
        <div style='border:1px solid #d1d5db; border-radius:4px; padding:6px 12px; display:inline-block; width:300px;'>
            <span style='color:#6b7280'>🔍 Search Activity & Orders</span>
        </div>
        <div style='color:#6b7280; font-size:0.9em;'>As of Mar-09-2026 6:44 p.m. ET 🔄 &nbsp;&nbsp; 🖨 &nbsp;&nbsp; 📥</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 25px;'>
        <div style='border:1px solid #d1d5db; border-radius:20px; padding:4px 15px;'>Past 30 days ▾</div>
        <div style='border:1px solid #008a00; color:#008a00; border-radius:20px; padding:4px 15px; font-weight:bold;'>Orders</div>
        <div style='border:1px solid #008a00; color:#008a00; border-radius:20px; padding:4px 15px;'>History</div>
        <div style='border:1px solid #d1d5db; border-radius:20px; padding:4px 15px;'>⧸⧹ More filters</div>
    </div>
    """, unsafe_allow_html=True)

    pending_df = portfolio.get_pending_orders()
    trades_df = portfolio.get_trade_history()
    
    # Build Fidelity-style table header
    st.markdown("""
    <div style='display:grid; grid-template-columns: 15% 20% 40% 15% 10%; border-bottom:1px solid #e5e7eb; padding-bottom:10px; color:#6b7280; font-size:0.9em; font-weight:bold;'>
        <div>Date ▾</div>
        <div>Account</div>
        <div>Description</div>
        <div>Status</div>
        <div style='text-align:right'>Amount</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pending Section
    with st.expander("Pending Orders", expanded=(not pending_df.empty)):
         if pending_df.empty:
              st.write("No pending orders.")
         else:
              for _, r in pending_df.iterrows():
                   amt = r['shares'] * r['limit_price'] if pd.notnull(r['limit_price']) else float('nan')
                   amt_str = f"${amt:.2f}" if pd.notnull(amt) else "--"
                   desc = f"{str(r['action']).capitalize()} {r['shares']} Shares of {r['ticker']} at {r['order_type']} ({r['tif']})"
                   dt_str = datetime.fromisoformat(r['submitted_at']).strftime('%b-%d-%Y')
                   
                   st.markdown(f"""
                   <div style='display:grid; grid-template-columns: 15% 20% 40% 15% 10%; padding:15px 0; border-bottom:1px solid #f3f4f6; align-items:center; font-size:0.95em'>
                       <div>{dt_str}</div>
                       <div>Individual - TOD<br><span style='color:#6b7280; font-size:0.9em'>Z52234364</span></div>
                       <div>{desc}</div>
                       <div>{r['status']}</div>
                       <div style='text-align:right'>{amt_str}</div>
                   </div>
                   """, unsafe_allow_html=True)
              
              # Provide a simple cancel input based on DB ID
              colA, colB, colC = st.columns([1, 1, 3])
              with colA:
                   c_id = st.number_input("Order ID to Cancel", min_value=0, step=1, label_visibility="collapsed")
              with colB:
                   if st.button("Cancel Order"):
                        portfolio.cancel_order(c_id)
                        st.rerun()

    with st.expander("Trade History", expanded=(not trades_df.empty)):
         if trades_df.empty:
              st.write("No executed trades yet.")
         else:
              for _, r in trades_df.iterrows():
                   desc = f"{str(r['action']).capitalize()} {r['shares']} Shares of {r['ticker']} at Market (Day)"
                   dt_str = datetime.fromisoformat(r['date']).strftime('%b-%d-%Y')
                   amt_str = f"${r['total']:.2f}"
                   status_str = f"Filled at<br>${r['price']:.2f}"
                   
                   st.markdown(f"""
                   <div style='display:grid; grid-template-columns: 15% 20% 40% 15% 10%; padding:15px 0; border-bottom:1px solid #f3f4f6; align-items:center; font-size:0.95em'>
                       <div>{dt_str}</div>
                       <div>Brokerage Account<br><span style='color:#6b7280; font-size:0.9em'>Z52234364</span></div>
                       <div>{desc}</div>
                       <div>{status_str}</div>
                       <div style='text-align:right'>{amt_str}</div>
                   </div>
                   """, unsafe_allow_html=True)


def render_balances_tab(cash, total_val, start_val, ret_color, sign):
    st.markdown(f"""
    <div style='text-align:right; color:#6b7280; font-size:0.9em; margin-bottom: 20px;'>
        As of {datetime.now().strftime('%b-%d-%Y %I:%M %p')} ET 🔄 ⚙️
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display:grid; grid-template-columns: 60% 20% 20%; border-bottom:2px solid #e5e7eb; padding-bottom:10px; color:#6b7280; font-size:0.95em;'>
        <div>Account</div>
        <div style='text-align:right'>Balance</div>
        <div style='text-align:right'>Day change</div>
    </div>
    """, unsafe_allow_html=True)

    # Main Brokerage Account
    st.markdown(f"""
    <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 20px 0 10px 0; font-weight:bold; font-size:1.1em;'>
        <div>📈 Brokerage Account <span style='color:#6b7280; font-weight:normal; font-size:0.95em;'>Paper Trading</span></div>
        <div style='text-align:right'>${total_val:,.2f}</div>
        <div style='text-align:right; color:{ret_color}'>{sign}${total_val - start_val:,.2f}</div>
    </div>
    <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 10px 0; font-size:0.95em; color:#374151;'>
        <div>Available to trade (all settled)</div>
        <div style='text-align:right'>${cash:,.2f}</div>
        <div></div>
    </div>
    <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 10px 0 20px 0; font-size:0.95em; color:#374151; border-bottom:1px solid #e5e7eb;'>
        <div>Available to withdraw</div>
        <div style='text-align:right'>${cash:,.2f}</div>
        <div></div>
    </div>
    """, unsafe_allow_html=True)
             


def render_order_ticket(portfolio: PaperPortfolio):
    st.markdown("### 📋 ORDER TICKET")
    
    with st.container(border=True):

        # Pre-fills from session state if coming from other tabs
        default_ticker = st.session_state.get('paper_trade_ticker', 'AAPL')
        default_notes = st.session_state.get('paper_trade_notes', '')

        action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        ticker = st.text_input("Symbol", value=default_ticker).upper()
        shares = st.number_input("Quantity", min_value=1, value=10, step=1, help="Number of shares to trade")
        
        st.markdown("---")
        
        o_types = ["Market", "Limit", "Stop Loss", "Stop Limit", "Trailing Stop $", "Trailing Stop %"]
        o_type = st.selectbox("Order Type", o_types, help="How your order will be priced and executed")
        
        limit_px = None
        stop_px = None
        trail_val = None
        trail_type = None
        
        if o_type in ["Limit", "Stop Limit"]:
            limit_px = st.number_input("Limit Price ($)", min_value=0.01, value=150.00, step=0.50, help="Max price you'll pay (buy) or min you'll accept (sell)")
        if o_type in ["Stop Loss", "Stop Limit"]:
            stop_px = st.number_input("Stop Price ($)", min_value=0.01, value=145.00, step=0.50, help="The trigger price that activates your order")
        if o_type in ["Trailing Stop $", "Trailing Stop %"]:
            trail_type = "$" if "$" in o_type else "%"
            trail_val = st.number_input(f"Trail Amount ({trail_type})", min_value=0.01, value=5.00, step=1.00, help="How far the stop trails the peak price")

        st.markdown("---")
        tif = st.selectbox("Time in Force", ["Day", "GTC", "IOC", "FOK", "GTD", "OPG", "MOC"], help="How long this order stays active")
        
        notes = st.text_area("Trade Notes (optional)", value=default_notes, help="Optional: record why you're making this trade")
        
        # Estimate Cost
        est_cost = 0.0
        live_px_str = ""
        if ticker:
             try:
                  p = get_price_robust(ticker)
                  est_cost = shares * (limit_px if limit_px else p)
                  live_px_str = f"Live Market Price: ${p:.2f}"
             except Exception:
                  pass
                  
        st.markdown(f"**{live_px_str}**")
        if action == "BUY":
             st.markdown(f"**Estimated Cost:** ${est_cost:,.2f}")
        else:
             st.markdown(f"**Estimated Proceeds:** ${est_cost:,.2f}")

        if st.button("Preview Order", type="primary"):
             st.session_state['order_preview'] = {
                 "ticker": ticker, "action": action, "order_type": o_type, "shares": shares,
                 "limit": limit_px, "stop": stop_px, "trail_val": trail_val, "trail_type": trail_type,
                 "tif": tif, "notes": notes, "est": est_cost
             }
             
    # Preview step
    if 'order_preview' in st.session_state:
         p = st.session_state['order_preview']
         st.info(f"**Please Review:** You are placing a {p['action']} order for {p['shares']} shares of {p['ticker']} at {p['order_type']} price, {p['tif']} order. Est value: ${p['est']:,.2f}.")
         if st.button("✅ Confirm & Submit"):
              try:
                   portfolio.submit_order(p['ticker'], p['action'], p['order_type'], p['shares'], p['limit'], p['stop'], p['trail_val'], p['trail_type'], None, p['tif'], p['notes'])
                   st.success("Order Submitted!")
                   del st.session_state['order_preview']
                   st.session_state['show_order_ticket'] = False
                   st.rerun()
              except Exception as e:
                   st.error(f"Failed: {e}")

def render_performance_tab(portfolio, cash, pos_df, total_val, start_val, total_ret, ret_color, sign):
    st.markdown("### Performance & Insights")
    
    # 1. Key Metrics Row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Return", f"{sign}{total_ret:.2f}%", f"{sign}${total_val - start_val:,.2f}")
    with m2:
        sharpe = 1.25 # Mock
        st.metric("Risk-Adjusted Return", f"{sharpe}", "Sharpe Ratio (Mock)")
    with m3:
        st.metric("Buying Power", f"${cash:,.2f}")

    # 2. Performance Chart
    st.markdown("#### Portfolio Value History")
    perf_df = portfolio.get_performance_history()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=perf_df['date'], y=perf_df['total_value'], mode='lines+markers', name="Portfolio Value", line=dict(color='#008a00', width=3)))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="Date",
        yaxis_title="Account Value ($)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Allocation breakdown
    if not pos_df.empty:
        st.markdown("#### Sector Allocation")
        # Mock sector data based on ticker
        sectors = ["Technology", "Healthcare", "Finance", "Consumer", "Energy"]
        pos_df['Sector'] = [sectors[i % len(sectors)] for i in range(len(pos_df))]
        sector_val = pos_df.groupby('Sector')['market_value'].sum().reset_index()
        
        fig_pie = go.Figure(data=[go.Pie(labels=sector_val['Sector'], values=sector_val['market_value'], hole=.4)])
        fig_pie.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
