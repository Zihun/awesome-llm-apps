import asyncio
import os
import uuid
from textwrap import dedent
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
from crewai_tools import GithubSearchTool, SerperDevTool
import gradio as gr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global state
state = {
    "initialized": False,
    "agent": None,
    "llm": None,
    "conversation_history": []
}

def setup_agent(openai_api_key, github_token, serper_api_key):
    """Setup the multi-service agent"""
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["GITHUB_TOKEN"] = github_token
    os.environ["SERPER_API_KEY"] = serper_api_key

    # Set up LLM
    llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

    # Initialize tools
    github_tool = GithubSearchTool(
        github_token=github_token,
        content_types=['code', 'repo', 'issue', 'pr']
    )

    search_tool = SerperDevTool()

    # Generate unique user and session IDs
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    # Create the multi-service agent
    agent = Agent(
        role="Multi-Service Intelligent Assistant",
        goal="Help users be incredibly productive across their digital workspace",
        backstory=dedent(f"""
            You are an elite AI assistant with powerful integrations across multiple platforms. Your mission is to help users be incredibly productive across their digital workspace.

            🎯 CORE CAPABILITIES & INSTRUCTIONS:

            1. 🔧 TOOL MASTERY
               • You have DIRECT access to GitHub and Web Search through CrewAI tools
               • ALWAYS use the appropriate tool calls for any requests related to these platforms
               • Be proactive in suggesting powerful workflows and automations
               • Chain multiple tool calls together for complex tasks

            2. 📋 GITHUB EXCELLENCE
               • Repository management: search repositories
               • Issue & PR workflow: find issues, PRs
               • Code analysis: search code, review information
               • Collaboration: explore repository workflows

            3. 🔍 WEB SEARCH & RESEARCH
               • Real-time web search and research
               • Current events and trending information
               • Technical documentation and learning resources
               • Fact-checking and verification

            4. 🎨 INTERACTION PRINCIPLES
               • Be conversational, helpful, and proactive
               • Explain what you're doing and why
               • Suggest follow-up actions and optimizations
               • Handle errors gracefully with alternative solutions
               • Ask clarifying questions when needed
               • Provide rich, formatted responses using markdown

            5. 🚀 ADVANCED WORKFLOWS
               • Cross-platform research (Web Search → GitHub)
               • Research-driven development
               • Documentation and knowledge sharing

            SESSION INFO:
            • User ID: {user_id}
            • Session ID: {session_id}
            • Active Services: GitHub, Web Search

            REMEMBER: You're not just answering questions - you're a productivity multiplier. Think big, suggest workflows, and help users achieve more than they imagined possible!
        """),
        llm=llm,
        tools=[github_tool, search_tool],
        verbose=True,
        allow_delegation=False
    )

    state["agent"] = agent
    state["llm"] = llm
    state["initialized"] = True

async def run_multi_agent(message, openai_api_key, github_token, serper_api_key):
    """Run the multi-service agent"""
    if not all([openai_api_key, github_token, serper_api_key]):
        return "Error: Please provide all required API keys."

    try:
        # Setup agent
        setup_agent(openai_api_key, github_token, serper_api_key)

        # Create task
        task = Task(
            description=message,
            expected_output="A helpful and detailed response to the user's request",
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

def process_message(message, openai_api_key, github_token, serper_api_key, history, progress=gr.Progress()):
    """Process user message"""
    if not message:
        return history, history, ""

    if not all([openai_api_key, github_token, serper_api_key]):
        error_msg = "Please provide all required API keys in the settings."
        history.append((message, error_msg))
        return history, history, ""

    # Add user message to history
    history.append((message, None))

    progress(0.5, desc="Processing your request...")

    # Get response
    response = asyncio.run(run_multi_agent(message, openai_api_key, github_token, serper_api_key))

    progress(1.0, desc="Complete!")

    # Update history with response
    history[-1] = (message, response)

    return history, history, ""

def clear_conversation():
    """Clear conversation history"""
    state["conversation_history"] = []
    return [], []

# Create Gradio interface
with gr.Blocks(title="Multi-Service Intelligent Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Multi-Service Intelligent Assistant")
    gr.Markdown("Powered by CrewAI with GitHub and Web Search Integration")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔑 API Configuration")
            openai_api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            github_token = gr.Textbox(
                label="GitHub Token",
                type="password",
                placeholder="Enter your GitHub token"
            )
            serper_api_key = gr.Textbox(
                label="Serper API Key",
                type="password",
                placeholder="Enter your Serper API key for web search"
            )

            gr.Markdown("### 💡 Example Commands")
            gr.Markdown("**GitHub**")
            gr.Markdown("- Show my recent GitHub repositories")
            gr.Markdown("- Find issues in a repository")

            gr.Markdown("**Web Search**")
            gr.Markdown("- Search for the latest AI developments")
            gr.Markdown("- Research current trends in LLMs")

            gr.Markdown("**Combined**")
            gr.Markdown("- Research best practices and find related repos")

        with gr.Column(scale=2):
            gr.Markdown("### 💬 Chat with Assistant")

            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                show_label=True
            )

            with gr.Row():
                message = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here...",
                    lines=2,
                    scale=4
                )

            with gr.Row():
                send_btn = gr.Button("📤 Send", variant="primary", scale=1)
                clear_btn = gr.Button("🗑️ Clear", scale=1)

            state_output = gr.State([])

    send_btn.click(
        fn=process_message,
        inputs=[message, openai_api_key, github_token, serper_api_key, state_output],
        outputs=[chatbot, state_output, message]
    )

    message.submit(
        fn=process_message,
        inputs=[message, openai_api_key, github_token, serper_api_key, state_output],
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
        <li>Enter your <strong>OpenAI API key</strong>, <strong>GitHub token</strong>, and <strong>Serper API key</strong></li>
        <li>Start chatting with the assistant</li>
        <li>Ask questions about GitHub repositories, search the web, or combine both</li>
    </ol>
    <p><strong>Capabilities:</strong></p>
    <ul>
        <li>GitHub repository exploration and analysis</li>
        <li>Real-time web search and research</li>
        <li>Cross-platform workflows</li>
        <li>Intelligent suggestions and automations</li>
    </ul>
    </div>
    """)

    gr.Markdown("---")
    gr.Markdown("Built with Gradio and CrewAI ❤️")

if __name__ == "__main__":
    demo.launch(share=False)
