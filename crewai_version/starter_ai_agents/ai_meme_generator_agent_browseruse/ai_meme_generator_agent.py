import asyncio
import gradio as gr
from browser_use import Agent as BrowserAgent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import re

async def generate_meme(query: str, model_choice: str, api_key: str) -> str:
    if not api_key or not query:
        return None

    try:
        # Initialize the appropriate LLM based on user selection
        if model_choice == "Claude":
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=api_key
            )
        elif model_choice == "Deepseek":
            llm = ChatOpenAI(
                base_url='https://api.deepseek.com/v1',
                model='deepseek-chat',
                api_key=api_key,
                temperature=0.3
            )
        else:  # OpenAI
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=api_key,
                temperature=0.0
            )

        task_description = (
            "You are a meme generator expert. You are given a query and you need to generate a meme for it.\n"
            "1. Go to https://imgflip.com/memetemplates \n"
            "2. Click on the Search bar in the middle and search for ONLY ONE MAIN ACTION VERB (like 'bully', 'laugh', 'cry') in this query: '{0}'\n"
            "3. Choose any meme template that metaphorically fits the meme topic: '{0}'\n"
            "   by clicking on the 'Add Caption' button below it\n"
            "4. Write a Top Text (setup/context) and Bottom Text (punchline/outcome) related to '{0}'.\n"
            "5. Check the preview making sure it is funny and a meaningful meme. Adjust text directly if needed. \n"
            "6. Look at the meme and text on it, if it doesnt make sense, PLEASE retry by filling the text boxes with different text. \n"
            "7. Click on the Generate meme button to generate the meme\n"
            "8. Copy the image link and give it as the output\n"
        ).format(query)

        agent = BrowserAgent(
            task=task_description,
            llm=llm,
            max_actions_per_step=5,
            max_failures=25,
            use_vision=(model_choice != "Deepseek")
        )

        history = await agent.run()

        # Extract final result from agent history
        final_result = history.final_result()

        # Use regex to find the meme URL in the result
        url_match = re.search(r'https://imgflip\.com/i/(\w+)', final_result)
        if url_match:
            meme_id = url_match.group(1)
            return f"https://i.imgflip.com/{meme_id}.jpg"
        return None

    except Exception as e:
        return f"Error: {str(e)}"

def generate_meme_sync(query, model_choice, api_key):
    result = asyncio.run(generate_meme(query, model_choice, api_key))
    if result and result.startswith("http"):
        return result, result
    else:
        return None, result or "Failed to generate meme"

def create_app():
    with gr.Blocks(title="AI Meme Generator Agent - Browser Use") as app:
        gr.Markdown("# AI Meme Generator Agent - Browser Use")
        gr.Markdown("This AI browser agent does browser automation to generate memes based on your input with browser use.")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Model Configuration")

                model_choice = gr.Radio(
                    ["Claude", "Deepseek", "OpenAI"],
                    label="Select AI Model",
                    value="Claude"
                )

                api_key = gr.Textbox(
                    label="API Key",
                    type="password",
                    placeholder="Enter your API key"
                )

                gr.Markdown("""
                **API Key Links:**
                - [Claude API Key](https://console.anthropic.com)
                - [Deepseek API Key](https://platform.deepseek.com)
                - [OpenAI API Key](https://platform.openai.com)
                """)

            with gr.Column(scale=2):
                gr.Markdown("### Describe Your Meme Concept")

                query = gr.Textbox(
                    label="Meme Idea",
                    placeholder="Example: 'Ilya's SSI quietly looking at the OpenAI vs Deepseek debate while diligently working on ASI'",
                    lines=3
                )

                generate_btn = gr.Button("Generate Meme", variant="primary")

        with gr.Row():
            with gr.Column():
                meme_image = gr.Image(label="Generated Meme")
                meme_info = gr.Textbox(label="Meme URL / Status", lines=2)

        generate_btn.click(
            fn=generate_meme_sync,
            inputs=[query, model_choice, api_key],
            outputs=[meme_image, meme_info]
        )

    return app

if __name__ == '__main__':
    app = create_app()
    app.launch()
