import gradio as gr
from mem0 import Memory
from litellm import completion

# Configuration for Memory
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "local-chatgpt-memory",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",
            "temperature": 0,
            "max_tokens": 8000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "version": "v1.1"
}

# Initialize Memory
m = Memory.from_config(config)

# Global variables for user state
current_user_id = None

def chat_with_memory(user_id, message, history):
    """Chat with Llama 3.1 using personalized memory"""
    global current_user_id

    if not user_id:
        return history + [[message, "Please enter your username first"]]

    # Check if user changed
    if user_id != current_user_id:
        current_user_id = user_id
        history = []

    if not message:
        return history

    try:
        # Add to memory
        m.add(message, user_id=user_id)

        # Get context from memory
        memories = m.get_all(user_id=user_id)
        context = ""
        if memories and "results" in memories:
            for memory in memories["results"]:
                if "memory" in memory:
                    context += f"- {memory['memory']}\n"

        # Generate response
        response = completion(
            model="ollama/llama3.1:latest",
            messages=[
                {"role": "system", "content": "You are a helpful assistant with access to past conversations. Use the context provided to give personalized responses."},
                {"role": "user", "content": f"Context from previous conversations with {user_id}: {context}\nCurrent message: {message}"}
            ],
            api_base="http://localhost:11434",
            stream=False
        )

        answer = response.choices[0].message.content

        # Add response to memory
        m.add(f"Assistant: {answer}", user_id=user_id)

        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

def view_memory(user_id):
    """View user's memory"""
    if not user_id:
        return "Please enter a username"

    try:
        memories = m.get_all(user_id=user_id)
        if memories and "results" in memories:
            memory_text = f"Memory history for {user_id}:\n\n"
            for memory in memories["results"]:
                if "memory" in memory:
                    memory_text += f"- {memory['memory']}\n"
            return memory_text
        else:
            return "No memory found for this user"
    except Exception as e:
        return f"Error retrieving memory: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Local ChatGPT with Personal Memory", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Local ChatGPT using Llama 3.1 with Personal Memory")
    gr.Markdown("Each user gets their own personalized memory space!")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### User Settings")
            user_id = gr.Textbox(
                label="Username",
                placeholder="Enter your username"
            )

            gr.Markdown("---")
            gr.Markdown("### Memory Context")
            view_mem_btn = gr.Button("View My Memory")

            memory_display = gr.Textbox(
                label="Memory History",
                lines=10,
                interactive=False
            )

            gr.Markdown("---")
            gr.Markdown("""
            ### Requirements
            - Ollama installed and running
            - Llama 3.1 model downloaded
            - Qdrant running on localhost:6333
            - nomic-embed-text model downloaded
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
    msg.submit(fn=chat_with_memory, inputs=[user_id, msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)
    view_mem_btn.click(fn=view_memory, inputs=[user_id], outputs=[memory_display])

if __name__ == "__main__":
    demo.launch()
