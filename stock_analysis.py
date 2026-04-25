import yfinance as yf

INDIAN_STOCKS = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "SBIN.NS": "SBI",
    "BHARTIARTL.NS": "Bharti Airtel",
    "WIPRO.NS": "Wipro"
}

def get_stock_data(ticker):
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
        "52w_low": info.get("fiftyTwoWeekLow")
    }

def main():
    print("=" * 60)
    print("INDIAN STOCK MARKET ANALYSIS")
    print("=" * 60)
    
    results = []
    for ticker, name in INDIAN_STOCKS.items():
        try:
            data = get_stock_data(ticker)
            results.append((name, data))
            print(f"\n{name} ({ticker})")
            print(f"  Price: Rs. {data['current_price']}")
            print(f"  Target: Rs. {data['target_price']}")
            print(f"  Rec: {data['recommendation']}")
            print(f"  P/E: {data['pe_ratio']}")
            print(f"  52W: {data['52w_low']} - {data['52w_high']}")
        except Exception as e:
            print(f"\n{name}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("BUY/SELL RECOMMENDATIONS")
    print("=" * 60)
    
    buy_recs = []
    for name, data in results:
        rec = data["recommendation"]
        if rec == "buy":
            buy_recs.append(f"BUY {name}")
        elif rec == "strongBuy":
            buy_recs.append(f"STRONG BUY {name}")
    
    if buy_recs:
        for r in buy_recs:
            print(r)
    else:
        print("No strong buy signals currently")

if __name__ == "__main__":
    main()