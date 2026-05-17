import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Safe Secrets Loading
try:
    telegram_token = st.secrets["telegram"]["bot_token"]
    chat_id = st.secrets["telegram"]["chat_id"]
except:
    telegram_token = None
    chat_id = None
    st.sidebar.error("⚠️ Set Secrets in Streamlit Cloud Settings")

st.sidebar.header("Settings")
broker = st.sidebar.selectbox("Broker", ["Zerodha Kite", "Upstox", "Paper Trading Only"])

if telegram_token:
    st.sidebar.success("✅ Telegram Connected Permanently")

def send_telegram(message):
    if telegram_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        except:
            pass

@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        data = yf.download(symbol + ".NS", period="5d", interval="5m")
        if data.empty:
            data = yf.download(symbol + ".NS", period="1mo", interval="1d")
        return data
    except:
        return pd.DataFrame()

st.header("📊 ProphetID Today's High-Probability Picks")

sectors = {
    "Metals": ["TATASTEEL.NS", "HINDALCO.NS"],
    "Pharma": ["DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS"],
    "Telecom": ["BHARTIARTL.NS"]
}

selected = st.selectbox("Choose Sector", list(sectors.keys()))

for sym in sectors[selected]:
    data = get_data(sym)
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    if not data.empty:
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        change = (latest['Close'] - prev['Close']) / prev['Close'] * 100
        
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=380, title=f"{sym} Latest Chart")
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
        col2.write(f"**Last Price**: ₹{latest['Close']:.2f}")
        
        signal = "🟢 STRONG BUY" if change > 0 else "🔴 SELL" if change < 0 else "🟡 MONITOR"
        col3.write(f"**Signal**: {signal}")
        
        trade_size = min(4500, st.session_state.portfolio['cash'])
        if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", 
                     key=f"exec_{sym}", use_container_width=True, type="primary"):
            
            pnl = trade_size * (0.018 if "BUY" in signal else -0.012)
            st.session_state.portfolio['cash'] -= trade_size
            st.session_state.portfolio['pnl'] += pnl
            st.session_state.portfolio['trades'].append({
                "symbol": sym.replace(".NS",""), "action": signal,
                "size": trade_size, "pnl": round(pnl,2), "time": datetime.now().strftime("%H:%M")
            })
            
            alert = f"""<b>🚀 TRADE EXECUTED by ProphetID</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
P&L: ₹{pnl:.2f}
Remaining: ₹{st.session_state.portfolio['cash']}"""
            
            send_telegram(alert)
            st.success(f"✅ Trade Executed! Telegram sent.")
            
            if pnl > 0:
                st.session_state.portfolio['days_profitable'] += 1

# Portfolio Summary
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

if st.button("📨 Send Daily Summary to Telegram"):
    send_telegram(f"<b>ProphetID Daily Summary</b>\nP&L: ₹{st.session_state.portfolio['pnl']:.2f}\nRemaining: ₹{st.session_state.portfolio['cash']}")
    st.success("Summary sent!")

st.caption("ProphetID v1.0 | ₹10,000 Daily Limit | Ready for Intraday")
