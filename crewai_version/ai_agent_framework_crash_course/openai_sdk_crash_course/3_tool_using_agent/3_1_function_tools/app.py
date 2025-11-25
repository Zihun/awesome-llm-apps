"""
Gradio Web Interface for Tool Using Agent

This provides an interactive web interface to test the function tools agent.
"""

import os
import gradio as gr
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from tools import add_numbers, multiply_numbers, get_weather, convert_temperature

# Load environment variables
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please create a .env file with your OpenAI API key.")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create the agent
function_tools_agent = Agent(
    role="Function Tools Agent",
    goal="Help users with calculations and information using available tools",
    backstory="""
    You are a helpful assistant with access to various tools.

    Available tools:
    - add_numbers: Add two numbers together
    - multiply_numbers: Multiply two numbers together
    - get_weather: Get weather information for a city
    - convert_temperature: Convert between Celsius and Fahrenheit

    When users ask for calculations or information:
    1. Use the appropriate tool for the task
    2. Explain what you're doing
    3. Show the result clearly

    Always use the provided tools rather than doing calculations yourself.
    """,
    tools=[add_numbers, multiply_numbers, get_weather, convert_temperature],
    llm=llm,
    verbose=True
)

def chat(message, history):
    """Process user message and return agent response"""
    try:
        task = Task(
            description=message,
            expected_output="A helpful response using the appropriate tools",
            agent=function_tools_agent
        )
        crew = Crew(agents=[function_tools_agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Function Tools Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Function Tools Agent")
    gr.Markdown("**Tutorial 3.1**: Agent with custom function tools")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, label="Chat Interface")
            msg = gr.Textbox(
                label="Message",
                placeholder="Ask me to do calculations or get information...",
                lines=2
            )
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear Chat")

        with gr.Column(scale=1):
            gr.Markdown("### Available Tools")
            gr.Markdown("""
            - **add_numbers**: Add two numbers
            - **multiply_numbers**: Multiply two numbers
            - **get_weather**: Get weather info
            - **convert_temperature**: Temperature conversion
            """)

            gr.Markdown("### Example Prompts")
            example_prompts = [
                "Add 25 and 17",
                "What's 8 times 9?",
                "Get weather for New York",
                "Convert 100 Fahrenheit to Celsius",
                "Add 50 and 30, then multiply by 2"
            ]

            for prompt in example_prompts:
                gr.Button(prompt, size="sm").click(
                    lambda p=prompt: p,
                    None,
                    msg
                )

    def respond(message, chat_history):
        bot_message = chat(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    submit.click(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

    gr.Markdown("""
    ---
    ### Tutorial Information

    This demonstrates **CrewAI agents with custom function tools**. The agent can:
    - Use custom tools for calculations and information retrieval
    - Explain its reasoning and tool usage
    - Chain multiple tool calls together

    **Note**: This is converted from OpenAI Agents SDK to CrewAI + Gradio.
    """)

if __name__ == "__main__":
    demo.launch(share=False)
