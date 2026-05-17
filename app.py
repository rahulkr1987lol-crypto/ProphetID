import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.7 - Stable Version for Monday Trading")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'pnl': 0, 'trades': []}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("⚙️ Controls")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])
auto_squareoff = st.sidebar.checkbox("Auto Square-off at 3:20 PM", value=True)
risk_per_trade = st.sidebar.slider("Risk per Trade %", 0.5, 2.0, 1.0, 0.1)

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

# Auto Square-off
def square_off_all():
    now = datetime.now().time()
    if auto_squareoff and now.hour == 15 and now.minute >= 20:
        send_telegram("🛑 Auto Square-off at 3:20 PM triggered!")
        st.warning("🛑 All positions squared off!")
        return True
    return False

square_off_all()

st.header("📊 ProphetID Smart Scanner")

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
        price = float(latest['Close'])
        change = (price - float(data.iloc[0]['Close'])) / float(data.iloc[0]['Close']) * 100 if len(data) > 1 else 0.0
    else:
        price = 0.0
        change = 0.0

    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])]) if not data.empty else go.Figure()
    fig.update_layout(height=350, title=f"{sym} Chart")
    st.plotly_chart(fig, use_container_width=True)

    # Dynamic Size
    risk_amount = st.session_state.portfolio['cash'] * (risk_per_trade / 100)
    stop_distance = price * 0.008
    dynamic_qty = int(risk_amount / stop_distance) if stop_distance > 0 else 1
    trade_size = min(dynamic_qty * price, st.session_state.portfolio['cash'] * 0.4)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(sym.replace(".NS",""), f"₹{price:.2f}", f"{change:.2f}%")
    col2.metric("Volume", "Normal")
    col3.metric("Size", f"₹{trade_size:.0f}")
    signal = "🟢 STRONG BUY" if change > 0.5 else "🔴 SELL" if change < -0.5 else "🟡 MONITOR"
    col4.write(f"**{signal}**")

    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size:.0f})", 
                 key=f"exec_{sym}", use_container_width=True, type="primary"):
        
        sl = round(price * (1 - 0.8/100), 2) if "BUY" in signal else round(price * (1 + 0.8/100), 2)
        target = round(price * (1 + 2.5/100), 2) if "BUY" in signal else round(price * (1 - 2.5/100), 2)

        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"✅ Trade Executed | SL ₹{sl} | Target ₹{target}")

        alert = f"<b>ProphetID TRADE</b>\nSymbol: {sym.replace('.NS','')}\nAction: {signal}\nSize: ₹{trade_size:.0f}\nSL: ₹{sl} | Target: ₹{target}"
        send_telegram(alert)

        if mode == "Zerodha Live" and kite:
            try:
                qty = max(1, int(trade_size / price))
                kite.place_order(variety=kite.VARIETY_BO, tradingsymbol=sym.replace(".NS",""), exchange=kite.EXCHANGE_NSE,
                                 transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                                 quantity=qty, product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET,
                                 squareoff=int(abs(target - price) * qty), stoploss=int(abs(price - sl) * qty))
                st.success("✅ Bracket Order Placed on Zerodha!")
            except Exception as e:
                st.error(f"Order Failed: {e}")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Win Days", st.session_state.portfolio['days_profitable'])

if st.button("🛑 Manual Square-off All"):
    square_off_all()

st.caption("ProphetID v5.7 | Stable for Monday Trading | Paper Mode Recommended First")
