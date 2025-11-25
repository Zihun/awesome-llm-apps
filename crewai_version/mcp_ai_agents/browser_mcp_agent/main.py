import asyncio
import os
import gradio as gr
from textwrap import dedent
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
from crewai_tools import ScrapeWebsiteTool, SeleniumScrapingTool

# Global state
state = {
    "initialized": False,
    "browser_agent": None,
    "llm": None,
    "openai_api_key": None
}

def setup_agent(openai_api_key):
    """Setup the browser agent"""
    if state["initialized"] and state["openai_api_key"] == openai_api_key:
        return

    # Set up LLM
    llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

    # Initialize web scraping tools
    scrape_tool = ScrapeWebsiteTool()
    selenium_tool = SeleniumScrapingTool()

    # Create browser agent
    browser_agent = Agent(
        role="Web Browsing Assistant",
        goal="Navigate websites, extract information, and interact with web content",
        backstory=dedent("""You are a helpful web browsing assistant that can interact with websites.
            - Navigate to websites and perform browser actions
            - Extract information from web pages
            - Provide concise summaries of web content using markdown
            - Follow multi-step browsing sequences to complete tasks

        Respond back with a status update on completing the commands."""),
        llm=llm,
        tools=[scrape_tool, selenium_tool],
        verbose=True,
        allow_delegation=False
    )

    state["browser_agent"] = browser_agent
    state["llm"] = llm
    state["openai_api_key"] = openai_api_key
    state["initialized"] = True

async def run_browser_agent(query, openai_api_key):
    """Run the browser agent with the given query"""
    if not openai_api_key:
        return "Error: Please enter your OpenAI API key."

    try:
        # Setup agent
        setup_agent(openai_api_key)

        # Create task
        task = Task(
            description=query,
            expected_output="A detailed response with information from the web",
            agent=state["browser_agent"]
        )

        # Create and run crew
        crew = Crew(
            agents=[state["browser_agent"]],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def process_query(query, openai_api_key, progress=gr.Progress()):
    """Process browser query"""
    if not query:
        return "Please enter a command."

    progress(0.5, desc="Processing your request...")

    result = asyncio.run(run_browser_agent(query, openai_api_key))

    progress(1.0, desc="Complete!")

    return result

# Create Gradio interface
with gr.Blocks(title="Browser Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🌐 Browser Agent")
    gr.Markdown("Interact with a powerful web browsing agent that can navigate and extract information from websites")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🔑 API Configuration")
            openai_api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )

            gr.Markdown("### Your Command")
            query = gr.Textbox(
                label="Command",
                placeholder="Ask the agent to navigate to websites and extract information",
                lines=3
            )

            run_btn = gr.Button("🚀 Run Command", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### Example Commands")
            gr.Markdown("**Navigation**")
            gr.Markdown("- Go to github.com/Shubhamsaboo/awesome-llm-apps")

            gr.Markdown("**Information Extraction**")
            gr.Markdown("- Extract the main content from example.com")
            gr.Markdown("- Summarize the content from a URL")

            gr.Markdown("**Multi-step Tasks**")
            gr.Markdown("- Navigate to a URL and summarize the readme")
            gr.Markdown("- Extract specific information from a webpage")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Response")
            response_output = gr.Textbox(label="Agent Response", lines=15, max_lines=25)

    run_btn.click(
        fn=process_query,
        inputs=[query, openai_api_key],
        outputs=[response_output]
    )

    gr.Markdown("---")
    gr.Markdown("""
    <div style='padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
    <h4>How to use this app:</h4>
    <ol>
        <li>Enter your OpenAI API key</li>
        <li>Type a command for the agent to navigate and extract information from websites</li>
        <li>Click 'Run Command' to see results</li>
    </ol>
    <p><strong>Capabilities:</strong></p>
    <ul>
        <li>Navigate to websites</li>
        <li>Extract information from web pages</li>
        <li>Perform multi-step browsing tasks</li>
        <li>Summarize web content</li>
    </ul>
    </div>
    """)

    gr.Markdown("---")
    gr.Markdown("Built with Gradio and CrewAI ❤️")

if __name__ == "__main__":
    demo.launch(share=False)
