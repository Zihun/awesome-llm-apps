# CrewAI + Gradio Versions of Starter AI Agents

This directory contains all the starter AI agents converted from the original agno/streamlit implementations to CrewAI/Gradio versions.

## Conversion Summary

All Python files from `/starter_ai_agents/` have been converted with the following changes:

### Framework Changes

#### 1. Agent Framework: agno → CrewAI
- `from agno.agent import Agent` → `from crewai import Agent, Task, Crew`
- `from agno.models.openai import OpenAIChat` → `from langchain_openai import ChatOpenAI`
- `from agno.models.google import Gemini` → `from langchain_google_genai import ChatGoogleGenerativeAI` + `google.generativeai`
- `from agno.models.ollama import Ollama` → `from langchain_community.llms import Ollama`
- `from agno.tools.duckduckgo import DuckDuckGoTools` → `from crewai_tools import SerperDevTool` or `DuckDuckGoSearchRun`
- `from agno.tools.serpapi import SerpApiTools` → `from crewai_tools import SerperDevTool`
- `from agno.run.agent import RunOutput` → CrewAI returns results directly

#### 2. UI Framework: Streamlit → Gradio
- `st.title()` → `gr.Markdown("# title")`
- `st.text_input()` → `gr.Textbox()`
- `st.text_area()` → `gr.Textbox(lines=N)`
- `st.button()` → `gr.Button()`
- `st.file_uploader()` → `gr.File()` or `gr.Image()`
- `st.image()` → `gr.Image()`
- `st.markdown()` → `gr.Markdown()`
- `st.sidebar` → `gr.Column()` or `gr.Accordion()`
- `st.columns()` → `gr.Row()`

