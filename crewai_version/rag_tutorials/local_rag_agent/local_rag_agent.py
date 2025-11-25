import gradio as gr
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from qdrant_client import QdrantClient

# Define the collection name for the vector database
collection_name = "thai-recipe-index"

# Set up Qdrant as the vector database with the embedder
embeddings = OllamaEmbeddings(model="llama3.2")
client = QdrantClient(url="http://localhost:6333/")

# Initialize vector store
vector_store = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=embeddings
)

# Load content to the knowledge base (comment out after the first run to avoid reloading)
loader = PyPDFLoader("https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf")
documents = loader.load()
vector_store.add_documents(documents)

# Create the Agent using Ollama's llama3.2 model
llm = Ollama(model="llama3.2")

rag_agent = Agent(
    role="Local RAG Agent",
    goal="Answer questions based on Thai recipes document",
    backstory="You are an expert in Thai cuisine with deep knowledge of traditional recipes.",
    llm=llm,
    verbose=True
)

def query_rag(question):
    """Query the RAG system with a question."""
    # Retrieve relevant documents
    docs = vector_store.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # Create task for the agent
    task = Task(
        description=f"""Answer the following question using the context provided:

Context: {context}

Question: {question}

Provide a detailed answer based on the context.""",
        agent=rag_agent,
        expected_output="A detailed answer to the question based on the provided context"
    )

    # Create crew and execute
    crew = Crew(
        agents=[rag_agent],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()
    return result

# Gradio Interface
with gr.Blocks(title="Local RAG Agent") as demo:
    gr.Markdown("# Local RAG Agent")
    gr.Markdown("Ask questions about Thai recipes using a local Ollama model")

    with gr.Row():
        question_input = gr.Textbox(
            label="Your Question",
            placeholder="e.g., How do I make Pad Thai?",
            lines=2
        )

    with gr.Row():
        submit_btn = gr.Button("Submit", variant="primary")

    with gr.Row():
        answer_output = gr.Textbox(
            label="Answer",
            lines=10
        )

    submit_btn.click(
        fn=query_rag,
        inputs=[question_input],
        outputs=[answer_output]
    )

if __name__ == "__main__":
    demo.launch()
