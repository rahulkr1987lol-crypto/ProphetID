import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet (Zerodha Live)")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
api_secret = st.secrets["zerodha"].get("api_secret", "")

st.sidebar.header("⚙️ Settings")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])

kite = None
access_token = st.secrets["zerodha"].get("access_token", None)

if mode == "Zerodha Live":
    try:
        kite = KiteConnect(api_key=api_key)
        if access_token:
            kite.set_access_token(access_token)
            st.sidebar.success("✅ Zerodha Connected")
        else:
            st.sidebar.warning("⚠️ Run Login below to get Access Token")
    except Exception as e:
        st.sidebar.error(f"Zerodha Error: {e}")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

# Login Helper
if st.sidebar.button("🔑 Generate Zerodha Access Token"):
    login_url = f"https://kite.trade/connect/login?api_key={api_key}&v=3"
    st.sidebar.markdown(f"[🔗 Open Zerodha Login]({login_url})")
    st.sidebar.info("After login, copy 'request_token' from URL and paste below")

request_token = st.sidebar.text_input("Paste Request Token (from URL)")
if st.sidebar.button("✅ Generate & Save Access Token"):
    if kite and request_token:
        try:
            data = kite.generate_session(request_token, api_secret=api_secret)
            new_token = data['access_token']
            st.success(f"✅ Access Token Generated: {new_token[:15]}...")
            st.sidebar.success("Token ready! Refresh app.")
        except Exception as e:
            st.error(f"Token Error: {e}")

@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="5m")
    except:
        return pd.DataFrame()

st.header("📊 ProphetID Smart Picks + News")

news = ["Metals strong on global cues", "Pharma defensive", "Nifty support ~23,500"]
for item in news:
    st.write(f"• {item}")

sectors = {
    "Metals 🔥": ["TATASTEEL.NS", "HINDALCO.NS"],
    "Pharma": ["DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS"],
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
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=380, title=f"{sym} Chart")
        st.plotly_chart(fig, use_container_width=True)
    else:
        change = 0.0
        latest = pd.Series({'Close': 0})

    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
    signal = "🟢 STRONG BUY" if change > 0.3 else "🔴 SELL" if change < -0.3 else "🟡 MONITOR"
    col3.write(f"**Signal**: {signal}")

    trade_size =
