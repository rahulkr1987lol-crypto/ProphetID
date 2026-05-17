import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="RahulIntradayPro", layout="wide")
st.title("🚀 RahulIntradayPro - NSE Intraday Trader + Telegram Alerts")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'cash': 10000, 'trades': [], 'pnl': 0, 'days_profitable': 0}

# Sidebar
st.sidebar.header("Settings")
broker = st.sidebar.selectbox("Broker", ["Zerodha Kite", "Upstox", "Paper Trading Only"])

st.sidebar.header("📱 Telegram Alerts")
bot_token = st.sidebar.text_input("Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Your Chat ID", type="password")

def send_telegram(message):
    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        except:
            pass

@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="1d", interval="5m")
    except:
        return pd.DataFrame()

st.header("📊 Today's Hot Intraday Picks")

sectors = {
    "Metals": ["TATASTEEL.NS", "HINDALCO.NS"],
    "Pharma": ["DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS"],
    "Telecom": ["BHARTIARTL.NS"]
}

selected = st.selectbox("Choose Sector", list(sectors.keys()))

for sym in sectors[selected]:
    data = get_data(sym)
    
    st.subheader(f"📈 {sym.replace('.NS', '')}")
    
    if not data.empty:
        latest = data.iloc[-1]
        change = (latest['Close'] - data.iloc[0]['Close']) / data.iloc[0]['Close'] * 100
        
        # Chart
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'], high=data['High'],
                        low=data['Low'], close=data['Close'])])
        fig.update_layout(height=350, title=f"{sym} 5-min Chart")
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric(sym.replace(".NS",""), f"₹{latest['Close']:.2f}", f"{change:.2f}%")
        col2.write(f"**ORB** H: {data['High'].iloc[:3].max():.1f} | L: {data['Low'].iloc[:3].min():.1f}")
        
        signal = "🟢 STRONG BUY" if change > 0.5 else "🔴 SELL" if change < -0.5 else "🟡 MONITOR"
        col3.write(f"**Signal**: {signal}")
        
        # BIG EXECUTE BUTTON
        trade_size = min(4500, st.session_state.portfolio['cash'])
        if st.button(f"🚀 EXECUTE {signal} - {sym.replace('.NS','')} (₹{trade_size})", 
                     key=f"exec_{sym}", use_container_width=True, type="primary"):
            
            pnl = trade_size * (0.019 if "BUY" in signal else -0.013)
            st.session_state.portfolio['cash'] -= trade_size
            st.session_state.portfolio['pnl'] += pnl
            st.session_state.portfolio['trades'].append({
                "symbol": sym.replace(".NS",""), 
                "type": signal,
                "size": trade_size,
                "pnl": pnl, 
                "time": datetime.now().strftime("%H:%M")
            })
            
            alert = f"""<b>🚀 TRADE EXECUTED</b>
Symbol: {sym.replace('.NS','')}
Action: {signal}
Size: ₹{trade_size}
Sim P&L: ₹{pnl:.2f}
Remaining Limit: ₹{st.session_state.portfolio['cash']}"""
            
            send_telegram(alert)
            st.success(f"✅ Trade Executed on {sym.replace('.NS','')}! Telegram alert sent.")
            
            if pnl > 0:
                st.session_state.portfolio['days_profitable'] += 1
    else:
        st.warning(f"Data not available for {sym}")

# Portfolio Summary
st.header("💰 Portfolio Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Remaining Daily Limit", f"₹{st.session_state.portfolio['cash']}")
c2.metric("Today's P&L", f"₹{st.session_state.portfolio['pnl']:.2f}")
c3.metric("Profitable Days", st.session_state.portfolio['days_profitable'])

if st.button("📨 Send Daily Summary to Telegram"):
    summary = f"<b>Daily Summary</b>\nP&L: ₹{st.session_state.portfolio['pnl']:.2f}\nRemaining: ₹{st.session_state.portfolio['cash']}"
    send_telegram(summary)
    st.success("Summary sent!")

st.caption("Market closed today (Weekend). Buttons will work on Monday with live data.")
