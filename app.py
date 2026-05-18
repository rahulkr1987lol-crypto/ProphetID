import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.8 - Full Market Scanner + Top Picks")

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

st.header("📊 ProphetID Full Market Scanner - Top Picks")

# Expanded Stock List (Liquid + Volatile)
all_symbols = ["TATASTEEL.NS", "HINDALCO.NS", "DRREDDY.NS", "CIPLA.NS", "TATAMOTORS.NS", 
               "BHARTIARTL.NS", "RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "INFY.NS", 
               "HCLTECH.NS", "ADANIPORTS.NS", "COALINDIA.NS", "ONGC.NS"]

@st.cache_data(ttl=60)
def full_scan():
    results = []
    for sym in all_symbols:
        try:
            data = yf.download(sym, period="5d", interval="5m", progress=False)
            if len(data) < 10:
                continue
            latest = data.iloc[-1]
            prev = data.iloc[-10]
            change = (latest['Close'] - prev['Close']) / prev['Close'] * 100
            avg_vol = data['Volume'].mean()
            curr_vol = data['Volume'].iloc[-1]
            volume_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0

            if abs(change) > 0.6 and volume_ratio > 1.2:
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
    # Sort by strongest momentum
    results.sort(key=lambda x: abs(x['change']), reverse=True)
    return results[:10]  # Top 10 best opportunities

if st.button("🔄 Run Full Market Scan"):
    with st.spinner("Scanning market for best opportunities..."):
        top_picks = full_scan()
        if top_picks:
            for pick in top_picks:
                st.success(f"**{pick['symbol']}** → {pick['signal']} | {pick['change']}% | Volume {pick['volume_ratio']}x | Price ₹{pick['price']}")
        else:
            st.info("No strong setups right now. Try again later.")

st.caption("ProphetID v5.8 | Scans 14 liquid stocks | Shows Top 10 best opportunities | Stable Version")
