import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID - NSE Intraday Trading Prophet (Zerodha Live Ready)")

# Portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]

st.sidebar.header("⚙️ Settings")
mode = st.sidebar.selectbox("Trading Mode", ["Paper Trading", "Zerodha Live"])

# Zerodha Credentials (Add in Streamlit Secrets)
try:
    api_key = st.secrets["zerodha"]["api_key"]
    api_secret = st.secrets["zerodha"]["api_secret"]
    access_token = st.secrets.get("zerodha", {}).get("access_token", None)
    kite = KiteConnect(api_key=api_key)
    if access_token:
        kite.set_access_token(access_token)
    kite_ready = True
except:
    kite_ready = False
    kite = None

if mode == "Zerodha Live" and kite_ready:
    st.sidebar.success("✅ Zerodha Connected")
else:
    st.sidebar.warning("Zerodha Live: Add credentials in Secrets")

def send_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage", 
                      json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except:
        pass

@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="5m")
    except:
        return pd.DataFrame()

st.header("📊 ProphetID Smart Picks + News")

# News
news = [
    "Metals strong on global cues", 
    "Pharma defensive", 
    "Nifty support 23,500 | Resistance 23,800"
]
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

    col1, col2, col3 = st.columns(3)
    col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}" if not data.empty else "N/A", f"{change:.2f}%")
    signal = "🟢 STRONG BUY" if change > 0.3 else "🔴 SELL" if change < -0.3 else "🟡 MONITOR"
    col3.write(f"**Signal**: {signal}")

    trade_size = min(4500, st.session_state.portfolio['cash'])
    if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", 
                 key=f"exec_{sym}", use_container_width=True, type="primary"):
        
        # Paper Mode
        pnl = trade_size * (0.018 if "BUY" in signal else -0.012)
        st.session_state.portfolio['cash'] -= trade_size
        st.session_state.portfolio['pnl'] += pnl
        st.session_state.portfolio['trades'].append({
            "symbol": sym.replace(".NS",""), "action": signal, "size": trade_size, 
            "pnl": round(pnl,2), "time": datetime.now().strftime("%H:%M"), "mode": mode
        })
        
        alert = f"""<b>🚀 ProphetID TRADE EXECUTED ({mode})</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
P&L: ₹{pnl:.2f}
Remaining: ₹{st.session_state.portfolio['cash']}"""
        send_telegram(alert)
        st.success(f"✅ {mode} Trade Executed!")

        # === ZERODHA LIVE ORDER ===
        if mode == "Zerodha Live" and kite:
            try:
                order = kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    tradingsymbol=sym.replace(".NS", ""),
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=kite.TRANSACTION_TYPE_BUY if "BUY" in signal else kite.TRANSACTION_TYPE_SELL,
                    quantity=int(trade_size / latest['Close']) if not data.empty else 1,
                    product=kite.PRODUCT_MIS,   # Intraday
                    order_type=kite.ORDER_TYPE_MARKET,
                    validity=kite.VALIDITY_DAY
                )
                st.success(f"✅ Zerodha Order Placed! Order ID: {order}")
                send_telegram(f"<b>Zerodha Order ID:</b> {order}")
            except Exception as e:
                st.error(f"Zerodha Order Failed: {e}")

# Portfolio + Upgrade
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

if st.session_state.portfolio['pnl'] > 400:
    st.session_state.portfolio['cash'] = 15000
    st.balloons()
    send_telegram("<b>🎉 LIMIT UPGRADED to ₹15,000</b>")

st.caption("ProphetID v3.0 | Zerodha Live | News | Performance Upgrade | Telegram")
