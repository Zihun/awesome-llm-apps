# CrewAI + Gradio Converted Advanced AI Agents

This directory contains AI agent applications converted from `agno` + `streamlit` to `crewai` + `gradio`.

## Overview

All applications have been converted following these principles:

### 1. Framework Conversions

#### From agno to CrewAI:
- `from agno.agent import Agent` → `from crewai import Agent, Task, Crew`
- `from agno.models.openai import OpenAIChat` → `from langchain_openai import ChatOpenAI`
- `from agno.models.google import Gemini` → `from langchain_google_genai import ChatGoogleGenerativeAI`
- `from agno.models.anthropic import Claude` → `from langchain_anthropic import ChatAnthropic`
- `from agno.team import Team` → `from crewai import Crew, Process`
- `from agno.tools import tool` → `from crewai_tools import tool`

#### From Streamlit to Gradio:
- `import streamlit as st` → `import gradio as gr`
- `st.title()` → `gr.Markdown("# Title")`
- `st.text_input()` → `gr.Textbox()`
- `st.button()` → `gr.Button()`
- `st.chat_message()` → `gr.Chatbot()`
- `st.selectbox()` → `gr.Dropdown()`
- `st.form()` → Gradio's interface components
- `st.session_state` → `gr.State()`

### 2. Multi-Agent Pattern

For multi-agent systems, CrewAI's Crew is used:

```python
from crewai import Agent, Task, Crew, Process

# Create agents
agent1 = Agent(role="...", goal="...", backstory="...", llm=llm)
agent2 = Agent(role="...", goal="...", backstory="...", llm=llm)

# Create tasks
task1 = Task(description="...", agent=agent1, expected_output="...")
task2 = Task(description="...", agent=agent2, expected_output="...")

# Create crew
crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.sequential  # or Process.hierarchical
)

# Execute
result = crew.kickoff()
```

## Converted Files

### Single Agent Apps (`single_agent_apps/`)

1. **ai_recipe_meal_planning_agent.py**
   - Meal planning and recipe search agent
   - Tools: Recipe search, nutrition analysis, cost estimation
   - UI: Gradio chat interface with API key configuration

2. **ai_personal_finance_agent.py**
   - Personal finance planning with research and planning agents
   - Multi-agent: Researcher + Planner
   - Uses SerperDevTool for web search
   - UI: Gradio form with progress tracking

3. **ai_health_fitness_agent.py**
   - Health and fitness planning
   - Multi-agent: Dietary Expert + Fitness Expert
   - Uses Google Gemini
   - UI: Gradio interface with profile inputs and Q&A

### Multi-Agent Apps (`multi_agent_apps/`)

1. **multi_agent_researcher.py**
   - HackerNews research with multiple specialized agents
   - Agents: HN Researcher, Web Searcher, Article Reader
   - Custom tools for HackerNews API
   - UI: Gradio interface with research query input

### Autonomous Game Playing Apps (`autonomous_game_playing_agent_apps/`)

1. **ai_tic_tac_toe_agent.py**
   - AI agents playing Tic-Tac-Toe against each other
   - Supports multiple LLMs (OpenAI, Anthropic, Google, Groq)
   - Real-time game visualization
   - UI: Gradio with game board display and move history

## Installation

```bash
pip install crewai crewai-tools gradio langchain-openai langchain-anthropic langchain-google-genai langchain-groq python-dotenv
```

### Additional dependencies by app:
- Recipe Planning: `requests`
- Personal Finance: `serper-dev` (requires SERPER_API_KEY)
- Health & Fitness: `google-generativeai`
- HackerNews Researcher: `requests`

## Environment Variables

Create a `.env` file with the required API keys:

```env
# OpenAI (for GPT models)
OPENAI_API_KEY=sk-...

# Google AI (for Gemini models)
GOOGLE_API_KEY=AIza...

# Anthropic (for Claude models)
ANTHROPIC_API_KEY=sk-ant-...

# Groq (for Llama models)
GROQ_API_KEY=gsk_...

# Serper (for web search)
SERPER_API_KEY=...

# Spoonacular (for recipe search)
SPOONACULAR_API_KEY=...

# Firecrawl (for web scraping)
FIRECRAWL_API_KEY=fc_...
```

## Running the Apps

Each app is a standalone Python file that can be run directly:

```bash
# Recipe Planning Agent
python crewai_version/advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent.py

# Personal Finance Agent
python crewai_version/advanced_ai_agents/single_agent_apps/ai_personal_finance_agent.py

# Health & Fitness Agent
python crewai_version/advanced_ai_agents/single_agent_apps/ai_health_fitness_agent.py

# Multi-Agent Researcher
python crewai_version/advanced_ai_agents/multi_agent_apps/multi_agent_researcher.py

# Tic-Tac-Toe Agent
python crewai_version/advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent.py
```

## Key Differences from Original

### Architecture Changes:

1. **Agent Definition**:
   - Original (agno): Direct Agent instantiation
   - Converted (CrewAI): Agent with role, goal, and backstory

2. **Tool Definition**:
   - Original: `@tool` decorator from agno
   - Converted: `@tool` decorator from crewai_tools

