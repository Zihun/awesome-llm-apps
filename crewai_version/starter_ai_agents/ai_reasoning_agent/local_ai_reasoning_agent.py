from crewai import Agent, Task, Crew
import gradio as gr
from langchain_community.llms import Ollama

def analyze_with_local_reasoning(question):
    if not question:
        return "Please provide a question"

    try:
        # Local reasoning model
        llm = Ollama(model="qwq:32b")

        reasoning_agent = Agent(
            role="Reasoning Expert",
            goal="Provide detailed step-by-step reasoning using local Ollama model",
            backstory="""You are an expert at breaking down complex problems.
            You always show your reasoning process step-by-step before providing
            the final answer.""",
            llm=llm,
            verbose=True
        )

        task = Task(
            description=question,
            agent=reasoning_agent,
            expected_output="Detailed reasoning and answer"
        )

        crew = Crew(agents=[reasoning_agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        return result.raw if hasattr(result, 'raw') else str(result)

    except Exception as e:
        return f"Error: {str(e)}\n\nMake sure Ollama is running and qwq:32b model is installed."

def create_app():
    with gr.Blocks(title="Local AI Reasoning Agent") as app:
        gr.Markdown("# Local AI Reasoning Agent")
        gr.Markdown("Uses Ollama with QwQ:32B model for local reasoning")
        gr.Markdown("*Make sure Ollama is running with `ollama pull qwq:32b`*")

        with gr.Row():
            with gr.Column():
                question = gr.Textbox(
                    label="Your Question",
                    placeholder="Enter your question here...",
                    lines=5
                )
                analyze_btn = gr.Button("Analyze", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="Reasoning and Answer")

        analyze_btn.click(
            fn=analyze_with_local_reasoning,
            inputs=question,
            outputs=output
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
