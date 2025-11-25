import gradio as gr
from ollama import Client

# Initialize Ollama client
client = Client()

def chat_response(message, history):
    """Generate chat response using Ollama"""
    # Convert history to Ollama format
    messages = []
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})

    # Generate response with streaming
    full_response = ""
    for response in client.chat(model="llama3.1:latest", messages=messages, stream=True):
        full_response += response['message']['content']

    return full_response

# Create Gradio interface
with gr.Blocks(title="Local ChatGPT Clone", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Local ChatGPT Clone")
    gr.Markdown("Chat with Ollama's llama3.1 model locally")

    chatbot = gr.Chatbot(
        label="Chat",
        height=500,
        show_copy_button=True
    )

    with gr.Row():
        msg = gr.Textbox(
            label="Message",
            placeholder="What's on your mind?",
            scale=9
        )
        clear = gr.Button("Clear", scale=1)

    # Event handlers
    msg.submit(
        fn=chat_response,
        inputs=[msg, chatbot],
        outputs=[chatbot]
    ).then(
        lambda: "",
        None,
        msg
    )

    clear.click(lambda: [], None, chatbot)

    # Sidebar information
    with gr.Accordion("About", open=False):
        gr.Markdown("""
        This is a local ChatGPT clone using:
        - Ollama's llama3.1:latest model
        - Gradio for the interface

        Make sure you have Ollama installed and the llama3.1:latest model downloaded.
        """)

if __name__ == "__main__":
    demo.launch()
