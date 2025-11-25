from crewai_tools import tool

@tool("Add two numbers")
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b

@tool("Multiply two numbers")
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together"""
    return a * b

@tool("Get weather information")
def get_weather(city: str) -> str:
    """Get weather information for a city (mock implementation)"""
    return f"The weather in {city} is sunny with 72°F"

@tool("Convert temperature")
def convert_temperature(temperature: float, from_unit: str, to_unit: str) -> str:
    """Convert temperature between Celsius and Fahrenheit"""
    if from_unit.lower() == "celsius" and to_unit.lower() == "fahrenheit":
        result = (temperature * 9/5) + 32
        return f"{temperature}°C = {result:.1f}°F"
    elif from_unit.lower() == "fahrenheit" and to_unit.lower() == "celsius":
        result = (temperature - 32) * 5/9
        return f"{temperature}°F = {result:.1f}°C"
    else:
        return "Unsupported temperature conversion"
