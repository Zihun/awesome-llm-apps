# Import the required libraries
import gradio as gr
from crewai import Agent
from langchain_openai import ChatOpenAI
from crewai_tools import tool
from arxiv import Search, SortCriterion

# Define ArXiv search tool
@tool("ArXiv Search")
def arxiv_search(query: str) -> str:
    """Search arXiv for research papers based on query"""
    try:
        search = Search(
            query=query,
            max_results=5,
            sort_by=SortCriterion.Relevance
        )

        results = []
        for result in search.results():
            results.append(f"Title: {result.title}\nAuthors: {', '.join([a.name for a in result.authors])}\nSummary: {result.summary}\nURL: {result.entry_id}\n")

        return "\n\n".join(results)
    except Exception as e:
        return f"Error searching arXiv: {str(e)}"

# Global variable for assistant
assistant = None

def initialize_agent(api_key):
    """Initialize CrewAI Agent with OpenAI API key"""
    global assistant
    if not api_key:
        return "Please provide an OpenAI API key"

    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.9,
            api_key=api_key
        )

        assistant = Agent(
            role="Research Paper Assistant",
            goal="Help users find and understand research papers from arXiv",
            backstory="You are an expert at finding relevant research papers and explaining their content",
            tools=[arxiv_search],
            llm=llm,
            verbose=True
        )
        return "Agent initialized successfully! Now you can search for research papers."
    except Exception as e:
        return f"Error initializing agent: {str(e)}"

def search_papers(query, history):
    """Search and chat about research papers"""
    global assistant
    if assistant is None:
        return history + [[query, "Please initialize the agent with your OpenAI API key first"]]

    if not query:
        return history

    try:
        # Use the assistant to process the query
        response = arxiv_search(query)
        return history + [[query, response]]
    except Exception as e:
        return history + [[query, f"Error: {str(e)}"]]

# Create Gradio interface
with gr.Blocks(title="Chat with Research Papers", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chat with Research Papers")
    gr.Markdown("This app allows you to chat with arXiv research papers using OpenAI GPT-4o model and CrewAI")

    with gr.Row():
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            init_btn = gr.Button("Initialize Agent", variant="primary")
            init_status = gr.Textbox(label="Initialization Status", interactive=False)

            gr.Markdown("---")
            gr.Markdown("### Search Tips")
            gr.Markdown("""
            - Use specific keywords for better results
            - Try author names, paper titles, or topics
            - Examples: "machine learning", "quantum computing", "neural networks"
            """)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Research Papers", height=500)
            msg = gr.Textbox(
                label="Enter your search query",
                placeholder="e.g., 'Find papers about transformer models in NLP'"
            )
            clear = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_agent, inputs=[api_key], outputs=[init_status])
    msg.submit(fn=search_papers, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
