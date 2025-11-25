import gradio as gr
from openai import OpenAI

# Point to the local server setup using LM Studio
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def chat_with_llama(message, history):
    """Chat with local Llama-3 model"""
    # Convert history to OpenAI format
    messages = [{"role": "system", "content": "When the input starts with /add, don't follow up with a prompt."}]

    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})

    messages.append({"role": "user", "content": message})

    try:
        # Generate response
        response = client.chat.completions.create(
            model="lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
            messages=messages,
            temperature=0.7
        )

        answer = response.choices[0].message.content
        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="Local ChatGPT with Memory", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Local ChatGPT with Memory")
    gr.Markdown("Chat with locally hosted memory-enabled Llama-3 using LM Studio")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Chat",
                height=500,
                show_copy_button=True
            )
            msg = gr.Textbox(
                label="Message",
                placeholder="What is up?"
            )
            clear = gr.Button("Clear Chat")

        with gr.Column(scale=1):
            gr.Markdown("### About")
            gr.Markdown("""
            This app uses:
            - Local Llama-3 model via LM Studio
            - Memory-enabled chat
            - Runs completely on your machine

            **Setup:**
            1. Install LM Studio
            2. Download Meta-Llama-3-8B-Instruct-GGUF
            3. Start the local server on port 1234
            4. Use this app!

            **Special Commands:**
            - Start message with `/add` to add information without response
            """)

    # Event handlers
    msg.submit(fn=chat_with_llama, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
