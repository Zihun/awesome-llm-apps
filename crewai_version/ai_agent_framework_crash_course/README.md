# AI Agent Framework Crash Course - CrewAI + Gradio Versions

This directory contains **CrewAI + Gradio** conversions of all Python files from the original AI Agent Framework Crash Course. All agents have been converted from their original frameworks (OpenAI Agents SDK, Google ADK, Agno) to use CrewAI with Gradio interfaces.

## Conversion Overview

### Framework Changes

#### 1. Agent Framework Conversions

**Original → CrewAI:**

| Original Framework | Replaced With | Notes |
|-------------------|---------------|-------|
| `from agno.agent import Agent` | `from crewai import Agent, Task, Crew` | Core agent framework |
| `from agno.models.openai import OpenAIChat` | `from langchain_openai import ChatOpenAI` | LLM models |
| `from agents import Agent, Runner` | `from crewai import Agent, Task, Crew` | OpenAI SDK agents |
| `from google.adk.agents import LlmAgent` | `from crewai import Agent` | Google ADK agents |

#### 2. UI Framework Conversions

**Streamlit → Gradio:**

| Streamlit | Gradio | Notes |
|-----------|--------|-------|
| `import streamlit as st` | `import gradio as gr` | Core library |
| `st.chat_message()` | `gr.Chatbot()` | Chat interface |
| `st.chat_input()` | `gr.Textbox()` | User input |
| `st.button()` | `gr.Button()` | Buttons |
| `st.session_state` | Function parameters/state | State management |
| `st.selectbox()` | `gr.Radio()` or `gr.Dropdown()` | Selection widgets |

#### 3. Tool Conversions

**Original → CrewAI Tools:**

| Original | CrewAI | Notes |
|----------|--------|-------|
| `@function_tool` (OpenAI SDK) | `from crewai_tools import tool` | Custom tools |
| Function tools (Google ADK) | `@tool` decorator | CrewAI tools |
| Built-in tools | `crewai_tools` package | Pre-built tools |
| `google_search` | `SerperDevTool()` | Search functionality |

### Key Conversion Patterns

#### Agent Creation

**Before (OpenAI SDK):**
```python
from agents import Agent

agent = Agent(
    name="My Agent",
    instructions="Do something helpful"
)
```

**After (CrewAI):**
```python
from crewai import Agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0.7)

agent = Agent(
    role="My Agent",
    goal="Help users accomplish their goals",
    backstory="Do something helpful",
    llm=llm,
    verbose=True
)
```

#### Running Agents

**Before (OpenAI SDK):**
```python
from agents import Runner

result = Runner.run_sync(agent, "Hello")
result = await Runner.run(agent, "Hello")
```

**After (CrewAI):**
```python
from crewai import Task, Crew

task = Task(
    description="Hello",
    expected_output="A helpful response",
    agent=agent
)
crew = Crew(agents=[agent], tasks=[task], verbose=False)
result = crew.kickoff()
```

#### Structured Output

**Before (OpenAI SDK):**
```python
from pydantic import BaseModel
from agents import Agent

class Output(BaseModel):
    field: str

agent = Agent(
    name="Agent",
    instructions="...",
    output_type=Output
)
```

**After (CrewAI):**
```python
from pydantic import BaseModel
from crewai import Agent, Task, Crew
import json

class Output(BaseModel):
    field: str

agent = Agent(
    role="Agent",
    backstory="""
    ...
    Return ONLY valid JSON matching this schema:
    {"field": "string"}
    """,
    llm=llm
)

# Parse JSON from result
result = crew.kickoff()
output = Output(**json.loads(result))
```

#### Multi-Agent Orchestration

**Before (OpenAI SDK):**
```python
import asyncio
from agents import Agent, Runner

res1, res2 = await asyncio.gather(
    Runner.run(agent1, msg),
    Runner.run(agent2, msg)
)
```

**After (CrewAI):**
```python
import asyncio
from crewai import Agent, Task, Crew

async def run_crew(agent, task):
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    return await asyncio.to_thread(crew.kickoff)

res1, res2 = await asyncio.gather(
    run_crew(agent1, task1),
    run_crew(agent2, task2)
)
```

