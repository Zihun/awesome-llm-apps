from crewai import Agent, Task, Crew
import gradio as gr
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
import tempfile
from pathlib import Path

def analyze_video(api_key, video_file, question):
    if not api_key or video_file is None or not question:
        return "Please provide API key, video, and question"

    try:
        genai.configure(api_key=api_key)

        # Upload video to Gemini
        video_path = video_file if isinstance(video_file, str) else video_file.name

        print(f"Uploading video from: {video_path}")
        video_file_obj = genai.upload_file(path=video_path)

        print(f"Waiting for video processing...")
        # Wait for video to be processed
        import time
        while video_file_obj.state.name == "PROCESSING":
            time.sleep(2)
            video_file_obj = genai.get_file(video_file_obj.name)

        if video_file_obj.state.name == "FAILED":
            return "Video processing failed"

        # Use Gemini model for video analysis
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        prompt = f"""
        First analyze this video and then answer the following question using both
        the video analysis and your knowledge: {question}

        Provide a comprehensive response focusing on practical, actionable information.
        """

        response = model.generate_content([video_file_obj, prompt])

        # Clean up uploaded file
        genai.delete_file(video_file_obj.name)

        return response.text

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="Multimodal AI Agent") as app:
        gr.Markdown("# Multimodal AI Agent")
        gr.Markdown("Upload a video and ask questions about it")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="Gemini API Key",
                    type="password",
                    placeholder="Enter your Gemini API Key"
                )
                gr.Markdown("[Get your API key](https://aistudio.google.com/apikey)")

                video_input = gr.Video(label="Upload Video")

                question_input = gr.Textbox(
                    label="What would you like to know?",
                    placeholder="Ask any question about the video",
                    lines=5
                )

                analyze_btn = gr.Button("Analyze & Research", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="Result")

        analyze_btn.click(
            fn=analyze_video,
            inputs=[api_key, video_input, question_input],
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
