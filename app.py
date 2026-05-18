import streamlit as st
from datetime import datetime
import requests
from kiteconnect import KiteConnect
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - Zerodha Live Version")

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("Zerodha Controls")
mode = st.sidebar.selectbox("Mode", ["Paper Trading", "Zerodha Live"])

kite = None
if mode == "Zerodha Live" and access_token:
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        st.sidebar.success("✅ Connected to Zerodha Live")
    except:
        st.sidebar.error("Zerodha connection failed")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

st.header("📊 Live Intraday Scanner (Zerodha Mode)")

# High Liquidity Stocks
symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", 
           "BHARTIARTL.NS", "TATAMOTORS.NS", "HINDALCO.NS", "DRREDDY.NS"]

for sym in symbols:
    data = yf.download(sym, period="1d", interval="5m", progress=False)
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    if not data.empty:
        latest = data.iloc[-1]
        price = float(latest['Close'])
        change = (price - float(data.iloc[0]['Close'])) / float(data.iloc[0]['Close']) * 100 if len(data) > 1 else 0.0
    else:
        price = 0.0
        change = 0.0

    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])]) if not data.empty else go.Figure()
    fig.update_layout(height=300, title=f"{sym} Live Chart")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"₹{price:.2f}", f"{change:.2f}%")
    col2.metric("Suggested Size", "₹4,500")
    signal = "🟢 BUY" if change > 0.3 else "🔴 SELL" if change < -0.3 else "HOLD"
    col3.write(f"**{signal}**")

    if st.button(f"🚀 EXECUTE {signal} {sym.replace('.NS','')} ₹4500", key=sym):
        if mode == "Zerodha Live" and kite:
            try:
                qty = 10  # Safe small quantity for testing
                order_id = kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    tradingsymbol=sym.replace(".NS",""),
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                    quantity=qty,
                    product=kite.PRODUCT_MIS,
                    order_type=kite.ORDER_TYPE_MARKET
                )
                st.success(f"✅ Real Order Placed on Zerodha! Order ID: {order_id}")
                send_telegram(f"Real Trade Executed\nSymbol: {sym.replace('.NS','')}\nOrder ID: {order_id}")
            except Exception as e:
                st.error(f"Zerodha Order Failed: {e}")
        else:
            st.success("Paper Trade Executed (₹4500)")
            send_telegram(f"Paper Trade: {signal} {sym.replace('.NS','')} ₹4500")

st.header("💰 Portfolio")
st.metric("Remaining Cash", f"₹{st.session_state.portfolio['cash']}")

st.caption("Zerodha Live Mode | Use Paper Trading first | Auto Square-off ready")
