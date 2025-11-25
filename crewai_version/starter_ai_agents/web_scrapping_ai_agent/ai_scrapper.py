from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
import gradio as gr
from langchain_openai import ChatOpenAI

def scrape_website(openai_key, model, url, prompt):
    if not all([openai_key, url, prompt]):
        return "Please provide all required inputs"

    try:
        llm = ChatOpenAI(model=model, api_key=openai_key)
        scrape_tool = ScrapeWebsiteTool(website_url=url)

        scraper_agent = Agent(
            role="Web Scraping Expert",
            goal="Extract specific information from websites based on user requirements",
            backstory="""You are an expert at web scraping and data extraction.
            You can analyze web pages and extract exactly what the user needs.""",
            llm=llm,
            tools=[scrape_tool],
            verbose=True
        )

        task = Task(
            description=f"Scrape this website: {url}\n\nExtract: {prompt}",
            agent=scraper_agent,
            expected_output="Extracted information from the website"
        )

        crew = Crew(agents=[scraper_agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        return result.raw if hasattr(result, 'raw') else str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="Web Scraping AI Agent") as app:
        gr.Markdown("# Web Scraping AI Agent")
        gr.Markdown("This app allows you to scrape a website using OpenAI API")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )

                model_select = gr.Radio(
                    ["gpt-4o", "gpt-4o-mini"],
                    label="Select the model",
                    value="gpt-4o"
                )

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
            fn=scrape_website,
            inputs=[api_key, model_select, url_input, prompt_input],
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
