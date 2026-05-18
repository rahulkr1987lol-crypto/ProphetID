import streamlit as st
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v6.0 - Practical Intraday Scanner (Live Market)")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000}

st.sidebar.header("Controls")
mode = st.sidebar.selectbox("Mode", ["Paper Trading", "Zerodha Live (Coming)"])
risk_per_trade = st.sidebar.slider("Risk per Trade %", 0.5, 2.0, 1.0, 0.1)

def send_telegram(message):
    # Optional - you can keep your token if you want alerts
    pass

st.header("📊 Live Market Scanner - Best Intraday Options")

# Big list of liquid stocks
symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", 
           "BHARTIARTL.NS", "HINDUNILVR.NS", "LT.NS", "AXISBANK.NS", "TATAMOTORS.NS", 
           "TATASTEEL.NS", "HINDALCO.NS", "DRREDDY.NS", "CIPLA.NS", "ADANIPORTS.NS"]

@st.cache_data(ttl=20)
def scan_market():
    results = []
    for sym in symbols:
        try:
            data = yf.download(sym, period="1d", interval="5m", progress=False)
            if len(data) < 5:
                continue
            latest = data.iloc[-1]
            open_price = data.iloc[0]['Close']
            change = (latest['Close'] - open_price) / open_price * 100
            volume_ratio = data['Volume'].iloc[-1] / data['Volume'].mean() if data['Volume'].mean() > 0 else 1.0

            if abs(change) > 0.2 or volume_ratio > 1.2:   # Lower threshold for live market
                signal = "🟢 BUY" if change > 0 else "🔴 SELL"
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
    return results

if st.button("🔄 Scan Market Now"):
    with st.spinner("Connecting to market and finding best opportunities..."):
        picks = scan_market()
        if picks:
            for p in picks[:12]:
                st.success(f"**{p['symbol']}** → {p['signal']} | **{p['change']}%** | Volume {p['volume_ratio']}x | ₹{p['price']}")
        else:
            st.info("Market is very quiet right now. Try again in 5-10 minutes.")

st.caption("v6.0 | Scans 16 liquid stocks | Shows current movers | Paper Trading Recommended")
