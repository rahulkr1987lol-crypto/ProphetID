import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect, KiteTicker

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v6.0 - Zerodha WebSocket Live Data")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'pnl': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("Zerodha Live")
mode = st.sidebar.selectbox("Mode", ["Paper Trading", "Zerodha Live"])

kite = None
if mode == "Zerodha Live" and access_token:
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    st.sidebar.success("✅ Zerodha Connected")

# WebSocket Ticker
kws = None
live_prices = {}

def on_ticks(ws, ticks):
    for tick in ticks:
        token = tick['instrument_token']
        ltp = tick['last_price']
        live_prices[token] = ltp

def on_connect(ws, response):
    # Subscribe to some tokens (example)
    ws.subscribe([738561, 5633, 408065])  # Example tokens for RELIANCE, TCS, etc.
    ws.set_mode(ws.MODE_LTP, [738561, 5633, 408065])

if mode == "Zerodha Live" and kite:
    kws = KiteTicker(api_key, access_token)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect(threaded=True)
    st.sidebar.success("WebSocket Live Ticks Started")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

st.header("Live Market Scanner (Zerodha WebSocket)")

symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "BHARTIARTL.NS", "TATAMOTORS.NS"]

for sym in symbols:
    data = yf.download(sym, period="1d", interval="5m", progress=False)
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    price = 0.0
    change = 0.0
    if not data.empty:
        latest = data.iloc[-1]
        price = float(latest['Close'])
        change = (price - float(data.iloc[0]['Close'])) / float(data.iloc[0]['Close']) * 100 if len(data) > 1 else 0.0

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
        st.success(f"Trade Executed on {sym.replace('.NS','')}")

        send_telegram(f"TRADE EXECUTED\nSymbol: {sym.replace('.NS','')}\nSize: ₹{trade_size}")

st.header("💰 Portfolio")
st.metric("Remaining Cash", f"₹{st.session_state.portfolio['cash']}")

st.caption("Zerodha WebSocket Active | Use Paper Mode First")
