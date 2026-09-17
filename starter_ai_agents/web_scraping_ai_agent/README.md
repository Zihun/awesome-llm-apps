# 🕷️ Web Scraping AI Agent

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-a-web-scraping-ai-agent-with-llama-3-2-running-locally) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

AI-powered web scraping using **ScrapeGraphAI** - extract structured data from websites using natural language prompts. This agent runs locally with the open-source `scrapegraphai` library.

---

## 📁 What's Inside

**Files**: `ai_scrapper.py`, `gemini_ai_scrapper.py`, `local_ai_scrapper.py`

| File | Model | Key needed |
|---|---|---|
| `ai_scrapper.py` | OpenAI GPT-4o / GPT-5 | OpenAI API key |
| `gemini_ai_scrapper.py` | Google Gemini 3.6 Flash / 2.5 Flash | Gemini API key |
| `local_ai_scrapper.py` | Ollama Llama 3.2 (local) | none |

Use the open-source ScrapeGraphAI library that runs on your local machine.

**✅ Pros:**
- Free to use (no API costs)
- Full control over execution
- Privacy-friendly (all data stays local)

**❌ Cons:**
- Requires local installation and dependencies
- Limited by your hardware
- Need to manage updates

---

## 🚀 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/web_scraping_ai_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

The second command is required. `pip install playwright` only installs the Python bindings — the headless Chromium that ScrapeGraphAI actually renders pages with is a separate download. Skip it and scraping fails with `BrowserType.launch: Executable doesn't exist at ...`.

3. **Get an API key for the model you want to use**
- OpenAI (`ai_scrapper.py`): sign up for an [OpenAI account](https://platform.openai.com/) and obtain your API key
- Gemini (`gemini_ai_scrapper.py`): create a key in [Google AI Studio](https://aistudio.google.com/apikey). You can also export it as `GEMINI_API_KEY` to have the app pre-fill the input
- Local (`local_ai_scrapper.py`): no key needed — install [Ollama](https://ollama.com/), then `ollama pull llama3.2` and `ollama pull nomic-embed-text`

4. **Run the Streamlit App**
```bash
streamlit run ai_scrapper.py
# Or for Gemini:
streamlit run gemini_ai_scrapper.py
# Or for local models:
streamlit run local_ai_scrapper.py
```

---

## 💡 Use Cases

### E-commerce Scraping
```python
# Extract product information
prompt = "Extract product names, prices, and availability"
```

### Content Aggregation
```python
# Convert articles to structured data
prompt = "Extract article title, author, date, and main content"
```

### Competitive Intelligence
```python
# Monitor competitor websites
prompt = "Extract pricing, features, and updates"
```

### Lead Generation
```python
# Extract contact information
prompt = "Find company names, emails, and phone numbers"
```

---

## 🔧 How It Works

1. You provide your API key (OpenAI or Gemini; the local version needs none)
2. Select the model (GPT-4o, GPT-5, Gemini 3.6 Flash, or local models)
3. Enter the URL and extraction prompt
4. The app uses ScrapeGraphAI to scrape and extract data locally
5. Results are displayed in the app

---

## 📖 Documentation

- **ScrapeGraphAI Library**: [ScrapeGraphAI GitHub](https://github.com/VinciGit00/Scrapegraph-ai)

---
