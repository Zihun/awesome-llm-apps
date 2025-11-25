# Import the required libraries
from embedchain.pipeline import Pipeline as App
from embedchain.loaders.github import GithubLoader
import gradio as gr
import os

loader = GithubLoader(
    config={
        "token":"Your GitHub Token",
        }
    )

# Global variable to store the app instance
app = None

def initialize_app(openai_api_key):
    """Initialize the Embedchain App with OpenAI API key"""
    global app
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
        app = App()
        return "API Key set successfully!"
    return "Please provide an OpenAI API Key"

def add_github_repo(git_repo):
    """Add GitHub repo to knowledge base"""
    global app
    if app is None:
        return "Please set OpenAI API Key first"

    if not git_repo:
        return "Please enter a GitHub repo"

    try:
        app.add("repo:" + git_repo + " " + "type:repo", data_type="github", loader=loader)
        return f"Added {git_repo} to knowledge base!"
    except Exception as e:
        return f"Error adding repo: {str(e)}"

def chat_with_repo(prompt, history):
    """Chat with the GitHub repo"""
    global app
    if app is None:
        return history + [[prompt, "Please set OpenAI API Key and add a GitHub repo first"]]

    if not prompt:
        return history

    try:
        answer = app.chat(prompt)
        return history + [[prompt, answer]]
    except Exception as e:
        return history + [[prompt, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="Chat with GitHub Repository", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chat with GitHub Repository")
    gr.Markdown("This app allows you to chat with a GitHub Repo using OpenAI API")

    with gr.Row():
        with gr.Column(scale=1):
            openai_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            init_btn = gr.Button("Initialize App", variant="primary")
            status_msg = gr.Textbox(label="Status", interactive=False)

            git_repo = gr.Textbox(
                label="GitHub Repository",
                placeholder="e.g., owner/repo-name"
            )
            add_repo_btn = gr.Button("Add Repository to Knowledge Base")
            repo_status = gr.Textbox(label="Repository Status", interactive=False)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat with Repository", height=400)
            msg = gr.Textbox(
                label="Ask a question about the GitHub Repo",
                placeholder="Type your question here..."
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_app, inputs=[openai_key], outputs=[status_msg])
    add_repo_btn.click(fn=add_github_repo, inputs=[git_repo], outputs=[repo_status])
    msg.submit(fn=chat_with_repo, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
