import gradio as gr
import requests
import fitz  # PyMuPDF for PDF parsing

# Helper: Extract text from PDF
def extract_pdf_text(file):
    """Extract text from PDF file"""
    text = ""
    with fitz.open(stream=file, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def match_resume_with_job(resume_file, job_file):
    """Match resume with job description using local Ollama"""
    if not resume_file or not job_file:
        return "Please upload both Resume and Job Description."

    try:
        # Extract Resume text
        if resume_file.name.endswith('.pdf'):
            resume_text = extract_pdf_text(resume_file)
        else:
            resume_text = resume_file.read().decode("utf-8")

        # Extract Job text
        if job_file.name.endswith('.pdf'):
            job_text = extract_pdf_text(job_file)
        else:
            job_text = job_file.read().decode("utf-8")

        # Prompt
        prompt = f"""
        You are an AI career assistant.

        Resume:
        {resume_text}

        Job Description:
        {job_text}

        Please analyze and return:
        1. A **Fit Score** (0-100%) of how well this resume matches the job.
        2. Key strengths (resume areas that align well).
        3. Specific recommendations to improve the resume to better fit the job.
        Format neatly in Markdown.
        """

        # Call local Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
        )
        data = response.json()
        output = data.get("response", "No response from model.")

        return output
    except Exception as e:
        return f"An error occurred: {str(e)}"

def download_report(report_text):
    """Return report text for download"""
    return report_text

# Create Gradio interface
with gr.Blocks(title="Resume & Job Matcher", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Resume & Job Matcher")
    gr.Markdown("Match your resume with job descriptions using local LLM via Ollama")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
            ### Instructions
            This app uses a local LLM via **Ollama**.

            **Setup:**
            1. Install Ollama: https://ollama.ai
            2. Run a model (e.g., `ollama run llama3`)
            3. Upload Resume + Job Description
            4. Get fit score and suggestions

            The analysis runs locally on your machine.
            """)

            resume_file = gr.File(
                label="Upload Resume (PDF/TXT)",
                file_types=[".pdf", ".txt"]
            )

            job_file = gr.File(
                label="Upload Job Description (PDF/TXT)",
                file_types=[".pdf", ".txt"]
            )

            match_btn = gr.Button("Match Resume with Job Description", variant="primary", size="lg")

        with gr.Column(scale=2):
            analysis_output = gr.Markdown(
                label="Match Analysis",
                value="Your analysis will appear here..."
            )

            download_btn = gr.Button("Download Match Report")
            download_file = gr.File(label="Download")

    # Event handlers
    match_btn.click(
        fn=match_resume_with_job,
        inputs=[resume_file, job_file],
        outputs=[analysis_output]
    )

    download_btn.click(
        fn=lambda x: gr.File(value=x, label="resume_match_report.md") if x else None,
        inputs=[analysis_output],
        outputs=[download_file]
    )

if __name__ == "__main__":
    demo.launch()
