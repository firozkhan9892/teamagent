import warnings
warnings.filterwarnings("ignore")

import os
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_STATISTICS"] = "false"

import sys
import traceback

try:
    import streamlit as st
    import yfinance as yf
    import pandas as pd
    import requests
except Exception as e:
    print(f"IMPORT FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

st.set_page_config(page_title="Stock Analyzer", page_icon="📈")

INDIAN_STOCKS = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "SBIN.NS": "SBI",
    "BHARTIARTL.NS": "Bharti Airtel",
    "WIPRO.NS": "Wipro",
}

@st.cache_data(ttl=3600)
def get_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName", ticker),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "target": info.get("targetMeanPrice"),
            "rec": info.get("recommendationKey"),
            "mcap": info.get("marketCap"),
            "pe": info.get("peRatio"),
            "ticker": ticker
        }
    except:
        return None

def send_telegram(msg, token, chat_id):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg}, timeout=5)
    except:
        pass

st.title("📈 Stock Market Analyzer")

with st.sidebar:
    st.header("Telegram Settings")
    token = st.text_input("Bot Token", value=os.getenv("TELEGRAM_BOT_TOKEN", ""), type="password")
    chat_id = st.text_input("Chat ID", value=os.getenv("CHAT_ID", ""))
    if token and chat_id:
        st.session_state.tg_token = token
        st.session_state.tg_chat = chat_id
        if st.button("Test Message"):
            send_telegram("✅ App connected!", token, chat_id)
            st.success("Sent!")

results = [r for r in [get_stock(t) for t in INDIAN_STOCKS.keys()] if r]

col1, col2 = st.columns(2)
col1.metric("Stocks", len(results))
col2.metric("Buy Signals", sum(1 for r in results if r.get("rec") in ["buy", "strongBuy"]))

df = pd.DataFrame(results)
df["price"] = df["price"].apply(lambda x: f"₹{x:.0f}" if x else "N/A")
df["target"] = df["target"].apply(lambda x: f"₹{x:.0f}" if x else "N/A")
df["pe"] = df["pe"].apply(lambda x: str(x) if x else "N/A")
df["mcap"] = df["mcap"].apply(lambda x: f"₹{x/1e12:.1f}T" if x else "N/A")
st.dataframe(df[["name", "price", "target", "rec", "pe", "mcap"]], use_container_width=True)

buys = [s for s in results if s.get("rec") in ["buy", "strongBuy"]]
if buys:
    st.subheader("Buy Recommendations")
    for s in buys:
        if st.button(f"📤 {s['name']}", key=s["ticker"]):
            if "tg_token" in st.session_state:
                send_telegram(f"BUY: {s['name']} @ ₹{s['price']}", st.session_state.tg_token, st.session_state.tg_chat)
                st.success("Sent!")