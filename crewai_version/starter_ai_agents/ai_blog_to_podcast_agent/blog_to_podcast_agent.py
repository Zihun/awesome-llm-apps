from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
import gradio as gr
from langchain_openai import ChatOpenAI
from elevenlabs import ElevenLabs
import os

def generate_podcast(openai_key, elevenlabs_key, url):
    if not all([openai_key, elevenlabs_key, url]):
        return None, "Please provide all required inputs"

    try:
        os.environ["OPENAI_API_KEY"] = openai_key

        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)

        # Initialize scraping tool
        scrape_tool = ScrapeWebsiteTool(website_url=url)

        # Create agent for scraping and summarization
        agent = Agent(
            role="Blog Summarizer",
            goal="Scrape the blog and create a concise, engaging summary suitable for a podcast",
            backstory="""You are an expert content curator who transforms blog posts into
            engaging podcast scripts. You create conversational summaries that capture
            the main points in an audio-friendly format.""",
            llm=llm,
            tools=[scrape_tool],
            verbose=True
        )

        # Create task
        task = Task(
            description=f"Scrape and summarize this blog for a podcast (max 2000 characters): {url}. The summary should be conversational and capture the main points.",
            agent=agent,
            expected_output="A concise, engaging podcast script summary"
        )

        # Create crew and execute
        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        summary = result.raw if hasattr(result, 'raw') else str(result)

        if summary:
            # Initialize ElevenLabs client and generate audio
            client = ElevenLabs(api_key=elevenlabs_key)

            # Generate audio using text_to_speech.convert
            audio_generator = client.text_to_speech.convert(
                text=summary,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2"
            )

            # Collect audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                if chunk:
                    audio_chunks.append(chunk)
            audio_bytes = b"".join(audio_chunks)

            # Save to temp file for Gradio
            temp_audio_path = "/tmp/podcast.mp3"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)

            return temp_audio_path, summary
        else:
            return None, "Failed to generate summary"

    except Exception as e:
        return None, f"Error: {e}"

def create_app():
    with gr.Blocks(title="Blog to Podcast Agent") as app:
        gr.Markdown("# Blog to Podcast Agent")
        gr.Markdown("Convert blog posts into podcast audio using AI")

        with gr.Row():
            with gr.Column():
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )
                elevenlabs_key = gr.Textbox(
                    label="ElevenLabs API Key",
                    type="password",
                    placeholder="Enter your ElevenLabs API Key"
                )
                url = gr.Textbox(
                    label="Blog URL",
                    placeholder="Enter the blog URL"
                )
                generate_btn = gr.Button("Generate Podcast", variant="primary")

        with gr.Row():
            with gr.Column():
                audio_output = gr.Audio(label="Generated Podcast", type="filepath")
                summary_output = gr.Textbox(label="Podcast Summary", lines=10)

        generate_btn.click(
            fn=generate_podcast,
            inputs=[openai_key, elevenlabs_key, url],
            outputs=[audio_output, summary_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
