import os
import tempfile
import gradio as gr
from embedchain import App

# Global variable for app instance
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
                "llm": {"provider": "openai", "config": {"api_key": api_key}},
                "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
                "embedder": {"provider": "openai", "config": {"api_key": api_key}},
            }
        )
        return "App initialized successfully! Now upload a PDF file."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def process_pdf(pdf_file):
    """Process uploaded PDF file"""
    global app
    if app is None:
        return "Please initialize the app with your OpenAI API key first"

    if pdf_file is None:
        return "Please upload a PDF file"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_file)
            temp_path = f.name

        app.add(temp_path, data_type="pdf_file")
        os.remove(temp_path)

        return f"Added {pdf_file.name if hasattr(pdf_file, 'name') else 'PDF'} to knowledge base!"
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def chat_with_pdf(message, history):
    """Chat with the PDF content"""
    global app
    if app is None:
        return history + [[message, "Please initialize the app and upload a PDF first"]]

    if not message:
        return history

    try:
        answer = app.chat(message)
        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="Chat with PDF", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chat with PDF")
    gr.Markdown("Upload a PDF and ask questions about its content using OpenAI")

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

            pdf_upload = gr.File(
                label="Upload PDF",
                file_types=[".pdf"],
                type="binary"
            )
            upload_btn = gr.Button("Process PDF")
            upload_status = gr.Textbox(label="Upload Status", interactive=False)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat", height=400)
            msg = gr.Textbox(
                label="Ask a question about the PDF",
                placeholder="Type your question here..."
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_embedchain, inputs=[api_key], outputs=[init_status])
    upload_btn.click(fn=process_pdf, inputs=[pdf_upload], outputs=[upload_status])
    msg.submit(fn=chat_with_pdf, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
