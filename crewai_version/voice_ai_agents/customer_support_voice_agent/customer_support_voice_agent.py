from typing import List, Dict, Optional
from pathlib import Path
import os
from firecrawl import FirecrawlApp
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from fastembed import TextEmbedding
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
import tempfile
import uuid
from datetime import datetime
import time
import gradio as gr
from dotenv import load_dotenv
import asyncio

load_dotenv()

def setup_qdrant_collection(qdrant_url: str, qdrant_api_key: str, collection_name: str = "docs_embeddings"):
    """Setup Qdrant collection for document embeddings"""
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    embedding_model = TextEmbedding()
    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )
    except Exception as e:
        if "already exists" not in str(e):
            raise e

    return client, embedding_model

def crawl_documentation(firecrawl_api_key: str, url: str, output_dir: Optional[str] = None):
    """Crawl documentation from URL"""
    firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
    pages = []

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    response = firecrawl.crawl_url(
        url,
        params={
            'limit': 5,
            'scrapeOptions': {
                'formats': ['markdown', 'html']
            }
        }
    )

    while True:
        for page in response.get('data', []):
            content = page.get('markdown') or page.get('html', '')
            metadata = page.get('metadata', {})
            source_url = metadata.get('sourceURL', '')

            if output_dir and content:
                filename = f"{uuid.uuid4()}.md"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            pages.append({
                "content": content,
                "url": source_url,
                "metadata": {
                    "title": metadata.get('title', ''),
                    "description": metadata.get('description', ''),
                    "language": metadata.get('language', 'en'),
                    "crawl_date": datetime.now().isoformat()
                }
            })

        next_url = response.get('next')
        if not next_url:
            break

        response = firecrawl.get(next_url)
        time.sleep(1)

    return pages

def store_embeddings(client: QdrantClient, embedding_model: TextEmbedding, pages: List[Dict], collection_name: str):
    """Store document embeddings in Qdrant"""
    for page in pages:
        embedding = list(embedding_model.embed([page["content"]]))[0]
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "content": page["content"],
                        "url": page["url"],
                        **page["metadata"]
                    }
                )
            ]
        )

def setup_agents(openai_api_key: str):
    """Setup CrewAI agents for documentation processing"""
    llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

    processor_agent = Agent(
        role="Documentation Processor",
        goal="""Analyze provided documentation content and answer user questions clearly and concisely.
        Include relevant examples when available. Cite source URLs when referencing specific content.
        Keep responses natural and conversational. Format response in a way that's easy to speak out loud.""",
        backstory="Expert documentation analyst specializing in technical content",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    tts_agent = Agent(
        role="Text-to-Speech Agent",
        goal="""Convert documentation responses into natural speech with proper pacing and emphasis.
        Handle technical terms clearly. Keep tone professional but friendly. Use appropriate pauses
        for better comprehension. Ensure speech is clear and well-articulated.""",
        backstory="Voice synthesis expert specializing in technical content narration",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return processor_agent, tts_agent

async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    processor_agent: Agent,
    tts_agent: Agent,
    collection_name: str,
    openai_api_key: str,
    voice: str
):
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

        # Prepare context
        context = "Based on the following documentation:\n\n"
        for result in search_results:
            payload = result.payload
            if not payload:
                continue
            url = payload.get('url', 'Unknown URL')
            content = payload.get('content', '')
            context += f"From {url}:\n{content}\n\n"

        context += f"\nUser Question: {query}\n\n"
        context += "Please provide a clear, concise answer that can be easily spoken out loud."

        # Create tasks for processor agent
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
        processor_response = str(processor_result)

        # Create tasks for TTS agent
        tts_task = Task(
            description=processor_response,
            expected_output="Voice instructions for natural speech synthesis",
            agent=tts_agent
        )

        tts_crew = Crew(
            agents=[tts_agent],
            tasks=[tts_task],
            verbose=True
        )

        tts_result = tts_crew.kickoff()
        tts_response = str(tts_result)

        # Generate audio
        async_openai = AsyncOpenAI(api_key=openai_api_key)
        audio_response = await async_openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=processor_response,
            instructions=tts_response,
            response_format="mp3"
        )

        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"response_{uuid.uuid4()}.mp3")

        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        return {
            "status": "success",
            "text_response": processor_response,
            "tts_instructions": tts_response,
            "audio_path": audio_path,
            "sources": [r.payload.get("url", "Unknown URL") for r in search_results if r.payload]
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }

