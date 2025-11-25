# CrewAI + Gradio RAG Tutorials

This directory contains conversions of all RAG tutorials from the agno+streamlit framework to CrewAI+Gradio.

## Conversion Overview

All Python files have been converted following these rules:

### 1. Import Conversions

**From agno to CrewAI:**
- `from agno.agent import Agent` → `from crewai import Agent, Task, Crew`
- `from agno.models.openai import OpenAIChat` → `from langchain_openai import ChatOpenAI`
- `from agno.models.google import Gemini` → `from langchain_google_genai import ChatGoogleGenerativeAI`
- `from agno.models.ollama import Ollama` → `from langchain_community.llms import Ollama`
- `from agno.tools.*` → `from crewai_tools import *` or langchain equivalents
- `from agno.knowledge.*` → langchain document loaders and vector stores

### 2. Streamlit to Gradio Conversions

**UI Components:**
- `st.title()` → `gr.Markdown("# title")`
- `st.text_input()` → `gr.Textbox()`
- `st.text_area()` → `gr.Textbox(lines=N)`
- `st.button()` → `gr.Button()`
- `st.file_uploader()` → `gr.File()`
- `st.sidebar` → `gr.Tab()` or `gr.Accordion()`
- `st.session_state` → Global variables or `gr.State()`
- `st.chat_input()` → `gr.Textbox()` with `gr.Button()`
- `st.chat_message()` → Custom formatting with `gr.Textbox()`

### 3. CrewAI Agent Pattern for RAG

```python
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", api_key=api_key)

# Create Agent
agent = Agent(
    role="RAG Agent",
    goal="Answer questions based on documents",
    backstory="Expert researcher with access to documents",
    llm=llm,
    tools=[tool1, tool2],
    verbose=True
)

# Create Task
task = Task(
    description="Answer the question using context...",
    agent=agent,
    expected_output="Detailed answer"
)

# Execute
crew = Crew(agents=[agent], tasks=[task], verbose=True)
result = crew.kickoff()
```

## Converted Files

### Core RAG Applications
1. ✅ **local_rag_agent/local_rag_agent.py** - Local RAG with Ollama
2. ✅ **rag_chain/app.py** - Pharmaceutical RAG with Gemini
3. ✅ **gemini_agentic_rag/agentic_rag_gemini.py** - Advanced Gemini RAG with Qdrant
4. ✅ **autonomous_rag/autorag.py** - Autonomous RAG with GPT-4o
5. ✅ **ai_blog_search/app.py** - LangGraph-based blog search (maintained LangGraph)
6. ✅ **hybrid_search_rag/main.py** - Hybrid search with RAGLite

### Local Model RAG
7. ✅ **qwen_local_rag/qwen_local_rag_agent.py** - Qwen local reasoning
8. ✅ **deepseek_local_rag_agent/deepseek_rag_agent.py** - DeepSeek local RAG
9. ✅ **llama3.1_local_rag/llama3.1_local_rag.py** - Llama 3.1 local RAG

### Advanced RAG Techniques
10. ✅ **agentic_rag_with_reasoning/rag_reasoning_agent.py** - RAG with reasoning
11. ✅ **agentic_rag_embedding_gemma/agentic_rag_embeddinggemma.py** - EmbeddingGemma
12. ✅ **corrective_rag/corrective_rag.py** - Corrective RAG
13. ✅ **vision_rag/vision_rag.py** - Vision-based RAG

### Specialized RAG
14. ✅ **rag_agent_cohere/rag_agent_cohere.py** - Cohere RAG agent
15. ✅ **rag-as-a-service/rag_app.py** - RAG as a service with Ragie
16. ✅ **contextualai_rag_agent/contextualai_rag_agent.py** - Contextual AI RAG
17. ✅ **rag_database_routing/rag_database_routing.py** - Database routing
18. ✅ **agentic_rag_gpt5/agentic_rag_gpt5.py** - GPT-5 RAG
19. ✅ **local_hybrid_search_rag/local_main.py** - Local hybrid search

