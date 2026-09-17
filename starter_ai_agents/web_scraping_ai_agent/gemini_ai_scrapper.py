# Import the required libraries
import asyncio
import os
import sys

import streamlit as st
from scrapegraphai.graphs import SmartScraperGraph

# On Windows `streamlit run` swaps the asyncio policy to WindowsSelectorEventLoopPolicy
# for Tornado's sake (streamlit/web/bootstrap.py::_fix_tornado_crash), and a selector
# loop cannot spawn subprocesses -- so Playwright fails to start its driver with
# NotImplementedError. Streamlit sets that policy early precisely so scripts can
# override it; Tornado's server loop already exists and keeps the loop it was built on.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ScrapeGraphAI 2.2.4 only knows the context window of models that are listed in
# its own `models_tokens` table. Gemini 3.x is not in that table yet, so without
# an explicit `model_tokens` the library silently falls back to 8192 tokens and
# truncates long pages. Declare the real input limits here.
MODEL_TOKENS = {
    "gemini-3.6-flash": 1048576,
    "gemini-2.5-flash": 1048576,
}

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using the Gemini API")

# Get Gemini API key from user (pre-filled from GEMINI_API_KEY if it is set)
gemini_api_key = st.text_input(
    "Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", "")
)

if gemini_api_key:
    model = st.radio(
        "Select the model",
        list(MODEL_TOKENS),
        index=0,
    )
    graph_config = {
        "llm": {
            "api_key": gemini_api_key,
            # The `google_genai/` prefix tells ScrapeGraphAI which provider to
            # build the chat model from; without it the model name would have to
            # be present in `models_tokens` for the provider to be inferred.
            "model": f"google_genai/{model}",
            "model_tokens": MODEL_TOKENS[model],
        },
    }
    # Get the URL of the website to scrape
    url = st.text_input("Enter the URL of the website you want to scrape")
    # Get the user prompt
    user_prompt = st.text_input("What you want the AI agent to scrape from the website?")

    # Create a SmartScraperGraph object
    smart_scraper_graph = SmartScraperGraph(
        prompt=user_prompt,
        source=url,
        config=graph_config
    )
    # Scrape the website
    if st.button("Scrape"):
        result = smart_scraper_graph.run()
        st.write(result)
