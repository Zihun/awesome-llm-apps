"""
Gradio Web Interface for Support Ticket Agent

This provides an interactive web interface to create structured support tickets
from customer complaints.
"""

import os
import json
import gradio as gr
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# Load environment variables
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please create a .env file with your OpenAI API key.")

# Define Pydantic models
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportTicket(BaseModel):
    title: str = Field(description="A concise summary of the issue")
    description: str = Field(description="Detailed description of the problem")
    priority: Priority = Field(description="The ticket priority level")
    category: str = Field(description="The department this ticket belongs to")
    steps_to_reproduce: Optional[List[str]] = Field(
        description="Steps to reproduce the issue (for technical problems)",
        default=None
    )
    estimated_resolution_time: str = Field(
        description="Estimated time to resolve this issue"
    )

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.3)

# Create agent
support_ticket_agent = Agent(
    role="Support Ticket Creator",
    goal="Convert customer complaints into well-structured support tickets",
    backstory="""
    You are a support ticket creation assistant that converts customer complaints
    into well-structured support tickets.

    Based on customer descriptions, create structured support tickets with:
    - Clear, concise titles
    - Detailed problem descriptions
    - Appropriate priority levels (low/medium/high/critical)
    - Correct categories (technical/billing/account/product/general)
    - Steps to reproduce for technical issues
    - Realistic resolution time estimates

    IMPORTANT: You must respond with valid JSON matching this schema:
    {
        "title": "string",
        "description": "string",
        "priority": "low|medium|high|critical",
        "category": "string",
        "steps_to_reproduce": ["string"] or null,
        "estimated_resolution_time": "string"
    }
    """,
    llm=llm,
    verbose=False
)

def create_ticket(complaint: str):
    """Create a support ticket from customer complaint"""
    try:
        task = Task(
            description=f"""
            Analyze this customer complaint and create a structured support ticket:

            {complaint}

            Return ONLY a valid JSON object matching the SupportTicket schema.
            """,
            expected_output="A valid JSON object representing a support ticket",
            agent=support_ticket_agent
        )

        crew = Crew(
            agents=[support_ticket_agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result)

        # Extract JSON from response
        if '{' in result_str:
            json_start = result_str.index('{')
            json_end = result_str.rindex('}') + 1
            json_str = result_str[json_start:json_end]
            ticket_data = json.loads(json_str)
            ticket = SupportTicket(**ticket_data)

            # Format output
            output = f"""
## Support Ticket Created

**Title:** {ticket.title}

**Priority:** {ticket.priority.upper()}

**Category:** {ticket.category.capitalize()}

**Description:**
{ticket.description}

**Estimated Resolution Time:** {ticket.estimated_resolution_time}
"""
            if ticket.steps_to_reproduce:
                output += "\n**Steps to Reproduce:**\n"
                for i, step in enumerate(ticket.steps_to_reproduce, 1):
                    output += f"{i}. {step}\n"

            # Return formatted output and JSON
            json_output = json.dumps(ticket_data, indent=2)
            return output, json_output

        else:
            return "Error: No JSON found in response", str(result)

    except Exception as e:
        return f"Error: {str(e)}", ""

# Create Gradio interface
with gr.Blocks(title="Support Ticket Creator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Support Ticket Creator")
    gr.Markdown("**Tutorial 2.1**: Create structured support tickets from customer complaints")

    with gr.Row():
        with gr.Column(scale=1):
            complaint_input = gr.Textbox(
                label="Customer Complaint",
                placeholder="Enter customer complaint here...",
                lines=8
            )
            create_btn = gr.Button("Create Support Ticket", variant="primary")

            gr.Markdown("### Example Complaints")
            examples = [
                "I can't log into my account. I keep getting an error message that says 'Invalid credentials' even though I know my password is correct. This is really urgent because I need to access my files for a client meeting.",
                "The mobile app crashes every time I try to upload a photo. It's been happening for 3 days now. I've tried reinstalling but it still doesn't work.",
                "I was charged twice for my subscription this month. Can someone please refund the duplicate charge?"
            ]

            for example in examples:
                gr.Button(example[:60] + "...", size="sm").click(
                    lambda e=example: e,
                    None,
                    complaint_input
                )

        with gr.Column(scale=1):
            ticket_output = gr.Markdown(label="Support Ticket")
            json_output = gr.Code(label="JSON Output", language="json")

    create_btn.click(
        create_ticket,
        inputs=[complaint_input],
        outputs=[ticket_output, json_output]
    )

    gr.Markdown("""
    ---
    ### Tutorial Information

    This demonstrates **CrewAI agents with structured output**. The agent:
    - Analyzes customer complaints
    - Extracts key information
    - Creates structured support tickets with Pydantic models
    - Returns valid JSON output

    **Conversion Notes:**
    - Original used `output_type=SupportTicket` (OpenAI SDK)
    - CrewAI requires explicit JSON formatting instructions
    - Manual JSON parsing from agent response

    **Next**: Try Tutorial 2.2: Product Review Agent
    """)

if __name__ == "__main__":
    demo.launch(share=False)