### Math Agent (Multi-file)
20. ✅ **agentic_rag_math_agent/app/streamlit.py** → **app/gradio_app.py**
21. ✅ **agentic_rag_math_agent/app/benchmark.py** - Kept as is
22. ✅ **agentic_rag_math_agent/rag/vector.py** - Kept as is
23. ✅ **agentic_rag_math_agent/rag/query_router.py** - Kept as is
24. ✅ **agentic_rag_math_agent/rag/guardrails.py** - Kept as is
25. ✅ **agentic_rag_math_agent/data/load_gsm8k_data.py** - Kept as is

## Directory Structure

```
crewai_version/rag_tutorials/
├── README.md (this file)
├── local_rag_agent/
│   └── local_rag_agent.py
├── rag_chain/
│   └── app.py
├── gemini_agentic_rag/
│   └── agentic_rag_gemini.py
├── ai_blog_search/
│   └── app.py
├── hybrid_search_rag/
│   └── main.py
├── autonomous_rag/
│   └── autorag.py
├── qwen_local_rag/
│   └── qwen_local_rag_agent.py
├── deepseek_local_rag_agent/
│   └── deepseek_rag_agent.py
├── rag-as-a-service/
│   └── rag_app.py
├── rag_agent_cohere/
│   └── rag_agent_cohere.py
├── contextualai_rag_agent/
│   └── contextualai_rag_agent.py
├── agentic_rag_embedding_gemma/
│   └── agentic_rag_embeddinggemma.py
├── agentic_rag_with_reasoning/
│   └── rag_reasoning_agent.py
├── llama3.1_local_rag/
│   └── llama3.1_local_rag.py
├── local_hybrid_search_rag/
│   └── local_main.py
├── corrective_rag/
│   └── corrective_rag.py
├── agentic_rag_gpt5/
│   └── agentic_rag_gpt5.py
├── vision_rag/
│   └── vision_rag.py
├── rag_database_routing/
│   └── rag_database_routing.py
└── agentic_rag_math_agent/
    ├── app/
    │   ├── gradio_app.py
    │   └── benchmark.py
    ├── rag/
    │   ├── vector.py
    │   ├── query_router.py
    │   └── guardrails.py
    └── data/
        └── load_gsm8k_data.py
```

## Running the Applications

Each converted application can be run independently:

```bash
# Example: Local RAG Agent
cd crewai_version/rag_tutorials/local_rag_agent
python local_rag_agent.py

# Example: Gemini Agentic RAG
cd crewai_version/rag_tutorials/gemini_agentic_rag
python agentic_rag_gemini.py
```

## Key Differences from Original

1. **Framework**: CrewAI instead of agno for agent orchestration
2. **UI**: Gradio instead of Streamlit for web interface
3. **Agent Pattern**: Using CrewAI's Agent→Task→Crew pattern
4. **Tools**: Using crewai_tools and langchain tools instead of agno tools
5. **State Management**: Gradio State() or global variables instead of st.session_state

## Dependencies

Main dependencies for the converted applications:

```bash
pip install crewai
pip install gradio
pip install langchain
pip install langchain-openai
pip install langchain-google-genai
pip install langchain-community
pip install langchain-qdrant
pip install qdrant-client
pip install crewai-tools
```

## Notes

- Some applications maintain their specialized frameworks (e.g., LangGraph in ai_blog_search)
- Local model applications require Ollama installation
- Cloud applications require appropriate API keys (OpenAI, Google, Qdrant, etc.)
- The math agent maintains its modular structure with separate files for different components

## Support

For issues or questions about the conversions, please refer to:
- CrewAI documentation: https://docs.crewai.com/
- Gradio documentation: https://gradio.app/docs/
- LangChain documentation: https://python.langchain.com/
