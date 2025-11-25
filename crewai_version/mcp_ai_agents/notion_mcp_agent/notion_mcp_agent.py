import asyncio
import os
import uuid
from textwrap import dedent
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
import gradio as gr
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Global state
state = {
    "initialized": False,
    "agent": None,
    "llm": None,
    "notion_api_key": None,
    "page_id": None,
    "conversation_history": []
}

class NotionTool:
    """Simple Notion API wrapper for basic operations"""

    def __init__(self, api_key: str, page_id: str):
        self.api_key = api_key
        self.page_id = page_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def read_page(self):
        """Read page content"""
        try:
            url = f"https://api.notion.com/v1/pages/{self.page_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def search_pages(self, query: str):
        """Search for pages"""
        try:
            url = "https://api.notion.com/v1/search"
            data = {"query": query, "filter": {"property": "object", "value": "page"}}
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_blocks(self):
        """Get blocks from page"""
        try:
            url = f"https://api.notion.com/v1/blocks/{self.page_id}/children"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def setup_agent(openai_api_key, notion_api_key, page_id):
    """Setup the Notion agent"""
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = openai_api_key

    # Set up LLM
    llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

    # Generate unique user and session IDs
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    # Create the Notion agent
    agent = Agent(
        role="Notion Assistant",
        goal="Help users interact with their Notion pages",
        backstory=dedent(f"""
            You are an expert Notion assistant that helps users interact with their Notion pages.

            IMPORTANT INSTRUCTIONS:
            1. You can help users read and understand their Notion documents.
            2. You work with page ID: {page_id}
            3. When asked to read or search pages, provide helpful information.
            4. Be proactive in explaining what information is available.
            5. Provide clear summaries of content.
            6. If you need to perform an operation, explain what you would do.

            Example tasks you can help with:
            - Understanding page content
            - Explaining page structure
            - Searching for information
            - Summarizing content
            - Providing insights about the page

            The user's current page ID is: {page_id}

            SESSION INFO:
            • User ID: {user_id}
            • Session ID: {session_id}
        """),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    state["agent"] = agent
    state["llm"] = llm
    state["notion_api_key"] = notion_api_key
    state["page_id"] = page_id
    state["initialized"] = True

async def run_notion_agent(message, openai_api_key, notion_api_key, page_id):
    """Run the Notion agent"""
    if not all([openai_api_key, notion_api_key, page_id]):
        return "Error: Please provide all required credentials."

    try:
        # Setup agent
        setup_agent(openai_api_key, notion_api_key, page_id)

        # Create Notion tool instance
        notion_tool = NotionTool(notion_api_key, page_id)

        # Get page information
        page_info = notion_tool.read_page()
        blocks_info = notion_tool.get_blocks()

        # Enhance message with page context
        enhanced_message = f"""
        User Request: {message}

        Current Page Information:
        {page_info}

        Page Blocks:
        {blocks_info}

        Please help the user with their request based on the Notion page information provided.
        """

        # Create task
        task = Task(
            description=enhanced_message,
            expected_output="A helpful response about the Notion page",
            agent=state["agent"]
        )

        # Create and run crew
        crew = Crew(
            agents=[state["agent"]],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def process_message(message, openai_api_key, notion_api_key, page_id, history, progress=gr.Progress()):
    """Process user message"""
    if not message:
        return history, history, ""

    if not all([openai_api_key, notion_api_key, page_id]):
        error_msg = "Please provide all required credentials (OpenAI API key, Notion API key, and Page ID)."
        history.append((message, error_msg))
        return history, history, ""

    # Add user message to history
    history.append((message, None))

    progress(0.5, desc="Processing your request...")

    # Get response
    response = asyncio.run(run_notion_agent(message, openai_api_key, notion_api_key, page_id))

    progress(1.0, desc="Complete!")

    # Update history with response
    history[-1] = (message, response)

    return history, history, ""

def clear_conversation():
    """Clear conversation history"""
    state["conversation_history"] = []
    return [], []

# Create Gradio interface
with gr.Blocks(title="Notion Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📝 Notion Agent")
    gr.Markdown("Interact with your Notion pages using AI powered by CrewAI")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔑 API Configuration")
            openai_api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            notion_api_key = gr.Textbox(
                label="Notion API Key",
                type="password",
                placeholder="Enter your Notion API key"
            )
            page_id = gr.Textbox(
                label="Notion Page ID",
                placeholder="Enter your Notion page ID"
            )

            gr.Markdown("""
            ### 📖 How to find your Page ID:
            1. Open your Notion page in a browser
            2. Look at the URL: `https://www.notion.so/workspace/Page-Name-{PAGE_ID}?v=...`
            3. The Page ID is the part after the last dash and before any query parameters
            """)

            gr.Markdown("### 💡 Example Commands")
            gr.Markdown("- Read the page content")
            gr.Markdown("- Summarize this page")
            gr.Markdown("- What information is on this page?")
            gr.Markdown("- Explain the page structure")

        with gr.Column(scale=2):
            gr.Markdown("### 💬 Chat with Notion Assistant")

            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                show_label=True
            )

            with gr.Row():
                message = gr.Textbox(
                    label="Your Message",
                    placeholder="Ask about your Notion page...",
                    lines=2,
                    scale=4
                )

            with gr.Row():
                send_btn = gr.Button("📤 Send", variant="primary", scale=1)
                clear_btn = gr.Button("🗑️ Clear", scale=1)

            state_output = gr.State([])

    send_btn.click(
        fn=process_message,
        inputs=[message, openai_api_key, notion_api_key, page_id, state_output],
        outputs=[chatbot, state_output, message]
    )

    message.submit(
        fn=process_message,
        inputs=[message, openai_api_key, notion_api_key, page_id, state_output],
        outputs=[chatbot, state_output, message]
    )

    clear_btn.click(
        fn=clear_conversation,
        outputs=[chatbot, state_output]
    )

    gr.Markdown("---")
    gr.Markdown("""
    <div style='padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
    <h4>How to use this app:</h4>
    <ol>
        <li>Get your <strong>Notion API key</strong> from https://www.notion.so/my-integrations</li>
        <li>Share your Notion page with the integration</li>
        <li>Enter your <strong>OpenAI API key</strong> and <strong>Notion API key</strong></li>
        <li>Enter the <strong>Page ID</strong> from your Notion page URL</li>
        <li>Start chatting with the assistant about your page</li>
    </ol>
    <p><strong>Capabilities:</strong></p>
    <ul>
        <li>Read and understand page content</li>
        <li>Summarize information</li>
        <li>Explain page structure</li>
        <li>Answer questions about the page</li>
    </ul>
    </div>
    """)

    gr.Markdown("---")
    gr.Markdown("Built with Gradio and CrewAI ❤️")

if __name__ == "__main__":
    demo.launch(share=False)
