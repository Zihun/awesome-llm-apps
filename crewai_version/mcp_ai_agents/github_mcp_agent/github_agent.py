import asyncio
import os
import gradio as gr
from textwrap import dedent
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
from crewai_tools import GithubSearchTool

# Global state
state = {
    "initialized": False,
    "github_agent": None,
    "llm": None
}

def setup_agent(openai_api_key, github_token):
    """Setup the GitHub agent"""
    # Set environment variable for GitHub token
    os.environ["GITHUB_TOKEN"] = github_token
    os.environ["OPENAI_API_KEY"] = openai_api_key

    # Set up LLM
    llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

    # Initialize GitHub search tool
    github_tool = GithubSearchTool(
        github_token=github_token,
        content_types=['code', 'repo', 'issue', 'pr']
    )

    # Create GitHub agent
    github_agent = Agent(
        role="GitHub Assistant",
        goal="Help users explore repositories and their activity with organized insights",
        backstory=dedent("""\
            You are a GitHub assistant. Help users explore repositories and their activity.
            - Provide organized, concise insights about the repository
            - Focus on facts and data from the GitHub API
            - Use markdown formatting for better readability
            - Present numerical data in tables when appropriate
            - Include links to relevant GitHub pages when helpful
        """),
        llm=llm,
        tools=[github_tool],
        verbose=True,
        allow_delegation=False
    )

    state["github_agent"] = github_agent
    state["llm"] = llm
    state["initialized"] = True

async def run_github_agent(query, repo, openai_api_key, github_token):
    """Run the GitHub agent with the given query"""
    if not openai_api_key:
        return "Error: Please enter your OpenAI API key."

    if not github_token:
        return "Error: Please enter your GitHub token."

    try:
        # Setup agent
        setup_agent(openai_api_key, github_token)

        # Add repo to query if needed
        if repo and repo not in query:
            full_query = f"{query} in {repo}"
        else:
            full_query = query

        # Create task
        task = Task(
            description=full_query,
            expected_output="Organized insights about the GitHub repository",
            agent=state["github_agent"]
        )

        # Create and run crew
        crew = Crew(
            agents=[state["github_agent"]],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def process_query(query, repo, query_type, openai_api_key, github_token, progress=gr.Progress()):
    """Process GitHub query"""
    if not query:
        return "Please enter a query."

    progress(0.5, desc="Analyzing GitHub repository...")

    result = asyncio.run(run_github_agent(query, repo, openai_api_key, github_token))

    progress(1.0, desc="Complete!")

    return result

def update_query_template(query_type, repo):
    """Update query template based on selection"""
    if query_type == "Issues":
        return f"Find issues labeled as bugs in {repo}"
    elif query_type == "Pull Requests":
        return f"Show me recent merged PRs in {repo}"
    elif query_type == "Repository Activity":
        return f"Analyze code quality trends in {repo}"
    else:
        return ""

# Create Gradio interface
with gr.Blocks(title="GitHub Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🐙 GitHub Agent")
    gr.Markdown("Explore GitHub repositories with natural language using CrewAI")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🔑 Authentication")
            openai_api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Required for the AI agent to interpret queries"
            )
            github_token = gr.Textbox(
                label="GitHub Token",
                type="password",
                placeholder="Create a token with repo scope at github.com/settings/tokens"
            )

            gr.Markdown("### Repository & Query")
            with gr.Row():
                repo = gr.Textbox(
                    label="Repository",
                    value="Shubhamsaboo/awesome-llm-apps",
                    placeholder="Format: owner/repo",
                    scale=3
                )
                query_type = gr.Dropdown(
                    label="Query Type",
                    choices=["Issues", "Pull Requests", "Repository Activity", "Custom"],
                    value="Issues",
                    scale=1
                )

            query = gr.Textbox(
                label="Your Query",
                value="Find issues labeled as bugs in Shubhamsaboo/awesome-llm-apps",
                placeholder="What would you like to know about this repository?",
                lines=3
            )

            run_btn = gr.Button("🚀 Run Query", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### Example Queries")
            gr.Markdown("**Issues**")
            gr.Markdown("- Show me issues by label")
            gr.Markdown("- What issues are being actively discussed?")

            gr.Markdown("**Pull Requests**")
            gr.Markdown("- What PRs need review?")
            gr.Markdown("- Show me recent merged PRs")

            gr.Markdown("**Repository**")
            gr.Markdown("- Show repository health metrics")
            gr.Markdown("- Show repository activity patterns")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Results")
            response_output = gr.Textbox(label="Analysis Results", lines=15, max_lines=25)

    # Update query template when query type or repo changes
    query_type.change(
        fn=update_query_template,
        inputs=[query_type, repo],
        outputs=[query]
    )

    run_btn.click(
        fn=process_query,
        inputs=[query, repo, query_type, openai_api_key, github_token],
        outputs=[response_output]
    )

    gr.Markdown("---")
    gr.Markdown("""
    <div style='padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
    <h4>How to use this app:</h4>
    <ol>
        <li>Enter your <strong>OpenAI API key</strong> (powers the AI agent)</li>
        <li>Enter your <strong>GitHub token</strong></li>
        <li>Specify a repository (e.g., Shubhamsaboo/awesome-llm-apps)</li>
        <li>Select a query type or write your own</li>
        <li>Click 'Run Query' to see results</li>
    </ol>
    <p><strong>How it works:</strong></p>
    <ul>
        <li>Uses CrewAI with GitHub tools for real-time access to GitHub API</li>
        <li>AI Agent (powered by OpenAI) interprets your queries and calls appropriate GitHub APIs</li>
        <li>Results are formatted in readable markdown with insights and links</li>
        <li>Queries work best when focused on specific aspects like issues, PRs, or repository info</li>
    </ul>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(share=False)
