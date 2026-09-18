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
            # ScrapeGraphAI forces real JSON output only for Ollama
            # (generate_answer_node.py:63-67 sets `llm_model.format`); every other
            # provider is merely *asked* for JSON inside the prompt. Gemini has a
            # native JSON mode that nothing wires up, and langchain-google-genai
            # defaults `temperature` to 0.7 -- extraction is not a creative task,
            # so pin both. (ChatOpenAI, by contrast, sends no temperature at all.)
            "temperature": 0,
            "response_mime_type": "application/json",
            # Gemini 3.x thinks by default, and thinking shares the response
            # budget -- which is how a long extraction comes back truncated or
            # hollow. Left unset, no ThinkingConfig is sent at all and the model's
            # own default depth applies. `thinking_level` is the Gemini 3+ knob
            # (`thinking_budget` is deprecated there, see langchain_google_genai
            # chat_models.py:3058-3086); pulling a list off a page needs little of it.
            "thinking_level": "low",
        },
        # Without this ScrapeGraphAI drops its own logger to WARNING
        # (scrapegraphai/graphs/abstract_graph.py:84-89). Every progress line it
        # writes -- `--- Executing FetchNode ---`, `Content scraped`,
        # `--- Executing GenerateAnswerNode ---` -- is an INFO record, so the
        # console stays completely silent while the graph runs and there is no way
        # to tell how far it got or whether it failed.
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
