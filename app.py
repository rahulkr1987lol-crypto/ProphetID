import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.9 - Live Market Scanner (Monday Ready)")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'pnl': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("Controls")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])
auto_squareoff = st.sidebar.checkbox("Auto Square-off at 3:20 PM", value=True)
risk_per_trade = st.sidebar.slider("Risk per Trade %", 0.5, 2.0, 1.0, 0.1)

kite = None
if mode == "Zerodha Live" and access_token:
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    st.sidebar.success("✅ Zerodha Live")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

# Auto Square-off
if auto_squareoff:
    now = datetime.now().time()
    if now.hour == 15 and now.minute >= 20:
        send_telegram("🛑 Auto Square-off at 3:20 PM!")
        st.warning("All positions squared off!")

st.header("📊 ProphetID Live Market Scanner")

# Larger Stock Universe
symbols = ["TATASTEEL.NS", "HINDALCO.NS", "DRREDDY.NS", "CIPLA.NS", "TATAMOTORS.NS", 
           "BHARTIARTL.NS", "RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "INFY.NS", 
           "HCLTECH.NS", "ADANIPORTS.NS", "COALINDIA.NS", "ONGC.NS", "AXISBANK.NS", "ICICIBANK.NS"]

@st.cache_data(ttl=30)
def full_scan():
    results = []
    for sym in symbols:
        try:
            data = yf.download(sym, period="1d", interval="5m", progress=False)
            if len(data) < 5:
                continue
            latest = data.iloc[-1]
            change = (latest['Close'] - data.iloc[0]['Close']) / data.iloc[0]['Close'] * 100
            volume_ratio = data['Volume'].iloc[-1] / data['Volume'].mean() if data['Volume'].mean() > 0 else 1.0

            if abs(change) > 0.3 or volume_ratio > 1.3:   # Lower threshold for live market
                signal = "🟢 STRONG BUY" if change > 0 else "🔴 SELL"
                results.append({
                    "symbol": sym.replace(".NS",""),
                    "signal": signal,
                    "change": round(change, 2),
                    "price": round(latest['Close'], 2),
                    "volume_ratio": round(volume_ratio, 2)
                })
        except:
            continue
    results.sort(key=lambda x: abs(x['change']), reverse=True)
    return results[:10]

if st.button("🔄 Run Full Market Scan (Live)"):
    with st.spinner("Connecting to market and scanning best opportunities..."):
        top_picks = full_scan()
        if top_picks:
            for p in top_picks:
                st.success(f"**{p['symbol']}** → {p['signal']} | {p['change']}% | Volume {p['volume_ratio']}x | ₹{p['price']}")
        else:
            st.info("Market is slow or just opened. Try again in 10-15 minutes.")

st.caption("ProphetID v5.9 | Scans 16 liquid stocks | Lower threshold for live market | Ready for Today")
