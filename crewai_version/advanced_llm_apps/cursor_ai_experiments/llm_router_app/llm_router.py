import os
import gradio as gr
from routellm.controller import Controller

# Environment variables for API keys
# Note: Users should set these in their environment or through the interface
# os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
# os.environ['TOGETHERAI_API_KEY'] = "your_togetherai_api_key"

# Global client
client = None

def initialize_client(openai_key, together_key):
    """Initialize RouteLLM client with API keys"""
    global client
    if not openai_key or not together_key:
        return "Please provide both API keys"

    try:
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ['TOGETHERAI_API_KEY'] = together_key

        client = Controller(
            routers=["mf"],
            strong_model="gpt-4o-mini",
            weak_model="together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        )
        return "Client initialized successfully!"
    except Exception as e:
        return f"Error initializing client: {str(e)}"

def chat_with_router(message, history):
    """Chat using RouteLLM"""
    global client
    if client is None:
        return history + [[message, "Please initialize the client with API keys first"]]

    if not message:
        return history

    try:
        response = client.chat.completions.create(
            model="router-mf-0.11593",
            messages=[{"role": "user", "content": message}]
        )
        message_content = response['choices'][0]['message']['content']
        model_name = response['model']

        response_text = f"{message_content}\n\n*Model used: {model_name}*"
        return history + [[message, response_text]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="RouteLLM Chat App", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# RouteLLM Chat App")
    gr.Markdown("Chat with AI using intelligent model routing between GPT-4o-mini and Llama 3.1")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Configuration")
            openai_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            together_key = gr.Textbox(
                label="Together AI API Key",
                type="password",
                placeholder="Enter your Together AI API key"
            )
            init_btn = gr.Button("Initialize Client", variant="primary")
            init_status = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")
            gr.Markdown("""
            ### About RouteLLM
            RouteLLM intelligently routes queries between:
            - **Strong model**: GPT-4o-mini (for complex queries)
            - **Weak model**: Llama 3.1-70B (for simpler queries)

            This helps optimize cost and performance.
            """)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Chat",
                height=500,
                show_copy_button=True
            )
            msg = gr.Textbox(
                label="Message",
                placeholder="What is your message?"
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_client, inputs=[openai_key, together_key], outputs=[init_status])
    msg.submit(fn=chat_with_router, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
