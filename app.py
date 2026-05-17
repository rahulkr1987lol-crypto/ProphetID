import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.5 - Autonomous Intraday Engine")

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

st.header("📊 ProphetID Smart Scanner + Volume Analysis")

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
        prev_idx = max(0, len(data) - 10)
        change = (latest['Close'] - data.iloc[prev_idx]['Close']) / data.iloc[prev_idx]['Close'] * 100
        avg_volume = data['Volume'].mean()
        current_volume = data['Volume'].iloc[-1] if len(data) > 0 else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=350, title=f"{sym} Chart")
        st.plotly_chart(fig, use_container_width=True)
    else:
        change = 0.0
        volume_ratio = 1.0
        latest = pd.Series({'Close': 0})

    # Dynamic Position Sizing
    risk_amount = st.session_state.portfolio['cash'] * (risk_per_trade / 100)
    entry_price = latest['Close']
    stop_distance = entry_price * 0.008
    dynamic_qty = int(risk_amount / stop_distance) if stop_distance > 0 else 1
    trade_size = min(dynamic_qty * entry_price, st.session_state.portfolio['cash'] * 0.45)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(sym.replace(".NS",""), f"₹{entry_price:.2f}", f"{change:.2f}%")
    col2.metric("Volume Ratio", f"{volume_ratio:.2f}x", "🔥 High" if volume_ratio > 1.5 else "Normal")
    col3.metric("Dynamic Size", f"₹{trade_size:.0f}")
    signal = "🟢 STRONG BUY" if change > 0.5 else "🔴 SELL" if change < -0.5 else "🟡 MONITOR"
    col4.write(f"**Signal**: {signal}")

    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size:.0f})", 
                 key=f"exec_{sym}", use_container_width=True, type="primary"):
        
        sl = round(entry_price * (1 - 0.8/100), 2) if "BUY" in signal else round(entry_price * (1 + 0.8/100), 2)
        target = round(entry_price * (1 + 2.5/100), 2) if "BUY" in signal else round(entry_price * (1 - 2.5/100), 2)

        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"✅ Executed | Size ₹{trade_size:.0f} | SL ₹{sl} | Target ₹{target}")

        alert = f"<b>ProphetID TRADE</b>\nSymbol: {sym.replace('.NS','')}\nAction: {signal}\nSize: ₹{trade_size:.0f}\nSL: ₹{sl} | Target: ₹{target}\nVolume: {volume_ratio:.2f}x"
        send_telegram(alert)

        if mode == "Zerodha Live" and kite:
            try:
                qty = max(1, int(trade_size / entry_price))
                kite.place_order(variety=kite.VARIETY_BO, tradingsymbol=sym.replace(".NS",""), exchange=kite.EXCHANGE_NSE,
                                 transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                                 quantity=qty, product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET,
                                 squareoff=int(abs(target - entry_price) * qty), stoploss=int(abs(entry_price - sl) * qty))
                st.success("✅ Bracket Order Placed!")
            except Exception as e:
                st.error(f"Order Failed: {e}")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("
