import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import SerperDevTool

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Initialize search tool (requires SERPER_API_KEY)
search_tool = SerperDevTool()

# --- Sub-agents ---
research_agent = Agent(
    role="Research Specialist",
    goal="Find key information and create outlines for given topics",
    backstory="""
    You are a focused research specialist. Given a user topic or goal,
    conduct thorough research and produce:
    1. A comprehensive bullet list of key facts and findings
    2. Relevant sources and references (when available)
    3. A structured outline for approaching the topic
    4. Current trends or recent developments

    Keep your research factual, well-organized, and comprehensive.
    Use the google_search tool to find current information when needed.
    """,
    tools=[search_tool],
    llm=llm,
    verbose=True
)

summarizer_agent = Agent(
    role="Summarizer",
    goal="Summarize research findings clearly and concisely",
    backstory="""
    You are a skilled summarizer. Given research findings, create:
    1. A concise executive summary (2-3 sentences)
    2. 5-7 key bullet points highlighting the most important information
    3. A clear takeaway message
    4. Any critical insights or patterns you notice

    Focus on clarity, relevance, and actionable insights.
    Avoid repetition and maintain the logical flow of information.
    """,
    llm=llm,
    verbose=True
)

critic_agent = Agent(
    role="Analyst and Critic",
    goal="Provide constructive critique and improvement suggestions",
    backstory="""
    You are a thoughtful analyst and critic. Given research and summaries, provide:
    1. **Gap Analysis**: Identify missing information or areas that need more research
    2. **Risk Assessment**: Highlight potential risks, limitations, or biases
    3. **Opportunity Identification**: Suggest areas for further exploration or improvement
    4. **Quality Score**: Rate the overall research quality (1-10) with justification
    5. **Actionable Recommendations**: Provide specific next steps or improvements

    Be constructive, thorough, and evidence-based in your analysis.
    """,
    llm=llm,
    verbose=True
)

# --- Coordinator (root) agent ---
coordinator_agent = Agent(
    role="Research Coordinator",
    goal="Orchestrate research, analysis, and critique to deliver comprehensive research reports",
    backstory="""
    You are an advanced research coordinator managing a team of specialized agents.

    **Your Research Team:**
    - **research_agent**: Conducts comprehensive research using web search and analysis
    - **summarizer_agent**: Synthesizes findings into clear, actionable insights
    - **critic_agent**: Provides quality analysis, gap identification, and recommendations

    **Research Workflow:**
    1. **Research Phase**: Delegate to research_agent to gather comprehensive information
    2. **Synthesis Phase**: Use summarizer_agent to distill findings into key insights
    3. **Analysis Phase**: Engage critic_agent to evaluate quality and identify opportunities
    4. **Integration**: Combine all outputs into a cohesive research report

    **Output Format:**
    Provide a structured response that includes:
    - Executive Summary
    - Key Findings
    - Critical Analysis
    - Recommendations
    - Next Steps

    Coordinate your team effectively to deliver high-quality, comprehensive research.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=True
)

def create_research_crew(topic: str) -> Crew:
    """Create a research crew for a given topic"""

    # Define tasks
    research_task = Task(
        description=f"""
        Conduct comprehensive research on the topic: {topic}

        Produce:
        1. Key facts and findings
        2. Relevant sources and references
        3. A structured outline
        4. Current trends or recent developments
        """,
        expected_output="A comprehensive research report with facts, sources, outline, and trends",
        agent=research_agent
    )

    summarize_task = Task(
        description="""
        Summarize the research findings into a clear, actionable format.

        Create:
        1. A concise executive summary (2-3 sentences)
        2. 5-7 key bullet points
        3. A clear takeaway message
        4. Critical insights or patterns
        """,
        expected_output="A concise summary with executive summary, key points, takeaway, and insights",
        agent=summarizer_agent,
        context=[research_task]
    )

    critique_task = Task(
        description="""
        Provide constructive critique and analysis of the research and summary.

        Include:
        1. Gap Analysis
        2. Risk Assessment
        3. Opportunity Identification
        4. Quality Score (1-10)
        5. Actionable Recommendations
        """,
        expected_output="A comprehensive critique with gap analysis, risks, opportunities, quality score, and recommendations",
        agent=critic_agent,
        context=[research_task, summarize_task]
    )

    coordination_task = Task(
        description=f"""
        Coordinate the research team to deliver a comprehensive research report on: {topic}

        Integrate outputs from:
        - Research findings
        - Summary and key insights
        - Critical analysis and recommendations

        Format the final report with:
        - Executive Summary
        - Key Findings
        - Critical Analysis
        - Recommendations
        - Next Steps
        """,
        expected_output="A complete, integrated research report with all sections",
        agent=coordinator_agent,
        context=[research_task, summarize_task, critique_task]
    )

    # Create and return crew
    crew = Crew(
        agents=[research_agent, summarizer_agent, critic_agent, coordinator_agent],
        tasks=[research_task, summarize_task, critique_task, coordination_task],
        process=Process.sequential,
        verbose=True
    )

    return crew

# Export root agent for compatibility
root_agent = coordinator_agent
