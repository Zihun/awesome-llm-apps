import tempfile
import gradio as gr
from embedchain import App

# Global variables
app = None
db_path = None

def initialize_embedchain(api_key):
    """Initialize Embedchain bot with API key"""
    global app, db_path
    if not api_key:
        return "Please provide an OpenAI API key"

    try:
        db_path = tempfile.mkdtemp()
        app = App.from_config(
            config={
                "llm": {"provider": "openai", "config": {"model": "gpt-4-turbo", "temperature": 0.5, "api_key": api_key}},
                "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
                "embedder": {"provider": "openai", "config": {"api_key": api_key}},
            }
        )
        return "App initialized successfully!"
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def load_gmail(gmail_filter):
    """Load Gmail emails to knowledge base"""
    global app
    if app is None:
        return "Please initialize the app with your OpenAI API key first"

    if not gmail_filter:
        gmail_filter = "to: me label:inbox"

    try:
        app.add(gmail_filter, data_type="gmail")
        return f"Added emails from '{gmail_filter}' to the knowledge base!"
    except Exception as e:
        return f"Error loading emails: {str(e)}"

def chat_with_emails(message, history):
    """Chat with Gmail emails"""
    global app
    if app is None:
        return history + [[message, "Please initialize the app and load emails first"]]

    if not message:
        return history

    try:
        answer = app.query(message)
        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="Chat with Gmail Inbox", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chat with your Gmail Inbox")
    gr.Markdown("This app allows you to chat with your Gmail inbox using OpenAI API")

    with gr.Row():
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            init_btn = gr.Button("Initialize App", variant="primary")
            init_status = gr.Textbox(label="Initialization Status", interactive=False)

            gr.Markdown("---")

            gmail_filter = gr.Textbox(
                label="Gmail Filter",
                value="to: me label:inbox",
                placeholder="e.g., to: me label:inbox"
            )
            load_btn = gr.Button("Load Emails")
            load_status = gr.Textbox(label="Load Status", interactive=False)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat with Emails", height=400)
            msg = gr.Textbox(
                label="Ask a question about your emails",
                placeholder="Type your question here..."
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_embedchain, inputs=[api_key], outputs=[init_status])
    load_btn.click(fn=load_gmail, inputs=[gmail_filter], outputs=[load_status])
    msg.submit(fn=chat_with_emails, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
