import gradio as gr
from openai import OpenAI
from mem0 import Memory

# Global variables
client = None
memory = None
initialized = False
current_user_id = None

def initialize_app(api_key):
    """Initialize OpenAI client and Mem0"""
    global client, memory, initialized

    if not api_key:
        return "Please provide an OpenAI API key"

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

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
        initialized = True

        return "App initialized successfully! Enter your username and start chatting."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def chat_with_agent(user_id, message, history):
    """Chat with the travel agent"""
    global client, memory, initialized, current_user_id

    if not initialized:
        return history + [[message, "Please initialize the app with your OpenAI API key first"]]

    if not user_id:
        return history + [[message, "Please enter a username first"]]

    if not message:
        return history

    # Check if user changed
    if user_id != current_user_id:
        current_user_id = user_id
        history = []

    try:
        # Retrieve relevant memories
        relevant_memories = memory.search(query=message, user_id=user_id)
        context = "Relevant past information:\n"
        if relevant_memories and "results" in relevant_memories:
            for mem in relevant_memories["results"]:
                if "memory" in mem:
                    context += f"- {mem['memory']}\n"

        # Prepare the full prompt
        full_prompt = f"{context}\nHuman: {message}\nAI:"

        # Generate response
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a travel assistant with access to past conversations."},
                {"role": "user", "content": full_prompt}
            ]
        )
        answer = response.choices[0].message.content

        # Store the user query and AI response in memory
        memory.add(message, user_id=user_id, metadata={"role": "user"})
        memory.add(answer, user_id=user_id, metadata={"role": "assistant"})

        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error: {str(e)}"]]

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
with gr.Blocks(title="AI Travel Agent with Memory", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Travel Agent with Memory")
    gr.Markdown("Chat with a travel assistant who remembers your preferences and past interactions")

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

            gr.Markdown("---")
            view_mem_btn = gr.Button("View My Memory")

            memory_display = gr.Textbox(
                label="Memory Info",
                lines=10,
                interactive=False
            )

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Travel Chat",
                height=500,
                show_copy_button=True
            )
            msg = gr.Textbox(
                label="Message",
                placeholder="Where would you like to travel?"
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_app, inputs=[api_key], outputs=[init_status])
    msg.submit(fn=chat_with_agent, inputs=[user_id, msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)
    view_mem_btn.click(fn=view_memory, inputs=[user_id], outputs=[memory_display])

if __name__ == "__main__":
    demo.launch()