# Global state
state = {
    "initialized": False,
    "client": None,
    "embedding_model": None,
    "processor_agent": None,
    "tts_agent": None
}

def initialize_system(qdrant_url, qdrant_api_key, firecrawl_api_key, openai_api_key, doc_url, progress=gr.Progress()):
    """Initialize the system with API keys and documentation"""
    if not all([qdrant_url, qdrant_api_key, firecrawl_api_key, openai_api_key, doc_url]):
        return "Error: Please fill in all required fields!", None

    try:
        progress(0.2, desc="Setting up Qdrant connection...")
        client, embedding_model = setup_qdrant_collection(qdrant_url, qdrant_api_key)
        state["client"] = client
        state["embedding_model"] = embedding_model

        progress(0.4, desc="Crawling documentation pages...")
        pages = crawl_documentation(firecrawl_api_key, doc_url)

        progress(0.6, desc="Storing embeddings...")
        store_embeddings(client, embedding_model, pages, "docs_embeddings")

        progress(0.8, desc="Setting up agents...")
        processor_agent, tts_agent = setup_agents(openai_api_key)
        state["processor_agent"] = processor_agent
        state["tts_agent"] = tts_agent
        state["openai_api_key"] = openai_api_key

        state["initialized"] = True
        progress(1.0, desc="Complete!")

        return f"✅ System initialized successfully! Crawled {len(pages)} documentation pages.", gr.update(interactive=True)

    except Exception as e:
        return f"Error during setup: {str(e)}", None

def process_user_query(query, voice, progress=gr.Progress()):
    """Process user query and generate response"""
    if not state["initialized"]:
        return "Please initialize the system first!", None, ""

    if not query:
        return "Please enter a query!", None, ""

    try:
        progress(0.3, desc="Searching documentation...")

        result = asyncio.run(process_query(
            query,
            state["client"],
            state["embedding_model"],
            state["processor_agent"],
            state["tts_agent"],
            "docs_embeddings",
            state["openai_api_key"],
            voice
        ))

        if result["status"] == "success":
            progress(1.0, desc="Complete!")
            sources_text = "\n".join([f"- {source}" for source in result["sources"]])
            return result["text_response"], result["audio_path"], sources_text
        else:
            return f"Error: {result.get('error', 'Unknown error occurred')}", None, ""

    except Exception as e:
        return f"Error processing query: {str(e)}", None, ""

# Create Gradio interface
with gr.Blocks(title="Customer Support Voice Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎙️ Customer Support Voice Agent")
    gr.Markdown("""
    Get OpenAI SDK voice-powered answers to your documentation questions! Simply:
    1. Configure your API keys below
    2. Enter the documentation URL you want to learn about
    3. Ask your question and get both text and voice responses
    """)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔑 API Configuration")
            qdrant_url = gr.Textbox(label="Qdrant URL", type="password")
            qdrant_api_key = gr.Textbox(label="Qdrant API Key", type="password")
            firecrawl_api_key = gr.Textbox(label="Firecrawl API Key", type="password")
            openai_api_key = gr.Textbox(label="OpenAI API Key", type="password")
            doc_url = gr.Textbox(label="Documentation URL", placeholder="https://docs.example.com")

            init_btn = gr.Button("Initialize System", variant="primary")
            init_status = gr.Textbox(label="Status", interactive=False)

        with gr.Column():
            gr.Markdown("### 🎤 Voice Settings")
            voice = gr.Dropdown(
                choices=["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"],
                value="coral",
                label="Select Voice"
            )

    gr.Markdown("---")

    query = gr.Textbox(
        label="What would you like to know about the documentation?",
        placeholder="e.g., How do I authenticate API requests?",
        interactive=False
    )

    query_btn = gr.Button("🚀 Ask Question", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Response")
            response_text = gr.Textbox(label="Text Response", lines=10)

            gr.Markdown("### 🔊 Audio Response")
            audio_output = gr.Audio(label="Listen to Response")

            gr.Markdown("### Sources")
            sources_output = gr.Textbox(label="Source URLs", lines=5)

    init_btn.click(
        fn=initialize_system,
        inputs=[qdrant_url, qdrant_api_key, firecrawl_api_key, openai_api_key, doc_url],
        outputs=[init_status, query]
    )

    query_btn.click(
        fn=process_user_query,
        inputs=[query, voice],
        outputs=[response_text, audio_output, sources_output]
    )

if __name__ == "__main__":
    demo.launch(share=False)
