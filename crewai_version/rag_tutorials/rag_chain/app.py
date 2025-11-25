import os
import gradio as gr
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters.sentence_transformers import SentenceTransformersTokenTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Initialize embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Initialize pharma database
db = Chroma(
    collection_name="pharma_database",
    embedding_function=embedding_model,
    persist_directory='./pharma_db'
)

def format_docs(docs):
    """Formats a list of document objects into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)

def add_to_db(uploaded_files, gemini_api_key):
    """Processes and adds uploaded PDF files to the database."""
    if not uploaded_files:
        return "No files uploaded!"

    results = []
    for uploaded_file in uploaded_files:
        # Save the uploaded file to a temporary path
        temp_file_path = os.path.join("./temp", uploaded_file.name)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(uploaded_file.read())

        # Load the file using PyPDFLoader
        loader = PyPDFLoader(temp_file_path)
        data = loader.load()

        # Store metadata and content
        doc_metadata = [data[i].metadata for i in range(len(data))]
        doc_content = [data[i].page_content for i in range(len(data))]

        # Split documents into smaller chunks
        st_text_splitter = SentenceTransformersTokenTextSplitter(
            model_name="sentence-transformers/all-mpnet-base-v2",
            chunk_size=100,
            chunk_overlap=50
        )
        st_chunks = st_text_splitter.create_documents(doc_content, doc_metadata)

        # Add chunks to database
        db.add_documents(st_chunks)

        # Remove the temporary file after processing
        os.remove(temp_file_path)
        results.append(f"Processed {uploaded_file.name}")

    return "\n".join(results)

def run_rag_chain(query, gemini_api_key):
    """Processes a query using a Retrieval-Augmented Generation (RAG) chain."""
    if not gemini_api_key:
        return "Please enter your Gemini API key first"

    # Create a Retriever Object and apply Similarity Search
    retriever = db.as_retriever(search_type="similarity", search_kwargs={'k': 5})

    # Initialize a Chat Prompt Template
    PROMPT_TEMPLATE = """
    You are a highly knowledgeable assistant specializing in pharmaceutical sciences.
    Answer the question based only on the following context:
    {context}

    Answer the question based on the above context:
    {question}

    Use the provided context to answer the user's question accurately and concisely.
    Don't justify your answers.
    Don't give information not mentioned in the CONTEXT INFORMATION.
    Do not say "according to the context" or "mentioned in the context" or similar.
    """

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    # Initialize a Generator (i.e. Chat Model)
    chat_model = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        api_key=gemini_api_key,
        temperature=1
    )

    # Initialize a Output Parser
    output_parser = StrOutputParser()

    # RAG Chain
    rag_chain = {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    } | prompt_template | chat_model | output_parser

    # Invoke the Chain
    response = rag_chain.invoke(query)

    return response

# Gradio Interface
with gr.Blocks(title="PharmaQuery") as demo:
    gr.Markdown("# Pharmaceutical Insight Retrieval System")

    with gr.Tab("Ask Question"):
        with gr.Row():
            with gr.Column():
                gemini_key = gr.Textbox(
                    label="Gemini API Key",
                    type="password",
                    placeholder="Enter your Gemini API key"
                )
                query_input = gr.Textbox(
                    label="Enter your query about the Pharmaceutical Industry",
                    placeholder="e.g., What are the AI applications in drug discovery?",
                    lines=3
                )
                submit_btn = gr.Button("Submit", variant="primary")

            with gr.Column():
                result_output = gr.Textbox(
                    label="Answer",
                    lines=10
                )

        submit_btn.click(
            fn=run_rag_chain,
            inputs=[query_input, gemini_key],
            outputs=[result_output]
        )

    with gr.Tab("Upload Documents"):
        gr.Markdown("Upload your research documents related to Pharmaceutical Sciences (Optional)")

        file_uploader = gr.File(
            label="Upload PDF files",
            file_count="multiple",
            file_types=[".pdf"]
        )
        upload_key = gr.Textbox(
            label="Gemini API Key",
            type="password",
            placeholder="Enter your Gemini API key"
        )
        upload_btn = gr.Button("Submit & Process", variant="primary")
        upload_output = gr.Textbox(label="Upload Status")

        upload_btn.click(
            fn=add_to_db,
            inputs=[file_uploader, upload_key],
            outputs=[upload_output]
        )

    gr.Markdown("Built with LangChain & Gradio by [Charan](https://www.linkedin.com/in/codewithcharan/)")

if __name__ == "__main__":
    demo.launch()