3. **Multi-Agent Coordination**:
   - Original: `Team` from agno
   - Converted: `Crew` with `Task` objects and `Process`

4. **UI Framework**:
   - Original: Streamlit (server-rendered, session-based)
   - Converted: Gradio (component-based, functional)

5. **State Management**:
   - Original: `st.session_state` dictionary
   - Converted: `gr.State()` objects

### Benefits of Conversion:

1. **CrewAI**:
   - More structured multi-agent patterns
   - Better task decomposition
   - Built-in process management (sequential, hierarchical)
   - Excellent integration with LangChain ecosystem

2. **Gradio**:
   - Simpler API and faster development
   - Better for demos and quick prototypes
   - Easy sharing with `share=True`
   - Modern, responsive UI out of the box
   - Easier testing with examples

## Conversion Guide for Remaining Files

To convert other files from the original repository, follow this pattern:

### 1. Import Replacements:
```python
# Old
from agno.agent import Agent
from agno.models.openai import OpenAIChat
import streamlit as st

# New
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import gradio as gr
```

### 2. Agent Creation:
```python
# Old (agno)
agent = Agent(
    name="Agent Name",
    model=OpenAIChat(id="gpt-4o"),
    tools=[tool1, tool2],
    instructions=["instruction1", "instruction2"]
)

# New (CrewAI)
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
agent = Agent(
    role="Agent Name",
    goal="What the agent aims to achieve",
    backstory="Background and expertise of the agent",
    tools=[tool1, tool2],
    llm=llm,
    verbose=True
)
```

### 3. Multi-Agent Teams:
```python
# Old (agno Team)
team = Team(
    name="Team Name",
    members=[agent1, agent2],
    instructions=["step1", "step2"]
)
result = team.run(query)

# New (CrewAI Crew)
task1 = Task(description="...", agent=agent1, expected_output="...")
task2 = Task(description="...", agent=agent2, expected_output="...")

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.sequential
)
result = crew.kickoff()
```

### 4. Streamlit to Gradio UI:
```python
# Old (Streamlit)
st.title("App Title")
user_input = st.text_input("Enter text")
if st.button("Submit"):
    result = process(user_input)
    st.write(result)

# New (Gradio)
def process_input(user_input):
    return process(user_input)

with gr.Blocks() as demo:
    gr.Markdown("# App Title")
    user_input = gr.Textbox(label="Enter text")
    submit_btn = gr.Button("Submit")
    output = gr.Textbox(label="Result")

    submit_btn.click(fn=process_input, inputs=user_input, outputs=output)

demo.launch()
```

## File Structure

```
crewai_version/advanced_ai_agents/
├── README.md (this file)
├── single_agent_apps/
│   ├── ai_recipe_meal_planning_agent.py
│   ├── ai_personal_finance_agent.py
│   └── ai_health_fitness_agent.py
├── multi_agent_apps/
│   └── multi_agent_researcher.py
└── autonomous_game_playing_agent_apps/
    └── ai_tic_tac_toe_agent.py
```

## Original Files (Not Yet Converted)

The following files from the original repository have not been converted yet. Use the conversion guide above to convert them:

### Single Agent Apps:
- ai_consultant_agent/
- ai_customer_support_agent/
- ai_deep_research_agent/
- ai_email_gtm_reachout_agent/
- ai_investment_agent/
- ai_journalist_agent/
- ai_meeting_agent/
- ai_movie_production_agent/
- ai_startup_insight_fire1_agent/
- ai_system_architect_r1/
- windows_use_autonomous_agent/

### Multi-Agent Apps:
- ai_Self-Evolving_agent/
- ai_aqi_analysis_agent/ (already has gradio version)
- ai_domain_deep_research_agent/
- ai_email_gtm_outreach_agent/
- ai_financial_coach_agent/
- ai_home_renovation_agent/
- ai_mental_wellbeing_agent/
- ai_news_and_podcast_agents/
- ai_speech_trainer_agent/
- product_launch_intelligence_agent/

### Agent Teams:
- multimodal_coding_agent_team/
- multimodal_design_agent_team/
- ai_game_design_agent_team/
- ai_travel_planner_agent_team/
- ai_recruitment_agent_team/
- ai_real_estate_agent_team/
- ai_competitor_intelligence_agent_team/
- multimodal_uiux_feedback_agent_team/
- ai_finance_agent_team/
- ai_legal_agent_team/
- ai_seo_audit_team/
- ai_services_agency/
- ai_teaching_agent_team/

### Autonomous Game Playing:
- ai_3dpygame_r1/
- ai_chess_agent/

## Contributing

When converting additional files:

1. Follow the patterns established in the converted files
2. Ensure all imports are updated to use CrewAI and Gradio
3. Convert agno.team to CrewAI Crew with proper Task definitions
4. Replace Streamlit UI with equivalent Gradio components
5. Test the converted app to ensure it works correctly
6. Update this README with the new conversion

## License

Same as the original awesome-llm-apps repository.

## Credits

Converted from the original awesome-llm-apps repository by Shubhamsaboo.
Original repository: https://github.com/Shubhamsaboo/awesome-llm-apps
