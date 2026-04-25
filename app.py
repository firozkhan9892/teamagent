import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Indian Stock Analyzer", page_icon="📈")

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

def send_telegram_message(message, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except:
        return False

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName", ticker),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "target_price": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("peRatio"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "ticker": ticker
        }
    except:
        return {"name": ticker, "error": "failed"}

def get_stock_news(name):
    try:
        url = f"https://news.google.com/rss/search?q={name}+stock+BSE&hl=en-IN&gl=IN&ceid=IN/en"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            items = []
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                items.append({"title": title, "link": link})
            return items
        return []
    except:
        return []

st.title("📈 Indian Stock Market Analyzer")
st.markdown("Real-time analysis of NSE stocks")

default_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip('"')
default_chat_id = os.getenv("CHAT_ID", "").strip().strip('"')

st.sidebar.header("📱 Telegram Notifications")
token = st.sidebar.text_input("Bot Token", value=default_token, type="password")
chat_id = st.sidebar.text_input("Chat ID", value=default_chat_id)

if token and chat_id:
    st.session_state.telegram_token = token
    st.session_state.telegram_chat_id = chat_id
    if st.sidebar.button("🔔 Test"):
        if send_telegram_message("✅ Bot working!", token, chat_id):
            st.sidebar.success("Sent!")
        else:
            st.sidebar.error("Failed")

col1, col2, col3 = st.columns(3)
st.metric("Stocks Tracked", len(INDIAN_STOCKS))

results = []
for ticker, name in INDIAN_STOCKS.items():
    data = get_stock_data(ticker)
    if "error" not in data:
        results.append(data)

buy_count = sum(1 for r in results if r.get("recommendation") in ["buy", "strongBuy"])
st.metric("Buy Signals", buy_count)

valid_pe = [r["pe_ratio"] for r in results if r.get("pe_ratio")]
avg_pe = sum(valid_pe) / len(valid_pe) if valid_pe else 0
st.metric("Avg P/E", f"{avg_pe:.1f}")

st.divider()
st.subheader("Stock Details")

df = pd.DataFrame(results)
df["market_cap"] = df["market_cap"].apply(lambda x: f"₹{x/1e12:.2f}T" if x else "N/A")
df["current_price"] = df["current_price"].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
df["target_price"] = df["target_price"].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
df["pe_ratio"] = df["pe_ratio"].apply(lambda x: f"{x:.2f}" if x else "N/A")

st.dataframe(df[["name", "current_price", "target_price", "recommendation", "pe_ratio", "market_cap"]], use_container_width=True)

st.divider()
st.subheader("Buy Recommendations")

buy_stocks = [r for r in results if r.get("recommendation") in ["buy", "strongBuy"]]
if buy_stocks:
    for stock in buy_stocks:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.success(f"✅ {stock['name']}: {stock['recommendation'].upper()}")
        with c2:
            if st.button("📤", key=stock["ticker"]):
                if "telegram_token" in st.session_state:
                    msg = f"📈 BUY ALERT\n\n{stock['name']}\nPrice: ₹{stock['current_price']}\nTarget: ₹{stock['target_price']}"
                    send_telegram_message(msg, st.session_state.telegram_token, st.session_state.telegram_chat_id)
                    st.success("Sent!")
else:
    st.info("No strong buy signals")

st.divider()
st.subheader("📰 Latest News")

stock_options = list(INDIAN_STOCKS.items())
selected = st.selectbox("Select stock", range(len(stock_options)), format_func=lambda i: stock_options[i][1])
selected_name = stock_options[selected][1]

news = get_stock_news(selected_name)
if news:
    for n in news:
        st.markdown(f"**{n['title']}**")
        st.markdown(f"[Read more]({n['link']})")
else:
    st.info("No news available")