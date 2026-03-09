import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, time as datetime_time
import pytz
import pandas_market_calendars as mcal
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "paper_portfolio.db"

class PaperPortfolio:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            
            # Cash Ledger
            c.execute('''CREATE TABLE IF NOT EXISTS cash (
                id INTEGER PRIMARY KEY,
                balance REAL,
                last_updated TEXT
            )''')
            
            # Positions
            c.execute('''CREATE TABLE IF NOT EXISTS positions (
                ticker TEXT PRIMARY KEY,
                company TEXT,
                shares INTEGER,
                avg_cost REAL,
                date_opened TEXT,
                notes TEXT
            )''')
            
            # Orders (Pending & Completed)
            c.execute('''CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                action TEXT,  -- BUY/SELL
                order_type TEXT, -- Market, Limit, Stop Loss, etc.
                shares INTEGER,
                limit_price REAL,
                stop_price REAL,
                trail_value REAL,
                trail_type TEXT, -- $ or %
                condition TEXT,
                tif TEXT, -- Time in Force (Day, GTC, etc.)
                status TEXT, -- PENDING, FILLED, CANCELLED, EXPIRED
                submitted_at TEXT,
                filled_at TEXT,
                filled_price REAL,
                notes TEXT
            )''')
            
            # Trade History
            c.execute('''CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                ticker TEXT,
                action TEXT,
                shares INTEGER,
                price REAL,
                total REAL,
                date TEXT
            )''')
            
            # Initialize cash to 100k if not exists
            c.execute('''SELECT COUNT(*) FROM cash''')
            if c.fetchone()[0] == 0:
                c.execute('''INSERT INTO cash (id, balance, last_updated) VALUES (1, 100000.0, ?)''', 
                          (datetime.now(pytz.UTC).isoformat(),))
            conn.commit()

    # --- Market Awareness ---
    def get_market_status(self) -> Dict[str, Any]:
        has_pandas_market_calendars = False
        try:
            nyse = mcal.get_calendar('NYSE')
            has_pandas_market_calendars = True
        except ImportError:
            pass

        now_utc = datetime.now(pytz.UTC)
        now_et = now_utc.astimezone(pytz.timezone('US/Eastern'))
        
        # Check holiday/weekend
        is_trading_day = True
        if has_pandas_market_calendars:
            # Check if today is a valid trading day
            schedule = nyse.schedule(start_date=now_et.date(), end_date=now_et.date())
            is_trading_day = not schedule.empty
        else:
            # Fallback if no calendar
            is_trading_day = now_et.weekday() < 5 # Mon-Fri

        if not is_trading_day:
            return {"status": "CLOSED", "reason": "Weekend or Holiday", "is_open": False}

        current_time = now_et.time()
        market_open = datetime_time(9, 30)
        market_close = datetime_time(16, 0)
        pre_market_start = datetime_time(4, 0)
        after_hours_end = datetime_time(20, 0)

        if market_open <= current_time <= market_close:
            return {"status": "OPEN", "reason": "Market is currently open", "is_open": True}
        elif pre_market_start <= current_time < market_open:
            return {"status": "PRE-MARKET", "reason": "Pre-market trading hours", "is_open": False}
        elif market_close < current_time <= after_hours_end:
            return {"status": "AFTER-HOURS", "reason": "After-hours trading", "is_open": False}
        else:
             return {"status": "CLOSED", "reason": "Outside all trading hours", "is_open": False}
             
    # --- Cash Management ---
    def get_cash_balance(self) -> float:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''SELECT balance FROM cash WHERE id = 1''')
            row = c.fetchone()
            return row[0] if row else 0.0
            
    def _update_cash(self, amount_change: float):
         with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''UPDATE cash SET balance = balance + ?, last_updated = ? WHERE id = 1''',
                      (amount_change, datetime.now(pytz.UTC).isoformat()))
            conn.commit()

    # --- Position Management ---
    def _get_position(self, ticker: str):
        with self._get_conn() as conn:
             c = conn.cursor()
             c.execute('''SELECT shares, avg_cost FROM positions WHERE ticker = ?''', (ticker,))
             return c.fetchone()
             
    def _update_position(self, ticker: str, company: str, action: str, shares: int, price: float, notes: str):
        current_pos = self._get_position(ticker)
        with self._get_conn() as conn:
            c = conn.cursor()
            if action == 'BUY':
                if current_pos:
                    curr_shares, curr_avg = current_pos
                    new_shares = curr_shares + shares
                    new_avg = ((curr_shares * curr_avg) + (shares * price)) / new_shares
                    c.execute('''UPDATE positions SET shares = ?, avg_cost = ? WHERE ticker = ?''',
                              (new_shares, new_avg, ticker))
                else:
                    c.execute('''INSERT INTO positions (ticker, company, shares, avg_cost, date_opened, notes)
                                 VALUES (?, ?, ?, ?, ?, ?)''', 
                              (ticker, company, shares, price, datetime.now(pytz.UTC).isoformat(), notes))
            elif action == 'SELL':
                if not current_pos:
                    raise ValueError(f"No position found for {ticker}")
                curr_shares, curr_avg = current_pos
                if shares > curr_shares:
                     raise ValueError(f"Trying to sell {shares} but only own {curr_shares}")
                new_shares = curr_shares - shares
                if new_shares == 0:
                    c.execute('''DELETE FROM positions WHERE ticker = ?''', (ticker,))
                else:
                    c.execute('''UPDATE positions SET shares = ? WHERE ticker = ?''', (new_shares, ticker))
            conn.commit()
            
    def get_open_positions(self, include_live_prices=True) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query('SELECT * FROM positions', conn)
            
        if df.empty or not include_live_prices:
             return df
             
        # Fetch live prices
        tickers = df['ticker'].tolist()
        try:
             # Fast fetch for multiple tickers
             prices = {}
             # yf.download can be tricky, fallback to Ticker if needed
             for tick in tickers:
                  t = yf.Ticker(tick)
                  info = t.info
                  # Try current price, then regular market price, then previous close
                  p = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                  if p is None:
                      # Ultimate fallback
                      h = t.history(period="1d")
                      if not h.empty:
                          p = h['Close'].iloc[-1]
                      else:
                          p = 0.0
                  prices[tick] = p
                  
             df['current_price'] = df['ticker'].map(prices)
             df['market_value'] = df['shares'] * df['current_price']
             df['total_cost'] = df['shares'] * df['avg_cost']
             df['unrealized_pnl'] = df['market_value'] - df['total_cost']
             df['return_pct'] = (df['unrealized_pnl'] / df['total_cost']) * 100
        except Exception as e:
             logger.error(f"Error fetching live prices: {e}")
             df['current_price'] = None
             
        return df
        
    def get_total_portfolio_value(self) -> float:
        cash = self.get_cash_balance()
        pos_df = self.get_open_positions(include_live_prices=True)
        if pos_df.empty or 'market_value' not in pos_df.columns:
             return cash
        return cash + pos_df['market_value'].sum()

    # --- Order Management ---
    def submit_order(self, ticker: str, action: str, order_type: str, shares: int, 
                     limit_price: float=None, stop_price: float=None, 
                     trail_value: float=None, trail_type: str=None, 
                     condition: str=None, tif: str='Day', notes: str=None) -> int:
        
        # Validation
        action = action.upper()
        if action not in ['BUY', 'SELL']:
             raise ValueError("Action must be BUY or SELL")
        if shares <= 0:
             raise ValueError("Shares must be positive")
             
        # Check cash/shares availability
        if action == 'BUY':
             cash = self.get_cash_balance()
             # Estimate cost for buy orders using current price if market, or limit price
             est_price = limit_price
             if est_price is None:
                  t = yf.Ticker(ticker)
                  p = t.info.get('currentPrice') or t.history(period="1d")['Close'].iloc[-1]
                  est_price = p
             if (shares * est_price) > cash:
                 raise ValueError(f"Insufficient cash. Est. Cost: ${shares*est_price:.2f}, Cash: ${cash:.2f}")
        elif action == 'SELL':
             pos = self._get_position(ticker)
             if not pos or pos[0] < shares:
                 current_shares = pos[0] if pos else 0
                 raise ValueError(f"Insufficient shares. Trying to sell {shares}, but own {current_shares}")

        submitted_at = datetime.now(pytz.UTC).isoformat()
        
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO orders (ticker, action, order_type, shares, limit_price, stop_price, trail_value, trail_type, condition, tif, status, submitted_at, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (ticker, action, order_type, shares, limit_price, stop_price, trail_value, trail_type, condition, tif, 'PENDING', submitted_at, notes))
            order_id = c.lastrowid
            conn.commit()
            
        logger.info(f"Order #{order_id} submitted: {action} {shares} {ticker} ({order_type})")
        
        # If market is open, try processing immediately
        market_stat = self.get_market_status()
        if market_stat['is_open'] or order_type != "Market":
            self.process_pending_orders()
            
        return order_id

    def cancel_order(self, order_id: int):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''UPDATE orders SET status = 'CANCELLED' WHERE id = ? AND status = 'PENDING' ''', (order_id,))
            conn.commit()

    def get_pending_orders(self) -> pd.DataFrame:
        with self._get_conn() as conn:
             return pd.read_sql_query("SELECT * FROM orders WHERE status = 'PENDING'", conn)
             
    def get_trade_history(self) -> pd.DataFrame:
         with self._get_conn() as conn:
             return pd.read_sql_query("SELECT * FROM trades ORDER BY date DESC", conn)

    # --- Execution Engine ---
    def _execute_trade(self, order_id: int, ticker: str, action: str, shares: int, price: float, notes: str):
        total = shares * price
        now_dt = datetime.now(pytz.UTC).isoformat()
        
        company_name = ticker # Default to ticker, could fetch actual name
        try:
             company_name = yf.Ticker(ticker).info.get('shortName', ticker)
        except Exception:
             pass

        # 1. Update Position
        self._update_position(ticker, company_name, action, shares, price, notes)
        
        # 2. Update Cash
        cash_delta = -total if action == 'BUY' else total
        self._update_cash(cash_delta)
        
        # 3. Log Trade
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO trades (order_id, ticker, action, shares, price, total, date)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (order_id, ticker, action, shares, price, total, now_dt))
            
            # 4. Mark Order Filled
            c.execute('''UPDATE orders SET status = 'FILLED', filled_at = ?, filled_price = ? WHERE id = ?''',
                      (now_dt, price, order_id))
            conn.commit()
            
        logger.info(f"✅ TRADE EXECUTED: {action} {shares} {ticker} @ ${price:.2f}")

    def process_pending_orders(self):
         """Evaluates all PENDING orders and fills them if conditions met."""
         market_stat = self.get_market_status()
         now_utc = datetime.now(pytz.UTC)
         now_dt = now_utc.isoformat()
         
         pending_orders = self.get_pending_orders()
         if pending_orders.empty:
             return
             
         # Fetch current prices for all relevant tickers
         tickers = pending_orders['ticker'].unique()
         prices = {}
         dailys = {}
         for tick in tickers:
             try:
                 t = yf.Ticker(tick)
                 p = t.info.get('currentPrice') or t.history(period="1d")['Close'].iloc[-1]
                 prices[tick] = p
                 # For evaluating trailing stops we need today's high/low
                 h = t.history(period="1d")
                 if not h.empty:
                     dailys[tick] = {'high': h['High'].iloc[-1], 'low': h['Low'].iloc[-1], 'close': h['Close'].iloc[-1]}
             except Exception:
                 pass
                 
         for _, order in pending_orders.iterrows():
             tick = order['ticker']
             current_price = prices.get(tick)
             if current_price is None:
                 continue
                 
             o_id = order['id']
             action = order['action']
             otype = order['order_type']
             shares = order['shares']
             limit_price = order['limit_price']
             stop_price = order['stop_price']
             notes = order['notes']
             tif = order['tif']
             
             # Time in Force Expirations
             # Real implementation would check dates for GTD, EOD for Day.
             # Simplified Day handling:
             if tif == 'Day' and not market_stat['is_open'] and market_stat['status'] == 'CLOSED':
                 # Rough approximation: if market closed and order is Day, expire it.
                 # Better to check if submitted date < today
                 pass 
             
             should_fill = False
             fill_price = current_price
             
             # Market Order
             if otype == 'Market':
                 if market_stat['is_open']:
                     should_fill = True
             
             # Limit Order
             elif otype == 'Limit':
                 if (action == 'BUY' and current_price <= limit_price) or \
                    (action == 'SELL' and current_price >= limit_price):
                     should_fill = True
                     # Improvement: Fills at the limit price or better.
                     fill_price = limit_price if action == 'BUY' else max(limit_price, current_price)
                     
             # Stop Loss
             elif otype == 'Stop Loss':
                 # Stop Loss usually assumes Sell, but can be buy.
                 if action == 'SELL' and current_price <= stop_price:
                     should_fill = True # Becomes market order
                 elif action == 'BUY' and current_price >= stop_price:
                      should_fill = True
                      
             # For trailing stops, we would need to continuously update the `stop_price` in the DB based on the `trail_value` and daily high/lows.
             # This requires regular jobs. For a mock platform, we check if today's high/low crossed it.
             
             if should_fill:
                 try:
                     self._execute_trade(o_id, tick, action, shares, fill_price, notes)
                 except Exception as e:
                     logger.error(f"Failed to execute order {o_id}: {e}")
                     # Maybe cancel order if failed due to cash/shares?
                     if "Insufficient" in str(e):
                          self.cancel_order(o_id)

    def reset_portfolio(self):
         """Wipes completely and returns to $100K cash"""
         with self._get_conn() as conn:
             c = conn.cursor()
             c.execute('DELETE FROM cash')
             c.execute('DELETE FROM positions')
             c.execute('DELETE FROM orders')
             c.execute('DELETE FROM trades')
             c.execute('''INSERT INTO cash (id, balance, last_updated) VALUES (1, 100000.0, ?)''', 
                          (datetime.now(pytz.UTC).isoformat(),))
             conn.commit()

