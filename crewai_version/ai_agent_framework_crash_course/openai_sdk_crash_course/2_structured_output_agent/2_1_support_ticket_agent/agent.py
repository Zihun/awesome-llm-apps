from typing import List, Optional
from enum import Enum
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json

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

# Create agent with structured output instructions
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
    verbose=True
)

def create_support_ticket(customer_complaint: str) -> SupportTicket:
    """Process customer complaint and return structured support ticket"""
    task = Task(
        description=f"""
        Analyze this customer complaint and create a structured support ticket:

        {customer_complaint}

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

    # Parse the JSON response into SupportTicket model
    try:
        # Extract JSON from the response
        result_str = str(result)
        # Try to find JSON in the response
        if '{' in result_str:
            json_start = result_str.index('{')
            json_end = result_str.rindex('}') + 1
            json_str = result_str[json_start:json_end]
            ticket_data = json.loads(json_str)
            return SupportTicket(**ticket_data)
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response was: {result}")
        raise

root_agent = support_ticket_agent
