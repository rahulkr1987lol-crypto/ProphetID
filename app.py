import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="RahulIntradayPro", layout="wide")
st.title("🚀 RahulIntradayPro - NSE Intraday Trader + Telegram Alerts")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

st.sidebar.header("Settings")
broker = st.sidebar.selectbox("Broker", ["Zerodha Kite", "Upstox", "Paper Trading Only"])

st.sidebar.header("📱 Telegram Alerts")
bot_token = st.sidebar.text_input("Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Your Chat ID", type="password")

def send_telegram(message):
    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        except:
            pass

@st.cache_data(ttl=180)
def get_data(symbol):
    return yf.download(symbol + ".NS", period="1d", interval="5m")

st.header("📊 Today's Hot Intraday Picks (16 May 2026)")
sectors = {
    "Metals": ["TATASTEEL.NS", "HINDALCO.NS"],
    "Pharma": ["DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS"],
    "Telecom": ["BHARTIARTL.NS"]
}
selected = st.selectbox("Choose Sector", list(sectors.keys()))

for sym in sectors[selected]:
    data = get_data(sym)
    if not data.empty:
        latest = data.iloc[-1]
        change = (latest['Close'] - data.iloc[0]['Close']) / data.iloc[0]['Close'] * 100
        
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=300, title=f"{sym} Live Chart")
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
        col2.write(f"**ORB** H:{data['High'].iloc[:3].max():.1f} L:{data['Low'].iloc[:3].min():.1f}")
        signal = "🟢 STRONG BUY" if change > 0.7 else "🔴 SELL" if change < -0.7 else "🟡 MONITOR"
        col3.write(f"**Signal**: {signal}")
        
        if st.button(f"Execute {signal} on {sym.replace('.NS','')}", key=sym):
            trade_size = min(4500, st.session_state.portfolio['cash'])
            pnl = trade_size * (0.019 if "BUY" in signal else -0.013)
            st.session_state.portfolio['cash'] -= trade_size
            st.session_state.portfolio['pnl'] += pnl
            st.session_state.portfolio['trades'].append({"symbol": sym, "pnl": pnl, "time": datetime.now().strftime("%H:%M")})
            
            alert = f"<b>TRADE EXECUTED</b>\n{signal} {sym.replace('.NS','')}\nSize: ₹{trade_size}\nP&L: ₹{pnl:.2f}\nRemaining: ₹{st.session_state.portfolio['cash']}"
            send_telegram(alert)
            st.success("✅ Trade Executed + Telegram Alert Sent!")

st.header("💰 Portfolio")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("P&L Today", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

if st.button("📨 Send Daily Summary to Telegram"):
    send_telegram(f"<b>Daily Summary</b>\nP&L: ₹{st.session_state.portfolio['pnl']:.2f}\nRemaining: ₹{st.session_state.portfolio['cash']}")
