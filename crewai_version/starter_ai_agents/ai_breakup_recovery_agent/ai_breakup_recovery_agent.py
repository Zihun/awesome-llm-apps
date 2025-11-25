from crewai import Agent, Task, Crew
import gradio as gr
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List
import logging
from pathlib import Path
import tempfile
import os
from PIL import Image as PILImage
import base64

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def initialize_agents(api_key: str) -> tuple:
    try:
        genai.configure(api_key=api_key)
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=api_key)

        therapist_agent = Agent(
            role="Empathetic Therapist",
            goal="Provide emotional support and validate feelings",
            backstory="""You are an empathetic therapist that:
            1. Listens with empathy and validates feelings
            2. Uses gentle humor to lighten the mood
            3. Shares relatable breakup experiences
            4. Offers comforting words and encouragement
            5. Analyzes both text and image inputs for emotional context
            Be supportive and understanding in your responses""",
            llm=llm,
            verbose=True
        )

        closure_agent = Agent(
            role="Closure Specialist",
            goal="Help create emotional closure and express unsent feelings",
            backstory="""You are a closure specialist that:
            1. Creates emotional messages for unsent feelings
            2. Helps express raw, honest emotions
            3. Formats messages clearly with headers
            4. Ensures tone is heartfelt and authentic
            Focus on emotional release and closure""",
            llm=llm,
            verbose=True
        )

        routine_planner_agent = Agent(
            role="Recovery Routine Planner",
            goal="Design practical 7-day recovery challenges",
            backstory="""You are a recovery routine planner that:
            1. Designs 7-day recovery challenges
            2. Includes fun activities and self-care tasks
            3. Suggests social media detox strategies
            4. Creates empowering playlists
            Focus on practical recovery steps""",
            llm=llm,
            verbose=True
        )

        brutal_honesty_agent = Agent(
            role="Direct Feedback Specialist",
            goal="Provide raw, objective feedback about breakups",
            backstory="""You are a direct feedback specialist that:
            1. Gives raw, objective feedback about breakups
            2. Explains relationship failures clearly
            3. Uses blunt, factual language
            4. Provides reasons to move forward
            Focus on honest insights without sugar-coating""",
            llm=llm,
            verbose=True
        )

        return therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent
    except Exception as e:
        logger.error(f"Error initializing agents: {str(e)}")
        return None, None, None, None

def process_recovery_plan(api_key, user_input, uploaded_files):
    if not api_key:
        return "Please enter your API key first!", "", "", ""

    if not user_input and not uploaded_files:
        return "Please share your feelings or upload screenshots to get help.", "", "", ""

    therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent = initialize_agents(api_key)

    if not all([therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent]):
        return "Failed to initialize agents. Please check your API key.", "", "", ""

    try:
        # Process images if uploaded
        image_context = ""
        if uploaded_files:
            image_context = f"\n\nUser uploaded {len(uploaded_files)} screenshot(s) for context."

        # Therapist Analysis
        therapist_prompt = f"""
        Analyze the emotional state and provide empathetic support based on:
        User's message: {user_input}
        {image_context}

        Please provide a compassionate response with:
        1. Validation of feelings
        2. Gentle words of comfort
        3. Relatable experiences
        4. Words of encouragement
        """

        therapist_task = Task(
            description=therapist_prompt,
            agent=therapist_agent,
            expected_output="Compassionate emotional support response"
        )

        # Closure Messages
        closure_prompt = f"""
        Help create emotional closure based on:
        User's feelings: {user_input}
        {image_context}

        Please provide:
        1. Template for unsent messages
        2. Emotional release exercises
        3. Closure rituals
        4. Moving forward strategies
        """

        closure_task = Task(
            description=closure_prompt,
            agent=closure_agent,
            expected_output="Closure messages and exercises"
        )

        # Recovery Plan
        routine_prompt = f"""
        Design a 7-day recovery plan based on:
        Current state: {user_input}
        {image_context}

        Include:
        1. Daily activities and challenges
        2. Self-care routines
        3. Social media guidelines
        4. Mood-lifting music suggestions
        """

        routine_task = Task(
            description=routine_prompt,
            agent=routine_planner_agent,
            expected_output="7-day recovery plan"
        )

        # Honest Feedback
        honesty_prompt = f"""
        Provide honest, constructive feedback about:
        Situation: {user_input}
        {image_context}

        Include:
        1. Objective analysis
        2. Growth opportunities
        3. Future outlook
        4. Actionable steps
        """

        honesty_task = Task(
            description=honesty_prompt,
            agent=brutal_honesty_agent,
            expected_output="Honest perspective and feedback"
        )

        # Create crew and execute
        crew = Crew(
            agents=[therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent],
            tasks=[therapist_task, closure_task, routine_task, honesty_task],
            verbose=True
        )

        result = crew.kickoff()

        # Parse results
        tasks_output = result.tasks_output if hasattr(result, 'tasks_output') else []

        therapist_result = tasks_output[0].raw if len(tasks_output) > 0 else "No response"
        closure_result = tasks_output[1].raw if len(tasks_output) > 1 else "No response"
        routine_result = tasks_output[2].raw if len(tasks_output) > 2 else "No response"
        honesty_result = tasks_output[3].raw if len(tasks_output) > 3 else "No response"

        return therapist_result, closure_result, routine_result, honesty_result

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return f"An error occurred: {str(e)}", "", "", ""

def create_app():
    with gr.Blocks(title="Breakup Recovery Squad") as app:
        gr.Markdown("# Breakup Recovery Squad")
        gr.Markdown("### Your AI-powered breakup recovery team is here to help!")
        gr.Markdown("Share your feelings and chat screenshots, and we'll help you navigate through this tough time.")

        with gr.Row():
            with gr.Column(scale=3):
                api_key_input = gr.Textbox(
                    label="Gemini API Key",
                    type="password",
                    placeholder="Enter your Gemini API Key"
                )
                gr.Markdown("""
                To get your API key:
                1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
                2. Enable the Generative Language API in your [Google Cloud Console](https://console.developers.google.com/apis/api/generativelanguage.googleapis.com)
                """)

                user_input = gr.Textbox(
                    label="Share Your Feelings",
                    placeholder="Tell us your story...",
                    lines=5
                )

                uploaded_files = gr.File(
                    label="Upload Chat Screenshots (optional)",
                    file_count="multiple",
                    file_types=["image"]
                )

                submit_btn = gr.Button("Get Recovery Plan", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown("### Configuration")
                gr.Markdown("Please enter your API key to proceed")

        gr.Markdown("## Your Personalized Recovery Plan")

        with gr.Tab("Emotional Support"):
            therapist_output = gr.Markdown()

        with gr.Tab("Finding Closure"):
            closure_output = gr.Markdown()

        with gr.Tab("Your Recovery Plan"):
            routine_output = gr.Markdown()

        with gr.Tab("Honest Perspective"):
            honesty_output = gr.Markdown()

        submit_btn.click(
            fn=process_recovery_plan,
            inputs=[api_key_input, user_input, uploaded_files],
            outputs=[therapist_output, closure_output, routine_output, honesty_output]
        )

        gr.Markdown("---")
        gr.Markdown("""
            <div style='text-align: center'>
                <p>Made with love by the Breakup Recovery Squad</p>
                <p>Share your recovery journey with #BreakupRecoverySquad</p>
            </div>
        """)

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
