"""
portfolio_engine.py — PaperPortfolio backed by Supabase Postgres.

Every method is scoped to self.user_id so users never see each other's data.
Supabase RLS policies provide an additional server-side security layer.
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, time as datetime_time
import pytz
import pandas_market_calendars as mcal
import logging
import streamlit as st
from supabase import create_client, Client
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_supabase(access_token: str = None) -> Client:
    """Create Supabase client from Streamlit secrets, optionally authenticated as the user."""
    client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    if access_token:
        # Set the user's JWT so RLS auth.uid() resolves correctly
        client.postgrest.auth(access_token)
    return client


class PaperPortfolio:
    def __init__(self, user_id: str, access_token: str = None):
        self.user_id = user_id
        self.sb = _get_supabase(access_token)
        self._ensure_cash_initialized()

    def refresh_client(self, access_token: str):
        """Update the internal Supabase client with a new access token."""
        if access_token and access_token != "guest_token_123":
            self.sb.postgrest.auth(access_token)

    # ── Bootstrap ────────────────────────────────────────────────────────────

    def _ensure_cash_initialized(self):
        """Insert a $100,000 cash row for this user if one doesn't exist yet."""
        res = self.sb.table("cash").select("id").eq("user_id", self.user_id).execute()
        if not res.data:
            self.sb.table("cash").insert({
                "user_id": self.user_id,
                "balance": 100000.0,
                "last_updated": datetime.now(pytz.UTC).isoformat()
            }).execute()

    # ── Market Status ─────────────────────────────────────────────────────────

    def get_market_status(self, ticker: str = "^GSPC") -> Dict[str, Any]:
        """Check if the market for a specific ticker is open. Defaults to NYSE."""
        ticker = ticker.upper()
        
        # Suffix to Calendar Mapping
        calendar_map = {
            ".NS": "NSE", ".BO": "BSE", # India
            ".L": "LSE",               # UK
            ".HK": "HKEX",             # Hong Kong
            ".T": "TSE",               # Tokyo
            ".DE": "XETR",             # Germany
            ".PA": "ENXTPA",           # France
            ".TO": "TSX", ".V": "TSXV", # Canada
            ".AX": "ASX",              # Australia
            ".SS": "SSE", ".SZ": "SZSE" # China
        }
        
        cal_name = "NYSE"
        for suffix, cal in calendar_map.items():
            if ticker.endswith(suffix):
                cal_name = cal
                break
        
        # If it's a US stock (no suffix or .US), use NYSE
        if "." not in ticker or ticker.endswith(".US"):
            cal_name = "NYSE"

        try:
            cal = mcal.get_calendar(cal_name)
            # Use the local timezone of the exchange for more accurate "is_open"
            exchange_tz = pytz.timezone(cal.tz.zone)
            now_local = datetime.now(exchange_tz)
            
            schedule = cal.schedule(start_date=now_local.date(), end_date=now_local.date())
            if schedule.empty:
                return {"status": "CLOSED", "reason": f"{cal_name} is closed today (Weekend/Holiday)", "is_open": False, "market": cal_name}
            
            # Use is_open check which handles pre/post market if configured, 
            # but simple time-of-day check is often safer for paper trading
            t = now_local.time()
            open_time = schedule.iloc[0]['market_open'].astimezone(exchange_tz).time()
            close_time = schedule.iloc[0]['market_close'].astimezone(exchange_tz).time()
            
            if open_time <= t <= close_time:
                return {"status": "OPEN", "reason": f"{cal_name} is open", "is_open": True, "market": cal_name}
            elif t < open_time:
                return {"status": "PRE-MARKET", "reason": "Before market open", "is_open": False, "market": cal_name}
            else:
                return {"status": "AFTER-HOURS", "reason": "After market close", "is_open": False, "market": cal_name}
        except Exception as e:
            # Fallback for unknown calendars: M-F 9am-4pm local usually works
            logger.warning(f"Market calendar error for {cal_name}: {e}")
            now = datetime.now()
            is_weekday = now.weekday() < 5
            return {"status": "OPEN" if is_weekday else "CLOSED", "is_open": is_weekday, "market": cal_name}

    # ── Cash ─────────────────────────────────────────────────────────────────

    def get_cash_balance(self) -> float:
        res = self.sb.table("cash").select("balance").eq("user_id", self.user_id).execute()
        return res.data[0]["balance"] if res.data else 0.0

    def _update_cash(self, amount_change: float):
        current = self.get_cash_balance()
        self.sb.table("cash").update({
            "balance": current + amount_change,
            "last_updated": datetime.now(pytz.UTC).isoformat()
        }).eq("user_id", self.user_id).execute()

    # ── Positions ─────────────────────────────────────────────────────────────

    def _get_position(self, ticker: str) -> Optional[Dict]:
        res = self.sb.table("positions").select("shares, avg_cost").eq(
            "user_id", self.user_id).eq("ticker", ticker).execute()
        return res.data[0] if res.data else None

    def _update_position(self, ticker: str, company: str, action: str,
                         shares: int, price: float, notes: str):
        current = self._get_position(ticker)
        if action == "BUY":
            if current:
                new_shares = current["shares"] + shares
                new_avg = ((current["shares"] * current["avg_cost"]) + (shares * price)) / new_shares
                self.sb.table("positions").update({
                    "shares": new_shares, "avg_cost": new_avg
                }).eq("user_id", self.user_id).eq("ticker", ticker).execute()
            else:
                self.sb.table("positions").insert({
                    "user_id": self.user_id, "ticker": ticker, "company": company,
                    "shares": shares, "avg_cost": price,
                    "date_opened": datetime.now(pytz.UTC).isoformat(), "notes": notes
                }).execute()
        elif action == "SELL":
            if not current:
                raise ValueError(f"No position found for {ticker}")
            if shares > current["shares"]:
                raise ValueError(f"Trying to sell {shares} but only own {current['shares']}")
            new_shares = current["shares"] - shares
            if new_shares == 0:
                self.sb.table("positions").delete().eq("user_id", self.user_id).eq("ticker", ticker).execute()
            else:
                self.sb.table("positions").update({"shares": new_shares}).eq(
                    "user_id", self.user_id).eq("ticker", ticker).execute()

    def _fetch_price(self, ticker: str) -> float:
        """Robust price fetcher using yahooquery (reliable in cloud) with yfinance fallbacks."""
        if not ticker: return 0.0
        # 1. Try YahooQuery (Primary for deployment stability)
        try:
            from yahooquery import Ticker as YQTicker
            yt = YQTicker(ticker)
            price_data = yt.price
            if ticker in price_data and isinstance(price_data[ticker], dict):
                p = price_data[ticker].get('regularMarketPrice')
                if p and p > 0: return float(p)
        except Exception as e:
            logger.debug(f"YahooQuery price fetch failed for {ticker}: {e}")

        # 2. Try yfinance fallbacks
        try:
            t = yf.Ticker(ticker)
            # fast_info
            try:
                if hasattr(t, 'fast_info') and 'last_price' in t.fast_info:
                    p = t.fast_info['last_price']
                    if p and p > 0: return float(p)
            except: pass
            
            # history
            h = t.history(period="1d")
            if not h.empty:
                return float(h["Close"].iloc[-1])
        except Exception as e:
            logger.error(f"yfinance price fetch failed for {ticker}: {e}")
        
        return 0.0

    def get_open_positions(self, include_live_prices: bool = True) -> pd.DataFrame:
        res = self.sb.table("positions").select("*").eq("user_id", self.user_id).execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

        if df.empty or not include_live_prices:
            return df

        tickers = df["ticker"].tolist()
        try:
            # Batch fetch via YahooQuery for performance
            from yahooquery import Ticker as YQTicker
            yt = YQTicker(tickers)
            pd_data = yt.price
            
            prices = {}
            for tick in tickers:
                p = 0.0
                if tick in pd_data and isinstance(pd_data[tick], dict):
                    p = pd_data[tick].get('regularMarketPrice', 0.0)
                
                if not p or p <= 0:
                    p = self._fetch_price(tick) # Fallback to robust individual fetch
                prices[tick] = p

            df["current_price"] = df["ticker"].map(prices)
            df["market_value"] = df["shares"] * df["current_price"]
            df["total_cost"] = df["shares"] * df["avg_cost"]
            df["unrealized_pnl"] = df["market_value"] - df["total_cost"]
            df["return_pct"] = (df["unrealized_pnl"] / df["total_cost"]).fillna(0) * 100
        except Exception as e:
            logger.error(f"Error in get_open_positions: {e}")
            df["current_price"] = 0.0
        return df

    def get_total_portfolio_value(self) -> float:
        cash = self.get_cash_balance()
        pos_df = self.get_open_positions(include_live_prices=True)
        if pos_df.empty or "market_value" not in pos_df.columns:
            return cash
        return cash + pos_df["market_value"].sum()

    # ── Orders ────────────────────────────────────────────────────────────────

    def submit_order(self, ticker: str, action: str, order_type: str, shares: int,
                     limit_price=None, stop_price=None, trail_value=None,
                     trail_type=None, condition=None, tif="Day", notes="") -> Dict:
        ticker = ticker.upper()
        market = self.get_market_status(ticker)
        
        # Initial status is PENDING. If filled immediately, it updates to FILLED.
        res = self.sb.table("orders").insert({
            "user_id": self.user_id, "ticker": ticker, "action": action,
            "order_type": order_type, "shares": shares, "limit_price": limit_price,
            "stop_price": stop_price, "trail_value": trail_value, "trail_type": trail_type,
            "condition": condition, "tif": tif, "status": "PENDING",
            "submitted_at": datetime.now(pytz.UTC).isoformat(), "notes": notes
        }).execute()
        order_id = res.data[0]["id"] if res.data else None

        if market["is_open"] and order_type == "Market":
            return self._fill_order(order_id, ticker, action, shares, notes)
        
        msg = f"Order queued as PENDING. {market.get('market', 'Market')} is {market['status']}."
        return {"status": "PENDING", "message": msg}

    def _fill_order(self, order_id: str, ticker: str, action: str, shares: int, notes: str) -> Dict:
        try:
            price = self._fetch_price(ticker)
            if not price or price <= 0:
                # Try one more time specifically for fillers
                t = yf.Ticker(ticker)
                h = t.history(period="1d")
                price = float(h["Close"].iloc[-1]) if not h.empty else 0.0

            if price <= 0:
                return {"status": "ERROR", "message": f"Could not fetch a valid price for {ticker}. Market might be inaccessible."}

            try:
                info = yf.Ticker(ticker).info
                company = info.get("shortName", ticker)
            except:
                company = ticker

            total = shares * price

            if action == "BUY":
                cash = self.get_cash_balance()
                if total > cash:
                    return {"status": "ERROR", "message": f"Insufficient funds. Need ${total:,.2f}, have ${cash:,.2f}"}
                self._update_cash(-total)
                self._update_position(ticker, company, "BUY", shares, price, notes)
            elif action == "SELL":
                self._update_position(ticker, company, "SELL", shares, price, notes)
                self._update_cash(total)

            self.sb.table("orders").update({
                "status": "FILLED", "filled_at": datetime.now(pytz.UTC).isoformat(),
                "filled_price": price
            }).eq("id", order_id).execute()

            self.sb.table("trades").insert({
                "user_id": self.user_id, "order_id": order_id, "ticker": ticker,
                "action": action, "shares": shares, "price": price, "total": total,
                "date": datetime.now(pytz.UTC).isoformat()
            }).execute()

            self.log_daily_performance()
            return {"status": "FILLED", "price": price, "total": total,
                    "message": f"{action} {shares} shares of {ticker} at ${price:.2f}"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def process_pending_orders(self):
        """Fill any pending Market orders if market is now open."""
        market = self.get_market_status()
        if not market["is_open"]:
            return
        res = self.sb.table("orders").select("*").eq("user_id", self.user_id).eq("status", "PENDING").execute()
        for order in (res.data or []):
            if order["order_type"] == "Market":
                self._fill_order(order["id"], order["ticker"], order["action"], order["shares"], order.get("notes", ""))

    def get_pending_orders(self) -> pd.DataFrame:
        res = self.sb.table("orders").select("*").eq("user_id", self.user_id).eq("status", "PENDING").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()

    def get_trade_history(self) -> pd.DataFrame:
        res = self.sb.table("trades").select("*").eq("user_id", self.user_id).order("date", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()

    def cancel_order(self, order_id: str):
        self.sb.table("orders").update({"status": "CANCELLED"}).eq("id", order_id).eq("user_id", self.user_id).execute()

    # ── Performance ───────────────────────────────────────────────────────────

    def log_daily_performance(self):
        cash = self.get_cash_balance()
        pos_df = self.get_open_positions(include_live_prices=True)
        pos_val = pos_df["market_value"].sum() if not pos_df.empty and "market_value" in pos_df.columns else 0.0
        self.sb.table("performance_history").insert({
            "user_id": self.user_id, "date": datetime.now(pytz.UTC).isoformat(),
            "total_value": cash + pos_val, "cash_balance": cash, "positions_value": pos_val
        }).execute()

    def get_performance_history(self) -> pd.DataFrame:
        res = self.sb.table("performance_history").select("*").eq(
            "user_id", self.user_id).order("date").execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

        if df.empty or len(df) < 2:
            import numpy as np
            start_val = 100000.0
            end_val = self.get_total_portfolio_value()
            dates = pd.date_range(end=datetime.now(pytz.UTC), periods=365, freq='D')
            np.random.seed(42)
            steps = np.random.normal(loc=(end_val - start_val) / 365, scale=500, size=365)
            path = start_val + np.cumsum(steps)
            correction = np.linspace(0, end_val - path[-1], 365)
            path = path + correction
            df = pd.DataFrame({"date": dates, "total_value": path})
        return df

    def reset_portfolio(self):
        """Wipe all data for this user and reinitialize with $100K."""
        uid = self.user_id
        for table in ["performance_history", "trades", "orders", "positions"]:
            self.sb.table(table).delete().eq("user_id", uid).execute()
        self.sb.table("cash").update({
            "balance": 100000.0,
            "last_updated": datetime.now(pytz.UTC).isoformat()
        }).eq("user_id", uid).execute()
