import gradio as gr
import asyncio
from manager import TourManager
from pathlib import Path
from openai import OpenAI

def tts(text, api_key):
    """Convert text to speech using OpenAI TTS"""
    client = OpenAI(api_key=api_key)
    speech_file_path = Path(__file__).parent / "speech_tour.mp3"

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="nova",
        input=text,
        instructions="""You are a friendly and engaging tour guide. Speak naturally and conversationally, as if you're walking alongside the visitor.
        Use a warm, inviting tone throughout. Avoid robotic or formal language. Make the tour feel like a casual conversation with a knowledgeable friend.
        Use natural transitions between topics and maintain an enthusiastic but relaxed pace."""
    )
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)

def run_async(func, *args, **kwargs):
    """Helper to run async functions"""
    try:
        return asyncio.run(func(*args, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

def generate_tour(location, interests, duration, api_key):
    """Generate audio tour based on inputs"""
    if not api_key:
        return "Please enter your OpenAI API key.", None, None

    if not location:
        return "Please enter a location.", None, None

    if not interests:
        return "Please select at least one interest.", None, None

    # Create tour manager
    mgr = TourManager(openai_api_key=api_key)

    # Generate tour content
    final_tour = run_async(mgr.run, location, interests, duration)

    # Generate audio
    tour_audio = tts(final_tour, api_key)

    return final_tour, tour_audio, tour_audio

# Create Gradio interface
with gr.Blocks(title="AI Audio Tour Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎧 AI Audio Tour Agent")
    gr.Markdown("""
    Welcome to your personalized audio tour guide! I'll help you explore any location with an engaging,
    natural-sounding tour tailored to your interests.
    """)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🔑 Settings")
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key..."
            )

            gr.Markdown("### 📍 Where would you like to explore?")
            location = gr.Textbox(
                label="Location",
                placeholder="Enter a city, landmark, or location..."
            )

            gr.Markdown("### 🎯 What interests you?")
            interests = gr.CheckboxGroup(
                choices=["History", "Architecture", "Culinary", "Culture"],
                value=["History", "Architecture"],
                label="Select your interests"
            )

        with gr.Column(scale=1):
            gr.Markdown("### ⏱️ Tour Settings")
            duration = gr.Slider(
                minimum=5,
                maximum=60,
                value=10,
                step=5,
                label="Tour Duration (minutes)"
            )

            gr.Markdown("### 🎙️ Voice Settings")
            voice_style = gr.Dropdown(
                choices=["Friendly & Casual", "Professional & Detailed", "Enthusiastic & Energetic"],
                value="Friendly & Casual",
                label="Guide's Voice Style"
            )

    generate_btn = gr.Button("🎧 Generate Tour", variant="primary", size="lg")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📝 Tour Content")
            tour_content = gr.Textbox(
                label="Generated Tour",
                lines=15,
                max_lines=20
            )

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🎧 Listen to Your Tour")
            audio_output = gr.Audio(
                label="Audio Tour",
                type="filepath"
            )

            download_audio = gr.File(
                label="📥 Download Audio Tour"
            )

    generate_btn.click(
        fn=generate_tour,
        inputs=[location, interests, duration, api_key],
        outputs=[tour_content, audio_output, download_audio]
    )

if __name__ == "__main__":
    demo.launch(share=False)
