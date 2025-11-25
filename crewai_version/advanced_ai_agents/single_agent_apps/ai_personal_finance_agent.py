import os
import gradio as gr
from textwrap import dedent
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def create_financial_planning_crew(openai_api_key: str, serper_api_key: str):
    """Create financial planning crew with researcher and planner agents"""

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=openai_api_key,
        temperature=0.7
    )

    # Initialize search tool
    search_tool = SerperDevTool(api_key=serper_api_key)

    # Create researcher agent
    researcher = Agent(
        role="Financial Research Specialist",
        goal="Search for financial advice, investment opportunities, and savings strategies based on user preferences",
        backstory=dedent("""\
            You are a world-class financial researcher with extensive experience in analyzing
            market trends, investment opportunities, and savings strategies. You excel at finding
            the most relevant and up-to-date financial information from various sources.
        """),
        tools=[search_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Create planner agent
    planner = Agent(
        role="Senior Financial Planner",
        goal="Generate personalized financial plans based on user preferences and research results",
        backstory=dedent("""\
            You are a senior financial planner with over 20 years of experience in creating
            personalized financial strategies. You excel at translating research insights into
            actionable, well-structured financial plans that meet individual needs and preferences.
            You always provide nuanced and balanced advice, citing facts where possible.
        """),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return researcher, planner

def generate_financial_plan(
    financial_goals: str,
    current_situation: str,
    openai_api_key: str,
    serper_api_key: str,
    progress=gr.Progress()
) -> str:
    """Generate personalized financial plan"""

    if not openai_api_key or not serper_api_key:
        return "Error: Please provide both OpenAI and Serper API keys."

    if not financial_goals or not current_situation:
        return "Error: Please provide both your financial goals and current financial situation."

    try:
        progress(0.1, desc="Initializing financial planning crew...")
        researcher, planner = create_financial_planning_crew(openai_api_key, serper_api_key)

        # Create research task
        progress(0.3, desc="Researching financial strategies...")
        research_task = Task(
            description=dedent(f"""\
                Given the user's financial goals and current situation, perform comprehensive research:

                Financial Goals: {financial_goals}
                Current Situation: {current_situation}

                Steps:
                1. Generate 3 specific search terms related to these financial goals
                2. Search for each term and analyze the results
                3. From all search results, identify the 10 most relevant findings
                4. Focus on quality over quantity in your research

                Provide a detailed summary of your research findings.
            """),
            agent=researcher,
            expected_output="Detailed research findings with the 10 most relevant financial insights and opportunities"
        )

        # Create planning task
        progress(0.6, desc="Creating personalized financial plan...")
        planning_task = Task(
            description=dedent(f"""\
                Based on the research findings and the user's information, create a comprehensive
                personalized financial plan.

                Financial Goals: {financial_goals}
                Current Situation: {current_situation}

                Your plan should include:
                1. Suggested budget breakdown
                2. Investment recommendations with rationale
                3. Savings strategies
                4. Timeline and milestones
                5. Risk considerations
                6. Action steps

                Ensure the plan is:
                - Well-structured and easy to follow
                - Informative and engaging
                - Nuanced and balanced
                - Supported by facts from the research
                - Focused on clarity and quality
                - Properly attributed (never make up facts)
            """),
            agent=planner,
            expected_output="A comprehensive, personalized financial plan with budgets, investment recommendations, and savings strategies"
        )

        # Create and run crew
        progress(0.8, desc="Finalizing your financial plan...")
        crew = Crew(
            agents=[researcher, planner],
            tasks=[research_task, planning_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        progress(1.0, desc="Complete!")

        return str(result)

    except Exception as e:
        return f"Error generating financial plan: {str(e)}"

def create_interface():
    """Create Gradio interface"""

    with gr.Blocks(title="AI Personal Finance Planner", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # AI Personal Finance Planner
            Manage your finances with AI Personal Finance Manager by creating personalized budgets,
            investment plans, and savings strategies using GPT-4o

            This AI-powered financial planner will:
            - Research the latest financial strategies and opportunities
            - Analyze your unique financial situation
            - Create a personalized plan tailored to your goals
            - Provide actionable steps and recommendations
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                financial_goals = gr.Textbox(
                    label="What are your financial goals?",
                    placeholder="E.g., Save for retirement, buy a house, pay off student loans...",
                    lines=3
                )

                current_situation = gr.Textbox(
                    label="Describe your current financial situation",
                    placeholder="E.g., Annual income, current savings, debts, monthly expenses...",
                    lines=5
                )

                generate_btn = gr.Button("Generate Financial Plan", variant="primary", size="lg")

            with gr.Column(scale=1):
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="sk-...",
                    value=OPENAI_API_KEY or ""
                )

                serper_key = gr.Textbox(
                    label="Serper API Key",
                    type="password",
                    placeholder="Your Serper API key",
                    value=SERPER_API_KEY or "",
                    info="Used for web search functionality"
                )

                gr.Markdown(
                    """
                    ### Tips:
                    - Be specific about your goals
                    - Include numbers (income, savings, etc.)
                    - Mention your timeline
                    - Note any constraints or preferences

                    ### Example:
                    **Goals:** Retire by 55, save $1M

                    **Situation:** 35 years old, $80k/year,
                    $50k saved, $200k mortgage, $2k/month expenses
                    """
                )

        with gr.Row():
            output = gr.Markdown(
                label="Your Personalized Financial Plan",
                value="Your financial plan will appear here..."
            )

        generate_btn.click(
            fn=generate_financial_plan,
            inputs=[financial_goals, current_situation, openai_key, serper_key],
            outputs=output
        )

        gr.Examples(
            examples=[
                [
                    "Build an emergency fund of $10,000, save for a down payment on a house, and start investing for retirement",
                    "Age: 28, Income: $65,000/year, Current savings: $5,000, Rent: $1,200/month, Student loans: $25,000, No current investments"
                ],
                [
                    "Pay off credit card debt, save for children's college education, and retire comfortably at 60",
                    "Age: 42, Income: $95,000/year, Savings: $30,000, Credit card debt: $15,000, Mortgage: $250,000, 2 children (ages 8 and 10)"
                ],
                [
                    "Maximize retirement savings, diversify investment portfolio, and generate passive income",
                    "Age: 50, Income: $150,000/year, Retirement savings: $400,000, No debt, Monthly expenses: $4,000"
                ]
            ],
            inputs=[financial_goals, current_situation]
        )

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