#### Gradio Chat Interface

**Standard Pattern:**
```python
import gradio as gr
from crewai import Agent, Task, Crew

def chat(message, history):
    task = Task(
        description=message,
        expected_output="A helpful response",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    return str(crew.kickoff())

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    submit = gr.Button("Send")

    def respond(message, chat_history):
        bot_message = chat(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    submit.click(respond, [msg, chatbot], [msg, chatbot])

demo.launch()
```

## Directory Structure

```
crewai_version/ai_agent_framework_crash_course/
├── openai_sdk_crash_course/
│   ├── 1_starter_agent/
│   │   ├── 1_personal_assistant_agent/
│   │   │   ├── agent.py
│   │   │   └── __init__.py
│   │   └── app.py (Gradio)
│   ├── 2_structured_output_agent/
│   │   ├── 2_1_support_ticket_agent/
│   │   │   ├── agent.py
│   │   │   └── __init__.py
│   │   └── 2_2_product_review_agent/
│   │       ├── agent.py
│   │       └── __init__.py
│   ├── 3_tool_using_agent/
│   │   └── 3_1_function_tools/
│   │       ├── agent.py
│   │       ├── tools.py
│   │       ├── app.py (Gradio)
│   │       └── __init__.py
│   └── 9_multi_agent_orchestration/
│       └── 9_1_parallel_execution/
│           ├── agent.py
│           └── __init__.py
├── google_adk_crash_course/
│   ├── 1_starter_agent/
│   │   └── creative_writing_agent/
│   │       ├── agent.py
│   │       └── __init__.py
│   ├── 4_tool_using_agent/
│   │   └── 4_2_function_tools/
│   │       └── calculator_agent/
│   │           ├── agent.py
│   │           ├── tools.py
│   │           └── __init__.py
│   └── 8_simple_multi_agent/
│       └── multi_agent_researcher/
│           ├── agent.py
│           └── __init__.py
└── README.md (this file)
```

## Files Converted

### OpenAI SDK Crash Course → CrewAI

