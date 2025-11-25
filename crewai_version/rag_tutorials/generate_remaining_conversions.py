#!/usr/bin/env python3
"""
Script to generate remaining RAG tutorial conversions from agno+Streamlit to CrewAI+Gradio
This creates functional template versions following the established patterns.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Template for basic RAG with Ollama (local models)
OLLAMA_RAG_TEMPLATE = '''import gradio as gr
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "{collection_name}"
vector_store = None

def init_client(url="http://localhost:6333"):
    """Initialize Qdrant client."""
    try:
        return QdrantClient(url=url)
    except Exception as e:
        return None

def process_documents(files, url_input):
    """Process uploaded documents."""
    global vector_store
    all_docs = []

    # Process PDFs
    if files:
        for file in files:
            loader = PyPDFLoader(file.name)
            docs = loader.load()
            all_docs.extend(docs)

    # Process URL
    if url_input:
        loader = WebBaseLoader(url_input)
        docs = loader.load()
        all_docs.extend(docs)

    if not all_docs:
        return "No documents to process"

    # Split documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)

    # Create vector store
    client = init_client()
    if not client:
        return "Failed to connect to Qdrant"

    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
    except:
        pass  # Collection may already exist

    embeddings = OllamaEmbeddings(model="{embedding_model}")
    vector_store = Qdrant(client=client, collection_name=COLLECTION_NAME, embeddings=embeddings)
    vector_store.add_documents(chunks)

    return f"Processed {{len(chunks)}} document chunks"

def query_rag(question, model_name):
    """Query the RAG system."""
    global vector_store

    if not vector_store:
        return "Please upload documents first"

    # Retrieve relevant documents
    docs = vector_store.similarity_search(question, k=3)
    context = "\\n\\n".join([doc.page_content for doc in docs])

    # Initialize LLM
    llm = Ollama(model=model_name)

    # Create agent
    agent = Agent(
        role="{agent_role}",
        goal="Answer questions based on provided documents",
        backstory="{agent_backstory}",
        llm=llm,
        verbose=True
    )

    # Create task
    task = Task(
        description=f"""Answer the following question using the context:

Context: {{context}}

Question: {{question}}

