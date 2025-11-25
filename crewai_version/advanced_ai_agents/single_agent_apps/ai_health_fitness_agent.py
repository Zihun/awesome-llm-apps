import os
import gradio as gr
from crewai import Agent, Task, Crew
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def create_health_fitness_agents(gemini_api_key: str):
    """Create dietary and fitness expert agents"""

    # Configure Gemini
    genai.configure(api_key=gemini_api_key)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=gemini_api_key,
        temperature=0.7
    )

    dietary_agent = Agent(
        role="Dietary Expert",
        goal="Provide personalized dietary recommendations tailored to individual needs",
        backstory="""\
            You are a certified nutritionist with over 15 years of experience in creating
            personalized meal plans. You excel at considering dietary restrictions, preferences,
            and health goals to design optimal nutrition strategies. Your recommendations are
            always practical, balanced, and focused on long-term health.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    fitness_agent = Agent(
        role="Fitness Expert",
        goal="Provide personalized fitness recommendations for various fitness goals",
        backstory="""\
            You are a certified personal trainer and exercise physiologist with extensive
            experience in designing workout programs for people of all fitness levels.
            You understand biomechanics, exercise science, and how to create safe yet
            effective training routines tailored to individual goals and constraints.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return dietary_agent, fitness_agent

def generate_dietary_plan(
    age: int,
    weight: float,
    height: float,
    sex: str,
    activity_level: str,
    dietary_preferences: str,
    fitness_goals: str,
    gemini_api_key: str
) -> str:
    """Generate personalized dietary plan"""

    try:
        dietary_agent, _ = create_health_fitness_agents(gemini_api_key)

        user_profile = f"""
        Age: {age}
        Weight: {weight}kg
        Height: {height}cm
        Sex: {sex}
        Activity Level: {activity_level}
        Dietary Preferences: {dietary_preferences}
        Fitness Goals: {fitness_goals}
        """

        task = Task(
            description=f"""\
                Create a comprehensive daily dietary plan for the following profile:
                {user_profile}

                Your plan should include:
                1. A brief explanation of why this plan suits the user's goals
                2. Detailed meal plan for breakfast, lunch, dinner, and snacks
                3. Approximate macronutrient breakdown for each meal
                4. Hydration recommendations
                5. Important considerations (electrolytes, fiber, etc.)

                Consider the user's dietary restrictions and preferences carefully.
                Ensure recommendations are clear, actionable, and high-quality.
            """,
            agent=dietary_agent,
            expected_output="A detailed daily dietary plan with meal recommendations and nutritional guidance"
        )

        crew = Crew(
            agents=[dietary_agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error generating dietary plan: {str(e)}"

def generate_fitness_plan(
    age: int,
    weight: float,
    height: float,
    sex: str,
    activity_level: str,
    dietary_preferences: str,
    fitness_goals: str,
    gemini_api_key: str
) -> str:
    """Generate personalized fitness plan"""

    try:
        _, fitness_agent = create_health_fitness_agents(gemini_api_key)

        user_profile = f"""
        Age: {age}
        Weight: {weight}kg
        Height: {height}cm
        Sex: {sex}
        Activity Level: {activity_level}
        Dietary Preferences: {dietary_preferences}
        Fitness Goals: {fitness_goals}
        """

        task = Task(
            description=f"""\
                Create a comprehensive fitness plan for the following profile:
                {user_profile}

                Your plan should include:
                1. Clear fitness goals based on user's objectives
                2. Warm-up exercises (5-10 minutes)
                3. Main workout routine with specific exercises, sets, and reps
                4. Cool-down and stretching (5-10 minutes)
                5. Benefits of each recommended exercise
                6. Progress tracking tips
                7. Rest and recovery recommendations

                Ensure exercises are tailored to the user's current fitness level and goals.
                The plan should be actionable, detailed, and safe.
            """,
            agent=fitness_agent,
            expected_output="A detailed fitness plan with exercise routines and progression guidance"
        )

        crew = Crew(
            agents=[fitness_agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error generating fitness plan: {str(e)}"

def answer_question(
    question: str,
    dietary_plan: str,
    fitness_plan: str,
    gemini_api_key: str
) -> str:
    """Answer questions about the generated plans"""

    try:
        genai.configure(api_key=gemini_api_key)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=gemini_api_key,
            temperature=0.7
        )

        qa_agent = Agent(
            role="Health & Fitness Advisor",
            goal="Answer questions about dietary and fitness plans",
            backstory="You are a knowledgeable health advisor who can explain plans and answer questions.",
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        context = f"""
        Dietary Plan:
        {dietary_plan}

        Fitness Plan:
        {fitness_plan}

        User Question: {question}
        """

        task = Task(
            description=f"Answer the following question based on the provided plans:\n{context}",
            agent=qa_agent,
            expected_output="A clear, helpful answer to the user's question"
        )

        crew = Crew(
            agents=[qa_agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error answering question: {str(e)}"

def create_interface():
    """Create Gradio interface"""

    custom_css = """
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
        margin: 1rem 0;
    }
    """

    with gr.Blocks(title="AI Health & Fitness Planner", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.HTML("""
            <div class="main-header">
                <h1>🏋️‍♂️ AI Health & Fitness Planner</h1>
                <p>Get personalized dietary and fitness plans tailored to your goals and preferences</p>
            </div>
        """)

        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("## 👤 Your Profile")

                with gr.Row():
                    age = gr.Number(label="Age", value=25, minimum=10, maximum=100)
                    sex = gr.Dropdown(
                        label="Sex",
                        choices=["Male", "Female", "Other"],
                        value="Male"
                    )

                with gr.Row():
                    weight = gr.Number(label="Weight (kg)", value=70, minimum=20, maximum=300)
                    height = gr.Number(label="Height (cm)", value=170, minimum=100, maximum=250)

                with gr.Row():
                    activity_level = gr.Dropdown(
                        label="Activity Level",
                        choices=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                        value="Moderately Active"
                    )

                with gr.Row():
                    dietary_preferences = gr.Dropdown(
                        label="Dietary Preferences",
                        choices=["Vegetarian", "Keto", "Gluten Free", "Low Carb", "Dairy Free", "No Restrictions"],
                        value="No Restrictions"
                    )
                    fitness_goals = gr.Dropdown(
                        label="Fitness Goals",
                        choices=["Lose Weight", "Gain Muscle", "Endurance", "Stay Fit", "Strength Training"],
                        value="Stay Fit"
                    )

                generate_btn = gr.Button("🎯 Generate My Personalized Plan", variant="primary", size="lg")

            with gr.Column(scale=1):
                gemini_key = gr.Textbox(
                    label="Gemini API Key",
                    type="password",
                    placeholder="Enter your Gemini API key",
                    value=GEMINI_API_KEY or ""
                )

                gr.Markdown(
                    """
                    ### 📋 What You'll Get:
                    - Personalized dietary plan
                    - Custom fitness routine
                    - Nutritional guidance
                    - Exercise instructions
                    - Progress tracking tips

                    ### 🔑 Get API Key:
                    [Get Gemini API Key](https://aistudio.google.com/apikey)
                    """
                )

        with gr.Row():
            with gr.Column():
                dietary_output = gr.Markdown(label="📋 Your Dietary Plan")
            with gr.Column():
                fitness_output = gr.Markdown(label="💪 Your Fitness Plan")

        gr.Markdown("## ❓ Questions About Your Plan?")
        with gr.Row():
            question_input = gr.Textbox(
                label="Ask a Question",
                placeholder="E.g., Can I substitute chicken with tofu? How many rest days should I take?",
                lines=2
            )
            ask_btn = gr.Button("Get Answer", variant="secondary")

        answer_output = gr.Markdown(label="💬 Answer")

        # Store plans in state
        dietary_plan_state = gr.State("")
        fitness_plan_state = gr.State("")

        def generate_plans(age, weight, height, sex, activity, diet_pref, fit_goals, api_key):
            if not api_key:
                return "⚠️ Please provide your Gemini API key.", "⚠️ Please provide your Gemini API key.", "", ""

            dietary = generate_dietary_plan(age, weight, height, sex, activity, diet_pref, fit_goals, api_key)
            fitness = generate_fitness_plan(age, weight, height, sex, activity, diet_pref, fit_goals, api_key)
            return dietary, fitness, dietary, fitness

        generate_btn.click(
            fn=generate_plans,
            inputs=[age, weight, height, sex, activity_level, dietary_preferences, fitness_goals, gemini_key],
            outputs=[dietary_output, fitness_output, dietary_plan_state, fitness_plan_state]
        )

        ask_btn.click(
            fn=answer_question,
            inputs=[question_input, dietary_plan_state, fitness_plan_state, gemini_key],
            outputs=answer_output
        )

        gr.Examples(
            examples=[
                [25, 70, 175, "Male", "Moderately Active", "No Restrictions", "Gain Muscle"],
                [35, 85, 168, "Female", "Lightly Active", "Vegetarian", "Lose Weight"],
                [45, 90, 180, "Male", "Very Active", "Low Carb", "Endurance"],
            ],
            inputs=[age, weight, height, sex, activity_level, dietary_preferences, fitness_goals]
        )

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
