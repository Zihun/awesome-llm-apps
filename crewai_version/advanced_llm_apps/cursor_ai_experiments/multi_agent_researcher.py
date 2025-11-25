import gradio as gr
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os

# Global variable for GPT-4 model
gpt4_model = None

def create_article_crew(topic):
    """Creates a team of agents to research, write, and edit an article on a given topic.

    This function sets up a crew consisting of three agents: a researcher, a writer, and an editor.
    Each agent is assigned a specific task to ensure the production of a well-researched,
    well-written, and polished article. The article is formatted using markdown standards.

    Args:
        topic (str): The subject matter on which the article will be based.

    Returns:
        Crew: A crew object that contains the agents and tasks necessary to complete the article."""
    # Create agents
    researcher = Agent(
        role='Researcher',
        goal='Conduct thorough research on the given topic',
        backstory='You are an expert researcher with a keen eye for detail',
        verbose=True,
        allow_delegation=False,
        llm=gpt4_model
    )

    writer = Agent(
        role='Writer',
        goal='Write a detailed and engaging article based on the research, using proper markdown formatting',
        backstory='You are a skilled writer with expertise in creating informative content and formatting it beautifully in markdown',
        verbose=True,
        allow_delegation=False,
        llm=gpt4_model
    )

    editor = Agent(
        role='Editor',
        goal='Review and refine the article for clarity, accuracy, engagement, and proper markdown formatting',
        backstory='You are an experienced editor with a sharp eye for quality content and excellent markdown structure',
        verbose=True,
        allow_delegation=False,
        llm=gpt4_model
    )

    # Create tasks
    research_task = Task(
        description=f"Conduct comprehensive research on the topic: {topic}. Gather key information, statistics, and expert opinions.",
        agent=researcher,
        expected_output="A comprehensive research report on the given topic, including key information, statistics, and expert opinions."
    )

    writing_task = Task(
        description="""Using the research provided, write a detailed and engaging article.
        Ensure proper structure, flow, and clarity. Format the article using markdown, including:
        1. A main title (H1)
        2. Section headings (H2)
        3. Subsection headings where appropriate (H3)
        4. Bullet points or numbered lists where relevant
        5. Emphasis on key points using bold or italic text
        Make sure the content is well-organized and easy to read.""",
        agent=writer,
        expected_output="A well-structured, detailed, and engaging article based on the provided research, formatted in markdown with proper headings and subheadings."
    )

    editing_task = Task(
        description="""Review the article for clarity, accuracy, engagement, and proper markdown formatting.
        Ensure that:
        1. The markdown formatting is correct and consistent
        2. Headings and subheadings are used appropriately
        3. The content flow is logical and engaging
        4. Key points are emphasized correctly
        Make necessary edits and improvements to both content and formatting.""",
        agent=editor,
        expected_output="A final, polished version of the article with improved clarity, accuracy, engagement, and proper markdown formatting."
    )

    # Create the crew
    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, writing_task, editing_task],
        verbose=2,
        process=Process.sequential
    )

    return crew

def initialize_agent(api_key):
    """Initialize the GPT-4 model with API key"""
    global gpt4_model
    if not api_key:
        return "Please provide an OpenAI API key"

    try:
        os.environ["OPENAI_API_KEY"] = api_key
        gpt4_model = ChatOpenAI(model_name="gpt-4o-mini")
        return "API Key set successfully! Now enter a topic to generate an article."
    except Exception as e:
        return f"Error setting API key: {str(e)}"

def generate_article(topic):
    """Generate an article using CrewAI agents"""
    global gpt4_model

    if gpt4_model is None:
        return "Please set your OpenAI API Key first"

    if not topic:
        return "Please enter a topic for the article"

    try:
        crew = create_article_crew(topic)
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error generating article: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Multi Agent AI Researcher", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Multi Agent AI Researcher")
    gr.Markdown("Generate detailed articles on any topic using AI agents powered by CrewAI!")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Configuration")
            api_key = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key"
            )
            init_btn = gr.Button("Set API Key", variant="primary")
            init_status = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")

            topic = gr.Textbox(
                label="Article Topic",
                placeholder="e.g., The Impact of Artificial Intelligence on Healthcare",
                lines=3
            )
            generate_btn = gr.Button("Generate Article", variant="primary", size="lg")

            gr.Markdown("---")
            gr.Markdown("""
            ### How it works
            This app uses three AI agents:
            1. **Researcher**: Gathers information and statistics
            2. **Writer**: Creates a well-structured article
            3. **Editor**: Refines and polishes the content

            The agents work sequentially to produce high-quality articles.
            """)

        with gr.Column(scale=2):
            article_output = gr.Markdown(
                label="Generated Article",
                value="Your article will appear here..."
            )

    # Event handlers
    init_btn.click(fn=initialize_agent, inputs=[api_key], outputs=[init_status])
    generate_btn.click(
        fn=generate_article,
        inputs=[topic],
        outputs=[article_output]
    )

    gr.Markdown("---")
    gr.Markdown("Powered by CrewAI and OpenAI")

if __name__ == "__main__":
    demo.launch()
