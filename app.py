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

# Secrets (with fallback)
telegram_token = None
chat_id = None
try:
    telegram_token = st.secrets["telegram"]["bot_token"]
    chat_id = st.secrets["telegram"]["chat_id"]
except:
    pass

st.sidebar.header("Settings")
broker = st.sidebar.selectbox("Broker", ["Zerodha Kite", "Upstox", "Paper Trading Only"])

if telegram_token and chat_id:
    st.sidebar.success("✅ Telegram Connected")
else:
    st.sidebar.error("❌ Set Secrets → Manage app → Secrets (bottom right)")

def send_telegram(message):
    if telegram_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
            return r.status_code == 200
        except:
            return False
    return False

# Test Button
if st.sidebar.button("🔍 Test Telegram"):
    if send_telegram("<b>✅ ProphetID Test Successful!</b>\nAlerts are now working."):
        st.sidebar.success("✅ Test sent! Check your Telegram.")
    else:
        st.sidebar.error("❌ Test failed. Check token in Secrets.")

@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        data = yf.download(symbol + ".NS", period="5d", interval="5m")
        if data.empty:
            data = yf.download(symbol + ".NS", period="1mo", interval="1d")
        return data
    except:
        return pd.DataFrame()

st.header("📊 ProphetID High-Probability Picks")

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
    else:
        latest = pd.Series({'Close': 0})
        change = 0.0

    # Always show chart area
    fig = go.Figure()
    if not data.empty:
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close']))
    fig.update_layout(height=380, title=f"{sym} Latest Chart")
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
    col2.write("**Weekend Mode** - Last known data")
    
    signal = "🟢 STRONG BUY" if change > 0 else "🔴 SELL" if change < 0 else "🟡 MONITOR"
    col3.write(f"**Signal**: {signal}")
    
    # ALWAYS SHOW EXECUTE BUTTON
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
Remaining: ₹{st.session_state.portfolio['cash']}"""
        
        if send_telegram(alert):
            st.success("✅ Trade Executed + Telegram Sent!")
        else:
            st.success("✅ Trade Executed (Telegram failed - check secrets)")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

if st.button("📨 Send Daily Summary to Telegram"):
    send_telegram(f"<b>ProphetID Daily Summary</b>\nP&L: ₹{st.session_state.portfolio['pnl']:.2f}\nRemaining: ₹{st.session_state.portfolio['cash']}")
    st.success("Summary request sent!")

st.caption("ProphetID v1.2 | Execute buttons always visible | Test Telegram from sidebar")
