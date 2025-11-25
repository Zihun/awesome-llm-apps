from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
import gradio as gr
from langchain_openai import ChatOpenAI
import os

def research_topic(openai_key, topic):
    if not openai_key or not topic:
        return "", "Please provide both API key and topic"

    try:
        os.environ["OPENAI_API_KEY"] = openai_key

        llm_mini = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)

        search_tool = SerperDevTool()

        # Research Agent
        research_agent = Agent(
            role="Research Assistant",
            goal="Search the web and produce concise summaries of results",
            backstory="""You are a research assistant who searches the web and creates
            2-3 paragraph summaries (less than 300 words) capturing the main points.
            Write succinctly, focusing on essence over complete sentences.""",
            llm=llm_mini,
            tools=[search_tool],
            verbose=True
        )

        # Editor Agent
        editor_agent = Agent(
            role="Senior Researcher",
            goal="Write comprehensive research reports",
            backstory="""You are a senior researcher tasked with writing cohesive reports.
            You create an outline first, then generate a lengthy, detailed report.
            Aim for 5-10 pages of content, at least 1000 words, in markdown format.""",
            llm=llm,
            verbose=True
        )

        # Triage Agent
        triage_agent = Agent(
            role="Research Coordinator",
            goal="Coordinate the research operation",
            backstory="""You are the coordinator who:
            1. Understands the research topic
            2. Creates a research plan with 3-5 search queries
            3. Identifies 3-5 key aspects to investigate
            4. Coordinates between research and editing""",
            llm=llm_mini,
            verbose=True
        )

        # Create tasks
        plan_task = Task(
            description=f"Create a research plan for topic: {topic}. Include 3-5 search queries and key focus areas.",
            agent=triage_agent,
            expected_output="Research plan with search queries and focus areas"
        )

        research_task = Task(
            description=f"Research {topic} thoroughly. Find the 10 most relevant results from web searches.",
            agent=research_agent,
            expected_output="Comprehensive research findings",
            context=[plan_task]
        )

        report_task = Task(
            description=f"""Write a comprehensive research report on {topic}.
            Use the research findings to create a detailed, well-structured report.
            Include an outline, then the full report (1000+ words) in markdown format.
            Include sources and references.""",
            agent=editor_agent,
            expected_output="Complete research report with outline and sources",
            context=[research_task]
        )

        # Create crew
        crew = Crew(
            agents=[triage_agent, research_agent, editor_agent],
            tasks=[plan_task, research_task, report_task],
            verbose=True
        )

        result = crew.kickoff()

        # Extract the report
        report = result.raw if hasattr(result, 'raw') else str(result)

        # Create process summary
        process_summary = f"""## Research Process Completed

**Topic:** {topic}

**Steps Completed:**
1. Research plan created
2. Web research conducted
3. Comprehensive report generated

**Report Preview:**
{report[:300]}...

*See the Report tab for the full document.*
"""

        return process_summary, report

    except Exception as e:
        return f"Error: {str(e)}", ""

def create_app():
    with gr.Blocks(title="OpenAI Researcher Agent") as app:
        gr.Markdown("# OpenAI Researcher Agent")
        gr.Markdown("Powered by CrewAI")
        gr.Markdown("""
        This app demonstrates the power of CrewAI by creating a multi-agent system
        that researches news topics and generates comprehensive research reports.
        """)

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )

                topic_input = gr.Textbox(
                    label="Research Topic",
                    placeholder="Enter a topic to research",
                    lines=2
                )

                gr.Markdown("### Example Topics")
                with gr.Row():
                    example1 = gr.Button("Best cruise lines in USA")
                    example2 = gr.Button("Best espresso machines")
                    example3 = gr.Button("Travel destinations in India")

                start_btn = gr.Button("Start Research", variant="primary")

        with gr.Tabs():
            with gr.Tab("Research Process"):
                process_output = gr.Markdown()

            with gr.Tab("Report"):
                report_output = gr.Markdown()

        def set_example1():
            return "What are the best cruise lines in USA for first-time travelers who have never been on a cruise?"

        def set_example2():
            return "What are the best affordable espresso machines for someone upgrading from a French press?"

        def set_example3():
            return "What are the best off-the-beaten-path destinations in India for a first-time solo traveler?"

        example1.click(fn=set_example1, outputs=topic_input)
        example2.click(fn=set_example2, outputs=topic_input)
        example3.click(fn=set_example3, outputs=topic_input)

        start_btn.click(
            fn=research_topic,
            inputs=[api_key, topic_input],
            outputs=[process_output, report_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
