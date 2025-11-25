import tempfile
import gradio as gr
from embedchain import App
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Tuple
import os

# Global variables
app = None
db_path = None
current_video_url = None
transcript_loaded = False
transcript_text = None
word_count = 0

def extract_video_id(video_url: str) -> str:
    if "youtube.com/watch?v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtube.com/shorts/" in video_url:
        return video_url.split("/shorts/")[-1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")

def fetch_video_data(video_url: str) -> Tuple[str, str]:
    try:
        video_id = extract_video_id(video_url)

        # Create API instance
        api = YouTubeTranscriptApi()

        # First, check if transcripts are available
        try:
            transcript_list = api.list(video_id)
            available_languages = [t.language_code for t in transcript_list]
            status_msg = f"Available transcripts: {available_languages}"
        except Exception as list_error:
            return "Unknown", f"Cannot retrieve transcript list: {list_error}"

        # Try to get transcript with multiple fallback languages
        languages_to_try = ['en', 'en-US', 'en-GB']
        transcript = None

        for lang in languages_to_try:
            if lang in available_languages:
                try:
                    fetched_transcript = api.fetch(video_id, languages=[lang])
                    transcript = list(fetched_transcript)
                    status_msg += f"\nSuccessfully fetched transcript in language: {lang}"
                    break
                except Exception:
                    continue

        # If no English transcript, try any available language
        if transcript is None and available_languages:
            try:
                fetched_transcript = api.fetch(video_id, languages=[available_languages[0]])
                transcript = list(fetched_transcript)
                status_msg += f"\nSuccessfully fetched transcript in language: {available_languages[0]}"
            except Exception as final_error:
                return "Unknown", f"Could not fetch transcript in any language: {final_error}"

        if transcript:
            transcript_text = " ".join([snippet.text for snippet in transcript])
            return "Unknown", transcript_text
        else:
            return "Unknown", "No transcript available for this video."

    except ValueError as ve:
        return "Unknown", f"Invalid YouTube URL: {ve}"
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        if "VideoUnavailable" in error_type:
            return "Unknown", "Video is unavailable, private, or has been removed."
        elif "TranscriptsDisabled" in error_type:
            return "Unknown", "Subtitles/transcripts are disabled for this video."
        elif "NoTranscriptFound" in error_type:
            return "Unknown", "No transcript found in the requested language."
        elif "ParseError" in error_type:
            return "Unknown", "Unable to parse video data."
        else:
            return "Unknown", f"Error fetching transcript ({error_type}): {error_msg}"

def initialize_embedchain(api_key):
    """Initialize Embedchain bot with API key"""
    global app, db_path
    if not api_key:
        return "Please provide an OpenAI API key"

    try:
        db_path = tempfile.mkdtemp()
        app = App.from_config(
            config={
                "llm": {"provider": "openai", "config": {"model": "gpt-4", "temperature": 0.5, "api_key": api_key}},
                "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
                "embedder": {"provider": "openai", "config": {"api_key": api_key}},
            }
        )
        return "App initialized successfully! Now enter a YouTube video URL."
    except Exception as e:
        return f"Error initializing app: {str(e)}"

def load_video(video_url):
    """Load YouTube video transcript to knowledge base"""
    global app, current_video_url, transcript_loaded, transcript_text, word_count

    if app is None:
        return "Please initialize the app with your OpenAI API key first", ""

    if not video_url:
        return "Please enter a YouTube video URL", ""

    try:
        title, transcript = fetch_video_data(video_url)

        if transcript != "No transcript available for this video." and "Invalid YouTube URL" not in transcript and "Error" not in transcript:
            # Clear previous video data if it exists
            if transcript_loaded:
                db_path_new = tempfile.mkdtemp()
                app = App.from_config(
                    config={
                        "llm": {"provider": "openai", "config": {"model": "gpt-4", "temperature": 0.5}},
                        "vectordb": {"provider": "chroma", "config": {"dir": db_path_new}},
                        "embedder": {"provider": "openai"},
                    }
                )

            app.add(transcript, data_type="text", metadata={"title": title, "url": video_url})

            # Store in global variables
            current_video_url = video_url
            transcript_loaded = True
            transcript_text = transcript
            word_count = len(transcript.split())

            return f"Added video to knowledge base! You can now ask questions about it.\nTranscript contains {word_count} words", video_url
        else:
            transcript_loaded = False
            current_video_url = None
            return f"Cannot add video to knowledge base: {transcript}", ""

    except Exception as e:
        transcript_loaded = False
        current_video_url = None
        return f"Error processing video: {e}", ""

def clear_video():
    """Clear current video"""
    global app, current_video_url, transcript_loaded, transcript_text, word_count
    transcript_loaded = False
    current_video_url = None
    transcript_text = None
    word_count = 0
    app = None
    return "", "", []

def chat_with_video(message, history):
    """Chat with YouTube video"""
    global app, transcript_loaded

    if not transcript_loaded or app is None:
        return history + [[message, "Please add a valid video with transcripts first before asking questions."]]

    if not message:
        return history

    try:
        answer = app.chat(message)
        return history + [[message, answer]]
    except Exception as e:
        return history + [[message, f"Error chatting with the video: {e}"]]

# Create Gradio interface
with gr.Blocks(title="Chat with YouTube Video", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chat with YouTube Video")
    gr.Markdown("This app allows you to chat with a YouTube video using OpenAI API")

    with gr.Accordion("How to use this app", open=False):
        gr.Markdown("""
        1. **Enter your OpenAI API key** (required for AI responses)
        2. **Paste a YouTube video URL** (must have subtitles/transcripts available)
        3. **Wait for the transcript to load** (you'll see confirmation messages)
        4. **Ask questions** about the video content

        **Note:** This app only works with videos that have:
        - Auto-generated subtitles, OR
        - Manually uploaded captions/transcripts

        **Common issues:**
        - "Transcripts disabled" = Video doesn't have subtitles
        - "Video unavailable" = Video might be private, restricted, or removed
        - Try popular educational videos (TED talks, tutorials, etc.) for best results
        """)

    with gr.Accordion("Try these working example videos", open=False):
        gr.Markdown("""
        **Working test videos (copy and paste these URLs):**
        ```
        https://www.youtube.com/watch?v=9bZkp7q19f0
        https://www.youtube.com/watch?v=UF8uR6Z6KLc
        https://www.youtube.com/watch?v=_uQrJ0TkZlc
        ```
        These videos are confirmed to have accessible transcripts.
        """)

    with gr.Row():
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            init_btn = gr.Button("Initialize App", variant="primary")
            init_status = gr.Textbox(label="Initialization Status", interactive=False)

            gr.Markdown("---")

            video_url = gr.Textbox(
                label="YouTube Video URL",
                placeholder="e.g., https://www.youtube.com/watch?v=..."
            )
            load_btn = gr.Button("Load Video")
            load_status = gr.Textbox(label="Load Status", interactive=False, lines=3)

            current_video_display = gr.Textbox(
                label="Current Video",
                interactive=False
            )
            clear_btn = gr.Button("Clear Video")

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat with Video", height=500)
            msg = gr.Textbox(
                label="Ask a question about the video",
                placeholder="Type your question here..."
            )
            clear_chat = gr.Button("Clear Chat")

    # Event handlers
    init_btn.click(fn=initialize_embedchain, inputs=[api_key], outputs=[init_status])
    load_btn.click(fn=load_video, inputs=[video_url], outputs=[load_status, current_video_display])
    clear_btn.click(fn=clear_video, outputs=[current_video_display, load_status, chatbot])
    msg.submit(fn=chat_with_video, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", None, msg)  # Clear input after submit
    clear_chat.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch()
