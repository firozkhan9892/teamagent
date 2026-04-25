import os
import yfinance as yf
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

kimi_llm = LLM(
    model="ollama/llama3",
    api_key="na",
    base_url="http://localhost:11434"
)

class StockDataTool:
    @staticmethod
    def get_stock_info(ticker: str):
        """Get stock info for Indian/NSE stocks using yfinance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "current_price": info.get("currentPrice", "N/A"),
                "target_mean": info.get("targetMeanPrice", "N/A"),
                "recommendation": info.get("recommendationKey", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("peRatio", "N/A"),
                "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52w_low": info.get("fiftyTwoWeekLow", "N/A")
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_trend(ticker: str):
        """Get price trend for a stock."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if len(hist) > 0:
                current = hist['Close'].iloc[-1]
                start = hist['Close'].iloc[0]
                change = ((current - start) / start) * 100
                return {"current": current, "3month_change": f"{change:.2f}%", "trend": "bullish" if change > 0 else "bearish"}
            return {"error": "No data available"}
        except Exception as e:
            return {"error": str(e)}

def create_research_agent():
    return Agent(
        role="Researcher",
        goal="Gather accurate stock data and financial information for Indian stocks",
        backstory="""You are an expert financial researcher with deep knowledge 
        of Indian stock market (NSE/BSE). You use yfinance to get real-time data.""",
        llm=kimi_llm,
        verbose=True
    )

def create_analyst_agent():
    return Agent(
        role="Analyst",
        goal="Analyze stock trends and patterns to identify investment opportunities",
        backstory="""You are a senior financial analyst specializing in Indian market 
        technical and fundamental analysis. You study price trends and patterns.""",
        llm=kimi_llm,
        verbose=True
    )

def create_advisor_agent():
    return Agent(
        role="Advisor",
        goal="Provide clear buy/sell recommendations based on research and analysis",
        backstory="""You are an experienced investment advisor with deep knowledge 
        of Indian equity markets. You provide actionable investment advice.""",
        llm=kimi_llm,
        verbose=True
    )

researcher = create_research_agent()
analyst = create_analyst_agent()
advisor = create_advisor_agent()

tasks = [
    Task(
        description="""Research Indian stocks (RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS).
        Get current price, market cap, PE ratio, and analyst recommendations.""",
        agent=researcher,
        expected_output="Stock data for major NSE stocks"
    ),
    Task(
        description="Analyze the stock data to identify trends and patterns",
        agent=analyst,
        expected_output="Trend analysis with bullish/bearish signals"
    ),
    Task(
        description="Provide final buy/sell recommendations for each stock",
        agent=advisor,
        expected_output="Clear investment recommendations"
    )
]

crew = Crew(
    agents=[researcher, analyst, advisor],
    tasks=tasks,
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff(inputs={"topic": "Indian Stock Market Analysis"})
    print("\n=== FINAL RESULT ===")
    print(result)