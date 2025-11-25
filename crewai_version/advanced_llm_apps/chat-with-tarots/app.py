from langchain.prompts import PromptTemplate
import pandas as pd
from langchain_core.runnables import RunnableParallel, RunnableLambda
import random
import gradio as gr
import helpers.help_func as hf
from PIL import Image


# --- Load the dataset ---
csv_file_path = 'data/tarots.csv'
try:
    # Read CSV file
    df = pd.read_csv(csv_file_path, sep=';', encoding='latin1')
    print(f"CSV dataset loaded successfully: {csv_file_path}. Number of rows: {len(df)}")

    # Clean and normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Debug: Show column details
    print("\nDetails after cleanup:")
    for col in df.columns:
        print(f"Column: '{col}' (length: {len(col)})")

    # Define required columns (in lowercase)
    required_columns = ['card', 'upright', 'reversed', 'symbolism']

    # Verify all required columns are present
    available_columns = set(df.columns)
    missing_columns = [col for col in required_columns if col not in available_columns]

    if missing_columns:
        raise ValueError(
            f"Missing columns in CSV file: {', '.join(missing_columns)}\n"
            f"Available columns: {', '.join(available_columns)}"
        )

    # Create card meanings dictionary with cleaned data
    card_meanings = {}
    for _, row in df.iterrows():
        card_name = row['card'].strip()
        card_meanings[card_name] = {
            'upright': str(row['upright']).strip() if pd.notna(row['upright']) else '',
            'reversed': str(row['reversed']).strip() if pd.notna(row['reversed']) else '',
            'symbolism': str(row['symbolism']).strip() if pd.notna(row['symbolism']) else ''
        }

    print(f"\nKnowledge base created with {len(card_meanings)} cards, meanings and symbolisms.")

except FileNotFoundError:
    print(f"Error: CSV File not found: {csv_file_path}")
    raise
except ValueError as e:
    print(f"Validation Error: {str(e)}")
    raise
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    raise


# --- Define the Prompt Template ---
prompt_analysis = PromptTemplate.from_template("""
Analyze the following tarot cards, based on the meanings provided (also considering if they are reversed):
{card_details}
Pay attention to these aspects:
- Provide a detailed analysis of the meaning of each card (upright or reversed).
- Then offer a general interpretation of the answer based on the cards, linking it to the context: {context}.
- Be mystical and provide information on the interpretation related to the symbolism of the cards, based on the specific column: {symbolism}.
- At the end of the reading, always offer advice to improve or address the situation. Also, base it on your knowledge of psychology.
""")
print("\nPrompt Template 'prompt_analysis' defined.")

# --- Create the LangChain Chain ---
analyzer = (
    RunnableParallel(
        cards=lambda x: x['cards'],
        context=lambda x: x['context']
    )
    | (lambda x: hf.prepare_prompt_input(x, card_meanings))
    | prompt_analysis
    | hf.llm
)


# --- Gradio Interface ---
def draw_and_analyze(num_cards, context_question):
    """Main function to draw cards and analyze them"""
    if not context_question:
        return None, "For a more precise reading, please enter your context or question."

    try:
        card_names_in_dataset = df['card'].unique().tolist()
        drawn_cards_list = hf.generate_random_draw(num_cards, card_names_in_dataset)

        # Prepare card images and info
        card_info_text = "Your Cards Revealed:\n\n"
        card_images = []

        for i, card_info in enumerate(drawn_cards_list):
            image_filename = card_info['name']
            image_path = f"images/{image_filename}"
            reversed_label = "(R)" if 'is_reversed' in card_info else ""
            caption = f"{card_info['name']} {reversed_label}"

            try:
                img = Image.open(image_path)
                if card_info.get('is_reversed', False):
                    img = img.rotate(180)
                card_images.append((img, caption))
            except FileNotFoundError:
                card_info_text += f"Symbol: {card_info['name']} {reversed_label} (Image not found)\n"

        # Get analysis
        analysis_result = analyzer.invoke({"cards": drawn_cards_list, "context": context_question})
        interpretation = f"The Interpretation:\n\n{analysis_result.content}\n\n---\n\nRemember, the cards offer insights and reflections; your future is in your hands."

        return card_images, interpretation

    except Exception as e:
        return None, f"An error has occurred: {e}"


# Create Gradio interface
with gr.Blocks(title="Interactive Tarot Reading", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Interactive Tarot Reading")
    gr.Markdown("Welcome to your personalized tarot consultation!")

    with gr.Row():
        with gr.Column(scale=1):
            num_cards = gr.Dropdown(
                choices=[3, 5, 7],
                value=3,
                label="Select the number of cards",
                info="3 for a more focused answer, 7 for a more general overview"
            )

            context_question = gr.Textbox(
                label="Your Context or Question",
                placeholder="Please enter your context or question here. You can speak in natural language.",
                lines=5
            )

            analyze_btn = gr.Button("Light your path: Draw and Analyze the Cards", variant="primary")

        with gr.Column(scale=2):
            card_gallery = gr.Gallery(
                label="Your Cards",
                show_label=True,
                columns=3,
                height="auto"
            )

            interpretation_output = gr.Textbox(
                label="Interpretation",
                lines=15,
                show_copy_button=True
            )

    analyze_btn.click(
        fn=draw_and_analyze,
        inputs=[num_cards, context_question],
        outputs=[card_gallery, interpretation_output]
    )

if __name__ == "__main__":
    demo.launch()
