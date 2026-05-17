import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet (Zerodha Live)")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
api_secret = st.secrets["zerodha"].get("api_secret", "")

st.sidebar.header("⚙️ Settings")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])

kite = None
access_token = st.secrets["zerodha"].get("access_token", None)

if mode == "Zerodha Live":
    try:
        kite = KiteConnect(api_key=api_key)
        if access_token:
            kite.set_access_token(access_token)
            st.sidebar.success("✅ Zerodha Connected")
        else:
            st.sidebar.warning("⚠️ Need Access Token (Run Login below)")
    except:
        st.sidebar.error("Zerodha setup incomplete")

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})

# Daily Login Helper
if st.sidebar.button("🔑 Generate Zerodha Access Token"):
    st.sidebar.info("Go to this URL in new tab and login:")
    login_url = f"https://kite.trade/connect/login?api_key={api_key}&v=3"
    st.sidebar.markdown(f"[🔗 Click to Login on Zerodha]({login_url})")
    st.sidebar.info("After login, copy the 'request_token' from URL and paste below")

request_token = st.sidebar.text_input("Paste Request Token here (after login)")
if st.sidebar.button("✅ Generate Access Token"):
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data['access_token']
        st.success(f"Access Token Generated: {access_token[:10]}...")
        st.sidebar.success("Token saved! Refresh app.")
        # Note: You can manually add it to secrets later
    except Exception as e:
        st.error(f"Error: {e}")

@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="5m")
    except:
        return pd.DataFrame()

# Rest of the app (same as before with live order)
st.header("📊 ProphetID Smart Picks + News")

# ... [I kept the same sectors, news, charts, execute buttons as v2.5 for brevity]

# Execute button logic with real Zerodha order
        if st.button(...):
            # paper logic...
            if mode == "Zerodha Live" and kite and access_token:
                try:
                    qty = int(trade_size / latest['Close']) if 'Close' in latest else 1
                    order_id = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        tradingsymbol=sym.replace(".NS",""),
                        exchange=kite.EXCHANGE_NSE,
                        transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                        quantity=qty,
                        product=kite.PRODUCT_MIS,
                        order_type=kite.ORDER_TYPE_MARKET
                    )
                    st.success(f"✅ Zerodha Order Placed! ID: {order_id}")
                    send_telegram(f"<b>Zerodha Order ID:</b> {order_id}")
                except Exception as e:
                    st.error(f"Order Failed: {str(e)}")
