# Import the required libraries
import asyncio
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

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using Llama 3.2")

# Set up the configuration for the SmartScraperGraph
graph_config = {
    "llm": {
        "model": "ollama/llama3.2",
        "temperature": 0,
        "format": "json",  # Ollama needs the format to be specified explicitly
        "base_url": "http://localhost:11434",  # set Ollama URL
    },
    "embeddings": {
        "model": "ollama/nomic-embed-text",
        "base_url": "http://localhost:11434",  # set Ollama URL
    },
    "verbose": True,
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
    with st.spinner("Fetching the page, then asking the model..."):
        result = smart_scraper_graph.run()
    st.write(result)

    # When the answer looks wrong it is usually the *input* to the model that
    # is wrong, not the model. `final_state` keeps every intermediate value,
    # so show what was fetched and what was actually handed to the LLM.
    state = smart_scraper_graph.final_state or {}
    docs = state.get("doc") or []
    html = docs[0].page_content if docs else ""
    chunks = [c for c in (state.get("parsed_doc") or []) if isinstance(c, str)]
    parsed = "\n\n".join(chunks)

    if not parsed.strip():
        st.warning(
            "The parsed text is empty, so the model was asked to answer from "
            "nothing. The page most likely renders its content with JavaScript, "
            "or the fetch landed on an error page."
        )

    with st.expander("What the model actually saw (open this if the answer looks wrong)"):
        st.write(
            f"fetched HTML: **{len(html):,}** chars → "
            f"text handed to the model: **{len(parsed):,}** chars "
            f"in **{len(chunks)}** chunk(s)"
        )
        st.text(parsed[:3000] if parsed.strip() else "(empty)")
        st.caption("Per-node time and token use")
        st.dataframe(smart_scraper_graph.get_execution_info())
