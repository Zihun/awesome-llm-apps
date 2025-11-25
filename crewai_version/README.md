# CrewAI + Gradio Versions

This directory contains converted versions of the original agents, now using **CrewAI** for agent orchestration and **Gradio** for the user interface.

## Conversion Summary

### What Changed

1. **Agent Framework**: `agno` → `crewai`
   - All agent imports converted to CrewAI
   - Agent definitions updated to use CrewAI's Agent class
   - Task and Crew patterns implemented

2. **Model/LLM**: Various → `langchain_openai.ChatOpenAI`
   - OpenAI models now accessed through LangChain's ChatOpenAI
   - Google Gemini replaced with OpenAI equivalents where applicable

3. **Tools**: `agno.tools` → `crewai_tools` and `langchain` tools
   - WebSearch → SerperDevTool (requires Serper API key)
   - MCP tools → Native CrewAI tools where available
   - Custom tool wrappers created where needed

4. **UI Framework**: `streamlit` → `gradio`
   - All Streamlit components converted to Gradio equivalents
   - Audio components use `gr.Audio()`
   - File uploads use `gr.File()`
   - Interactive chat interfaces use `gr.Chatbot()`

## Directory Structure

```
crewai_version/
├── voice_ai_agents/
│   ├── ai_audio_tour_agent/
│   │   ├── agent.py                          # CrewAI agent definitions
│   │   ├── manager.py                        # CrewAI crew orchestration
│   │   ├── printer.py                        # Utility for status updates
│   │   └── ai_audio_tour_agent.py           # Gradio interface
│   ├── customer_support_voice_agent/
│   │   └── customer_support_voice_agent.py  # Gradio interface with CrewAI
│   └── voice_rag_openaisdk/
│       └── rag_voice.py                     # Gradio interface with CrewAI
└── mcp_ai_agents/
    ├── ai_travel_planner_mcp_agent_team/
    │   └── app.py                           # Gradio interface with CrewAI
    ├── browser_mcp_agent/
    │   └── main.py                          # Gradio interface with CrewAI
    ├── github_mcp_agent/
    │   └── github_agent.py                  # Gradio interface with CrewAI
    ├── multi_mcp_agent/
    │   └── multi_mcp_agent.py              # Gradio interface with CrewAI
    └── notion_mcp_agent/
        └── notion_mcp_agent.py             # Gradio interface with CrewAI
```

## Installation

### Prerequisites

```bash
pip install crewai crewai-tools gradio langchain-openai openai
pip install qdrant-client fastembed firecrawl-py  # For RAG agents
pip install icalendar                              # For travel planner
pip install python-dotenv requests                 # General utilities
```

### API Keys Required

Different agents require different API keys:

1. **All Agents**: OpenAI API key
2. **Search-based agents**: Serper API key (for web search)
3. **Voice agents**: OpenAI API key (for TTS)
4. **RAG agents**: Qdrant URL and API key, Firecrawl API key
5. **GitHub agent**: GitHub Personal Access Token
6. **Notion agent**: Notion API key
7. **Multi-agent**: Multiple API keys as needed

## Running the Converted Agents

### Voice AI Agents

#### AI Audio Tour Agent
```bash
cd crewai_version/voice_ai_agents/ai_audio_tour_agent
python ai_audio_tour_agent.py
```
- Enter OpenAI API key in the interface
- Specify location and interests
- Generate audio tour

#### Customer Support Voice Agent
```bash
cd crewai_version/voice_ai_agents/customer_support_voice_agent
python customer_support_voice_agent.py
```
- Configure Qdrant, Firecrawl, and OpenAI API keys
- Enter documentation URL
- Ask questions and receive voice responses

#### Voice RAG Agent
```bash
cd crewai_version/voice_ai_agents/voice_rag_openaisdk
python rag_voice.py
```
- Configure Qdrant and OpenAI API keys
- Upload PDF documents
- Ask questions and receive voice responses

### MCP AI Agents

#### AI Travel Planner
```bash
cd crewai_version/mcp_ai_agents/ai_travel_planner_mcp_agent_team
python app.py
```
- Enter OpenAI API key
- Specify destination, duration, budget, and preferences
- Generate detailed itinerary with calendar download

#### Browser Agent
```bash
cd crewai_version/mcp_ai_agents/browser_mcp_agent
python main.py
```
- Enter OpenAI API key
- Send commands to navigate and extract information from websites

#### GitHub Agent
```bash
cd crewai_version/mcp_ai_agents/github_mcp_agent
python github_agent.py
```
- Enter OpenAI API key and GitHub token
- Query repositories, issues, and PRs

#### Multi-Service Agent
```bash
cd crewai_version/mcp_ai_agents/multi_mcp_agent
python multi_mcp_agent.py
```
- Enter OpenAI, GitHub, and Serper API keys
- Chat with assistant for GitHub and web search tasks

#### Notion Agent
```bash
cd crewai_version/mcp_ai_agents/notion_mcp_agent
python notion_mcp_agent.py
```
- Enter OpenAI and Notion API keys
- Provide Notion page ID
- Interact with Notion pages

## Key Differences from Original

### Agent Implementation
- **Original**: Used `agno.agent.Agent` with specific model classes
- **Converted**: Uses `crewai.Agent` with `langchain_openai.ChatOpenAI`

### Task Execution
- **Original**: Direct agent execution with `Runner.run()` or `agent.arun()`
- **Converted**: Task-based execution with `Crew.kickoff()`

### Tool Usage
- **Original**: Native MCP tools and agno-specific tools
- **Converted**: CrewAI tools and LangChain tools

### UI Framework
- **Original**: Streamlit components (`st.button()`, `st.audio()`, etc.)
- **Converted**: Gradio components (`gr.Button()`, `gr.Audio()`, etc.)

## Notes

1. **Voice Features**: All voice agents maintain OpenAI TTS functionality
2. **Async Operations**: Converted to work with Gradio's async handling
3. **Session State**: Gradio uses global state instead of Streamlit's session state
4. **Progress Indicators**: Gradio's `Progress` component replaces Streamlit's `spinner`

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure all required API keys are provided in the interface
2. **Tool Errors**: Some CrewAI tools may require additional configuration
3. **Audio Issues**: Make sure OpenAI API key has access to TTS models
4. **Import Errors**: Verify all dependencies are installed

### Getting Help

If you encounter issues:
1. Check the console output for detailed error messages
2. Verify API keys are valid and have appropriate permissions
3. Ensure all dependencies are installed correctly
4. Review the original implementation for context

## License

Same as the original awesome-llm-apps repository.
