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
        requests.post(url, data=data)
        return True
    except Exception as e:
        return False

def init_telegram():
    st.sidebar.header("📱 Telegram Notifications")
    
    default_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip('"')
    default_chat_id = os.getenv("CHAT_ID", "").strip().strip('"')
    
    token = st.sidebar.text_input("Bot Token", value=default_token, type="password", placeholder="123456:ABC-DEF...")
    chat_id = st.sidebar.text_input("Chat ID", value=default_chat_id, placeholder="123456789")
    
    if token and chat_id:
        st.session_state.telegram_token = token
        st.session_state.telegram_chat_id = chat_id
        if st.sidebar.button("🔔 Test Notification"):
            if send_telegram_message("✅ Stock Alert: Bot is working!", token, chat_id):
                st.sidebar.success("Message sent!")
            else:
                st.sidebar.error("Failed to send")
    else:
        st.sidebar.info("Add Telegram bot token & chat ID to enable alerts")

def get_stock_news(ticker, name):
    try:
        import time
        url = f"https://news.google.com/rss/search?q={name}+stock+BSE&hl=en-IN&gl=IN&ceid=IN/en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
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
    except Exception as e:
        return []

@st.cache_data(ttl=300)
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
    except Exception as e:
        return {"error": str(e)}

st.title("📈 Indian Stock Market Analyzer")
st.markdown("Real-time analysis of NSE stocks")

init_telegram()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Stocks Tracked", len(INDIAN_STOCKS))

results = []
for ticker, name in INDIAN_STOCKS.items():
    data = get_stock_data(ticker)
    if "error" not in data:
        results.append(data)

with col2:
    buy_count = sum(1 for r in results if r["recommendation"] in ["buy", "strongBuy"])
    st.metric("Buy Signals", buy_count)

with col3:
    avg_pe = sum(r["pe_ratio"] for r in results if r["pe_ratio"]) / len([r for r in results if r["pe_ratio"]]) if any(r["pe_ratio"] for r in results) else 0
    st.metric("Avg P/E Ratio", f"{avg_pe:.1f}")

st.divider()

st.subheader("Stock Details")
df = pd.DataFrame(results)
df["market_cap"] = df["market_cap"].apply(lambda x: f"₹{x/1e12:.2f}T" if x else "N/A")
df["current_price"] = df["current_price"].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
df["target_price"] = df["target_price"].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
df["pe_ratio"] = df["pe_ratio"].apply(lambda x: f"{x:.2f}" if x else "N/A")
df["52w_high"] = df["52w_high"].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
df["52w_low"] = df["52w_low"].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
st.dataframe(df[["name", "current_price", "target_price", "recommendation", "pe_ratio", "market_cap"]], use_container_width=True)

st.divider()
st.subheader("Buy Recommendations")

buy_stocks = [r for r in results if r["recommendation"] in ["buy", "strongBuy"]]
if buy_stocks:
    for stock in buy_stocks:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.success(f"✅ {stock['name']}: {stock['recommendation'].upper()} (Target: ₹{stock['target_price']:.2f})")
        with col2:
            if st.button(f"📤 Alert", key=stock["ticker"]):
                if "telegram_token" in st.session_state:
                    msg = f"📈 *BUY ALERT*\n\n*{stock['name']}*\nPrice: ₹{stock['current_price']:.2f}\nTarget: ₹{stock['target_price']:.2f}\nRecommendation: {stock['recommendation'].upper()}"
                    if send_telegram_message(msg, st.session_state.telegram_token, st.session_state.telegram_chat_id):
                        st.success("Sent to Telegram!")
                    else:
                        st.error("Failed to send")
                else:
                    st.warning("Configure Telegram in sidebar")
else:
    st.info("No strong buy signals at the moment")

st.divider()
st.subheader("📰 Latest News")

stock_options = list(INDIAN_STOCKS.items())
selected = st.selectbox("Select stock for news", range(len(stock_options)), format_func=lambda i: stock_options[i][1])
selected_ticker = stock_options[selected][0]
selected_name = stock_options[selected][1]

news = get_stock_news(selected_ticker, selected_name)
if news:
    for n in news:
        st.markdown(f"**{n['title']}**")
        st.markdown(f"[Read more →]({n['link']})")
else:
    st.info("No recent news available")

st.divider()
st.subheader("Quick Alert")
alert_stock = st.selectbox("Select Stock", [f"{r['name']} ({r['ticker']})" for r in results])
qty = st.number_input("Quantity", min_value=1, value=10)
alert_msg = st.text_area("Custom Message", f"I want to buy {alert_stock.split('(')[0]} - {qty} shares")
if st.button("📤 Send Alert"):
    if "telegram_token" in st.session_state:
        msg = f"📊 *STOCK ALERT*\n\n{alert_msg}"
        if send_telegram_message(msg, st.session_state.telegram_token, st.session_state.telegram_chat_id):
            st.success("Sent to Telegram!")
        else:
            st.error("Failed to send")
    else:
        st.warning("Configure Telegram in sidebar first")