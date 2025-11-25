from typing import List, Dict, Optional, Tuple
import os
import tempfile
from datetime import datetime
import uuid
import asyncio

import gradio as gr
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from fastembed import TextEmbedding
from openai import AsyncOpenAI
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI

load_dotenv()

# Constants
COLLECTION_NAME = "voice-rag-agent"

# Global state
state = {
    "client": None,
    "embedding_model": None,
    "processor_agent": None,
    "tts_agent": None,
    "openai_api_key": None,
    "processed_documents": []
}

def setup_qdrant() -> Tuple[QdrantClient, TextEmbedding]:
    """Initialize Qdrant client and embedding model"""
    if not state.get("qdrant_url") or not state.get("qdrant_api_key"):
        raise ValueError("Qdrant credentials not provided")

    client = QdrantClient(
        url=state["qdrant_url"],
        api_key=state["qdrant_api_key"]
    )

    embedding_model = TextEmbedding()
    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)

    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE
            )
        )
    except Exception as e:
        if "already exists" not in str(e):
            raise e

    return client, embedding_model

def process_pdf(file) -> List:
    """Process PDF file and split into chunks with metadata"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file)
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()

            # Add source metadata
            for doc in documents:
                doc.metadata.update({
                    "source_type": "pdf",
                    "file_name": "uploaded_document.pdf",
                    "timestamp": datetime.now().isoformat()
                })

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            return text_splitter.split_documents(documents)
    except Exception as e:
        raise Exception(f"PDF processing error: {str(e)}")

def store_embeddings(
    client: QdrantClient,
    embedding_model: TextEmbedding,
    documents: List,
    collection_name: str
) -> None:
    """Store document embeddings in Qdrant"""
    for doc in documents:
        embedding = list(embedding_model.embed([doc.page_content]))[0]
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "content": doc.page_content,
                        **doc.metadata
                    }
                )
            ]
        )

def setup_agents(openai_api_key: str) -> Tuple[Agent, Agent]:
    """Initialize the processor and TTS agents using CrewAI"""
    llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

    processor_agent = Agent(
        role="Documentation Processor",
        goal="""Analyze provided documentation content and answer user questions clearly and concisely.
        Include relevant examples when available. Cite source files when referencing specific content.
        Keep responses natural and conversational. Format response in a way that's easy to speak out loud.""",
        backstory="Expert documentation analyst with deep knowledge of technical content",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    tts_agent = Agent(
        role="Text-to-Speech Agent",
        goal="""Convert documentation responses into natural speech with proper pacing and emphasis.
        Handle technical terms clearly. Keep tone professional but friendly. Use appropriate pauses
        for better comprehension. Ensure speech is clear and well-articulated.""",
        backstory="Voice synthesis expert specializing in technical documentation narration",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return processor_agent, tts_agent

async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    collection_name: str,
    openai_api_key: str,
    voice: str
) -> Dict:
    """Process user query and generate voice response"""
    try:
        # Get query embedding and search
        query_embedding = list(embedding_model.embed([query]))[0]

        search_response = client.query_points(
            collection_name=collection_name,
            query=query_embedding.tolist(),
            limit=3,
            with_payload=True
        )

        search_results = search_response.points if hasattr(search_response, 'points') else []

        if not search_results:
            raise Exception("No relevant documents found in the vector database")

        # Prepare context from search results
        context = "Based on the following documentation:\n\n"
        for i, result in enumerate(search_results, 1):
            payload = result.payload
            if not payload:
                continue
            content = payload.get('content', '')
            source = payload.get('file_name', 'Unknown Source')
            context += f"From {source}:\n{content}\n\n"

        context += f"\nUser Question: {query}\n\n"
        context += "Please provide a clear, concise answer that can be easily spoken out loud."

        # Setup agents if not already done
        if not state["processor_agent"] or not state["tts_agent"]:
            processor_agent, tts_agent = setup_agents(openai_api_key)
            state["processor_agent"] = processor_agent
            state["tts_agent"] = tts_agent
        else:
            processor_agent = state["processor_agent"]
            tts_agent = state["tts_agent"]

        # Generate text response using processor agent
        processor_task = Task(
            description=context,
            expected_output="A clear and concise answer to the user's question",
            agent=processor_agent
        )

        processor_crew = Crew(
            agents=[processor_agent],
            tasks=[processor_task],
            verbose=True
        )

        processor_result = processor_crew.kickoff()
        text_response = str(processor_result)

        # Generate voice instructions using TTS agent
        tts_task = Task(
            description=text_response,
            expected_output="Voice synthesis instructions for natural speech",
            agent=tts_agent
        )

        tts_crew = Crew(
            agents=[tts_agent],
            tasks=[tts_task],
            verbose=True
        )

        tts_result = tts_crew.kickoff()
        voice_instructions = str(tts_result)

        # Generate audio
        async_openai = AsyncOpenAI(api_key=openai_api_key)

        audio_response = await async_openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text_response,
            instructions=voice_instructions,
            response_format="mp3"
        )

        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"response_{uuid.uuid4()}.mp3")

        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        return {
            "status": "success",
            "text_response": text_response,
            "voice_instructions": voice_instructions,
            "audio_path": audio_path,
            "sources": [r.payload.get('file_name', 'Unknown Source') for r in search_results if r.payload]
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }

