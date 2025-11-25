from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
import gradio as gr
from langchain_openai import ChatOpenAI
import json
from datetime import datetime

def format_currency(amount: float, currency_code: str) -> str:
    symbol_map = {
        "USD": "$", "EUR": "€", "GBP": "£",
        "CAD": "C$", "AUD": "A$", "INR": "₹"
    }
    code = (currency_code or "USD").upper()
    symbol = symbol_map.get(code, "")
    formatted = f"{amount:,.0f}"
    return f"{symbol}{formatted}" if symbol else f"{formatted} {code}"

def calculate_coverage(openai_key, age, income, dependents, debt, savings, existing_cover, years, currency):
    if not openai_key:
        return "Please provide OpenAI API key"

    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)

        search_tool = SerperDevTool()
        scrape_tool = ScrapeWebsiteTool()

        # Create calculation agent
        calculator_agent = Agent(
            role="Life Insurance Calculator",
            goal="Calculate recommended life insurance coverage using financial formulas",
            backstory="""You are a financial expert who calculates life insurance needs
            using the income replacement method with present value calculations.
            Use a 2% real discount rate for income replacement.""",
            llm=llm,
            verbose=True
        )

        # Create research agent
        researcher_agent = Agent(
            role="Insurance Product Researcher",
            goal="Find suitable life insurance options for clients",
            backstory="""You are an insurance researcher who finds the best
            term life insurance options based on client profiles.""",
            llm=llm,
            tools=[search_tool, scrape_tool],
            verbose=True
        )

        # Profile data
        profile = {
            "age": age,
            "annual_income": income,
            "dependents": dependents,
            "total_debt": debt,
            "available_savings": savings,
            "existing_life_insurance": existing_cover,
            "income_replacement_years": years,
            "currency": currency,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Calculation task
        calc_task = Task(
            description=f"""Calculate life insurance coverage needed for this profile:
            {json.dumps(profile, indent=2)}

            Use this formula:
            1. Calculate present value of income replacement using 2% discount rate
            2. Add total debt
            3. Subtract available savings and existing insurance
            4. Return recommended coverage amount

            Provide breakdown of the calculation.""",
            agent=calculator_agent,
            expected_output="Recommended coverage amount with detailed calculation breakdown"
        )

        # Research task
        research_task = Task(
            description=f"""Find 3-5 suitable term life insurance options for:
            - Age: {age}
            - Coverage needed: (from calculation)
            - Location: United States

            Return product names, brief summaries, and links.""",
            agent=researcher_agent,
            expected_output="List of recommended insurance products",
            context=[calc_task]
        )

        # Create crew
        crew = Crew(
            agents=[calculator_agent, researcher_agent],
            tasks=[calc_task, research_task],
            verbose=True
        )

        result = crew.kickoff()

        # Format result
        output = f"""# Life Insurance Coverage Recommendation

## Client Profile
- **Age:** {age}
- **Annual Income:** {format_currency(income, currency)}
- **Dependents:** {dependents}
- **Total Debt:** {format_currency(debt, currency)}
- **Savings:** {format_currency(savings, currency)}
- **Existing Coverage:** {format_currency(existing_cover, currency)}
- **Income Replacement:** {years} years

---

## Analysis Results

{result.raw if hasattr(result, 'raw') else str(result)}

---

**Disclaimer:** This is for educational purposes only. Consult with a licensed
financial advisor before making insurance decisions.

*Generated: {datetime.utcnow().isoformat()}*
"""

        return output

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="Life Insurance Coverage Advisor") as app:
        gr.Markdown("# Life Insurance Coverage Advisor")
        gr.Markdown("Powered by CrewAI Agents, OpenAI GPT-4o, and Web Search")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )

        gr.Markdown("## Tell us about yourself")

        with gr.Row():
            with gr.Column():
                age = gr.Number(label="Age", value=35, minimum=18, maximum=85)
                income = gr.Number(label="Annual Income", value=85000, minimum=0)
                dependents = gr.Number(label="Dependents", value=2, minimum=0, maximum=10)
                location = gr.Textbox(label="Country / State", value="United States")

            with gr.Column():
                debt = gr.Number(label="Total Debt (incl. mortgage)", value=200000, minimum=0)
                savings = gr.Number(label="Savings & Investments", value=50000, minimum=0)
                existing_cover = gr.Number(label="Existing Life Insurance", value=100000, minimum=0)
                currency = gr.Dropdown(
                    ["USD", "CAD", "EUR", "GBP", "AUD", "INR"],
                    label="Currency",
                    value="USD"
                )

        years = gr.Radio([5, 10, 15], label="Income Replacement Horizon (years)", value=10)

        submit_btn = gr.Button("Generate Coverage & Options", variant="primary")

        with gr.Row():
            output = gr.Markdown()

        submit_btn.click(
            fn=calculate_coverage,
            inputs=[api_key, age, income, dependents, debt, savings, existing_cover, years, currency],
            outputs=output
        )

        gr.Markdown("""
        ---
        **Disclaimer:** This prototype is for educational use only and does not provide
        licensed financial advice. Verify all recommendations with a qualified professional.
        """)

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
