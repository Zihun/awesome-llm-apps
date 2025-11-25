"""
Gradio Web Interface for Tutorial 1: Your First Agent

This provides an interactive web interface to test the personal assistant agent
with different execution methods.
"""

import os
import asyncio
import gradio as gr
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please create a .env file with your OpenAI API key.")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create the agent
personal_assistant = Agent(
    role="Personal Assistant",
    goal="Help users with their questions and provide helpful information",
    backstory="""
    You are a helpful personal assistant.

    Your role is to:
    1. Answer questions clearly and concisely
    2. Provide helpful information and advice
    3. Be friendly and professional
    4. Offer practical solutions to problems

    When users ask questions:
    - Give accurate and helpful responses
    - Explain complex topics in simple terms
    - Offer follow-up suggestions when appropriate
    - Maintain a positive and supportive tone

    Keep responses concise but informative.
    """,
    llm=llm,
    verbose=True
)

def chat_sync(message, history):
    """Synchronous chat function"""
    try:
        task = Task(
            description=message,
            expected_output="A helpful response to the user's question",
            agent=personal_assistant
        )
        crew = Crew(agents=[personal_assistant], tasks=[task], verbose=False)
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def chat_async(message, history):
    """Asynchronous chat function"""
    try:
        task = Task(
            description=message,
            expected_output="A helpful response to the user's question",
            agent=personal_assistant
        )
        crew = Crew(agents=[personal_assistant], tasks=[task], verbose=False)
        result = asyncio.run(asyncio.to_thread(crew.kickoff))
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Personal Assistant Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Personal Assistant Agent")
    gr.Markdown("**Tutorial 1**: Your first CrewAI agent with different execution methods")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, label="Chat Interface")
            msg = gr.Textbox(
                label="Message",
                placeholder="Ask your personal assistant anything...",
                lines=2
            )
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear Chat")

        with gr.Column(scale=1):
            execution_method = gr.Radio(
                ["Synchronous", "Asynchronous"],
                label="Execution Method",
                value="Synchronous",
                info="Choose how to execute the agent"
            )

            gr.Markdown("### About Execution Methods")
            gr.Markdown("""
            **Synchronous**: Blocks until response is complete. Simple and straightforward.

            **Asynchronous**: Non-blocking execution. Good for concurrent operations.

            Note: CrewAI doesn't support native streaming like OpenAI Agents SDK.
            """)

            gr.Markdown("### Example Prompts")
            example_prompts = [
                "What are 3 productivity tips for remote work?",
                "Explain quantum computing in simple terms",
                "Write a short poem about technology",
                "How can I improve my focus and concentration?",
                "What's the difference between AI and machine learning?"
            ]

            for prompt in example_prompts:
                gr.Button(prompt, size="sm").click(
                    lambda p=prompt: p,
                    None,
                    msg
                )

    def respond(message, chat_history, method):
        if method == "Synchronous":
            bot_message = chat_sync(message, chat_history)
        else:
            bot_message = chat_async(message, chat_history)

        chat_history.append((message, bot_message))
        return "", chat_history

    msg.submit(respond, [msg, chatbot, execution_method], [msg, chatbot])
    submit.click(respond, [msg, chatbot, execution_method], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

    gr.Markdown("""
    ---
    ### Tutorial Information

    This is **Tutorial 1** of the CrewAI crash course. You're learning:
    - Basic agent creation with the Agent class
    - Different execution methods (sync, async)
    - Agent configuration with role, goal, and backstory
    - Interactive web interfaces with Gradio

    **Next**: Try Tutorial 2: Structured Output Agent to learn about type-safe responses.
    """)

if __name__ == "__main__":
    demo.launch(share=False)