1. **1_starter_agent/**
   - `1_personal_assistant_agent/agent.py` - Basic agent with sync/async execution
   - `app.py` - Gradio chat interface

2. **2_structured_output_agent/**
   - `2_1_support_ticket_agent/agent.py` - Structured output with Pydantic models
   - `2_2_product_review_agent/agent.py` - Product review analysis with structured output

3. **3_tool_using_agent/**
   - `3_1_function_tools/agent.py` - Agent with custom function tools
   - `3_1_function_tools/tools.py` - Custom tool implementations (add, multiply, weather, temperature)
   - `3_1_function_tools/app.py` - Gradio interface for tool-using agent

4. **9_multi_agent_orchestration/**
   - `9_1_parallel_execution/agent.py` - Parallel multi-agent execution with translation examples

### Google ADK Crash Course → CrewAI

1. **1_starter_agent/**
   - `creative_writing_agent/agent.py` - Creative writing assistant

2. **4_tool_using_agent/**
   - `4_2_function_tools/calculator_agent/agent.py` - Calculator agent with multiple tools
   - `4_2_function_tools/calculator_agent/tools.py` - Mathematical and statistical tools

3. **8_simple_multi_agent/**
   - `multi_agent_researcher/agent.py` - Multi-agent research system with coordinator pattern

## Installation

### Requirements

```bash
pip install crewai crewai-tools gradio langchain-openai python-dotenv pydantic
```

### Optional Tools

For search functionality:
```bash
pip install google-serper
```

### Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here  # Optional, for search tools
```

## Usage

### Running Individual Agents

```python
from crewai_version.ai_agent_framework_crash_course.openai_sdk_crash_course.1_starter_agent.1_personal_assistant_agent.agent import personal_assistant
from crewai import Task, Crew

task = Task(
    description="What are 3 productivity tips?",
    expected_output="3 helpful productivity tips",
    agent=personal_assistant
)

crew = Crew(agents=[personal_assistant], tasks=[task], verbose=True)
result = crew.kickoff()
print(result)
```

### Running Gradio Apps

```bash
cd crewai_version/ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent
python app.py
```

Then open your browser to `http://localhost:7860`

### Running Multi-Agent Systems

```python
from crewai_version.ai_agent_framework_crash_course.google_adk_crash_course.8_simple_multi_agent.multi_agent_researcher.agent import create_research_crew

crew = create_research_crew("Artificial Intelligence trends in 2025")
result = crew.kickoff()
print(result)
```

## Key Differences from Original

### Advantages of CrewAI Version

1. **Unified Framework**: All agents use the same CrewAI framework regardless of original source
2. **LangChain Integration**: Direct access to LangChain tools and models
3. **Gradio UI**: Modern, shareable web interfaces instead of Streamlit
4. **Process Control**: Explicit control over sequential, parallel, or hierarchical execution
5. **Task Definition**: Clear separation between agent capabilities and tasks

### Limitations

1. **No Native Streaming**: CrewAI doesn't support token-level streaming like OpenAI SDK
2. **Async Wrapper**: Async operations require `asyncio.to_thread` wrapper
3. **Structured Output**: Requires manual JSON parsing instead of native output_type
4. **Voice Features**: Voice/audio features from OpenAI SDK not directly portable

## Advanced Patterns

### Sequential Multi-Agent Workflow

```python
from crewai import Process

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.sequential  # Tasks run in order
)
```

### Parallel Multi-Agent Workflow

```python
import asyncio

async def run_parallel():
    results = await asyncio.gather(
        asyncio.to_thread(crew1.kickoff),
        asyncio.to_thread(crew2.kickoff),
        asyncio.to_thread(crew3.kickoff)
    )
    return results
```

### Hierarchical Multi-Agent Workflow

```python
from crewai import Process

crew = Crew(
    agents=[manager, worker1, worker2],
    tasks=[task1, task2, task3],
    process=Process.hierarchical,  # Manager delegates tasks
    manager_llm=manager_llm
)
```

### Context Sharing Between Tasks

```python
task1 = Task(description="Research topic", agent=researcher)
task2 = Task(
    description="Write article based on research",
    agent=writer,
    context=[task1]  # Has access to task1 output
)
```

## Callbacks and Memory

CrewAI supports callbacks through LangChain:

```python
from langchain.callbacks import StdOutCallbackHandler

crew = Crew(
    agents=[agent],
    tasks=[task],
    verbose=True,
    callbacks=[StdOutCallbackHandler()]
)
```

For memory, use LangChain's memory classes:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
# Use with agent's llm configuration
```

## Testing

Each converted file maintains the same functionality as the original. To test:

1. **Run the agent directly** using Python
2. **Launch Gradio apps** and test through the web interface
3. **Compare outputs** with original implementations

## Contributing

When adding new conversions:

1. Follow the established patterns in this README
2. Include both agent files and Gradio apps where applicable
3. Add proper error handling
4. Document any framework-specific quirks
5. Test thoroughly before committing

## Troubleshooting

### Common Issues

**Issue**: `No module named 'crewai'`
- **Solution**: `pip install crewai crewai-tools`

**Issue**: `OPENAI_API_KEY not found`
- **Solution**: Create `.env` file with your API key

**Issue**: Gradio app doesn't launch
- **Solution**: Check port 7860 is available, try `demo.launch(server_port=7861)`

**Issue**: Structured output parsing fails
- **Solution**: Ensure agent backstory explicitly requests JSON format

**Issue**: Search tools don't work
- **Solution**: Install `google-serper` and set `SERPER_API_KEY`

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Gradio Documentation](https://gradio.app/docs/)
- [LangChain Documentation](https://python.langchain.com/)
- [Original Repository](https://github.com/Shubhamsaboo/awesome-llm-apps)

## License

Same as the original repository.

---

**Note**: This conversion focuses on core functionality. Some advanced features from the original frameworks may require additional adaptation or have different implementations in CrewAI.
