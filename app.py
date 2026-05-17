import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet with Stop Loss & Target")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]
api_key = st.secrets["zerodha"]["api_key"]
api_secret = st.secrets["zerodha"].get("api_secret", "")
access_token = st.secrets["zerodha"].get("access_token", None)

st.sidebar.header("⚙️ Risk Settings")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])
sl_percent = st.sidebar.slider("Stop Loss %", 0.5, 2.0, 0.8, 0.1)
target_percent = st.sidebar.slider("Target %", 1.0, 4.0, 1.8, 0.1)

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

# Login Helper (keep if needed)
if st.sidebar.button("🔑 Generate Access Token"):
    login_url = f"https://kite.trade/connect/login?api_key={api_key}&v=3"
    st.sidebar.markdown(f"[Login on Zerodha]({login_url})")

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

    trade_size = min(4500, st.session_state.portfolio['cash'])
    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", 
                 key=f"exec_{sym}", use_container_width=True, type="primary"):
        
        if data.empty:
            st.error("No price data")
            continue
            
        entry_price = latest['Close']
        sl_price = round(entry_price * (1 - sl_percent/100), 2) if "BUY" in signal else round(entry_price * (1 + sl_percent/100), 2)
        target_price = round(entry_price * (1 + target_percent/100), 2) if "BUY" in signal else round(entry_price * (1 - target_percent/100), 2)
        
        # Record Trade
        st.session_state.portfolio['cash'] -= trade_size
        st.success(f"✅ Order Placed | SL: ₹{sl_price} | Target: ₹{target_price}")

        alert = f"""<b>🚀 ProphetID TRADE + SL</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
Entry: ₹{entry_price:.2f}
SL: ₹{sl_price} ({sl_percent}%)
Target: ₹{target_price} ({target_percent}%)"""
        send_telegram(alert)

        # Real Zerodha Bracket Order (Entry + SL + Target)
        if mode == "Zerodha Live" and kite:
            try:
                qty = max(1, int(trade_size / entry_price))
                kite.place_order(
                    variety=kite.VARIETY_BO,
                    tradingsymbol=sym.replace(".NS", ""),
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                    quantity=qty,
                    product=kite.PRODUCT_MIS,
                    order_type=kite.ORDER_TYPE_MARKET,
                    squareoff=int((target_price - entry_price) * qty) if "BUY" in signal else int((entry_price - target_price) * qty),
                    stoploss=int((entry_price - sl_price) * qty) if "BUY" in signal else int((sl_price - entry_price) * qty),
                    trailing_stoploss=0
                )
                st.success("✅ Bracket Order (Entry + SL + Target) Placed on Zerodha!")
            except Exception as e:
                st.error(f"Order Failed: {e}")

# Portfolio
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

st.caption("ProphetID with Stop Loss & Target | Test in Paper Mode First")
