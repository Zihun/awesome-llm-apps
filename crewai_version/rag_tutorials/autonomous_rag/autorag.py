import gradio as gr
from io import BytesIO
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFReader
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from crewai_tools import PDFSearchTool, WebsiteSearchTool

# Database connection string for PostgreSQL
DB_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"

def setup_assistant(api_key: str):
    """Initializes and returns an AI Assistant agent."""
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

    # Set up the Assistant with CrewAI
    assistant = Agent(
        role="Auto RAG Agent",
        goal="Answer questions based on uploaded documents and web search",
        backstory="""You are an intelligent research assistant.
        You first search your knowledge base for relevant information.
        If not found, you search the internet using DuckDuckGo.
        You provide clear and concise answers with proper citations.""",
        llm=llm,
        tools=[PDFSearchTool(), WebsiteSearchTool()],
        verbose=True
    )

    return assistant

def add_document(agent: Agent, file: BytesIO, api_key: str):
    """Add a PDF document to the agent's knowledge base."""
    try:
        # For CrewAI, we'd typically use the PDFSearchTool
        # This is a simplified version
        return "Document processing with CrewAI tools - configure PDFSearchTool with your document path"
    except Exception as e:
        return f"Failed to read the document: {str(e)}"

def query_assistant(agent: Agent, question: str):
    """Queries the Assistant and returns a response."""
    task = Task(
        description=f"""Answer the following question using available knowledge and tools:

Question: {question}

Steps:
1. Search the knowledge base first
2. If not found, search the internet
3. Provide a clear and concise answer""",
        agent=agent,
        expected_output="A comprehensive answer with sources"
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    return str(result)

# Gradio Interface
def create_interface():
    with gr.Blocks(title="AutoRAG", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Auto-RAG: Autonomous RAG with GPT-4o")

        with gr.Row():
            api_key_input = gr.Textbox(
                label="Enter your OpenAI API Key",
                type="password",
                placeholder="sk-..."
            )

        agent_state = gr.State(None)

        def initialize_agent(api_key):
            if not api_key:
                return "Please enter an API key", None
            agent = setup_assistant(api_key)
            return "Assistant initialized successfully!", agent

        init_btn = gr.Button("Initialize Assistant", variant="primary")
        init_status = gr.Textbox(label="Status")

        init_btn.click(
            fn=initialize_agent,
            inputs=[api_key_input],
            outputs=[init_status, agent_state]
        )

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Upload PDF")
                pdf_file = gr.File(label="Upload PDF Document", file_types=[".pdf"])
                upload_btn = gr.Button("Add to Knowledge Base")
                upload_status = gr.Textbox(label="Upload Status")

                def handle_upload(file, api_key, agent):
                    if not agent:
                        return "Please initialize the assistant first"
                    if not file:
                        return "Please upload a file"
                    return add_document(agent, BytesIO(file), api_key)

                upload_btn.click(
                    fn=handle_upload,
                    inputs=[pdf_file, api_key_input, agent_state],
                    outputs=[upload_status]
                )

            with gr.Column():
                gr.Markdown("### Ask Question")
                question_input = gr.Textbox(
                    label="Your Question",
                    placeholder="What is the main topic of the document?",
                    lines=3
                )
                ask_btn = gr.Button("Get Answer", variant="primary")
                answer_output = gr.Textbox(label="Response", lines=10)

                def handle_question(question, agent):
                    if not agent:
                        return "Please initialize the assistant first"
                    if not question.strip():
                        return "Please enter a question"
                    return query_assistant(agent, question)

                ask_btn.click(
                    fn=handle_question,
                    inputs=[question_input, agent_state],
                    outputs=[answer_output]
                )

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch()
