from crewai import Agent, Task, Crew
import gradio as gr
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
import tempfile
import os
from PIL import Image as PILImage

def analyze_image(api_key, image, question):
    if not api_key or image is None or not question:
        return "Please provide API key, image, and question"

    try:
        genai.configure(api_key=api_key)
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=api_key)

        # Save image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            if isinstance(image, str):
                # If image is a file path
                img = PILImage.open(image)
            else:
                img = image
            img.save(tmp_file.name)
            temp_path = tmp_file.name

        # For multimodal, we'll use Gemini directly
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        img_obj = PILImage.open(temp_path)

        response = model.generate_content([question, img_obj])

        # Clean up
        os.unlink(temp_path)

        return response.text

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="Multimodal Reasoning AI Agent") as app:
        gr.Markdown("# Multimodal Reasoning AI Agent")
        gr.Markdown("Upload an image and provide a reasoning-based task for the AI Agent")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="Gemini API Key",
                    type="password",
                    placeholder="Enter your Gemini API Key"
                )
                gr.Markdown("[Get your API key from Google AI Studio](https://aistudio.google.com/apikey)")

                image_input = gr.Image(
                    label="Upload Image",
                    type="pil"
                )

                question_input = gr.Textbox(
                    label="Your Question/Task",
                    placeholder="What would you like to know about this image?",
                    lines=5
                )

                analyze_btn = gr.Button("Analyze Image", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="AI Response")

        analyze_btn.click(
            fn=analyze_image,
            inputs=[api_key, image_input, question_input],
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