Provide a detailed answer based on the context.""",
        agent=agent,
        expected_output="A comprehensive answer with relevant details"
    )

    # Execute
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()

    return str(result)

# Gradio Interface
with gr.Blocks(title="{app_title}", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# {app_title}")
    gr.Markdown("{app_description}")

    with gr.Tab("Upload"):
        files = gr.File(label="Upload PDFs", file_count="multiple", file_types=[".pdf"])
        url = gr.Textbox(label="Or enter URL", placeholder="https://example.com")
        upload_btn = gr.Button("Process Documents", variant="primary")
        upload_status = gr.Textbox(label="Status")

        upload_btn.click(
            fn=process_documents,
            inputs=[files, url],
            outputs=[upload_status]
        )

    with gr.Tab("Query"):
        model_select = gr.Dropdown(
            choices={model_choices},
            value="{default_model}",
            label="Select Model"
        )
        question = gr.Textbox(label="Your Question", lines=3)
        query_btn = gr.Button("Get Answer", variant="primary")
        answer = gr.Textbox(label="Answer", lines=10)

        query_btn.click(
            fn=query_rag,
            inputs=[question, model_select],
            outputs=[answer]
        )

if __name__ == "__main__":
    demo.launch()
'''

# Template for cloud-based RAG
CLOUD_RAG_TEMPLATE = '''import gradio as gr
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "{collection_name}"
vector_store = None

def process_docs(files, api_key, qdrant_key, qdrant_url):
    """Process and store documents."""
    global vector_store

    if not all([api_key, qdrant_key, qdrant_url]):
        return "Please provide all API keys"

    # Load documents
    all_docs = []
    for file in files:
        loader = PyPDFLoader(file.name)
        docs = loader.load()
        all_docs.extend(docs)

    # Split
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)

    # Create vector store
    client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
    embeddings = OpenAIEmbeddings(api_key=api_key)

    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
    except:
        pass

    vector_store = Qdrant(client=client, collection_name=COLLECTION_NAME, embeddings=embeddings)
    vector_store.add_documents(chunks)

    return f"Processed {{len(chunks)}} chunks"

def query(question, api_key):
    """Query the system."""
    if not vector_store:
        return "Upload documents first"

    docs = vector_store.similarity_search(question, k=3)
    context = "\\n\\n".join([d.page_content for d in docs])

    llm = ChatOpenAI(model="{model_name}", api_key=api_key)

    agent = Agent(
        role="{agent_role}",
        goal="Provide accurate answers from documents",
        backstory="{agent_backstory}",
        llm=llm,
        verbose=True
    )

    task = Task(
        description=f"Context: {{context}}\\n\\nQuestion: {{question}}",
        agent=agent,
        expected_output="Detailed answer"
    )

    crew = Crew(agents=[agent], tasks=[task])
    return str(crew.kickoff())

with gr.Blocks(title="{app_title}") as demo:
    gr.Markdown("# {app_title}")

    with gr.Row():
        api_key = gr.Textbox(label="OpenAI API Key", type="password")
        qdrant_key = gr.Textbox(label="Qdrant API Key", type="password")
        qdrant_url = gr.Textbox(label="Qdrant URL")

    with gr.Tab("Upload"):
        files = gr.File(label="PDFs", file_count="multiple")
        upload_btn = gr.Button("Process")
        status = gr.Textbox(label="Status")
        upload_btn.click(process_docs, [files, api_key, qdrant_key, qdrant_url], [status])

    with gr.Tab("Query"):
        q = gr.Textbox(label="Question", lines=3)
        btn = gr.Button("Ask")
        ans = gr.Textbox(label="Answer", lines=10)
        btn.click(query, [q, api_key], [ans])

if __name__ == "__main__":
    demo.launch()
'''

# Definitions for each remaining file
FILES_TO_CREATE = {
    "qwen_local_rag/qwen_local_rag_agent.py": {
        "template": OLLAMA_RAG_TEMPLATE,
        "params": {
            "collection_name": "qwen-rag",
            "embedding_model": "snowflake-arctic-embed",
            "agent_role": "Qwen RAG Agent",
            "agent_backstory": "Expert using Qwen 3 model for answering questions",
            "app_title": "Qwen 3 Local RAG Agent",
            "app_description": "RAG system using Qwen 3 local models",
            "model_choices": str(["qwen3:1.7b", "qwen3:8b", "gemma3:1b", "gemma3:4b"]),
            "default_model": "qwen3:1.7b"
        }
    },
    "deepseek_local_rag_agent/deepseek_rag_agent.py": {
        "template": OLLAMA_RAG_TEMPLATE,
        "params": {
            "collection_name": "deepseek-rag",
            "embedding_model": "snowflake-arctic-embed",
            "agent_role": "DeepSeek RAG Agent",
            "agent_backstory": "Expert using DeepSeek R1 for reasoning and answers",
            "app_title": "DeepSeek Local RAG Agent",
            "app_description": "RAG with DeepSeek R1 reasoning capabilities",
            "model_choices": str(["deepseek-r1:1.5b", "deepseek-r1:7b"]),
            "default_model": "deepseek-r1:1.5b"
        }
    },
    "llama3.1_local_rag/llama3.1_local_rag.py": {
        "template": OLLAMA_RAG_TEMPLATE,
        "params": {
            "collection_name": "llama-rag",
            "embedding_model": "llama3.2",
            "agent_role": "Llama RAG Agent",
            "agent_backstory": "Expert using Llama 3.1 for document Q&A",
            "app_title": "Llama 3.1 Local RAG",
            "app_description": "RAG system with Llama 3.1",
            "model_choices": str(["llama3.1", "llama3.2"]),
            "default_model": "llama3.1"
        }
    },
    # Add more files here following the same pattern
}

def create_file(filepath, content):
    """Create a file with given content."""
    full_path = BASE_DIR / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, 'w') as f:
        f.write(content)

    print(f"Created: {filepath}")

def main():
    """Generate all files."""
    print("Generating remaining RAG tutorial conversions...")

    for filepath, config in FILES_TO_CREATE.items():
        template = config["template"]
        params = config["params"]

        # Format template with parameters
        content = template.format(**params)

        # Create file
        create_file(filepath, content)

    print(f"\\nGenerated {len(FILES_TO_CREATE)} files")
    print("See README.md for usage instructions")

if __name__ == "__main__":
    main()
