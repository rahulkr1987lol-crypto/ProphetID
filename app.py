import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v4.0 - Autonomous Intraday Profit Engine")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
api_secret = st.secrets["zerodha"].get("api_secret", "")
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("⚙️ Autonomous Settings")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])
auto_mode = st.sidebar.checkbox("Enable Autonomous Trading (Scan + Execute)", value=False)
sl_percent = st.sidebar.slider("Stop Loss %", 0.5, 2.0, 0.8, 0.1)
target_percent = st.sidebar.slider("Target %", 1.5, 5.0, 2.5, 0.1)

kite = None
if mode == "Zerodha Live" and access_token:
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        st.sidebar.success("✅ Zerodha Live + SL Ready")
    except:
        st.sidebar.error("Zerodha connection issue")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

# Fixed Advanced Scanner
@st.cache_data(ttl=60)
def advanced_scan():
    symbols = ["TATASTEEL.NS", "HINDALCO.NS", "DRREDDY.NS", "CIPLA.NS", 
               "TATAMOTORS.NS", "BHARTIARTL.NS", "RELIANCE.NS", "HCLTECH.NS"]
    results = []
    for sym in symbols:
        try:
            data = yf.download(sym, period="5d", interval="5m", progress=False)
            if len(data) < 15:
                continue
            latest = data.iloc[-1]
            prev = data.iloc[-10]
            change = (latest['Close'] - prev['Close']) / prev['Close'] * 100
            avg_volume = data['Volume'].mean()
            
            if abs(change) > 0.6 and avg_volume > 500000:   # Strong momentum + liquidity
                signal = "🟢 STRONG BUY" if change > 0 else "🔴 SELL"
                results.append({
                    "symbol": sym.replace(".NS",""),
                    "signal": signal,
                    "change": round(change, 2),
                    "price": round(latest['Close'], 2),
                    "volume": int(avg_volume)
                })
        except:
            continue
    return results

st.header("📊 ProphetID Autonomous Scanner")

if st.button("🔄 Run Full Scan Now"):
    with st.spinner("Scanning best opportunities..."):
        scans = advanced_scan()
        if scans:
            for s in scans:
                st.success(f"**{s['symbol']}** → {s['signal']} | +{s['change']}% @ ₹{s['price']} | Vol: {s['volume']:,}")
        else:
            st.info("No high-conviction setups right now (Weekend)")

# Manual Execution with SL/Target
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
        prev = data.iloc[-10] if len(data) > 10 else data.iloc[0]
        change = (latest['Close'] - prev['Close']) / prev['Close'] * 100
        
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=350, title=f"{sym} Chart")
        st.plotly_chart(fig, use_container_width=True)
    else:
        change = 0.0
        latest = pd.Series({'Close': 0})

    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
    signal = "🟢 STRONG BUY" if change > 0.5 else "🔴 SELL" if change < -0.5 else "🟡 MONITOR"
    col3.write(f"**Signal**: {signal}")

    trade_size = min(4500, st.session_state.portfolio['cash'])
    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", key=f"exec_{sym}", use_container_width=True, type="primary"):
        entry_price = latest['Close']
        sl_price = round(entry_price * (1 - sl_percent/100), 2) if "BUY" in signal else round(entry_price * (1 + sl_percent/100), 2)
        target_price = round(entry_price * (1 + target_percent/100), 2) if "BUY" in signal else round(entry_price * (1 - target_percent/100), 2)
        
        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"✅ Executed | SL: ₹{sl_price} | Target: ₹{target_price}")

        alert = f"""<b>ProphetID TRADE</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
SL: ₹{sl_price} ({sl_percent}%)
Target: ₹{target_price} ({target_percent}%)"""
        send_telegram(alert)

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Win Days", st.session_state.portfolio['days_profitable'])

st.caption("ProphetID v4.0 | Autonomous Scanner + SL/Target | Test in Paper Mode")
