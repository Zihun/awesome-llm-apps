# CrewAI + Gradio Converted Apps

This directory contains all Python applications from `/advanced_llm_apps/` converted from Agno + Streamlit to CrewAI + Gradio.

## Conversion Summary

All applications have been converted following these rules:

### 1. Framework Conversions

#### Agno → CrewAI
- `from agno.agent import Agent` → `from crewai import Agent`
- `from agno.models.openai import OpenAIChat` → `from langchain_openai import ChatOpenAI`
- `from agno.tools.*` → `crewai_tools` or `langchain` equivalents
- Memory classes updated to use LangChain implementations

#### Streamlit → Gradio
- `st.title()` → `gr.Markdown("# title")`
- `st.text_input()` → `gr.Textbox()`
- `st.chat_message()` → `gr.Chatbot()`
- `st.chat_input()` → `gr.Textbox()` with submit
- `st.session_state` → `gr.State()` or global variables
- `st.file_uploader()` → `gr.File()`
- `st.button()` → `gr.Button()`
- `st.selectbox()` → `gr.Dropdown()` or `gr.Radio()`

### 2. Converted Applications

#### Chat with Tarots (2 files)
- `/chat-with-tarots/app.py` - Tarot reading app with image gallery
- `/chat-with-tarots/helpers/help_func.py` - Helper functions

#### Chat with X Tutorials (6 files)
- `/chat_with_X_tutorials/chat_with_github/chat_github.py` - Chat with GitHub repositories
- `/chat_with_X_tutorials/chat_with_gmail/chat_gmail.py` - Chat with Gmail inbox
- `/chat_with_X_tutorials/chat_with_pdf/chat_pdf.py` - Chat with PDF documents
- `/chat_with_X_tutorials/chat_with_research_papers/chat_arxiv.py` - Search and chat with arXiv papers (uses CrewAI Agent)
- `/chat_with_X_tutorials/chat_with_substack/chat_substack.py` - Chat with Substack newsletters
- `/chat_with_X_tutorials/chat_with_youtube_videos/chat_youtube.py` - Chat with YouTube video transcripts

#### Cursor AI Experiments (4 files)
- `/cursor_ai_experiments/ai_web_scrapper.py` - AI-powered web scraper
- `/cursor_ai_experiments/chatgpt_clone_llama3.py` - Local ChatGPT clone with Llama3
- `/cursor_ai_experiments/llm_router_app/llm_router.py` - LLM router between GPT-4 and Llama
- `/cursor_ai_experiments/multi_agent_researcher.py` - Multi-agent article researcher (CrewAI-based)

#### LLM Apps with Memory Tutorials (6 files)
- `/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory/ai_arxiv_agent_memory.py` - arXiv agent with Mem0
- `/llm_apps_with_memory_tutorials/ai_travel_agent_memory/travel_agent_memory.py` - Travel agent with memory
- `/llm_apps_with_memory_tutorials/llama3_stateful_chat/local_llama3_chat.py` - Local Llama3 with state
- `/llm_apps_with_memory_tutorials/llm_app_personalized_memory/llm_app_memory.py` - LLM with personalized memory
- `/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py` - Local ChatGPT with Mem0
- `/llm_apps_with_memory_tutorials/multi_llm_memory/multi_llm_memory.py` - Multi-LLM with shared memory

#### Other Apps (2 files)
- `/gpt_oss_critique_improvement_loop/streamlit_app.py` - Critique & improvement loop with Groq
- `/resume_job_matcher/app.py` - Resume and job description matcher

**Total: 20 Python files converted**

## Key Features of Converted Apps

### Gradio Interface Patterns

1. **Chat Applications**
   ```python
   with gr.Blocks() as demo:
       chatbot = gr.Chatbot()
       msg = gr.Textbox()
       msg.submit(respond, [msg, chatbot], [chatbot])
   ```

2. **Configuration + Main Content**
   ```python
   with gr.Row():
       with gr.Column(scale=1):
           # Configuration inputs
       with gr.Column(scale=2):
           # Main content area
   ```

3. **State Management**
   - Global variables for persistent state
   - History parameter in chat functions
   - User session tracking

### CrewAI Integration

Applications using CrewAI:
- `multi_agent_researcher.py` - Uses Agent, Task, Crew, Process
- `chat_arxiv.py` - Uses Agent with custom tools

### Memory Integration (Mem0)

Applications with memory features use:
- Qdrant vector store
- User-specific memory contexts
- Search and retrieval of relevant memories
- Memory viewing and management

## Running the Apps

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install gradio crewai langchain-openai embedchain mem0 multion
   pip install ollama litellm groq scrapegraphai
   pip install youtube-transcript-api pymupdf arxiv
   ```

2. **Set up Services**
   - Ollama (for local models): https://ollama.ai
   - Qdrant (for memory apps): Run on localhost:6333
   - LM Studio (for some apps): Run on localhost:1234

3. **API Keys**
   - OpenAI API Key
   - Anthropic API Key (for multi-LLM apps)
   - Groq API Key (for critique loop)
   - MultiOn API Key (for arXiv agent)
   - Together AI API Key (for router app)

### Running Individual Apps

```bash
# Navigate to any app directory
cd /Users/zihun/work/awesome-llm-apps/crewai_version/advanced_llm_apps/[app_name]

# Run the app
python app.py  # or the specific filename

# The Gradio interface will launch in your browser
```

### Example Commands

```bash
# Chat with PDF
cd chat_with_X_tutorials/chat_with_pdf
python chat_pdf.py

# Multi-agent researcher
cd cursor_ai_experiments
python multi_agent_researcher.py

# Travel agent with memory
cd llm_apps_with_memory_tutorials/ai_travel_agent_memory
python travel_agent_memory.py
```

## Differences from Original

1. **UI Framework**: Gradio provides a more modern, responsive interface compared to Streamlit
2. **State Management**: Uses global variables or function parameters instead of `st.session_state`
3. **Event Handling**: Explicit event handlers with `.click()` and `.submit()` methods
4. **Layout**: Row/Column based layout system in Gradio
5. **Real-time Updates**: Gradio's reactive nature allows for dynamic updates

## Notes

- All file paths in this README are absolute paths starting from `/Users/zihun/work/awesome-llm-apps/crewai_version/advanced_llm_apps/`
- Original apps remain unchanged in `/Users/zihun/work/awesome-llm-apps/advanced_llm_apps/`
- Some apps require external services (Ollama, Qdrant, etc.) to be running locally
- API keys should be provided through the UI or environment variables
- Error handling has been improved in the converted versions

## Testing

To test an app:
1. Install required dependencies
2. Start necessary services (Ollama, Qdrant, etc.)
3. Run the Python file
4. Access the Gradio interface in your browser
5. Provide API keys through the UI
6. Test the functionality

## Support

For issues or questions about the converted apps, please refer to:
- CrewAI Documentation: https://docs.crewai.com
- Gradio Documentation: https://gradio.app/docs
- Original app documentation in the parent directory
