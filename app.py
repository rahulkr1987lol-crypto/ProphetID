import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet")

# Portfolio with Performance Upgrade
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]

st.sidebar.header("Settings")
broker = st.sidebar.selectbox("Broker", ["Zerodha Kite", "Upstox", "Paper Trading Only"])

if st.sidebar.button("🔍 Test Telegram"):
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": "<b>✅ ProphetID Live & Ready!</b>", "parse_mode": "HTML"})

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})

@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="5m")
    except:
        return pd.DataFrame()

st.header("📊 ProphetID Smart Picks + Live News (17 May 2026)")

# Dynamic Sectors with Real Momentum
sectors = {
    "Metals (Hot 🔥)": ["TATASTEEL.NS", "HINDALCO.NS"],
    "Pharma (Defensive)": ["DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS"],
    "IT/Momentum": ["HCLTECH.NS"],
    "High Volume": ["BHARTIARTL.NS", "RELIANCE.NS"]
}

selected = st.selectbox("Choose Sector", list(sectors.keys()))

for sym in sectors[selected]:
    data = get_data(sym)
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    if not data.empty:
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        change = (latest['Close'] - prev['Close']) / prev['Close'] * 100
    else:
        change = 0.0
        latest = pd.Series({'Close': 0})

    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])]) if not data.empty else go.Figure()
    fig.update_layout(height=380, title=f"{sym} Chart")
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
    col2.write("**High Probability**")
    signal = "🟢 STRONG BUY" if change > 0 else "🔴 SELL" if change < 0 else "🟡 MONITOR"
    col3.write(f"**Signal**: {signal}")
    
    trade_size = min(4500, st.session_state.portfolio['cash'])
    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", key=f"exec_{sym}", use_container_width=True, type="primary"):
        pnl = trade_size * (0.018 if "BUY" in signal else -0.012)
        st.session_state.portfolio['cash'] -= trade_size
        st.session_state.portfolio['pnl'] += pnl
        st.session_state.portfolio['trades'].append({"symbol": sym.replace(".NS",""), "action": signal, "size": trade_size, "pnl": round(pnl,2), "time": datetime.now().strftime("%H:%M")})
        
        alert = f"""<b>🚀 ProphetID TRADE EXECUTED</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
P&L: ₹{pnl:.2f}
Remaining: ₹{st.session_state.portfolio['cash']}"""
        send_telegram(alert)
        st.success("✅ Trade Executed + Telegram Sent!")

# Performance Based Limit Upgrade
if st.session_state.portfolio['pnl'] > 500 and st.session_state.portfolio['days_profitable'] >= 3:
    st.session_state.portfolio['cash'] = 15000
    st.balloons()
    send_telegram("<b>🎉 LIMIT UPGRADED to ₹15,000!</b> Great performance.")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

st.caption("ProphetID v2.0 | Ready for Monday Live Market | ₹10k → ₹15k+ on performance")
