from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
import gradio as gr
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

def analyze_trends(api_key, topic):
    if not api_key or not topic:
        return "Please provide API key and topic"

    try:
        genai.configure(api_key=api_key)
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=api_key)

        search_tool = SerperDevTool()
        scrape_tool = ScrapeWebsiteTool()

        # News Collector Agent
        news_collector = Agent(
            role="News Collector",
            goal="Collect recent news articles on the given topic",
            backstory="You are a skilled researcher who finds the latest and most relevant news articles.",
            tools=[search_tool],
            llm=llm,
            verbose=True
        )

        # Summary Writer Agent
        summary_writer = Agent(
            role="Summary Writer",
            goal="Summarize collected news articles",
            backstory="You are an expert at distilling key information from articles into concise summaries.",
            tools=[scrape_tool],
            llm=llm,
            verbose=True
        )

        # Trend Analyzer Agent
        trend_analyzer = Agent(
            role="Trend Analyzer",
            goal="Analyze trends and identify startup opportunities",
            backstory="You are a trend analyst who identifies emerging patterns and startup opportunities from news summaries.",
            llm=llm,
            verbose=True
        )

        # Tasks
        collect_task = Task(
            description=f"Collect recent news articles on {topic}",
            agent=news_collector,
            expected_output="List of relevant news articles"
        )

        summarize_task = Task(
            description="Summarize the collected articles",
            agent=summary_writer,
            expected_output="Concise summaries of articles",
            context=[collect_task]
        )

        analyze_task = Task(
            description="Analyze trends and identify startup opportunities",
            agent=trend_analyzer,
            expected_output="Trend analysis with startup opportunities",
            context=[summarize_task]
        )

        # Create crew
        crew = Crew(
            agents=[news_collector, summary_writer, trend_analyzer],
            tasks=[collect_task, summarize_task, analyze_task],
            verbose=True
        )

        result = crew.kickoff()
        return result.raw if hasattr(result, 'raw') else str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="AI Startup Trend Analysis Agent") as app:
        gr.Markdown("# AI Startup Trend Analysis Agent")
        gr.Markdown("Get the latest trend analysis and startup opportunities based on your topic of interest in a click!")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="Google API Key",
                    type="password",
                    placeholder="Enter your Google API Key"
                )

                topic = gr.Textbox(
                    label="Enter the area of interest for your Startup",
                    placeholder="e.g., AI in healthcare",
                    lines=2
                )

                analyze_btn = gr.Button("Generate Analysis", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="Trend Analysis and Potential Startup Opportunities")

        analyze_btn.click(
            fn=analyze_trends,
            inputs=[api_key, topic],
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
