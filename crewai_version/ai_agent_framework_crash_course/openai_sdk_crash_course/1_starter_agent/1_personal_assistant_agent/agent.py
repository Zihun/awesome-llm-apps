from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import asyncio

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create an agent for demonstrating different execution methods
personal_assistant = Agent(
    role="Personal Assistant",
    goal="Help users with their questions and provide helpful information",
    backstory="""
    You are a helpful personal assistant.

    Your role is to:
    1. Answer questions clearly and concisely
    2. Provide helpful information and advice
    3. Be friendly and professional
    4. Offer practical solutions to problems

    When users ask questions:
    - Give accurate and helpful responses
    - Explain complex topics in simple terms
    - Offer follow-up suggestions when appropriate
    - Maintain a positive and supportive tone

    Keep responses concise but informative.
    """,
    llm=llm,
    verbose=True
)

# Example usage patterns
def sync_example():
    """Synchronous execution example"""
    task = Task(
        description="Hello, how does sync execution work?",
        expected_output="A clear explanation of synchronous execution",
        agent=personal_assistant
    )
    crew = Crew(agents=[personal_assistant], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result

async def async_example():
    """Asynchronous execution example"""
    task = Task(
        description="Hello, how does async execution work?",
        expected_output="A clear explanation of asynchronous execution",
        agent=personal_assistant
    )
    crew = Crew(agents=[personal_assistant], tasks=[task], verbose=True)
    # Note: CrewAI doesn't have native async support, so we run in thread pool
    result = await asyncio.to_thread(crew.kickoff)
    return result

def streaming_example():
    """Streaming execution example - CrewAI doesn't support streaming in the same way"""
    task = Task(
        description="Tell me about streaming execution",
        expected_output="A detailed explanation of streaming execution",
        agent=personal_assistant
    )
    crew = Crew(agents=[personal_assistant], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result
