import gradio as gr
import asyncio
import os
from together import AsyncTogether, Together

def create_app():
    # Define the models
    reference_models = [
        "Qwen/Qwen2-72B-Instruct",
        "Qwen/Qwen1.5-72B-Chat",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "databricks/dbrx-instruct",
    ]
    aggregator_model = "mistralai/Mixtral-8x22B-Instruct-v0.1"

    # Define the aggregator system prompt
    aggregator_system_prompt = """You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability. Responses from models:"""

    async def run_llm(model, user_prompt, together_api_key):
        """Run a single LLM call with a reference model."""
        async_client = AsyncTogether(api_key=together_api_key)
        response = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=512,
        )
        return model, response.choices[0].message.content

    async def process_query(together_api_key, user_prompt):
        if not together_api_key:
            return "Please enter your Together API key to use the app.", ""

        if not user_prompt:
            return "Please enter a question.", ""

        os.environ["TOGETHER_API_KEY"] = together_api_key
        client = Together(api_key=together_api_key)

        # Get individual model responses
        results = await asyncio.gather(*[run_llm(model, user_prompt, together_api_key) for model in reference_models])

        # Format individual responses
        individual_responses = ""
        for model, response in results:
            individual_responses += f"\n\n### Response from {model}\n\n{response}\n\n---"

        # Aggregate responses
        finalStream = client.chat.completions.create(
            model=aggregator_model,
            messages=[
                {"role": "system", "content": aggregator_system_prompt},
                {"role": "user", "content": ",".join(response for _, response in results)},
            ],
            stream=True,
        )

        # Collect aggregated response
        full_response = ""
        for chunk in finalStream:
            content = chunk.choices[0].delta.content or ""
            full_response += content

        return individual_responses, full_response

    def get_answer(together_api_key, user_prompt):
        individual, aggregated = asyncio.run(process_query(together_api_key, user_prompt))
        return individual, aggregated

    # Create Gradio interface
    with gr.Blocks(title="Mixture-of-Agents LLM App") as app:
        gr.Markdown("# Mixture-of-Agents LLM App")

        with gr.Row():
            with gr.Column(scale=3):
                api_key_input = gr.Textbox(
                    label="Together API Key",
                    type="password",
                    placeholder="Enter your Together API Key"
                )
                user_prompt_input = gr.Textbox(
                    label="Your Question",
                    placeholder="Enter your question here..."
                )
                submit_btn = gr.Button("Get Answer", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown("### About this app")
                gr.Markdown(
                    "This app demonstrates a Mixture-of-Agents approach using multiple Language Models (LLMs) "
                    "to answer a single question."
                )
                gr.Markdown("### How it works:")
                gr.Markdown(
                    """
                    1. The app sends your question to multiple LLMs:
                        - Qwen/Qwen2-72B-Instruct
                        - Qwen/Qwen1.5-72B-Chat
                        - mistralai/Mixtral-8x22B-Instruct-v0.1
                        - databricks/dbrx-instruct
                    2. Each model provides its own response
                    3. All responses are then aggregated using Mixtral-8x22B-Instruct-v0.1
                    4. The final aggregated response is displayed
                    """
                )
                gr.Markdown(
                    "This approach allows for a more comprehensive and balanced answer by leveraging multiple AI models."
                )

        with gr.Row():
            with gr.Column():
                gr.Markdown("## Individual Model Responses")
                individual_output = gr.Markdown()

            with gr.Column():
                gr.Markdown("## Aggregated Response")
                aggregated_output = gr.Markdown()

        submit_btn.click(
            fn=get_answer,
            inputs=[api_key_input, user_prompt_input],
            outputs=[individual_output, aggregated_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
