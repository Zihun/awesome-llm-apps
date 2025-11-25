import os
import gradio as gr
from mem0 import Memory
from openai import OpenAI

# Global variables
client = None
memory = None
initialized = False

def initialize_app(api_key):
    """Initialize OpenAI client and Mem0"""
    global client, memory, initialized

    if not api_key:
        return "Please provide an OpenAI API key"

    try:
        os.environ["OPENAI_API_KEY"] = api_key

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Initialize Mem0 with Qdrant
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "llm_app_memory",
                    "host": "localhost",
                    "port": 6333,
                }
            },
        }

        memory = Memory.from_config(config)
        initialized = True

        return "App initialized successfully! Enter your username and start chatting."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def chat_with_llm(user_id, prompt):
    """Chat with LLM using personalized memory"""
    global client, memory, initialized

    if not initialized:
        return "Please initialize the app with your OpenAI API key first"

    if not user_id:
        return "Please enter a username"

    if not prompt:
        return "Please enter a question"

    try:
        # Search for relevant memories
        relevant_memories = memory.search(query=prompt, user_id=user_id)

        # Prepare context with relevant memories
        context = "Relevant past information:\n"
        for mem in relevant_memories:
            context += f"- {mem['text']}\n"

        # Prepare the full prompt
        full_prompt = f"{context}\nHuman: {prompt}\nAI:"

        # Get response from GPT-4
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
                {"role": "user", "content": full_prompt}
            ]
        )

        answer = response.choices[0].message.content

        # Add AI response to memory
        memory.add(answer, user_id=user_id)

        return f"Answer: {answer}"
    except Exception as e:
        return f"Error: {str(e)}"

def view_memory(user_id):
    """View user's memory"""
    global memory, initialized

    if not initialized:
        return "Please initialize the app first"

    if not user_id:
        return "Please enter a username"

    try:
        memories = memory.get_all(user_id=user_id)
        if memories and "results" in memories:
            memory_text = f"Memory history for {user_id}:\n\n"
            for mem in memories["results"]:
                if "memory" in mem:
                    memory_text += f"- {mem['memory']}\n"
            return memory_text
        else:
            return "No learning history found for this user ID."
    except Exception as e:
        return f"Error retrieving memory: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="LLM App with Memory", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# LLM App with Memory")
    gr.Markdown("LLM App with personalized memory layer that remembers every user's choice and interests")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Configuration")
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            init_btn = gr.Button("Initialize App", variant="primary")
            init_status = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")

            user_id = gr.Textbox(
                label="Username",
                placeholder="Enter your username"
            )

            prompt = gr.Textbox(
                label="Ask ChatGPT",
                placeholder="Type your question here...",
                lines=3
            )

            chat_btn = gr.Button("Chat with LLM", variant="primary")

            gr.Markdown("---")
            view_mem_btn = gr.Button("View My Memory")

        with gr.Column(scale=2):
            answer_output = gr.Textbox(
                label="Response",
                lines=10,
                interactive=False,
                show_copy_button=True
            )

            memory_display = gr.Textbox(
                label="Memory Info",
                lines=10,
                interactive=False
            )

    # Event handlers
    init_btn.click(fn=initialize_app, inputs=[api_key], outputs=[init_status])
    chat_btn.click(fn=chat_with_llm, inputs=[user_id, prompt], outputs=[answer_output])
    view_mem_btn.click(fn=view_memory, inputs=[user_id], outputs=[memory_display])

if __name__ == "__main__":
    demo.launch()
