import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import plotly.graph_objects as go
from portfolio_engine import PaperPortfolio

# ---- Cached helpers (called outside the class so st.cache_data works) ----

@st.cache_data(ttl=60)  # Refresh prices at most once per minute
def fetch_live_prices(tickers: tuple) -> dict:
    """Batch-fetch prices for a list of tickers in ONE yfinance call."""
    if not tickers:
        return {}
    try:
        data = yf.download(list(tickers), period="1d", progress=False, auto_adjust=True)
        prices = {}
        if len(tickers) == 1:
            # yf.download returns a flat DataFrame for a single ticker
            tick = tickers[0]
            prices[tick] = float(data['Close'].iloc[-1]) if not data.empty else 0.0
        else:
            for tick in tickers:
                try:
                    prices[tick] = float(data['Close'][tick].dropna().iloc[-1])
                except Exception:
                    prices[tick] = 0.0
        return prices
    except Exception:
        return {t: 0.0 for t in tickers}

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
    # Fetch positions from DB (no live prices yet)
    pos_df_raw = portfolio.get_open_positions(include_live_prices=False)
    # Batch-fetch all live prices in a single HTTP call (cached 60s)
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

    # GLOBAL LAYOUT: Action Bar on Top
    col_t, col_tr, col_b, col_q, col_s, col_m = st.columns([1.2, 1.2, 1.2, 1.2, 3, 1.5])
    with col_t:
        if st.button("🔄 Trade", use_container_width=True):
            st.session_state['show_order_ticket'] = True
    with col_tr:
        st.button("💸 Transfer", use_container_width=True, disabled=True)
    with col_b:
        st.button("💵 Pay Bills", use_container_width=True, disabled=True)
    with col_q:
        if st.button("🔍 Quote", use_container_width=True):
             st.session_state['show_quote_modal'] = True
    with col_s:
        pass
    with col_m:
         st.markdown("<div style='padding-top:10px; text-align:right'>🔔 <b>Messages (0)</b></div>", unsafe_allow_html=True)
         
    market_stat = get_cached_market_status()
    if not market_stat['is_open']:
        st.warning(f"Market is currently {market_stat['status']}. Orders placed now will queue as PENDING and execute at the next market open.")

    # Initialize account selection
    if 'selected_account' not in st.session_state:
        st.session_state['selected_account'] = 'all'

    # GLOBAL LAYOUT: Left Sidebar (Accounts) and Right Main Content
    left_col, right_col = st.columns([1.2, 3.8])

    # --- Account definitions ---
    accounts = [
        {"key": "all",            "label": "All accounts",         "group": None,         "number": "",           "balance": total_val,  "change": total_val - start_val, "pct": total_ret, "real": True},
        {"key": "individual_tod", "label": "Individual - TOD",     "group": "Investment", "number": "Z52234364", "balance": total_val,  "change": total_val - start_val, "pct": total_ret, "real": True},
        {"key": "rollover_ira_1", "label": "Rollover IRA",         "group": "Retirement", "number": "259767522", "balance": 0.0,        "change": 0.0,                   "pct": 0.0,       "real": False},
        {"key": "rollover_ira_2", "label": "Rollover IRA",         "group": "Retirement", "number": "264408975", "balance": 0.0,        "change": 0.0,                   "pct": 0.0,       "real": False},
        {"key": "cash_mgmt",      "label": "Cash Management\n(Individual - TOD)", "group": "Spend & Save", "number": "Z35653896", "balance": 0.0, "change": 0.0, "pct": 0.0, "real": False},
    ]

    with left_col:
        st.markdown("<div style='border:1px solid #d1d5db; border-radius:8px; padding:10px;'>", unsafe_allow_html=True)
        st.markdown("<span style='font-weight:bold; font-size:1.05em;'>Accounts</span>", unsafe_allow_html=True)
        st.caption("As of Mar-09-2026 5:45 p.m. ET")

        # All accounts button
        acct = accounts[0]
        is_sel = st.session_state['selected_account'] == acct['key']
        border = "2px solid #111827" if is_sel else "1px solid #d1d5db"
        st.markdown(f"<div style='border:{border}; border-radius:8px; padding:6px 10px; margin-bottom:12px; cursor:pointer;'><b>All accounts</b> <span style='float:right'>${acct['balance']:,.2f}</span></div>", unsafe_allow_html=True)
        if st.button("All accounts", key="btn_all", use_container_width=True):
            st.session_state['selected_account'] = 'all'
            st.rerun()

        # Group accounts by section
        current_group = None
        for acct in accounts[1:]:
            if acct['group'] != current_group:
                current_group = acct['group']
                st.markdown(f"<p style='font-weight:bold; font-size:0.82em; margin:10px 0 4px 0; color:#374151;'>{current_group}</p>", unsafe_allow_html=True)

            is_sel = st.session_state['selected_account'] == acct['key']
            chg_color = ret_color if acct['real'] else "#6b7280"
            chg_sign = "+" if acct['change'] >= 0 else ""

            label_display = acct['label'].replace('\n', ' ')
            highlight = "background:#f0fdf4;" if is_sel else ""
            st.markdown(
                f"<div style='{highlight} border-radius:6px; padding:4px 6px; margin-bottom:2px;'>"
                f"<span style='font-size:0.82em; font-weight:{'bold' if is_sel else 'normal'};'>{label_display}</span>"
                f"<span style='float:right; font-size:0.82em;'>${acct['balance']:,.2f}</span><br>"
                f"<span style='font-size:0.75em; color:#6b7280;'>{acct['number']}</span>"
                f"<span style='float:right; font-size:0.75em; color:{chg_color};'>{chg_sign}${acct['change']:,.2f} ({chg_sign}{acct['pct']:.2f}%)</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            if st.button(label_display, key=f"btn_{acct['key']}", use_container_width=True):
                st.session_state['selected_account'] = acct['key']
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        # Resolve active account
        sel_key = st.session_state['selected_account']
        sel_acct = next((a for a in accounts if a['key'] == sel_key), accounts[0])
        title = sel_acct['label'].replace('\n', ' ') if sel_key != 'all' else 'All accounts'
        st.markdown(f"<h1 style='margin-top:-20px; margin-bottom:20px; font-size:2.8em;'>{title}</h1>", unsafe_allow_html=True)

        # Gate: show banner for mock accounts
        if sel_key not in ('all', 'individual_tod') :
            st.info(f"ℹ️ **{title}** ({sel_acct['number']}) — This account has no activity yet. All your paper trading activity is under **Individual - TOD (Z52234364)**.")
            return

        # Order Ticket Panel Overlay
        if st.session_state.get('show_order_ticket', False):
             render_order_ticket(portfolio)
             return

        # Quote Panel Overlay
        if st.session_state.get('show_quote_modal', False):
             render_quote_panel()

        # Render the Tabs
        render_main_tabs(portfolio, cash, pos_df, total_val, start_val, total_ret, ret_color, sign)


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
                 info = t.info
                 cp = info.get('currentPrice', info.get('regularMarketPrice', 0))
                 
                 st.markdown(f"**{info.get('longName', q_ticker)} ({q_ticker})** | **${cp:.2f}**")
                 
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


def render_main_tabs(portfolio, cash, pos_df, total_val, start_val, total_ret, ret_color, sign):
    # Restructured Sub-tabs
    t_sum, t_pos, t_act, t_bal, _, _, t_perf, _ = st.tabs([
        "Summary", "Positions", "Activity & Orders", "Balances", 
        "Documents", "Planning", "Performance", "More(4)"
    ])
    
    with t_sum:
        st.markdown("<br>", unsafe_allow_html=True)
        # 4-box metrics layout matching Fidelity Summary specifically
        sm1, sm2 = st.columns([2, 1])
        with sm1:
             st.markdown("""
             <div style="border:1px solid #e5e7eb; border-radius:15px; padding:20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
             """, unsafe_allow_html=True)
             
             pos_val = pos_df['market_value'].sum() if not pos_df.empty and 'market_value' in pos_df.columns else 0.0
             st.markdown(f"<p style='margin:0; font-size:1.4em; font-weight:bold; color:#111827'>Balance ⓘ</p><h1 style='margin:0; font-size:2.5em;'>${total_val:,.2f}</h1>", unsafe_allow_html=True)
             st.markdown(f"<p style='color: {ret_color}; font-weight: bold; margin-bottom: 25px;'>{sign}${total_val - start_val:,.2f} ({sign}{total_ret:.2f}%) <span style='font-weight:normal; color:#6b7280'>Today's gain/loss</span></p>", unsafe_allow_html=True)
             
             # Small mini-chart mocked for the Balance card
             perf_df = portfolio.get_performance_history()
             fig_small = go.Figure()
             fig_small.add_trace(go.Scatter(x=perf_df['date'], y=perf_df['total_value'], mode='lines', line=dict(color='#3b82f6', width=2)))
             fig_small.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='#e5e7eb', side='right', tickprefix='$'), plot_bgcolor='white', height=180, showlegend=False)
             st.plotly_chart(fig_small, use_container_width=True)
             
             st.markdown("</div>", unsafe_allow_html=True)

        with sm2:
             # The Up Next mock card
             st.markdown("""
             <div style="border:1px solid #e5e7eb; border-radius:15px; padding:20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 20px;">
                  <h3 style="margin-top:0;">Up next </h3>
                  <div style="display:flex; gap:10px; margin-top:15px;">
                      <div style="background-color:#dcfce7; border-radius:50%; width:40px; height:40px; display:flex; align-items:center; justify-content:center; flex-shrink:0;">💡</div>
                      <div>
                          <p style="font-weight:bold; margin:0;">You opened a new account. Nice! Lets talk about what's next.</p>
                          <p style="font-size:0.9em; color:#374151; margin-top:5px;">Connect with a Fidelity representative to help you take action on your goals and investing ideas.</p>
                          <button style="background:white; border:1px solid #111827; border-radius:20px; padding:6px 15px; font-weight:bold; cursor:pointer;">Make an appointment</button>
                      </div>
                  </div>
             </div>
             """, unsafe_allow_html=True)
             
             # The Tax mock card
             st.markdown("""
             <div style="border:1px solid #e5e7eb; border-radius:15px; padding:20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                  <h3 style="margin-top:0;">Download your 2025 tax forms</h3>
                  <p style="font-size:0.9em; color:#374151;">Access them today — along with resources and tools to help answer your tax questions.</p>
                  <a href="#" style="color:#2563eb; font-weight:bold; text-decoration:none;">Get access now</a>
             </div>
             """, unsafe_allow_html=True)
             
    with t_perf:
        pos_val = pos_df['market_value'].sum() if not pos_df.empty and 'market_value' in pos_df.columns else 0.0
        perf_df = portfolio.get_performance_history()
        st.markdown("<br>", unsafe_allow_html=True)
        # Use st.columns for dynamic values instead of HTML f-string to avoid Streamlit blank-line parsing issue
        pc1, pc2, pc3 = st.columns([2, 2, 1])
        with pc1:
            st.markdown(f"<p style='margin:0; font-weight:bold; font-size:1.1em;'>Balance ⓘ</p><h2 style='margin:0;'>${total_val:,.2f}</h2><p style='color:{ret_color}; font-weight:bold;'>{sign}${total_val - start_val:,.2f} (--%%)</p>", unsafe_allow_html=True)
        with pc2:
            st.markdown("<p style='margin:0; font-weight:bold; font-size:1.1em;'>Return ⓘ</p><p style='margin:0;'>-- ✏️</p>", unsafe_allow_html=True)
        with pc3:
            st.markdown("<div style='padding-top:8px'><button style='background:white; border:1px solid #111827; border-radius:20px; padding:6px 15px; font-weight:bold;'>See all →</button></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown(f"<p style='color:#6b7280; margin:0;'>Invested</p><h4 style='margin:0;'>${pos_val:,.2f}</h4>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='color:#6b7280; margin:0;'>Investment income</p><h4 style='margin:0;'>$0.00</h4>", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"<p style='color:#6b7280; margin:0;'>Cash</p><h4 style='margin:0;'>${cash:,.2f}</h4>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#6b7280; margin:0;'>Net deposits and withdrawals</p><h4 style='margin:0; color:#008a00;'>+$100,000.00</h4>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        # Time filter pills
        st.markdown("<div style='display:flex; gap:15px; margin-bottom:15px; font-size:0.9em;'><span style='color:#374151; font-weight:bold;'>1M</span><span style='color:#374151; font-weight:bold;'>3M</span><span style='color:#374151; font-weight:bold;'>YTD</span><span style='background:#008a00; color:white; padding:2px 12px; border-radius:15px; font-weight:bold;'>1Y</span><span style='color:#374151; font-weight:bold;'>3Y</span><span style='color:#374151; font-weight:bold;'>5Y</span><span style='color:#374151; font-weight:bold;'>10Y</span><span style='color:#374151; font-weight:bold;'>ALL</span></div>", unsafe_allow_html=True)
        # Plotly Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=perf_df['date'], y=perf_df['total_value'], mode='lines', line=dict(color='black', width=2), name='Balance'))
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='#e5e7eb', side='right', tickprefix='$'), plot_bgcolor='white', hovermode='x unified', height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with t_pos:
        st.markdown("### Positions")
        if pos_df.empty:
             st.info("No open positions. Click 'Trade' to get started!")
        else:
             # Format exactly like Fidelity
             display_df = pd.DataFrame()
             display_df['Symbol'] = pos_df['ticker']
             display_df['Last Price'] = pos_df['current_price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
             
             # Gain formatting
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
             st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    with t_act:
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
            <div style='border:1px solid #008a00; color:#008a00; border-radius:20px; padding:4px 15px;'>Transfers</div>
            <div style='border:1px solid #008a00; color:#008a00; border-radius:20px; padding:4px 15px;'>Deposits ✕</div>
            <div style='border:1px solid #008a00; color:#008a00; border-radius:20px; padding:4px 15px;'>Dividends/Interest ✕</div>
            <div style='border:1px solid #008a00; color:#008a00; border-radius:20px; padding:4px 15px;'>Withdrawals ✕</div>
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
        with st.expander("Pending", expanded=(not pending_df.empty)):
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
                  
                  # Provide a simple cancel input based on DB ID (as hidden fidelity action)
                  colA, colB, colC = st.columns([1, 1, 3])
                  with colA:
                       c_id = st.number_input("Order ID to Cancel", min_value=0, step=1, label_visibility="collapsed")
                  with colB:
                       if st.button("Cancel Order"):
                            portfolio.cancel_order(c_id)
                            st.rerun()

        with st.expander("History", expanded=(not trades_df.empty)):
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
                           <div>Individual - TOD<br><span style='color:#6b7280; font-size:0.9em'>Z52234364</span></div>
                           <div>{desc}</div>
                           <div>{status_str}</div>
                           <div style='text-align:right'>{amt_str}</div>
                       </div>
                       """, unsafe_allow_html=True)

    with t_bal:
        st.markdown("""
        <div style='text-align:right; color:#6b7280; font-size:0.9em; margin-bottom: 20px;'>
            As of Mar-09-2026 6:44 p.m. ET 🔄 ⚙️
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='display:grid; grid-template-columns: 60% 20% 20%; border-bottom:2px solid #e5e7eb; padding-bottom:10px; color:#6b7280; font-size:0.95em;'>
            <div>Account</div>
            <div style='text-align:right'>Balance</div>
            <div style='text-align:right'>Day change</div>
        </div>
        """, unsafe_allow_html=True)

        # Main Account
        st.markdown(f"""
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 20px 0 10px 0; font-weight:bold; font-size:1.1em;'>
            <div>Individual - TOD <span style='color:#6b7280; font-weight:normal; font-size:0.95em;'>Z52234364</span></div>
            <div style='text-align:right'>${total_val:,.2f}</div>
            <div style='text-align:right; color:{ret_color}'>{sign}${total_val - start_val:,.2f} ▾</div>
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
        
        # Mock Accounts
        st.markdown("""
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 20px 0 10px 0; font-weight:bold; font-size:1.1em;'>
            <div>Rollover IRA <span style='color:#6b7280; font-weight:normal; font-size:0.95em;'>259767522</span></div>
            <div style='text-align:right'>$0.00</div>
            <div style='text-align:right; color:#6b7280'>$0.00 ▾</div>
        </div>
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 10px 0; font-size:0.95em; color:#374151;'>
            <div>Available to trade (all settled)</div>
            <div style='text-align:right'>$0.00</div>
            <div></div>
        </div>
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 10px 0 20px 0; font-size:0.95em; color:#374151; border-bottom:1px solid #e5e7eb;'>
            <div>Available to withdraw</div>
            <div style='text-align:right'>$0.00</div>
            <div></div>
        </div>
        
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 20px 0 10px 0; font-weight:bold; font-size:1.1em;'>
            <div>Rollover IRA <span style='color:#6b7280; font-weight:normal; font-size:0.95em;'>264408975</span></div>
            <div style='text-align:right'>$0.00</div>
            <div style='text-align:right'></div>
        </div>
        <div style='border-bottom:1px solid #e5e7eb; padding-bottom:10px;'></div>

        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 20px 0 10px 0; font-weight:bold; font-size:1.1em;'>
            <div>Cash Management (Individual - TOD) <br><span style='color:#6b7280; font-weight:normal; font-size:0.95em;'>Z35653896</span></div>
            <div style='text-align:right'>$0.00</div>
            <div style='text-align:right; color:#111827'>$0.00 ▾</div>
        </div>
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 10px 0; font-size:0.95em; color:#374151;'>
            <div>Available to trade (all settled)</div>
            <div style='text-align:right'>$0.00</div>
            <div></div>
        </div>
        <div style='display:grid; grid-template-columns: 60% 20% 20%; padding: 10px 0 20px 0; font-size:0.95em; color:#374151; border-bottom:1px solid #e5e7eb;'>
            <div>Available to withdraw</div>
            <div style='text-align:right'>$0.00</div>
            <div></div>
        </div>
        """, unsafe_allow_html=True)
             
        st.markdown("---")
        if st.button("🚨 Reset Portfolio", help="Warning: Wipes all trades and positions, resets to $100K."):
             portfolio.reset_portfolio()
             st.rerun()


def render_order_ticket(portfolio: PaperPortfolio):
    st.markdown("### 📋 ORDER TICKET")
    
    with st.container(border=True):
        if st.button("← Back to Portfolio"):
             st.session_state['show_order_ticket'] = False
             st.rerun()
             
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
                  t = yf.Ticker(ticker)
                  p = t.info.get('currentPrice') or t.history(period="1d")['Close'].iloc[-1]
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

