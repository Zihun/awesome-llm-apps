import streamlit as st
from openai import OpenAI
from agno.agent import Agent as AgnoAgent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat as AgnoOpenAIChat
from langchain_openai import ChatOpenAI 
import asyncio
from browser_use import Browser

st.set_page_config(page_title="PyGame Code Generator", layout="wide")

# Initialize session state
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {
        "openai": "",
        "gemini": ""
    }
if "model_provider" not in st.session_state:
    st.session_state.model_provider = "OpenAI"

# Streamlit sidebar for API keys
with st.sidebar:
    st.title("API Keys Configuration")

    st.session_state.model_provider = st.selectbox(
        "Select Model Provider",
        ["OpenAI", "Google Gemini"]
    )

    st.session_state.api_keys["openai"] = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.api_keys["openai"]
    )
    st.session_state.api_keys["gemini"] = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=st.session_state.api_keys["gemini"]
    )
    
    st.markdown("---")
    st.info("""
    📝 How to use:
    1. Enter your API keys above
    2. Write your PyGame visualization query
    3. Click 'Generate Code' to get the code
    4. Click 'Generate Visualization' to:
       - Open Trinket.io PyGame editor
       - Copy and paste the generated code
       - Watch it run automatically
    """)

# Main UI
st.title("🎮 AI 3D PyGame Visualizer")
example_query = "Create a particle system simulation where 100 particles emit from the mouse position and respond to keyboard-controlled wind forces"
query = st.text_area(
    "Enter your PyGame query:",
    height=70,
    placeholder=f"e.g.: {example_query}"
)

# Split the buttons into columns
col1, col2 = st.columns(2)
generate_code_btn = col1.button("Generate Code")
generate_vis_btn = col2.button("Generate Visualization")

if generate_code_btn and query:
    provider = st.session_state.model_provider

    # Validate API keys
    if provider == "OpenAI" and not st.session_state.api_keys["openai"]:
        st.error("Please provide OpenAI API key in the sidebar")
        st.stop()
    elif provider == "Google Gemini" and not st.session_state.api_keys["gemini"]:
        st.error("Please provide Google Gemini API key in the sidebar")
        st.stop()

    system_prompt = """You are a Pygame and Python Expert that specializes in making games and visualisation through pygame and python programming.
    Generate complete, working Python pygame code for the user's request.
    Return ONLY the Python code without any explanations or markdown backticks."""

    try:
        with st.spinner("Generating code..."):
            if provider == "OpenAI":
                client = OpenAI(api_key=st.session_state.api_keys["openai"])
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ]
                )
                extracted_code = response.choices[0].message.content
            else:  # Google Gemini
                import google.generativeai as genai
                genai.configure(api_key=st.session_state.api_keys["gemini"])
                model = genai.GenerativeModel("gemini-1.5-pro")
                response = model.generate_content(f"{system_prompt}\n\nUser request: {query}")
                extracted_code = response.text

        # Clean up code if wrapped in markdown
        if extracted_code.startswith("```python"):
            extracted_code = extracted_code[9:]
        if extracted_code.startswith("```"):
            extracted_code = extracted_code[3:]
        if extracted_code.endswith("```"):
            extracted_code = extracted_code[:-3]
        extracted_code = extracted_code.strip()

        # Store the generated code in session state
        st.session_state.generated_code = extracted_code

        # Display the code
        with st.expander("Generated PyGame Code", expanded=True):
            st.code(extracted_code, language="python")

        st.success("Code generated successfully! Click 'Generate Visualization' to run it.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

elif generate_vis_btn:
    if "generated_code" not in st.session_state:
        st.warning("Please generate code first before visualization")
    else:
        async def run_pygame_on_trinket(code: str) -> None:
            browser = Browser()
            from browser_use import Agent 
            async with await browser.new_context() as context:
                model = ChatOpenAI(
                    model="gpt-4o", 
                    api_key=st.session_state.api_keys["openai"]
                )
                
                agent1 = Agent(
                    task='Go to https://trinket.io/features/pygame, thats your only job.',
                    llm=model,
                    browser_context=context,
                )
                
                executor = Agent(
                    task='Executor. Execute the code written by the User by clicking on the run button on the right. ',
                    llm=model,
                    browser_context=context
                )

                coder = Agent(
                    task='Coder. Your job is to wait for the user for 10 seconds to write the code in the code editor.',
                    llm=model,
                    browser_context=context
                )
                
                viewer = Agent(
                    task='Viewer. Your job is to just view the pygame window for 10 seconds.',
                    llm=model,
                    browser_context=context,
                )

                with st.spinner("Running code on Trinket..."):
                    try:
                        await agent1.run()
                        await coder.run()
                        await executor.run()
                        await viewer.run()
                        st.success("Code is running on Trinket!")
                    except Exception as e:
                        st.error(f"Error running code on Trinket: {str(e)}")
                        st.info("You can still copy the code above and run it manually on Trinket")

        # Run the async function with the stored code
        asyncio.run(run_pygame_on_trinket(st.session_state.generated_code))

elif generate_code_btn and not query:
    st.warning("Please enter a query before generating code")