import gradio as gr
import os
from mem0 import Memory
from multion.client import MultiOn
from openai import OpenAI

# Global variables
memory = None
multion = None
openai_client = None
initialized = False

def initialize_app(openai_key, multion_key):
    """Initialize all required services"""
    global memory, multion, openai_client, initialized

    if not openai_key or not multion_key:
        return "Please provide both API keys"

    try:
        os.environ['OPENAI_API_KEY'] = openai_key

        # Initialize Mem0 with Qdrant
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "model": "gpt-4o-mini",
                    "host": "localhost",
                    "port": 6333,
                }
            },
        }

        memory = Memory.from_config(config)
        multion = MultiOn(api_key=multion_key)
        openai_client = OpenAI(api_key=openai_key)
        initialized = True

        return "App initialized successfully! Enter your username and start searching."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def process_with_gpt4(result):
    """Processes an arXiv search result to produce a structured markdown output"""
    prompt = f"""
    Based on the following arXiv search result, provide a proper structured output in markdown that is readable by the users.
    Each paper should have a title, authors, abstract, and link.
    Search Result: {result}
    Output Format: Table with the following columns: [{{"title": "Paper Title", "authors": "Author Names", "abstract": "Brief abstract", "link": "arXiv link"}}, ...]
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def search_papers(user_id, search_query):
    """Search for research papers"""
    global memory, multion, initialized

    if not initialized:
        return "Please initialize the app with API keys first"

    if not user_id:
        return "Please enter a username"

    if not search_query:
        return "Please enter a search query"

    try:
        relevant_memories = memory.search(search_query, user_id=user_id, limit=3)
        prompt = f"Search for arXiv papers: {search_query}\nUser background: {' '.join(mem['text'] for mem in relevant_memories)}"
        result = process_with_gpt4(multion.browse(cmd=prompt, url="https://arxiv.org/"))
        return result
    except Exception as e:
        return f"Error searching papers: {str(e)}"

def view_memory(user_id):
    """View user's memory"""
    global memory, initialized

    if not initialized:
        return "Please initialize the app first"

    if not user_id:
        return "Please enter a username"

    try:
        memories = memory.get_all(user_id=user_id)
        if memories:
            memory_text = "\n".join([f"- {mem['text']}" for mem in memories])
            return f"Memory for {user_id}:\n\n{memory_text}"
        else:
            return "No memory found for this user"
    except Exception as e:
        return f"Error retrieving memory: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="AI Research Agent with Memory", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Research Agent with Memory")
    gr.Markdown("Search arXiv papers with an AI agent that remembers your research interests")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Configuration")
            openai_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            multion_key = gr.Textbox(
                label="MultiOn API Key",
                type="password",
                placeholder="Enter your MultiOn API key"
            )
            init_btn = gr.Button("Initialize App", variant="primary")
            init_status = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")

            user_id = gr.Textbox(
                label="Username",
                placeholder="Enter your username"
            )

            search_query = gr.Textbox(
                label="Research Paper Search Query",
                placeholder="e.g., machine learning transformers",
                lines=2
            )

            search_btn = gr.Button("Search for Papers", variant="primary")

            gr.Markdown("---")
            view_mem_btn = gr.Button("View My Memory")

        with gr.Column(scale=2):
            search_results = gr.Markdown(
                label="Search Results",
                value="Your search results will appear here..."
            )

            memory_display = gr.Textbox(
                label="Memory",
                lines=10,
                interactive=False
            )

    # Event handlers
    init_btn.click(fn=initialize_app, inputs=[openai_key, multion_key], outputs=[init_status])
    search_btn.click(fn=search_papers, inputs=[user_id, search_query], outputs=[search_results])
    view_mem_btn.click(fn=view_memory, inputs=[user_id], outputs=[memory_display])

if __name__ == "__main__":
    demo.launch()
