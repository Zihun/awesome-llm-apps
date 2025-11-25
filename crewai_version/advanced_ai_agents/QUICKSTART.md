# Quick Start Guide - CrewAI + Gradio AI Agents

Get started with the converted AI agent applications in minutes!

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/zihun/work/awesome-llm-apps/crewai_version/advanced_ai_agents
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in this directory:

```bash
# Copy the example and edit with your keys
cat > .env << 'EOF'
# OpenAI (Required for most apps)
OPENAI_API_KEY=sk-your-key-here

# Google AI (For Gemini models)
GOOGLE_API_KEY=AIza-your-key-here

# Anthropic (For Claude models)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Groq (For Llama models - free tier available!)
GROQ_API_KEY=gsk_your-key-here

# Optional: For specific apps
SERPER_API_KEY=your-serper-key
SPOONACULAR_API_KEY=your-spoonacular-key
FIRECRAWL_API_KEY=fc_your-firecrawl-key
EOF
```

**Where to get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Google AI: https://aistudio.google.com/apikey
- Anthropic: https://console.anthropic.com/
- Groq (FREE!): https://console.groq.com/
- Serper: https://serper.dev/
- Spoonacular: https://spoonacular.com/food-api
- Firecrawl: https://firecrawl.dev/

## Run Your First App (30 seconds)

### Option 1: Tic-Tac-Toe Battle (Most Fun!)

Watch AI agents battle each other in Tic-Tac-Toe:

```bash
python autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent.py
```

**What you'll see:**
- Real-time game between Claude 3.7 Sonnet and GPT-4o
- Live move-by-move visualization
- Full game history
- Choose different AI models to compete

**Requirements:** Just OPENAI_API_KEY and ANTHROPIC_API_KEY

---

### Option 2: Recipe & Meal Planning (Most Practical!)

Your personal AI chef and nutritionist:

```bash
python single_agent_apps/ai_recipe_meal_planning_agent.py
```

**Try asking:**
- "Find healthy chicken recipes for dinner"
- "Create a vegetarian meal plan for 2 people for one week"
- "What's the nutrition info for Greek salad?"
- "Estimate costs for pasta, tomatoes, cheese for 4 servings"

**Requirements:** OPENAI_API_KEY, SPOONACULAR_API_KEY (optional)

---

### Option 3: Personal Finance Planner (Most Valuable!)

Get AI-powered financial planning:

```bash
python single_agent_apps/ai_personal_finance_agent.py
```

**Example inputs:**
- **Goals:** "Save for retirement by 55, build emergency fund"
- **Situation:** "35 years old, $80k salary, $50k savings, $200k mortgage"

**What you get:**
- Comprehensive research on financial strategies
- Personalized budget breakdown
- Investment recommendations
- Actionable savings strategies

**Requirements:** OPENAI_API_KEY, SERPER_API_KEY

---

### Option 4: Health & Fitness Coach

Personalized health and fitness plans:

```bash
python single_agent_apps/ai_health_fitness_agent.py
```

**Input your profile:**
- Age, weight, height
- Activity level
- Dietary preferences
- Fitness goals

**Get:**
- Custom daily meal plans
- Personalized workout routines
- Nutritional guidance
- Q&A about your plan

**Requirements:** GOOGLE_API_KEY (Gemini)

---

### Option 5: HackerNews Researcher (For Tech Enthusiasts!)

Multi-agent research team for HackerNews topics:

```bash
python multi_agent_apps/multi_agent_researcher.py
```

**Try researching:**
- "Latest AI developments"
- "Startup funding trends"
- "Modern web development frameworks"

**What happens:**
- Agents search HackerNews
- Read and summarize articles
- Gather web context
- Create comprehensive report

**Requirements:** OPENAI_API_KEY

## Understanding the Apps

### Single Agent Apps
Simple, focused AI agents for specific tasks:
- **Recipe Planning** - Food and nutrition expert
- **Personal Finance** - Financial advisor (with research team)
- **Health & Fitness** - Wellness coach (dietary + fitness experts)

### Multi-Agent Apps
Collaborative AI teams with specialized roles:
- **HackerNews Researcher** - Research team (HN expert, web searcher, article reader)

### Autonomous Game Playing
AI agents playing games autonomously:
- **Tic-Tac-Toe Battle** - Watch AIs compete in strategy game

## Gradio Features

All apps run in your browser at `http://localhost:7860` with:

- 🎨 Modern, responsive UI
- 💬 Interactive chat interfaces
- 📊 Real-time progress updates
- 🔄 Easy sharing with `share=True`
- 📱 Mobile-friendly
- 🎯 Example queries to get started

## Customization

### Change AI Models

Most apps let you switch models easily:

```python
# In the code, change:
llm = ChatOpenAI(model="gpt-4o")  # OpenAI
# To:
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")  # Google
# Or:
llm = ChatAnthropic(model="claude-3-7-sonnet-20250219")  # Anthropic
```

### Modify Gradio Interface

Gradio makes UI changes easy:

```python
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Your Title")

    # Add components
    input_box = gr.Textbox(label="Input")
    button = gr.Button("Submit")
    output = gr.Markdown()

    # Connect them
    button.click(fn=your_function, inputs=input_box, outputs=output)

demo.launch(share=True)  # share=True for public URL
```

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### API Key errors
1. Check `.env` file exists in the correct directory
2. Verify API key format (no extra spaces)
3. Test keys at provider websites
4. Restart the Python script after adding keys

### "Rate limit exceeded"
- Wait a few moments
- Check your API quota/billing
- For OpenAI: Consider using gpt-4o-mini instead of gpt-4o

### Gradio won't open in browser
```bash
# The app will print the URL, manually open it:
# Running on local URL:  http://127.0.0.1:7860
```

## Tips for Best Results

### 1. Start with Free/Cheap Options
- Use Groq's Llama models (FREE!)
- Google's Gemini Flash is very affordable
- OpenAI's gpt-4o-mini is 80% cheaper than gpt-4o

### 2. Use Share Links
```python
demo.launch(share=True)  # Get a public URL to show others
```

### 3. Try Examples
All apps include example queries - click them to see what's possible!

### 4. Monitor Costs
- OpenAI: https://platform.openai.com/usage
- Anthropic: https://console.anthropic.com/
- Google: https://console.cloud.google.com/

## Next Steps

1. ✅ Run all 5 demo apps
2. 📚 Read the main [README.md](README.md) for conversion details
3. 🔨 Try converting more apps from the original repo
4. 🎨 Customize the Gradio interfaces
5. 🤖 Experiment with different AI models
6. 🚀 Deploy your favorite app (Hugging Face Spaces, Railway, etc.)

## Deployment

Deploy any app to Hugging Face Spaces:

```bash
# Install Hugging Face CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Create a Space (one-time)
# Then push your app file as app.py
```

Or use Railway, Render, or any Python hosting service.

## Support

- Original repo: https://github.com/Shubhamsaboo/awesome-llm-apps
- CrewAI docs: https://docs.crewai.com/
- Gradio docs: https://gradio.app/docs/

## Have Fun!

These apps demonstrate the power of:
- 🤖 **CrewAI** - structured multi-agent collaboration
- 🎨 **Gradio** - beautiful, shareable UIs
- 🧠 **Multiple LLMs** - best model for each task

Start building your own AI agent teams! 🚀
