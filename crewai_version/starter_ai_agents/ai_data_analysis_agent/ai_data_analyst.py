from crewai import Agent, Task, Crew
import gradio as gr
from langchain_openai import ChatOpenAI
import pandas as pd
import duckdb
import tempfile
import csv

def preprocess_and_save(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file.name, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file.name, na_values=['NA', 'N/A', 'missing'])
        else:
            return None, None, "Unsupported file format"

        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)

        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w') as temp_file:
            temp_path = temp_file.name
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)

        return temp_path, df.head().to_html(), None

    except Exception as e:
        return None, None, f"Error processing file: {e}"

def analyze_data(openai_key, file, query):
    if not openai_key or file is None or not query:
        return "Please provide API key, data file, and query"

    try:
        # Preprocess file
        temp_path, preview, error = preprocess_and_save(file)
        if error:
            return error

        # Load into DuckDB
        conn = duckdb.connect(':memory:')
        conn.execute(f"CREATE TABLE uploaded_data AS SELECT * FROM read_csv_auto('{temp_path}')")

        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)

        # Get schema
        schema = conn.execute("DESCRIBE uploaded_data").fetchdf()
        schema_str = schema.to_string()

        analyst_agent = Agent(
            role="Expert Data Analyst",
            goal="Analyze data using SQL and provide clear insights",
            backstory=f"""You are an expert data analyst. You have access to a table
            called 'uploaded_data' with this schema:
            {schema_str}

            You write SQL queries to answer questions about the data.""",
            llm=llm,
            verbose=True
        )

        task = Task(
            description=f"""Answer this query about the data: {query}

            Write a DuckDB SQL query to answer the question, then explain the results clearly.
            Return both the SQL query and the interpretation of results.""",
            agent=analyst_agent,
            expected_output="SQL query and data analysis results"
        )

        crew = Crew(agents=[analyst_agent], tasks=[task], verbose=True)
        result = crew.kickoff()

        response = result.raw if hasattr(result, 'raw') else str(result)

        # Try to extract and execute SQL from response
        import re
        sql_match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1)
            try:
                query_result = conn.execute(sql_query).fetchdf()
                response += f"\n\n### Query Results:\n{query_result.to_markdown()}"
            except Exception as e:
                response += f"\n\n(Note: Could not execute SQL: {e})"

        conn.close()
        return response

    except Exception as e:
        return f"Error: {str(e)}"

def create_app():
    with gr.Blocks(title="Data Analyst Agent") as app:
        gr.Markdown("# Data Analyst Agent")
        gr.Markdown("Upload CSV/Excel data and ask questions using AI-powered analysis")

        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )

                file_input = gr.File(
                    label="Upload CSV or Excel file",
                    file_types=[".csv", ".xlsx"]
                )

                query_input = gr.Textbox(
                    label="Ask a query about the data",
                    placeholder="e.g., What is the average sales by region?",
                    lines=3
                )

                submit_btn = gr.Button("Submit Query", variant="primary")

        with gr.Row():
            output = gr.Markdown(label="Analysis Result")

        submit_btn.click(
            fn=analyze_data,
            inputs=[api_key, file_input, query_input],
            outputs=output
        )

        gr.Markdown("Check the console for detailed agent output")

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
