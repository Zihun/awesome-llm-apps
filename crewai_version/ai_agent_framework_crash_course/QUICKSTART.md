# Quick Start Guide

This guide will help you get started with the CrewAI + Gradio conversions of the AI Agent Framework Crash Course.

## Installation

### 1. Install Dependencies

```bash
cd crewai_version/ai_agent_framework_crash_course
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
SERPER_API_KEY=your-serper-api-key-here  # Optional, for search
```

## Quick Examples

### Example 1: Personal Assistant Agent (Gradio UI)

```bash
cd openai_sdk_crash_course/1_starter_agent
python app.py
```

Then open http://localhost:7860 in your browser.

### Example 2: Support Ticket Creator (Gradio UI)

```bash
cd openai_sdk_crash_course/2_structured_output_agent
python support_ticket_app.py
```

### Example 3: Function Tools Agent (Gradio UI)

```bash
cd openai_sdk_crash_course/3_tool_using_agent/3_1_function_tools
python app.py
```

### Example 4: Multi-Agent Researcher (Gradio UI)

```bash
cd google_adk_crash_course/8_simple_multi_agent/multi_agent_researcher
python app.py
```

## Using Agents Programmatically

### Basic Agent Usage

```python
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create agent
agent = Agent(
    role="Assistant",
    goal="Help users with their questions",
    backstory="You are a helpful assistant.",
    llm=llm
)

# Create task
task = Task(
    description="What are 3 tips for productivity?",
    expected_output="3 helpful productivity tips",
    agent=agent
)

# Run crew
crew = Crew(agents=[agent], tasks=[task], verbose=True)
result = crew.kickoff()
print(result)
```

### Using Structured Output

```python
from crewai_version.ai_agent_framework_crash_course.openai_sdk_crash_course.2_structured_output_agent.2_1_support_ticket_agent.agent import create_support_ticket

complaint = "I can't log into my account!"
ticket = create_support_ticket(complaint)
print(f"Title: {ticket.title}")
print(f"Priority: {ticket.priority}")
```

### Using Tools

```python
from crewai_version.ai_agent_framework_crash_course.openai_sdk_crash_course.3_tool_using_agent.3_1_function_tools.agent import function_tools_agent
from crewai import Task, Crew

task = Task(
    description="Add 25 and 17, then convert the result to a percentage of 100",
    expected_output="The calculation result",
    agent=function_tools_agent
)

crew = Crew(agents=[function_tools_agent], tasks=[task])
result = crew.kickoff()
print(result)
```

### Multi-Agent Research

```python
from crewai_version.ai_agent_framework_crash_course.google_adk_crash_course.8_simple_multi_agent.multi_agent_researcher.agent import create_research_crew

crew = create_research_crew("AI trends in 2025")
result = crew.kickoff()
print(result)
```

## Directory Structure

```
crewai_version/ai_agent_framework_crash_course/
├── openai_sdk_crash_course/          # Converted from OpenAI Agents SDK
│   ├── 1_starter_agent/              # Basic agents
│   ├── 2_structured_output_agent/    # Pydantic models
│   ├── 3_tool_using_agent/           # Custom tools
│   └── 9_multi_agent_orchestration/  # Parallel execution
├── google_adk_crash_course/          # Converted from Google ADK
│   ├── 1_starter_agent/              # Basic agents
│   ├── 4_tool_using_agent/           # Tools (calculator)
│   └── 8_simple_multi_agent/         # Multi-agent systems
├── requirements.txt
├── .env.example
├── README.md                          # Full documentation
└── QUICKSTART.md                      # This file
```

## Available Gradio Apps

| App | Location | Description |
|-----|----------|-------------|
| Personal Assistant | `openai_sdk_crash_course/1_starter_agent/app.py` | Basic conversational agent |
| Support Ticket Creator | `openai_sdk_crash_course/2_structured_output_agent/support_ticket_app.py` | Structured output example |
| Function Tools Agent | `openai_sdk_crash_course/3_tool_using_agent/3_1_function_tools/app.py` | Custom tools demo |
| Multi-Agent Researcher | `google_adk_crash_course/8_simple_multi_agent/multi_agent_researcher/app.py` | Multi-agent coordination |

## Common Commands

### Run All Tests (if you create tests)

```bash
pytest tests/
```

### Format Code

```bash
black .
```

### Check Types

```bash
mypy .
```

## Troubleshooting

### Issue: Import errors

**Solution:** Make sure you're running from the correct directory and have installed all dependencies.

```bash
pip install -r requirements.txt
```

### Issue: API key errors

**Solution:** Check your `.env` file has the correct API keys:

```bash
cat .env
```

### Issue: Gradio port already in use

**Solution:** Use a different port:

```python
demo.launch(server_port=7861)
```

### Issue: Search tools not working

**Solution:** Make sure you have `SERPER_API_KEY` set in `.env` and have installed:

```bash
pip install google-serper
```

## Next Steps

1. **Explore Examples**: Try all the Gradio apps
2. **Modify Agents**: Change backstories and goals
3. **Add Tools**: Create custom tools for your use case
4. **Build Multi-Agent Systems**: Combine agents for complex workflows
5. **Read Full Documentation**: Check `README.md` for detailed information

## Learning Path

### Beginner

1. Start with `1_starter_agent/app.py`
2. Understand basic agent creation and tasks
3. Try modifying the agent's backstory

### Intermediate

1. Explore `2_structured_output_agent/support_ticket_app.py`
2. Learn about Pydantic models and structured output
3. Create your own structured output agent

### Advanced

1. Study `3_tool_using_agent/3_1_function_tools/agent.py`
2. Build custom tools for your domain
3. Explore `8_simple_multi_agent/multi_agent_researcher/agent.py`
4. Create multi-agent workflows with task dependencies

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Gradio Documentation](https://gradio.app/docs/)
- [LangChain Documentation](https://python.langchain.com/)
- [Original Repository](https://github.com/Shubhamsaboo/awesome-llm-apps)

## Support

For issues or questions:
1. Check the `README.md` for detailed documentation
2. Review the troubleshooting section above
3. Check the original repository for comparison
4. Open an issue on GitHub

## Contributing

To add new conversions:
1. Follow the patterns in existing files
2. Include both agent files and Gradio apps
3. Update `README.md` with your additions
4. Test thoroughly before submitting

---

Happy coding! 🚀
