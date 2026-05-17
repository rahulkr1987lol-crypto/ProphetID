import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.2 - Full Autonomous Intraday Engine")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
api_secret = st.secrets["zerodha"].get("api_secret", "")
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("⚙️ Controls")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])
auto_mode = st.sidebar.checkbox("Autonomous Mode", value=False)
sl_percent = st.sidebar.slider("Stop Loss %", 0.5, 2.0, 0.8, 0.1)
target_percent = st.sidebar.slider("Target %", 1.5, 5.0, 2.5, 0.1)

kite = None
if mode == "Zerodha Live" and access_token:
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    st.sidebar.success("✅ Zerodha Live")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

# Telegram Commands
if st.sidebar.button("🔄 Check Telegram Commands"):
    try:
        r = requests.get(f"https://api.telegram.org/bot{telegram_token}/getUpdates")
        data = r.json()
        if data['ok'] and data['result']:
            text = data['result'][-1]['message']['text'].lower()
            if text == "/status":
                send_telegram(f"<b>ProphetID Status</b>\nLimit: ₹{st.session_state.portfolio['cash']}\nP&L: ₹{st.session_state.portfolio['pnl']:.2f}")
                st.success("Status sent!")
            elif text == "/scan":
                st.success("Scan triggered via Telegram")
            elif text == "/stop":
                auto_mode = False
                st.warning("Autonomous mode stopped")
    except:
        st.info("No new commands")

@st.cache_data(ttl=30)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="5m", progress=False)
    except:
        return pd.DataFrame()

# Scanner
def advanced_scan():
    symbols = ["TATASTEEL.NS", "HINDALCO.NS", "DRREDDY.NS", "CIPLA.NS", "TATAMOTORS.NS", "BHARTIARTL.NS", "RELIANCE.NS"]
    results = []
    for sym in symbols:
        data = get_data(sym)
        if len(data) < 10: continue
        latest = data.iloc[-1]
        change = (latest['Close'] - data.iloc[-10]['Close']) / data.iloc[-10]['Close'] * 100
        vol = data['Volume'].mean()
        if abs(change) > 0.6 and vol > 500000:
            signal = "🟢 STRONG BUY" if change > 0 else "🔴 SELL"
            results.append({"symbol": sym.replace(".NS",""), "signal": signal, "change": round(change,2), "price": round(latest['Close'],2)})
    return results

st.header("📊 ProphetID Autonomous Scanner")
if st.button("🔄 Run Full Scan") or auto_mode:
    scans = advanced_scan()
    for s in scans:
        st.success(f"{s['symbol']} → {s['signal']} | {s['change']}% @ ₹{s['price']}")

# Execution Section
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
        change = (latest['Close'] - data.iloc[-10]['Close']) / data.iloc[-10]['Close'] * 100 if len(data) > 10 else 0
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=350, title=f"{sym} Live Chart")
        st.plotly_chart(fig, use_container_width=True)
    else:
        change = 0
        latest = pd.Series({'Close': 0})

    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
    signal = "🟢 STRONG BUY" if change > 0.5 else "🔴 SELL" if change < -0.5 else "🟡 MONITOR"
    col3.write(f"**Signal**: {signal}")

    trade_size = min(4500, st.session_state.portfolio['cash'])
    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", key=f"exec_{sym}", use_container_width=True, type="primary"):
        entry = latest['Close']
        sl = round(entry * (1 - sl_percent/100), 2) if "BUY" in signal else round(entry * (1 + sl_percent/100), 2)
        target = round(entry * (1 + target_percent/100), 2) if "BUY" in signal else round(entry * (1 - target_percent/100), 2)

        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"✅ Executed | SL ₹{sl} | Target ₹{target}")

        alert = f"""<b>ProphetID TRADE</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
SL: ₹{sl} | Target: ₹{target}"""
        send_telegram(alert)

        # Zerodha Bracket Order
        if mode == "Zerodha Live" and kite:
            try:
                qty = max(1, int(trade_size / entry))
                kite.place_order(variety=kite.VARIETY_BO, tradingsymbol=sym.replace(".NS",""), exchange=kite.EXCHANGE_NSE,
                                 transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                                 quantity=qty, product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET,
                                 squareoff=int(abs(target - entry) * qty), stoploss=int(abs(entry - sl) * qty))
                st.success("Bracket Order Placed on Zerodha!")
            except Exception as e:
                st.error(f"Order Error: {e}")

# Portfolio
st.header("💰 Portfolio")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("P&L Today", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Win Days", st.session_state.portfolio['days_profitable'])

st.caption("ProphetID v5.2 | Full Features | Test in Paper Mode First")
