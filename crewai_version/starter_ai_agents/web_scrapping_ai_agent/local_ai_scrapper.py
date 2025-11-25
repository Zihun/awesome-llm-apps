from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
import gradio as gr
from langchain_community.llms import Ollama

def scrape_website_local(url, prompt):
    if not all([url, prompt]):
        return "Please provide both URL and prompt"

    try:
        llm = Ollama(model="llama3.2")
        scrape_tool = ScrapeWebsiteTool(website_url=url)

        scraper_agent = Agent(
            role="Web Scraping Expert",
            goal="Extract specific information from websites using local Llama model",
            backstory="""You are an expert at web scraping and data extraction.""",
            llm=llm,
            tools=[scrape_tool],
            verbose=True
        )

        task = Task(
            description=f"Scrape this website: {url}\n\nExtract: {prompt}",
            agent=scraper_agent,
            expected_output="Extracted information"
        )

        crew = Crew(agents=[scraper_agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        return result.raw if hasattr(result, 'raw') else str(result)

    except Exception as e:
        return f"Error: {str(e)}\n\nMake sure Ollama is running with llama3.2 model installed."

def create_app():
    with gr.Blocks(title="Web Scraping AI Agent - Local") as app:
        gr.Markdown("# Web Scraping AI Agent")
        gr.Markdown("This app allows you to scrape a website using Llama 3.2 (local)")
        gr.Markdown("*Make sure Ollama is running with `ollama pull llama3.2`*")

        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(
                    label="Enter the URL of the website you want to scrape",
                    placeholder="https://example.com"
                )

                prompt_input = gr.Textbox(
                    label="What do you want the AI agent to scrape from the website?",
                    placeholder="Extract all product names and prices",
                    lines=3
                )

                scrape_btn = gr.Button("Scrape", variant="primary")

        with gr.Row():
            output = gr.Textbox(label="Scraped Result", lines=15)

        scrape_btn.click(
            fn=scrape_website_local,
            inputs=[url_input, prompt_input],
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