def setup_system(qdrant_url, qdrant_api_key, openai_api_key, progress=gr.Progress()):
    """Setup the system with API credentials"""
    if not all([qdrant_url, qdrant_api_key, openai_api_key]):
        return "Error: Please provide all API credentials", gr.update(interactive=False)

    try:
        state["qdrant_url"] = qdrant_url
        state["qdrant_api_key"] = qdrant_api_key
        state["openai_api_key"] = openai_api_key

        progress(0.5, desc="Setting up Qdrant...")
        client, embedding_model = setup_qdrant()
        state["client"] = client
        state["embedding_model"] = embedding_model

        progress(1.0, desc="Complete!")
        return "✅ System configured successfully! Upload a PDF to begin.", gr.update(interactive=True)

    except Exception as e:
        return f"Error: {str(e)}", gr.update(interactive=False)

def upload_pdf(file, progress=gr.Progress()):
    """Process and store uploaded PDF"""
    if not state.get("client"):
        return "Please configure the system first!", ""

    try:
        progress(0.3, desc="Processing PDF...")
        documents = process_pdf(file)

        if documents:
            progress(0.6, desc="Storing embeddings...")
            store_embeddings(
                state["client"],
                state["embedding_model"],
                documents,
                COLLECTION_NAME
            )

            file_name = "uploaded_document.pdf"
            state["processed_documents"].append(file_name)

            progress(1.0, desc="Complete!")
            docs_list = "\n".join([f"📄 {doc}" for doc in state["processed_documents"]])
            return f"✅ Successfully processed PDF with {len(documents)} chunks!", docs_list
        else:
            return "Error: No content extracted from PDF", ""

    except Exception as e:
        return f"Error: {str(e)}", ""

def ask_question(query, voice, progress=gr.Progress()):
    """Process user query"""
    if not state.get("client") or not state["processed_documents"]:
        return "Please configure system and upload documents first!", None, ""

    if not query:
        return "Please enter a question!", None, ""

    try:
        progress(0.5, desc="Processing query...")

        result = asyncio.run(process_query(
            query,
            state["client"],
            state["embedding_model"],
            COLLECTION_NAME,
            state["openai_api_key"],
            voice
        ))

        if result["status"] == "success":
            progress(1.0, desc="Complete!")
            sources_text = "\n".join([f"- {source}" for source in result["sources"]])
            return result["text_response"], result["audio_path"], sources_text
        else:
            return f"Error: {result.get('error', 'Unknown error')}", None, ""

    except Exception as e:
        return f"Error: {str(e)}", None, ""

# Create Gradio interface
with gr.Blocks(title="Voice RAG Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎙️ Voice RAG Agent")
    gr.Markdown("""
    Get voice-powered answers to your documentation questions by configuring your API keys and uploading PDF documents.
    Then, simply ask questions to receive both text and voice responses!
    """)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔑 API Configuration")
            qdrant_url = gr.Textbox(label="Qdrant URL", type="password")
            qdrant_api_key = gr.Textbox(label="Qdrant API Key", type="password")
            openai_api_key = gr.Textbox(label="OpenAI API Key", type="password")

            setup_btn = gr.Button("Configure System", variant="primary")
            setup_status = gr.Textbox(label="Status", interactive=False)

        with gr.Column():
            gr.Markdown("### 🎤 Voice Settings")
            voice = gr.Dropdown(
                choices=["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"],
                value="coral",
                label="Select Voice"
            )

            gr.Markdown("### 📚 Processed Documents")
            docs_list = gr.Textbox(label="Documents", interactive=False, lines=3)

    gr.Markdown("---")

    with gr.Row():
        with gr.Column():
            pdf_upload = gr.File(label="Upload PDF", file_types=[".pdf"], interactive=False)
            upload_status = gr.Textbox(label="Upload Status", interactive=False)

    gr.Markdown("---")

    query = gr.Textbox(
        label="What would you like to know about the documentation?",
        placeholder="e.g., How do I authenticate API requests?"
    )

    ask_btn = gr.Button("🚀 Ask Question", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Response")
            response_text = gr.Textbox(label="Text Response", lines=10)

            gr.Markdown("### 🔊 Audio Response")
            audio_output = gr.Audio(label="Listen to Response")

            gr.Markdown("### Sources")
            sources_output = gr.Textbox(label="Source Files", lines=3)

    setup_btn.click(
        fn=setup_system,
        inputs=[qdrant_url, qdrant_api_key, openai_api_key],
        outputs=[setup_status, pdf_upload]
    )

    pdf_upload.upload(
        fn=upload_pdf,
        inputs=[pdf_upload],
        outputs=[upload_status, docs_list]
    )

    ask_btn.click(
        fn=ask_question,
        inputs=[query, voice],
        outputs=[response_text, audio_output, sources_output]
    )

if __name__ == "__main__":
    demo.launch(share=False)
