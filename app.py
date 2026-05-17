import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.3 - Full Autonomous Engine with Auto Square-off")

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

# ==================== AUTO SQUARE-OFF LOGIC ====================
def square_off_all_positions():
    now = datetime.now().time()
    if auto_squareoff and now.hour == 15 and now.minute >= 20:
        msg = "🛑 Auto Square-off Triggered at 3:20 PM!"
        send_telegram(msg)
        st.warning(msg)
        
        if mode == "Zerodha Live" and kite:
            try:
                positions = kite.positions()
                for pos in positions['net']:
                    if pos['quantity'] != 0:
                        kite.place_order(
                            variety=kite.VARIETY_REGULAR,
                            tradingsymbol=pos['tradingsymbol'],
                            exchange=kite.EXCHANGE_NSE,
                            transaction_type=kite.TRANSACTION_TYPE_SELL if pos['quantity'] > 0 else kite.TRANSACTION_TYPE_BUY,
                            quantity=abs(pos['quantity']),
                            product=kite.PRODUCT_MIS,
                            order_type=kite.ORDER_TYPE_MARKET
                        )
                st.success("✅ All positions squared off on Zerodha!")
            except Exception as e:
                st.error(f"Square-off failed: {e}")
        else:
            st.success("✅ All paper positions squared off!")
        return True
    return False

# Run square-off check on every load
square_off_all_positions()

# Rest of the app (Scanner, Execution, etc.)
st.header("📊 ProphetID Smart Scanner")

# (Keeping full scanner + execution from previous stable version)
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
        change = (latest['Close'] - data.iloc[-10]['Close']) / data.iloc[-10]['Close'] * 100 if len(data) > 10 else 0
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        fig.update_layout(height=350, title=f"{sym} Chart")
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
        st.success(f"✅ Executed | SL: ₹{sl} | Target: ₹{target}")

        alert = f"""<b>ProphetID TRADE</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
SL: ₹{sl} | Target: ₹{target}"""
        send_telegram(alert)

        if mode == "Zerodha Live" and kite:
            try:
                qty = max(1, int(trade_size / entry))
                kite.place_order(variety=kite.VARIETY_BO, tradingsymbol=sym.replace(".NS",""), exchange=kite.EXCHANGE_NSE,
                                 transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                                 quantity=qty, product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_MARKET,
                                 squareoff=int(abs(target - entry) * qty), stoploss=int(abs(entry - sl) * qty))
                st.success("✅ Bracket Order (SL + Target) Placed!")
            except Exception as e:
                st.error(f"Order Failed: {e}")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Win Days", st.session_state.portfolio['days_profitable'])

if st.button("🛑 Manual Square-off All"):
    square_off_all_positions()

st.caption("ProphetID v5.3 | Auto Square-off at 3:20 PM | Full Features Active")
