from crewai import Agent
from langchain_openai import ChatOpenAI
from .tools import add_numbers, multiply_numbers, get_weather, convert_temperature

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create an agent with custom function tools
function_tools_agent = Agent(
    role="Function Tools Agent",
    goal="Help users with calculations and information using available tools",
    backstory="""
    You are a helpful assistant with access to various tools.

    Available tools:
    - add_numbers: Add two numbers together
    - multiply_numbers: Multiply two numbers together
    - get_weather: Get weather information for a city
    - convert_temperature: Convert between Celsius and Fahrenheit

    When users ask for calculations or information:
    1. Use the appropriate tool for the task
    2. Explain what you're doing
    3. Show the result clearly

    Always use the provided tools rather than doing calculations yourself.
    """,
    tools=[add_numbers, multiply_numbers, get_weather, convert_temperature],
    llm=llm,
    verbose=True
)

root_agent = function_tools_agent
