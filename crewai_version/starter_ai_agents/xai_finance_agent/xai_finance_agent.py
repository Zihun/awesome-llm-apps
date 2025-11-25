from crewai import Agent, Task, Crew
import gradio as gr
from langchain_community.llms import OpenAI
import yfinance as yf
from langchain_community.tools import DuckDuckGoSearchRun

def get_stock_data(symbol):
    """Get stock price and fundamentals"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")

        data = {
            "symbol": symbol,
            "current_price": hist['Close'].iloc[-1] if not hist.empty else "N/A",
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "analyst_recommendations": info.get('recommendationKey', 'N/A')
        }
        return str(data)
    except Exception as e:
        return f"Error fetching data: {str(e)}"

def analyze_finance(xai_api_key, query):
    if not xai_api_key or not query:
        return "Please provide both API key and query"

    try:
        # Use OpenAI-compatible endpoint for xAI
        llm = OpenAI(
            model="grok-beta",
            openai_api_key=xai_api_key,
            openai_api_base="https://api.x.ai/v1"
        )

        # Initialize tools
        search_tool = DuckDuckGoSearchRun()

        # Create finance agent
        agent = Agent(
            role="xAI Finance Agent",
            goal="Provide comprehensive financial analysis and stock insights",
            backstory="""You are an expert financial analyst with deep knowledge of
            markets, stocks, and financial instruments. You always use tables to display
            financial/numerical data and bullet points for text analysis.""",
            llm=llm,
            verbose=True
        )

        # Check if query mentions specific stocks
        stock_data = ""
        common_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA"]
        for symbol in common_symbols:
            if symbol.lower() in query.lower():
                stock_data += f"\n\nStock Data for {symbol}:\n{get_stock_data(symbol)}"

        # Create task
        task = Task(
            description=f"""Analyze this financial query: {query}

            {stock_data if stock_data else ''}

            Use web search if needed for latest information. Present data in tables
            and use bullet points for analysis. Always use tables to display
            financial/numerical data.""",
            agent=agent,
            expected_output="Comprehensive financial analysis with tables and bullet points"
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        return result.raw if hasattr(result, 'raw') else str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="xAI Finance Agent") as app:
        gr.Markdown("# xAI Finance Agent")
        gr.Markdown("Get financial analysis powered by xAI Grok")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="xAI API Key",
                    type="password",
                    placeholder="Enter your xAI API Key"
                )
                query = gr.Textbox(
                    label="Financial Query",
                    placeholder="What is the current price of AAPL? Analyze its fundamentals.",
                    lines=3
                )
                analyze_btn = gr.Button("Analyze", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="Analysis Result")

        analyze_btn.click(
            fn=analyze_finance,
            inputs=[api_key, query],
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
