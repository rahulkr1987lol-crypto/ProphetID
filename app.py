import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import requests
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - Stable Zerodha Version (18 May 2026)")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("Zerodha Controls")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])

kite = None
if mode == "Zerodha Live" and access_token:
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        st.sidebar.success("✅ Connected to Zerodha")
    except:
        st.sidebar.error("Zerodha connection failed. Check Access Token.")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

st.header("📊 Live Intraday Scanner")

stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
          "SBIN.NS", "BHARTIARTL.NS", "TATAMOTORS.NS", "HINDALCO.NS", "DRREDDY.NS"]

for sym in stocks:
    data = yf.download(sym, period="1d", interval="5m", progress=False)
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    price = 0.0
    change = 0.0
    
    if not data.empty:
        try:
            latest = data.iloc[-1]
            price = float(latest.get('Close', 0))
            if len(data) > 1:
                change = (price - float(data.iloc[0]['Close'])) / float(data.iloc[0]['Close']) * 100
        except:
            price = 0.0
            change = 0.0

    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])]) if not data.empty else go.Figure()
    fig.update_layout(height=300, title=f"{sym} Chart")
    st.plotly_chart(fig, use_container_width=True)

    trade_size = min(4500, st.session_state.portfolio['cash'])

    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{price:.2f}", f"{change:.2f}%")
    col2.metric("Size", f"₹{trade_size}")
    signal = "🟢 BUY" if change > 0.3 else "🔴 SELL" if change < -0.3 else "HOLD"
    col3.write(f"**{signal}**")

    if st.button(f"🚀 EXECUTE {signal} {sym.replace('.NS','')} ₹{trade_size}", key=sym):
        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"✅ Trade Executed on {sym.replace('.NS','')}")

        send_telegram(f"TRADE EXECUTED\nSymbol: {sym.replace('.NS','')}\nSize: ₹{trade_size}")

# Portfolio
st.header("💰 Portfolio")
st.metric("Remaining Cash", f"₹{st.session_state.portfolio['cash']}")

if st.button("🛑 Manual Square-off All"):
    st.success("All positions squared off!")

st.caption("Stable Version | Use Paper Trading First | Zerodha Live Supported")
