import gradio as gr
from mem0 import Memory
from openai import OpenAI
import os
from litellm import completion

# Global variables
memory = None
client = None
initialized = False

def initialize_app(openai_key, anthropic_key):
    """Initialize clients and memory"""
    global memory, client, initialized

    if not openai_key or not anthropic_key:
        return "Please provide both API keys"

    try:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key

        # Initialize Mem0 with Qdrant
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333,
                }
            },
        }

        memory = Memory.from_config(config)
        client = OpenAI(api_key=openai_key)
        initialized = True

        return "App initialized successfully! Enter your username and select an LLM."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def chat_with_llm(user_id, llm_choice, prompt):
    """Chat with selected LLM using shared memory"""
    global memory, client, initialized

    if not initialized:
        return "Please initialize the app with API keys first"

    if not user_id:
        return "Please enter a username"

    if not prompt:
        return "Please enter a question"

    try:
        # Search for relevant memories
        relevant_memories = memory.search(query=prompt, user_id=user_id)
        context = "Relevant past information:\n"
        if relevant_memories and "results" in relevant_memories:
            for mem in relevant_memories["results"]:
                if "memory" in mem:
                    context += f"- {mem['memory']}\n"

        full_prompt = f"{context}\nHuman: {prompt}\nAI:"

        # Generate response based on selected LLM
        if llm_choice == 'OpenAI GPT-4o':
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            answer = response.choices[0].message.content
        elif llm_choice == 'Claude Sonnet 3.5':
            messages = [
                {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
                {"role": "user", "content": full_prompt}
            ]
            response = completion(model="claude-3-5-sonnet-20240620", messages=messages)
            answer = response.choices[0].message.content

        # Add response to memory
        memory.add(answer, user_id=user_id)

        return f"Answer ({llm_choice}): {answer}"
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
with gr.Blocks(title="Multi-LLM App with Shared Memory", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Multi-LLM App with Shared Memory")
    gr.Markdown("LLM App with a personalized memory layer that remembers each user's choices and interests across multiple users and LLMs")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Configuration")
            openai_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            anthropic_key = gr.Textbox(
                label="Anthropic API Key",
                type="password",
                placeholder="Enter your Anthropic API key"
            )
            init_btn = gr.Button("Initialize App", variant="primary")
            init_status = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")

            user_id = gr.Textbox(
                label="Username",
                placeholder="Enter your username"
            )

            llm_choice = gr.Radio(
                choices=['OpenAI GPT-4o', 'Claude Sonnet 3.5'],
                label="Select LLM",
                value='OpenAI GPT-4o'
            )

            prompt = gr.Textbox(
                label="Ask the LLM",
                placeholder="Type your question here...",
                lines=3
            )

            chat_btn = gr.Button("Chat with LLM", variant="primary")

            gr.Markdown("---")
            view_mem_btn = gr.Button("View My Memory")

        with gr.Column(scale=2):
            answer_output = gr.Textbox(
                label="Response",
                lines=15,
                interactive=False,
                show_copy_button=True
            )

            memory_display = gr.Textbox(
                label="Memory Info",
                lines=10,
                interactive=False
            )

    # Event handlers
    init_btn.click(fn=initialize_app, inputs=[openai_key, anthropic_key], outputs=[init_status])
    chat_btn.click(fn=chat_with_llm, inputs=[user_id, llm_choice, prompt], outputs=[answer_output])
    view_mem_btn.click(fn=view_memory, inputs=[user_id], outputs=[memory_display])

if __name__ == "__main__":
    demo.launch()
