from crewai import Agent, Task, Crew
import gradio as gr
from langchain_openai import ChatOpenAI
import requests
from uuid import uuid4
import os

def generate_music(openai_key, models_lab_key, prompt):
    if not all([openai_key, models_lab_key, prompt]):
        return None, "Please provide all required inputs"

    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)

        # Create music generation agent
        agent = Agent(
            role="Music Generation Expert",
            goal="Create detailed music generation prompts and coordinate music creation",
            backstory="""You are an AI music expert who understands how to craft
            detailed prompts for music generation. You specify genre, style, instruments,
            tempo, mood, and structure to create high-quality music.""",
            llm=llm,
            verbose=True
        )

        # Create task to enhance the prompt
        task = Task(
            description=f"""Transform this music request into a detailed prompt: '{prompt}'.
            Specify: genre, instruments, tempo, mood, structure. Return ONLY the enhanced prompt text.""",
            agent=agent,
            expected_output="A detailed music generation prompt"
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        enhanced_prompt = result.raw if hasattr(result, 'raw') else str(result)

        # Call ModelsLab API directly
        api_url = "https://modelslab.com/api/v6/music/text2music"
        headers = {"Content-Type": "application/json"}
        payload = {
            "key": models_lab_key,
            "prompt": enhanced_prompt,
            "duration": 30
        }

        response = requests.post(api_url, json=payload, headers=headers)

        if response.ok:
            data = response.json()
            if data.get("status") == "success" and data.get("output"):
                audio_url = data["output"][0] if isinstance(data["output"], list) else data["output"]

                # Download the audio
                audio_response = requests.get(audio_url)
                if audio_response.ok:
                    save_dir = "/tmp/audio_generations"
                    os.makedirs(save_dir, exist_ok=True)
                    filename = f"{save_dir}/music_{uuid4()}.mp3"

                    with open(filename, "wb") as f:
                        f.write(audio_response.content)

                    return filename, f"Music generated successfully!\n\nEnhanced prompt: {enhanced_prompt}"
                else:
                    return None, f"Failed to download audio. Status: {audio_response.status_code}"
            else:
                return None, f"API Error: {data.get('message', 'Unknown error')}"
        else:
            return None, f"API request failed. Status: {response.status_code}"

    except Exception as e:
        return None, f"An error occurred: {e}"

def create_app():
    with gr.Blocks(title="Music Generator Agent") as app:
        gr.Markdown("# ModelsLab Music Generator")
        gr.Markdown("Generate music using AI with CrewAI agents")

        with gr.Row():
            with gr.Column():
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )
                models_lab_key = gr.Textbox(
                    label="ModelsLab API Key",
                    type="password",
                    placeholder="Enter your ModelsLab API Key"
                )
                prompt = gr.Textbox(
                    label="Music Generation Prompt",
                    placeholder="Generate a 30 second classical music piece",
                    lines=3
                )
                generate_btn = gr.Button("Generate Music", variant="primary")

        with gr.Row():
            with gr.Column():
                audio_output = gr.Audio(label="Generated Music", type="filepath")
                info_output = gr.Textbox(label="Generation Info", lines=5)

        generate_btn.click(
            fn=generate_music,
            inputs=[openai_key, models_lab_key, prompt],
            outputs=[audio_output, info_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
