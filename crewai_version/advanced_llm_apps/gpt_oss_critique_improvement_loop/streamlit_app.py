"""Gradio Critique & Improvement Loop Demo using GPT-OSS via Groq

This implements the "Automatic Critique + Improvement Loop" pattern:
1. Generate initial answer (Pro Mode style)
2. Have a critic model identify flaws/missing pieces
3. Revise the answer addressing all critiques
4. Repeat if needed
"""

import os
import time
import concurrent.futures as cf
from typing import List, Dict, Any
import gradio as gr
from groq import Groq, GroqError

MODEL = "openai/gpt-oss-120b"
MAX_COMPLETION_TOKENS = 1024  # stay within Groq limits

SAMPLE_PROMPTS = [
    "Explain how to implement a binary search tree in Python.",
    "What are the best practices for API design?",
    "How would you optimize a slow database query?",
    "Explain the concept of recursion with examples.",
]

# --- Helper functions --------------------------------------------------------

def _one_completion(client: Groq, messages: List[Dict[str, str]], temperature: float) -> str:
    """Single non-streaming completion with basic retries."""
    delay = 0.5
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                top_p=1,
                stream=False,
            )
            return resp.choices[0].message.content
        except GroqError:
            if attempt == 2:
                raise
            time.sleep(delay)
            delay *= 2


def generate_initial_answer(client: Groq, prompt: str) -> str:
    """Generate initial answer using parallel candidates + synthesis (Pro Mode)."""
    # Generate 3 candidates in parallel
    candidates = []
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        futures = [
            ex.submit(_one_completion, client,
                     [{"role": "user", "content": prompt}], 0.9)
            for _ in range(3)
        ]
        for fut in cf.as_completed(futures):
            candidates.append(fut.result())

    # Synthesize candidates
    candidate_texts = []
    for i, c in enumerate(candidates):
        candidate_texts.append(f"--- Candidate {i+1} ---\n{c}")

    synthesis_prompt = (
        f"You are given 3 candidate answers. Synthesize them into ONE best answer, "
        f"eliminating repetition and ensuring coherence:\n\n"
        f"{chr(10).join(candidate_texts)}\n\n"
        f"Return the single best final answer."
    )

    return _one_completion(client, [{"role": "user", "content": synthesis_prompt}], 0.2)


def critique_answer(client: Groq, prompt: str, answer: str) -> str:
    """Have a critic model identify flaws and missing pieces."""
    critique_prompt = (
        f"Original question: {prompt}\n\n"
        f"Answer to critique:\n{answer}\n\n"
        f"Act as a critical reviewer. List specific flaws, missing information, "
        f"unclear explanations, or areas that need improvement. Be constructive but thorough. "
        f"Format as a bulleted list starting with '•'."
    )

    return _one_completion(client, [{"role": "user", "content": critique_prompt}], 0.3)


def revise_answer(client: Groq, prompt: str, original_answer: str, critiques: str) -> str:
    """Revise the original answer addressing all critiques."""
    revision_prompt = (
        f"Original question: {prompt}\n\n"
        f"Original answer:\n{original_answer}\n\n"
        f"Critiques to address:\n{critiques}\n\n"
        f"Revise the original answer to address every critique point. "
        f"Maintain the good parts, fix the issues, and add missing information. "
        f"Return the improved answer."
    )

    return _one_completion(client, [{"role": "user", "content": revision_prompt}], 0.2)


def critique_improvement_loop(prompt: str, max_iterations: int = 2, groq_api_key: str = None) -> Dict[str, Any]:
    """Main function implementing the critique and improvement loop."""
    client = Groq(api_key=groq_api_key) if groq_api_key else Groq()

    results = {
        "iterations": [],
        "final_answer": "",
        "total_iterations": 0
    }

    # Generate initial answer
    initial_answer = generate_initial_answer(client, prompt)
    results["iterations"].append({
        "type": "initial",
        "answer": initial_answer,
        "critiques": None
    })

    current_answer = initial_answer

    # Improvement loop
    for iteration in range(max_iterations):
        critiques = critique_answer(client, prompt, current_answer)
        revised_answer = revise_answer(client, prompt, current_answer, critiques)

        results["iterations"].append({
            "type": "improvement",
            "answer": revised_answer,
            "critiques": critiques
        })

        current_answer = revised_answer

    results["final_answer"] = current_answer
    results["total_iterations"] = len(results["iterations"])

    return results


# --- Gradio UI ------------------------------------------------------------

def process_critique_loop(prompt, max_iterations, api_key):
    """Process the critique loop and return formatted results"""
    if not prompt.strip():
        return "Please enter a prompt.", "", ""

    try:
        results = critique_improvement_loop(prompt, max_iterations, groq_api_key=api_key or None)

        # Format final answer
        final_answer = f"# Final Answer\n\n{results['final_answer']}"

        # Format improvement history
        history = ""
        for i, iteration in enumerate(results["iterations"]):
            if iteration["type"] == "initial":
                history += f"## Initial Answer\n\n{iteration['answer']}\n\n---\n\n"
            else:
                history += f"## Iteration {i}\n\n"

                # Show critiques
                if iteration["critiques"]:
                    history += f"**Critiques:**\n\n{iteration['critiques']}\n\n"

                # Show improved answer
                history += f"**Improved Answer:**\n\n{iteration['answer']}\n\n---\n\n"

        # Format metrics
        metrics = f"**Total Iterations:** {results['total_iterations']}\n\n"
        metrics += f"**Improvement Rounds:** {max_iterations}\n\n"
        metrics += f"**Final Answer Length:** {len(results['final_answer'])} characters"

        return final_answer, history, metrics
    except Exception as e:
        return f"Error: {str(e)}", "", ""


def random_prompt():
    """Return a random sample prompt"""
    import random
    return random.choice(SAMPLE_PROMPTS)


# Create Gradio interface
with gr.Blocks(title="Critique & Improvement Loop", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Critique & Improvement Loop")
    gr.Markdown("Generate high-quality answers through iterative critique and improvement using GPT-OSS")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            api_key = gr.Textbox(
                label="Groq API Key",
                type="password",
                placeholder="Enter your Groq API key (or set GROQ_API_KEY env var)",
                value=os.getenv("GROQ_API_KEY", "")
            )
            max_iterations = gr.Slider(
                minimum=1,
                maximum=3,
                value=2,
                step=1,
                label="Max Improvement Iterations"
            )

            gr.Markdown("---")

            prompt = gr.Textbox(
                label="Your Prompt",
                placeholder="Ask me anything...",
                lines=5
            )

            with gr.Row():
                random_btn = gr.Button("Random Sample Prompt")
                generate_btn = gr.Button("Start Critique Loop", variant="primary")

            gr.Markdown("---")
            gr.Markdown("Each iteration adds critique + revision steps for higher quality")

        with gr.Column(scale=2):
            final_answer_output = gr.Markdown(label="Final Answer")

            with gr.Accordion("Show Improvement History", open=False):
                history_output = gr.Markdown()

            with gr.Accordion("Show Metrics", open=False):
                metrics_output = gr.Markdown()

    # Event handlers
    random_btn.click(fn=random_prompt, outputs=[prompt])
    generate_btn.click(
        fn=process_critique_loop,
        inputs=[prompt, max_iterations, api_key],
        outputs=[final_answer_output, history_output, metrics_output]
    )

if __name__ == "__main__":
    demo.launch()
