import gradio as gr
from scrapegraphai.graphs import SmartScraperGraph

def scrape_website(prompt, source_url, api_key):
    """Scrape website based on prompt and source URL"""
    if not prompt or not source_url or not api_key:
        return "Please provide all the required inputs."

    try:
        # Configuration for the scraping pipeline
        graph_config = {
            "llm": {
                "api_key": api_key,
                "model": "openai/gpt-4o-mini",
            },
            "verbose": True,
            "headless": False,
        }

        # Create the SmartScraperGraph instance
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=source_url,
            config=graph_config
        )

        # Run the pipeline
        result = smart_scraper_graph.run()

        return str(result)
    except Exception as e:
        return f"Error during scraping: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="AI Web Scraper", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Web Scraper")
    gr.Markdown("Extract information from websites using AI")

    with gr.Row():
        with gr.Column(scale=1):
            prompt = gr.Textbox(
                label="Information to Extract",
                placeholder="Enter the information you want to extract...",
                lines=3
            )

            source_url = gr.Textbox(
                label="Source URL",
                placeholder="https://example.com"
            )

            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )

            scrape_btn = gr.Button("Scrape", variant="primary")

        with gr.Column(scale=2):
            output = gr.Textbox(
                label="Scraped Result",
                lines=15,
                show_copy_button=True
            )

    gr.Markdown("""
    ### Instructions
    1. Enter the information you want to extract in the first input box.
    2. Enter the source URL from which you want to extract the information.
    3. Enter your OpenAI API key.
    4. Click on the "Scrape" button to start the scraping process.
    """)

    # Event handler
    scrape_btn.click(
        fn=scrape_website,
        inputs=[prompt, source_url, api_key],
        outputs=[output]
    )

if __name__ == "__main__":
    demo.launch()
