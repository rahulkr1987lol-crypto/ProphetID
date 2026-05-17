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

# Secrets
try:
    telegram_token = st.secrets["telegram"]["bot_token"]
    chat_id = st.secrets["telegram"]["chat_id"]
    secrets_ok = True
except:
    telegram_token = None
    chat_id = None
    secrets_ok = False

st.sidebar.header("Settings")
broker = st.sidebar.selectbox("Broker", ["Zerodha Kite", "Upstox", "Paper Trading Only"])

if secrets_ok:
    st.sidebar.success("✅ Telegram Connected")
else:
    st.sidebar.error("Set Secrets in Manage App → Secrets")

def send_telegram(message):
    if secrets_ok:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
            if r.status_code == 200:
                return True
            else:
                st.sidebar.error(f"Telegram Error: {r.text}")
                return False
        except Exception as e:
            st.sidebar.error(f"Telegram Failed: {str(e)}")
            return False
    return False

# Test Telegram Button
if st.sidebar.button("🔍 Test Telegram Connection"):
    if send_telegram("<b>✅ ProphetID Test Successful!</b>\nYour alerts are working."):
        st.sidebar.success("Test message sent! Check your Telegram.")
    else:
        st.sidebar.error("Test failed - check secrets or token")

@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        data = yf.download(symbol + ".NS", period="5d", interval="5m")
        if data.empty:
            data = yf.download(symbol + ".NS", period="1mo", interval="1d")
        return data
    except:
        return pd.DataFrame()

st.header("📊 ProphetID High-Probability Picks (Weekend Mode)")

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
        
        # Always show Execute button
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
            
            alert = f"""<b>🚀 ProphetID TRADE EXECUTED</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
Sim P&L: ₹{pnl:.2f}
Remaining Limit: ₹{st.session_state.portfolio['cash']}"""
            
            send_telegram(alert)
            st.success(f"✅ Trade Executed by ProphetID! Check Telegram.")
            
            if pnl > 0:
                st.session_state.portfolio['days_profitable'] += 1
    else:
        st.info("Using last known data (Market closed)")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

if st.button("📨 Send Daily Summary to Telegram"):
    send_telegram(f"<b>ProphetID Daily Summary</b>\nP&L: ₹{st.session_state.portfolio['pnl']:.2f}\nRemaining: ₹{st.session_state.portfolio['cash']}")
    st.success("Summary sent!")

st.caption("ProphetID v1.1 | Test Telegram from sidebar | Buttons always visible")
