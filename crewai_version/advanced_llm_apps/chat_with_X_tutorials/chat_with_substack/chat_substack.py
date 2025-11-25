import gradio as gr
from embedchain import App
import tempfile

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
        return "App initialized successfully! Now enter a Substack URL."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def load_substack(substack_url):
    """Load Substack newsletter to knowledge base"""
    global app
    if app is None:
        return "Please initialize the app with your OpenAI API key first"

    if not substack_url:
        return "Please enter a Substack URL"

    try:
        app.add(substack_url, data_type='substack')
        return f"Added {substack_url} to knowledge base!"
    except Exception as e:
        return f"Error loading Substack: {str(e)}"

def chat_with_substack(message, history):
    """Chat with Substack newsletter"""
    global app
    if app is None:
        return history + [[message, "Please initialize the app and load a Substack newsletter first"]]

    if not message:
        return history

    try:
        answer = app.query(message)
        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="Chat with Substack Newsletter", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chat with Substack Newsletter")
    gr.Markdown("This app allows you to chat with Substack newsletter using OpenAI API")

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

            substack_url = gr.Textbox(
                label="Substack Newsletter URL",
                placeholder="e.g., https://example.substack.com/p/article-title"
            )
            load_btn = gr.Button("Load Newsletter")
            load_status = gr.Textbox(label="Load Status", interactive=False)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat with Newsletter", height=400)
            msg = gr.Textbox(
                label="Ask a question about the newsletter",
                placeholder="Type your question here..."
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_embedchain, inputs=[api_key], outputs=[init_status])
    load_btn.click(fn=load_substack, inputs=[substack_url], outputs=[load_status])
    msg.submit(fn=chat_with_substack, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
