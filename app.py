import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import time
import plotly.graph_objects as go
from kiteconnect import KiteConnect

st.set_page_config(page_title="ProphetID", layout="wide")
st.title("🚀 ProphetID v5.1 - Two-Way Telegram Control")

# Secrets
telegram_token = st.secrets["telegram"]["bot_token"]
chat_id = st.secrets["telegram"]["chat_id"]

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                  json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})

def get_telegram_updates():
    try:
        r = requests.get(f"https://api.telegram.org/bot{telegram_token}/getUpdates")
        data = r.json()
        if data['ok'] and data['result']:
            return data['result'][-1]  # Latest message
        return None
    except:
        return None

# Check Commands Button
if st.sidebar.button("🔄 Check Telegram Commands Now"):
    update = get_telegram_updates()
    if update and 'message' in update:
        text = update['message']['text'].lower()
        if text == "/status":
            send_telegram(f"""<b>ProphetID Status</b>
Remaining Limit: ₹{st.session_state.portfolio.get('cash',10000)}
Today's P&L: ₹{st.session_state.portfolio.get('pnl',0):.2f}
Active Trades: {len(st.session_state.portfolio.get('trades',[]))}""")
            st.success("Status sent to Telegram!")
        elif text == "/scan":
            st.success("Running Scan...")
            # Trigger scan logic
        elif text == "/stop":
            send_telegram("🛑 Autonomous Trading Paused")
            st.warning("Autonomous mode paused")
        else:
            send_telegram("Unknown command. Use /status, /scan, /stop")
    else:
        st.info("No new commands found")

st.sidebar.info("Click 'Check Telegram Commands' after sending /status from Telegram")

# Rest of your app (sectors, execution, etc.)
# ... keep your existing scanner, execution, portfolio code here

send_telegram("✅ ProphetID Two-Way Commands Activated!")
st.success("Telegram bot is now ready for commands!")
