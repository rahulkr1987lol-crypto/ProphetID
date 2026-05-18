import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - Practical Live Scanner (18 May 2026)")

st.sidebar.header("Controls")
risk = st.sidebar.slider("Risk per Trade %", 0.5, 2.0, 1.0)

st.header("Current Top Intraday Opportunities")

stocks = ["SUNPHARMA.NS", "TECHM.NS", "INFY.NS", "BHARTIARTL.NS", "TATAMOTORS.NS", "HDFCBANK.NS", "COALINDIA.NS", "PIDILITIND.NS"]

for sym in stocks:
    data = yf.download(sym, period="1d", interval="5m", progress=False)
    if not data.empty:
        latest = data.iloc[-1]
        change = (latest['Close'] - data.iloc[0]['Close']) / data.iloc[0]['Close'] * 100 if len(data) > 1 else 0
        price = latest['Close']
        
        st.subheader(f"{sym.replace('.NS','')}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Price", f"₹{price:.2f}", f"{change:.2f}%")
        col2.metric("Suggested Size", "₹4,500 max")
        signal = "🟢 STRONG BUY" if change > 0.3 else "🔴 SELL" if change < -0.3 else "Monitor"
        col3.write(f"**{signal}**")
        
        if st.button(f"Execute on {sym.replace('.NS','')}", key=sym):
            st.success(f"Paper Trade Executed on {sym.replace('.NS','')} | Size ₹4500")
            st.info("Use Zerodha Kite app for real execution")

st.caption("Practical Scanner | Focus on high liquidity stocks | Paper mode for safety")
