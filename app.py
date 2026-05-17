import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet with Stop Loss")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets (same as before)
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
api_secret = st.secrets["zerodha"].get("api_secret", "")
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("⚙️ Settings")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])
sl_percent = st.sidebar.slider("Stop Loss %", 0.5, 2.0, 0.8)
target_percent = st.sidebar.slider("Target %", 1.0, 4.0, 1.8)

# Kite Setup (same as before)
kite = None
if mode == "Zerodha Live" and access_token:
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    st.sidebar.success("✅ Zerodha + SL Ready")

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                  json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})

# ... (Keep your existing login helper, get_data, sectors, news etc.)

for sym in sectors[selected]:
    # ... (chart and signal logic same)

    trade_size = min(4500, st.session_state.portfolio['cash'])
    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", 
                 key=f"exec_{sym}", use_container_width=True, type="primary"):
        
        if not data.empty:
            entry_price = latest['Close']
            sl_price = entry_price * (1 - sl_percent/100) if "BUY" in signal else entry_price * (1 + sl_percent/100)
            target_price = entry_price * (1 + target_percent/100) if "BUY" in signal else entry_price * (1 - target_percent/100)
            
            # Paper Trade Record
            st.session_state.portfolio['cash'] -= trade_size
            st.success(f"✅ Order Placed | SL: ₹{sl_price:.2f} | Target: ₹{target_price:.2f}")

            alert = f"""<b>🚀 ProphetID TRADE + SL</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Qty: {int(trade_size/entry_price)}
Entry: ₹{entry_price:.2f}
SL: ₹{sl_price:.2f} ({sl_percent}%)
Target: ₹{target_price:.2f} ({target_percent}%)"""
            send_telegram(alert)

            # === REAL ZERODHA BRACKET / SL ORDER ===
            if mode == "Zerodha Live" and kite:
                try:
                    qty = int(trade_size / entry_price)
                    # Place Main Order + SL + Target (Bracket Order)
                    kite.place_order(
                        variety=kite.VARIETY_BO,
                        tradingsymbol=sym.replace(".NS",""),
                        exchange=kite.EXCHANGE_NSE,
                        transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                        quantity=qty,
                        product=kite.PRODUCT_MIS,
                        order_type=kite.ORDER_TYPE_MARKET,
                        squareoff=int(target_price * qty - entry_price * qty),   # Target value
                        stoploss=int(entry_price * qty - sl_price * qty),        # SL value
                        trailing_stoploss=0
                    )
                    st.success("✅ Bracket Order (Entry + SL + Target) Placed on Zerodha!")
                except Exception as e:
                    st.error(f"Order Failed: {e}")
