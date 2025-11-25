from crewai import Agent, Task, Crew
import gradio as gr
from langchain_openai import ChatOpenAI
import pandas as pd
import base64
from PIL import Image
from io import BytesIO
from together import Together
from e2b_code_interpreter import Sandbox
import re

pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)

def analyze_and_visualize(together_key, e2b_key, model_name, file, query):
    if not all([together_key, e2b_key, file, query]):
        return None, "Please provide all required inputs"

    try:
        # Read dataset
        df = pd.read_csv(file.name)
        dataset_path = f"./{file.name.split('/')[-1]}"

        # Initialize E2B sandbox
        with Sandbox(api_key=e2b_key) as code_interpreter:
            # Upload dataset
            code_interpreter.files.write(dataset_path, file)

            # Create prompt for LLM
            system_prompt = f"""You're a Python data scientist and data visualization expert.
            You have a dataset at path '{dataset_path}'.
            Analyze the dataset and answer the user's query with Python code for visualization.
            Always use the dataset path '{dataset_path}' when reading the CSV file.
            Use matplotlib or seaborn for visualizations."""

            client = Together(api_key=together_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
            )

            response_message = response.choices[0].message.content

            # Extract Python code
            match = pattern.search(response_message)
            if match:
                code = match.group(1)

                # Execute code in E2B sandbox
                exec_result = code_interpreter.run_code(code)

                if exec_result.error:
                    return None, f"Code execution error: {exec_result.error}\n\nLLM Response:\n{response_message}"

                # Get visualization if available
                if exec_result.results:
                    for result in exec_result.results:
                        if hasattr(result, 'png') and result.png:
                            png_data = base64.b64decode(result.png)
                            image = Image.open(BytesIO(png_data))
                            return image, response_message

                return None, response_message
            else:
                return None, f"No Python code found in response:\n{response_message}"

    except Exception as e:
        return None, f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="AI Data Visualization Agent") as app:
        gr.Markdown("# AI Data Visualization Agent")
        gr.Markdown("Upload your dataset and get AI-powered visualizations!")

        with gr.Row():
            with gr.Column():
                together_key = gr.Textbox(
                    label="Together AI API Key",
                    type="password",
                    placeholder="Enter Together AI API Key"
                )
                gr.Markdown("[Get Together AI API Key](https://api.together.ai/signin)")

                e2b_key = gr.Textbox(
                    label="E2B API Key",
                    type="password",
                    placeholder="Enter E2B API Key"
                )
                gr.Markdown("[Get E2B API Key](https://e2b.dev/docs/legacy/getting-started/api-key)")

                model_options = {
                    "Meta-Llama 3.1 405B": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                    "DeepSeek V3": "deepseek-ai/DeepSeek-V3",
                    "Qwen 2.5 7B": "Qwen/Qwen2.5-7B-Instruct-Turbo",
                    "Meta-Llama 3.3 70B": "meta-llama/Llama-3.3-70B-Instruct-Turbo"
                }

                model_select = gr.Dropdown(
                    choices=list(model_options.keys()),
                    value="Meta-Llama 3.1 405B",
                    label="Select Model"
                )

                file_input = gr.File(
                    label="Choose a CSV file",
                    file_types=[".csv"]
                )

                query_input = gr.Textbox(
                    label="What would you like to know about your data?",
                    placeholder="Can you compare the average cost for two people between different categories?",
                    lines=3
                )

                analyze_btn = gr.Button("Analyze", variant="primary")

        with gr.Row():
            with gr.Column():
                viz_output = gr.Image(label="Visualization")

            with gr.Column():
                text_output = gr.Textbox(label="AI Response", lines=15)

        def process_request(together_key, e2b_key, model_name, file, query):
            model_id = model_options[model_name]
            return analyze_and_visualize(together_key, e2b_key, model_id, file, query)

        analyze_btn.click(
            fn=process_request,
            inputs=[together_key, e2b_key, model_select, file_input, query_input],
            outputs=[viz_output, text_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