#### 3. CrewAI Agent Pattern
```python
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
agent = Agent(
    role="Role name",
    goal="Goal description",
    backstory="Agent backstory",
    llm=llm,
    verbose=True
)
task = Task(
    description="task description",
    agent=agent,
    expected_output="output description"
)
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

## Converted Files

### 1. mixture_of_agents/mixture-of-agents.py
- **Original**: Mixture-of-Agents with Together API
- **Converted**: Gradio interface with async processing
- **Changes**: Streamlit → Gradio, maintained Together API integration

### 2. ai_breakup_recovery_agent/ai_breakup_recovery_agent.py
- **Original**: Agno agents with Gemini for breakup recovery
- **Converted**: CrewAI agents with Google Generative AI
- **Changes**: 4 specialized agents (Therapist, Closure, Routine Planner, Honest Feedback)

### 3. ai_blog_to_podcast_agent/blog_to_podcast_agent.py
- **Original**: Agno with FirecrawlTools
- **Converted**: CrewAI with ScrapeWebsiteTool
- **Changes**: Blog scraping + ElevenLabs audio generation

### 4. ai_music_generator_agent/music_generator_agent.py
- **Original**: Agno with ModelsLabTools
- **Converted**: CrewAI with direct ModelsLab API calls
- **Changes**: Enhanced prompt generation with CrewAI agent

### 5. xai_finance_agent/xai_finance_agent.py
- **Original**: Agno with xAI model
- **Converted**: CrewAI with xAI Grok via OpenAI-compatible endpoint
- **Changes**: YFinance integration for stock data

### 6. opeani_research_agent/research_agent.py
- **Original**: OpenAI Agents SDK (not agno)
- **Converted**: CrewAI multi-agent research system
- **Changes**: Triage → Researcher → Editor workflow

### 7. ai_reasoning_agent/reasoning_agent.py
- **Original**: Agno with reasoning mode
- **Converted**: CrewAI with two agents (regular vs reasoning)
- **Changes**: Comparison between GPT-4o-mini and GPT-4o

### 8. ai_reasoning_agent/local_ai_reasoning_agent.py
- **Original**: Agno with Ollama
- **Converted**: CrewAI with Ollama (qwq:32b)
- **Changes**: Local reasoning model integration

### 9. ai_meme_generator_agent_browseruse/ai_meme_generator_agent.py
- **Original**: Browser-use with Streamlit
- **Converted**: Browser-use with Gradio
- **Changes**: Maintained browser automation, changed UI framework

### 10. ai_life_insurance_advisor_agent/life_insurance_advisor_agent.py
- **Original**: Agno with E2B and Firecrawl
- **Converted**: CrewAI with web search tools
- **Changes**: Calculator + Researcher agents for coverage calculation

### 11. ai_travel_agent/travel_agent.py
- **Original**: Agno with SerpAPI
- **Converted**: CrewAI with SerperDevTool
- **Changes**: Researcher + Planner agents with ICS calendar export

### 12. ai_travel_agent/local_travel_agent.py
- **Original**: Agno with Ollama + SerpAPI
- **Converted**: CrewAI with Ollama + SerperDevTool
- **Changes**: Local model version of travel planner

### 13. multimodal_ai_agent/multimodal_reasoning_agent.py
- **Original**: Agno with Gemini for image analysis
- **Converted**: Direct Gemini API (multimodal requires native support)
- **Changes**: Image upload and analysis with Gemini 2.0

### 14. multimodal_ai_agent/mutimodal_agent.py
- **Original**: Agno with Gemini for video analysis
- **Converted**: Direct Gemini API for video processing
- **Changes**: Video upload and analysis with file API

### 15. ai_data_analysis_agent/ai_data_analyst.py
- **Original**: Agno with DuckDB and Pandas tools
- **Converted**: CrewAI with DuckDB integration
- **Changes**: SQL query generation for data analysis

### 16. ai_startup_trend_analysis_agent/startup_trends_agent.py
- **Original**: Agno with DuckDuckGo and Newspaper4k
- **Converted**: CrewAI with SerperDevTool and ScrapeWebsiteTool
- **Changes**: News Collector → Summarizer → Analyzer workflow

### 17. ai_data_visualisation_agent/ai_data_visualisation_agent.py
- **Original**: Together AI + E2B with Streamlit
- **Converted**: Together AI + E2B with Gradio
- **Changes**: Maintained E2B sandbox, changed UI to Gradio

### 18. ai_medical_imaging_agent/ai_medical_imaging.py
- **Original**: Agno with Gemini for medical imaging
- **Converted**: Direct Gemini API for medical analysis
- **Changes**: Professional medical image analysis with web research

### 19. web_scrapping_ai_agent/ai_scrapper.py
- **Original**: ScrapeGraphAI with OpenAI
- **Converted**: CrewAI with ScrapeWebsiteTool
- **Changes**: Web scraping agent with OpenAI models

### 20. web_scrapping_ai_agent/local_ai_scrapper.py
- **Original**: ScrapeGraphAI with Ollama
- **Converted**: CrewAI with ScrapeWebsiteTool + Ollama
- **Changes**: Local model version of web scraper

## Running the Apps

Each app can be run individually:

```bash
cd /Users/zihun/work/awesome-llm-apps/crewai_version/starter_ai_agents/<agent_directory>
python <agent_file>.py
```

For example:
```bash
cd /Users/zihun/work/awesome-llm-apps/crewai_version/starter_ai_agents/ai_travel_agent
python travel_agent.py
```

The Gradio interface will launch in your browser automatically.

## Dependencies

Key dependencies needed for the converted versions:

```bash
pip install crewai crewai-tools
pip install gradio
pip install langchain langchain-openai langchain-google-genai langchain-community langchain-anthropic
pip install google-generativeai
pip install elevenlabs  # for podcast agent
pip install together  # for mixture of agents, data viz
pip install e2b-code-interpreter  # for data viz, insurance advisor
pip install browser-use  # for meme generator
pip install yfinance  # for finance agent
pip install duckdb pandas  # for data analysis
pip install icalendar  # for travel agents
```

## Key Differences from Original

1. **Agent Framework**: All agents now use CrewAI's Task-based execution model
2. **UI Framework**: All UIs now use Gradio instead of Streamlit
3. **Tool Integration**: Updated to use crewai-tools and langchain tools
4. **Multi-Agent Workflows**: Preserved multi-agent patterns using CrewAI's Crew concept
5. **Multimodal Support**: Direct API usage for Gemini where CrewAI doesn't support multimodal natively

## Notes

- Some agents use direct API calls (Gemini multimodal, Together AI) where CrewAI abstraction wasn't suitable
- All agents maintain the same core functionality as the originals
- Gradio provides a cleaner, more modern UI compared to Streamlit
- CrewAI's task-based approach provides better agent orchestration

## License

Same as the original awesome-llm-apps repository.
