import os
import tempfile
from datetime import datetime
from typing import List
import gradio as gr
import google.generativeai as genai
import bs4
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.embeddings import Embeddings
from crewai_tools import SerperDevTool

class GeminiEmbedder(Embeddings):
    def __init__(self, model_name="models/text-embedding-004", api_key=None):
        genai.configure(api_key=api_key)
        self.model = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        response = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document"
        )
        return response['embedding']

COLLECTION_NAME = "gemini-thinking-agent-crew"

# Global state
processed_documents = []
vector_store = None

def init_qdrant(api_key, url):
    """Initialize Qdrant client with configured settings."""
    try:
        return QdrantClient(url=url, api_key=api_key, timeout=60)
    except Exception as e:
        return None

def process_pdf(file, google_api_key):
    """Process PDF file and add source metadata."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file)
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()

            for doc in documents:
                doc.metadata.update({
                    "source_type": "pdf",
                    "file_name": file.name if hasattr(file, 'name') else 'document.pdf',
                    "timestamp": datetime.now().isoformat()
                })

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            return text_splitter.split_documents(documents)
    except Exception as e:
        return []

def process_web(url: str):
    """Process web URL and add source metadata."""
    try:
        loader = WebBaseLoader(
            web_paths=(url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header", "content", "main")
                )
            )
        )
        documents = loader.load()

        for doc in documents:
            doc.metadata.update({
                "source_type": "url",
                "url": url,
                "timestamp": datetime.now().isoformat()
            })

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        return text_splitter.split_documents(documents)
    except Exception as e:
        return []

def create_vector_store(client, texts, google_api_key):
    """Create and initialize vector store with documents."""
    global vector_store
    try:
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=GeminiEmbedder(api_key=google_api_key)
        )

        vector_store.add_documents(texts)
        return "Documents stored successfully!"
    except Exception as e:
        return f"Error: {str(e)}"

def query_documents(question, google_api_key, qdrant_api_key, qdrant_url, similarity_threshold=0.7):
    """Query the RAG system."""
    global vector_store

    if not vector_store:
        return "Please upload documents first"

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-thinking-exp-01-21",
        api_key=google_api_key,
        temperature=0.7
    )

    # Retrieve documents
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": similarity_threshold}
    )
    docs = retriever.invoke(question)

    if not docs:
        return "No relevant documents found for your question."

    context = "\n\n".join([d.page_content for d in docs])

    # Create RAG Agent
    rag_agent = Agent(
        role="RAG Agent",
        goal="Answer questions based on provided documents",
        backstory="You are an expert researcher who provides accurate answers based on document context.",
        llm=llm,
        verbose=True
    )

    # Create task
    task = Task(
        description=f"""Answer the following question using the context provided:

Context: {context}

Question: {question}

Provide a comprehensive answer based on the available information.""",
        agent=rag_agent,
        expected_output="A detailed answer based on the document context"
    )

    # Execute
    crew = Crew(agents=[rag_agent], tasks=[task], verbose=True)
    result = crew.kickoff()

    # Format sources
    sources = "\n\nSources:\n"
    for i, doc in enumerate(docs[:3], 1):
        source_type = doc.metadata.get("source_type", "unknown")
        source_name = doc.metadata.get("file_name" if source_type == "pdf" else "url", "unknown")
        sources += f"{i}. {source_name}\n"

    return str(result) + sources

def upload_pdf(file, google_api_key, qdrant_api_key, qdrant_url):
    """Upload and process PDF."""
    global processed_documents

    if not all([google_api_key, qdrant_api_key, qdrant_url]):
        return "Please enter all API keys first"

    client = init_qdrant(qdrant_api_key, qdrant_url)
    if not client:
        return "Failed to connect to Qdrant"

    texts = process_pdf(file, google_api_key)
    if texts:
        result = create_vector_store(client, texts, google_api_key)
        processed_documents.append(file.name if hasattr(file, 'name') else 'document.pdf')
        return f"Successfully processed document. {result}"
    return "Failed to process PDF"

def upload_url(url, google_api_key, qdrant_api_key, qdrant_url):
    """Upload and process URL."""
    global processed_documents

    if not all([google_api_key, qdrant_api_key, qdrant_url]):
        return "Please enter all API keys first"

    client = init_qdrant(qdrant_api_key, qdrant_url)
    if not client:
        return "Failed to connect to Qdrant"

    texts = process_web(url)
    if texts:
        result = create_vector_store(client, texts, google_api_key)
        processed_documents.append(url)
        return f"Successfully processed URL. {result}"
    return "Failed to process URL"

# Gradio Interface
with gr.Blocks(title="Agentic RAG with Gemini", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Agentic RAG with Gemini Thinking and CrewAI")

    with gr.Tab("Configuration"):
        gr.Markdown("## API Configuration")
        google_key = gr.Textbox(label="Google API Key", type="password")
        qdrant_key = gr.Textbox(label="Qdrant API Key", type="password")
        qdrant_url_input = gr.Textbox(
            label="Qdrant URL",
            placeholder="https://your-cluster.cloud.qdrant.io:6333"
        )

    with gr.Tab("Upload Documents"):
        gr.Markdown("## Upload Documents")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Upload PDF")
                pdf_file = gr.File(label="Choose PDF", file_types=[".pdf"])
                pdf_btn = gr.Button("Upload PDF", variant="primary")
                pdf_output = gr.Textbox(label="Status")

            with gr.Column():
                gr.Markdown("### Or Enter URL")
                url_input = gr.Textbox(label="URL", placeholder="https://example.com/document.pdf")
                url_btn = gr.Button("Process URL", variant="primary")
                url_output = gr.Textbox(label="Status")

        pdf_btn.click(
            fn=upload_pdf,
            inputs=[pdf_file, google_key, qdrant_key, qdrant_url_input],
            outputs=[pdf_output]
        )

        url_btn.click(
            fn=upload_url,
            inputs=[url_input, google_key, qdrant_key, qdrant_url_input],
            outputs=[url_output]
        )

    with gr.Tab("Ask Questions"):
        gr.Markdown("## Ask Questions")

        similarity_slider = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=0.7,
            label="Similarity Threshold",
            info="Higher values are more strict"
        )

        question_input = gr.Textbox(
            label="Your Question",
            placeholder="What does the document say about...?",
            lines=3
        )

        submit_btn = gr.Button("Get Answer", variant="primary")
        answer_output = gr.Textbox(label="Answer", lines=15)

        submit_btn.click(
            fn=query_documents,
            inputs=[question_input, google_key, qdrant_key, qdrant_url_input, similarity_slider],
            outputs=[answer_output]
        )

if __name__ == "__main__":
    demo.launch()
