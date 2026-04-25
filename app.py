import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os

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
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ITC.NS": "ITC",
    "LT.NS": "Larsen & Toubro",
    "KOTAKBANK.NS": "Kotak Bank",
    "AXISBANK.NS": "Axis Bank",
    "SUNPHARMA.NS": "Sun Pharma",
    "BAJFINANCE.NS": "Bajaj Finance",
    "TITAN.NS": "Titan",
    "NESTLEIND.NS": "Nestle India",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "ONGC.NS": "Oil & Natural Gas",
    "ADANIPORTS.NS": "Adani Ports"
}

@st.cache_data(ttl=3600, show_spinner=False)
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

st.subheader("Stock Prices")
results = []
with st.spinner("Loading stocks..."):
    for ticker in INDIAN_STOCKS.keys():
        r = get_stock(ticker)
        if r:
            results.append(r)

if results:
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
            col = st.container()
            with col:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.success(f"📈 {s['name']} - {s['rec'].upper()}")
                with c2:
                    if st.button("Alert", key=s["ticker"]):
                        if "tg_token" in st.session_state:
                            send_telegram(f"BUY: {s['name']} @ ₹{s['price']}", st.session_state.tg_token, st.session_state.tg_chat)
                            st.rerun()
else:
    st.warning("Could not load stock data. Please try again later.")

st.subheader("📰 Latest News")
name = st.selectbox("Select Stock", [v for v in INDIAN_STOCKS.values()])
try:
    import xml.etree.ElementTree as ET
    url = f"https://news.google.com/rss/search?q={name}+stock+NSE&hl=en-IN&gl=IN&ceid=IN/en"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    if r.ok:
        root = ET.fromstring(r.content)
        for item in list(root.findall('.//item'))[:5]:
            t = item.find('title')
            l = item.find('link')
            if t is not None and l is not None:
                st.markdown(f"**{t.text}**")
                st.markdown(f"[Read →]({l.text})")
except:
    st.info("No news available")