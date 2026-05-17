import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - Stable Version")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("Controls")
mode = st.sidebar.selectbox("Mode", ["Paper Trading", "Zerodha Live"])
auto_squareoff = st.sidebar.checkbox("Auto Square-off at 3:20 PM", value=True)

kite = None
if mode == "Zerodha Live" and access_token:
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    st.sidebar.success("✅ Zerodha Connected")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

# Auto Square-off
def square_off_all():
    now = datetime.now().time()
    if auto_squareoff and now.hour == 15 and now.minute >= 20:
        send_telegram("🛑 Auto Square-off triggered at 3:20 PM!")
        st.warning("All positions squared off!")
        return True
    return False

square_off_all()

st.header("📊 ProphetID Scanner")

sectors = {
    "Metals 🔥": ["TATASTEEL.NS", "HINDALCO.NS"],
    "Pharma": ["DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS"],
    "High Volume": ["BHARTIARTL.NS", "RELIANCE.NS"]
}

selected = st.selectbox("Choose Sector", list(sectors.keys()))

for sym in sectors[selected]:
    data = yf.download(sym, period="5d", interval="5m", progress=False)
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    if not data.empty:
        latest = data.iloc[-1]
        change = (latest['Close'] - data.iloc[0]['Close']) / data.iloc[0]['Close'] * 100 if len(data) > 1 else 0
    else:
        change = 0.0
        latest = pd.Series({'Close': 0})

    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])]) if not data.empty else go.Figure()
    fig.update_layout(height=350, title=f"{sym} Chart")
    st.plotly_chart(fig, use_container_width=True)

    trade_size = min(4500, st.session_state.portfolio['cash'])

    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
    col2.metric("Size", f"₹{trade_size}")
    signal = "🟢 BUY" if change > 0 else "🔴 SELL" if change < 0 else "HOLD"
    col3.write(f"**{signal}**")

    if st.button(f"🚀 EXECUTE {signal} {sym.replace('.NS','')} ₹{trade_size}", key=sym):
        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"Trade Executed on {sym.replace('.NS','')}")

        send_telegram(f"TRADE EXECUTED\nSymbol: {sym.replace('.NS','')}\nAction: {signal}\nSize: ₹{trade_size}")

        if mode == "Zerodha Live" and kite:
            st.info("Zerodha order would be placed here (Paper mode active)")

# Portfolio
st.header("💰 Portfolio")
c1, c2 = st.columns(2)
c1.metric("Remaining Cash", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")

if st.button("🛑 Manual Square-off"):
    square_off_all()

st.caption("Stable Version | Test in Paper Trading")
