"""
Gradio Web Interface for Multi-Agent Researcher

This provides an interactive web interface for the multi-agent research system
that coordinates research, summarization, and critique.
"""

import os
import gradio as gr
from dotenv import load_dotenv
from agent import create_research_crew

# Load environment variables
load_dotenv()

# Check API keys
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please create a .env file with your OpenAI API key.")

def research_topic(topic: str, progress=gr.Progress()):
    """
    Research a topic using the multi-agent system
    """
    if not topic or not topic.strip():
        return "Please enter a research topic."

    try:
        progress(0, desc="Initializing research crew...")

        # Create the research crew
        crew = create_research_crew(topic)

        progress(0.2, desc="Research agent gathering information...")

        # Execute the crew
        result = crew.kickoff()

        progress(1.0, desc="Research complete!")

        return str(result)

    except Exception as e:
        return f"Error during research: {str(e)}\n\nPlease check your API keys and try again."

# Create Gradio interface
with gr.Blocks(title="Multi-Agent Researcher", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Multi-Agent Research System")
    gr.Markdown("""
    **Tutorial 8**: Advanced multi-agent research coordinator with specialized agents

    This system coordinates a team of specialized agents:
    - **Research Agent**: Gathers comprehensive information using web search
    - **Summarizer Agent**: Distills findings into clear, actionable insights
    - **Critic Agent**: Provides quality analysis and recommendations
    - **Coordinator Agent**: Integrates all outputs into a cohesive report
    """)

    with gr.Row():
        with gr.Column(scale=1):
            topic_input = gr.Textbox(
                label="Research Topic",
                placeholder="Enter a topic to research...",
                lines=3
            )
            research_btn = gr.Button("Start Research", variant="primary", size="lg")

            gr.Markdown("### Example Topics")
            examples = [
                "Artificial Intelligence trends in 2025",
                "Climate change impact on agriculture",
                "Quantum computing applications in cryptography",
                "Remote work productivity best practices",
                "Renewable energy storage technologies"
            ]

            for example in examples:
                gr.Button(example, size="sm").click(
                    lambda e=example: e,
                    None,
                    topic_input
                )

            gr.Markdown("""
            ### Research Process
            1. **Research Phase**: Gathering comprehensive information
            2. **Synthesis Phase**: Creating clear summaries
            3. **Analysis Phase**: Evaluating quality and gaps
            4. **Integration**: Combining into final report
            """)

        with gr.Column(scale=2):
            output_area = gr.Markdown(
                label="Research Report",
                value="*Research results will appear here...*"
            )

    research_btn.click(
        research_topic,
        inputs=[topic_input],
        outputs=[output_area]
    )

    topic_input.submit(
        research_topic,
        inputs=[topic_input],
        outputs=[output_area]
    )

    gr.Markdown("""
    ---
    ### Tutorial Information

    This demonstrates **CrewAI multi-agent orchestration** with:
    - Multiple specialized agents working together
    - Sequential task execution with context sharing
    - Hierarchical coordination pattern
    - Integration of research, analysis, and synthesis

    **Agent Roles:**
    - **Research Agent**: Uses search tools to gather current information
    - **Summarizer Agent**: Creates executive summaries and key insights
    - **Critic Agent**: Identifies gaps, risks, and opportunities
    - **Coordinator Agent**: Manages workflow and integrates outputs

    **Conversion Notes:**
    - Original used Google ADK's `sub_agents` and `AgentTool`
    - CrewAI uses `Task` with `context` parameter for task dependencies
    - `Process.sequential` ensures ordered execution
    - Search functionality uses `SerperDevTool` (requires SERPER_API_KEY)

    **Requirements:**
    - `OPENAI_API_KEY`: Required for LLM access
    - `SERPER_API_KEY`: Optional but recommended for search functionality

    **Next Steps:**
    - Try different research topics
    - Modify agent roles and backstories
    - Add custom tools for specialized research
    - Experiment with `Process.hierarchical` for dynamic delegation
    """)

    gr.Markdown("""
    ### Tips for Better Research

    1. **Be Specific**: Include key aspects you want to explore
    2. **Time Context**: Mention time periods if relevant (e.g., "in 2025")
    3. **Scope**: Indicate if you want broad overview or deep dive
    4. **Perspective**: Specify industry, region, or application area

    **Good Examples:**
    - "Impact of generative AI on software development workflows in 2024-2025"
    - "Sustainable packaging solutions for e-commerce: cost-benefit analysis"
    - "Edge computing adoption in healthcare: challenges and opportunities"

    **Less Specific Examples:**
    - "AI" (too broad)
    - "Technology" (too vague)
    """)

if __name__ == "__main__":
    demo.launch(share=False, server_port=7860)
