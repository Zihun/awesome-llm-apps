from crewai import Agent, Task, Crew
import gradio as gr
from langchain_openai import ChatOpenAI

def analyze_with_reasoning(openai_key, question):
    if not openai_key or not question:
        return "Please provide both API key and question", ""

    try:
        # Regular agent with GPT-4o-mini
        regular_llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
        regular_agent = Agent(
            role="Regular Assistant",
            goal="Answer questions directly",
            backstory="You are a helpful AI assistant that answers questions concisely.",
            llm=regular_llm,
            verbose=True
        )

        regular_task = Task(
            description=question,
            agent=regular_agent,
            expected_output="Direct answer to the question"
        )

        # Reasoning agent with GPT-4o
        reasoning_llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0.7)
        reasoning_agent = Agent(
            role="Reasoning Expert",
            goal="Provide detailed step-by-step reasoning before answering",
            backstory="""You are an expert at breaking down complex problems.
            You always show your reasoning process step-by-step before providing
            the final answer. Think through each step carefully.""",
            llm=reasoning_llm,
            verbose=True
        )

        reasoning_task = Task(
            description=f"""Solve this problem with detailed reasoning: {question}

            Show your complete thought process step by step, then provide the final answer.""",
            agent=reasoning_agent,
            expected_output="Step-by-step reasoning followed by the answer"
        )

        # Execute both crews
        regular_crew = Crew(agents=[regular_agent], tasks=[regular_task], verbose=False)
        reasoning_crew = Crew(agents=[reasoning_agent], tasks=[reasoning_task], verbose=False)

        regular_result = regular_crew.kickoff()
        reasoning_result = reasoning_crew.kickoff()

        regular_output = regular_result.raw if hasattr(regular_result, 'raw') else str(regular_result)
        reasoning_output = reasoning_result.raw if hasattr(reasoning_result, 'raw') else str(reasoning_result)

        return regular_output, reasoning_output

    except Exception as e:
        return f"Error: {str(e)}", f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="AI Reasoning Agent") as app:
        gr.Markdown("# AI Reasoning Agent Comparison")
        gr.Markdown("Compare regular vs reasoning-enhanced AI responses")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )
                question = gr.Textbox(
                    label="Your Question",
                    placeholder="How many 'r' are in the word 'supercalifragilisticexpialidocious'?",
                    lines=3
                )
                analyze_btn = gr.Button("Analyze", variant="primary")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Regular Agent (GPT-4o-mini)")
                regular_output = gr.Markdown()

            with gr.Column():
                gr.Markdown("### Reasoning Agent (GPT-4o)")
                reasoning_output = gr.Markdown()

        analyze_btn.click(
            fn=analyze_with_reasoning,
            inputs=[api_key, question],
            outputs=[regular_output, reasoning_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
