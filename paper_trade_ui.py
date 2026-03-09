import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from portfolio_engine import PaperPortfolio

def render_paper_trader(portfolio: PaperPortfolio):
    # Process any orders that can execute right now
    portfolio.process_pending_orders()
    
    # Header: Action Bar + Market Status
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Trade", use_container_width=True, type="primary"):
            st.session_state['show_order_ticket'] = True
    with col2:
        st.button("🔍 Quote", use_container_width=True, disabled=True, help="Coming soon")
    with col3:
        market_stat = portfolio.get_market_status()
        status_color = "#22c55e" if market_stat['is_open'] else "#9ca3af"
        if market_stat['status'] in ['PRE-MARKET', 'AFTER-HOURS']:
             status_color = "#eab308"
        
        st.markdown(
            f"""<div style="text-align: right; padding-top: 5px;">
                <span style="color: #6b7280; font-size: 0.9em;">Market Status: </span>
                <span style="color: {status_color}; font-weight: bold;">● {market_stat['status']}</span>
            </div>""", 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Order Ticket Panel Overlay (handled via a conditional block at top if expanded)
    if st.session_state.get('show_order_ticket', False):
         render_order_ticket(portfolio)
         return # Stop rendering the rest of the dashboard while ticket is open

    # Sub-tabs (Fidelity style)
    t_sum, t_pos, t_act, t_bal = st.tabs(["Summary", "Positions", "Activity & Orders", "Balances"])
    
    cash = portfolio.get_cash_balance()
    pos_df = portfolio.get_open_positions()
    total_val = portfolio.get_total_portfolio_value()
    
    with t_sum:
        st.markdown("### All accounts")
        st.markdown(f"<h1 style='margin-bottom:0;'>${total_val:,.2f}</h1>", unsafe_allow_html=True)
        # Needs start balance logic to calculate daily gain, assuming $100K total starting
        start_val = 100000.0
        total_ret = ((total_val - start_val) / start_val) * 100
        ret_color = "#e11d48" if total_ret < 0 else "#22c55e"
        sign = "+" if total_ret >= 0 else ""
        st.markdown(f"<p style='color: {ret_color}; font-weight: bold;'>{sign}${total_val - start_val:,.2f} ({sign}{total_ret:.2f}%) <span style='color:#6b7280; font-weight: normal;'>All-time</span></p>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### Account Breakdown")
        
        account_df = pd.DataFrame([
             {"Account": "Individual - Paper Trading", "Value": f"${total_val:,.2f}", "Total Gain/Loss": f"{sign}${total_val - start_val:,.2f}"},
             {"Account": "Available Cash", "Value": f"${cash:,.2f}", "Total Gain/Loss": "-"}
        ])
        st.table(account_df)

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
        st.markdown("### Pending Orders")
        pending_df = portfolio.get_pending_orders()
        if pending_df.empty:
             st.write("No pending orders.")
        else:
             st.dataframe(pending_df[['id', 'ticker', 'action', 'order_type', 'shares', 'limit_price', 'status', 'submitted_at']], use_container_width=True)
             c_id = st.number_input("Order ID to Cancel", min_value=0, step=1)
             if st.button("Cancel Order"):
                  portfolio.cancel_order(c_id)
                  st.rerun()

        st.markdown("---")
        st.markdown("### Trade History")
        trades_df = portfolio.get_trade_history()
        if trades_df.empty:
             st.write("No executed trades yet.")
        else:
             st.dataframe(trades_df[['date', 'ticker', 'action', 'shares', 'price', 'total']], use_container_width=True)

    with t_bal:
        st.markdown("### Balances")
        colA, colB = st.columns(2)
        with colA:
             st.metric("Total Account Value", f"${total_val:,.2f}")
             st.metric("Unrealized P&L", f"{sign}${total_val - start_val:,.2f}")
        with colB:
             st.metric("Cash Available to Trade", f"${cash:,.2f}")
             st.metric("Settled Cash", f"${cash:,.2f}")
             
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

