import re
import asyncio
from textwrap import dedent
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
from crewai_tools import SerperDevTool
from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
import gradio as gr
import os

def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """
    Generate an ICS calendar file from a travel itinerary text.

    Args:
        plan_text: The travel itinerary text
        start_date: Optional start date for the itinerary (defaults to today)

    Returns:
        bytes: The ICS file content as bytes
    """
    cal = Calendar()
    cal.add('prodid','-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # Split the plan into days
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days:  # If no day pattern found, create a single all-day event with the entire content
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)
    else:
        # Process each day
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)

            # Create a single event for the entire day
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())

            # Make it an all-day event
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()

async def run_crewai_travel_planner(destination: str, num_days: int, preferences: str, budget: int, openai_key: str):
    """Run the CrewAI-based travel planner agent"""

    try:
        # Set up the LLM
        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)

        # Initialize search tool
        search_tool = SerperDevTool()

        # Create travel planner agent
        travel_planner = Agent(
            role="Travel Planner",
            goal="Create highly detailed travel itineraries using web search for current information",
            backstory=dedent(
                """\
                You are a professional travel consultant AI that creates highly detailed travel itineraries directly without asking questions.

                You have access to:
                🔍 Web search capabilities for current information, reviews, and travel updates

                ALWAYS create a complete, detailed itinerary immediately without asking for clarification or additional information.
                If information is missing, use your best judgment and available tools to fill in the gaps.
                """
            ),
            llm=llm,
            tools=[search_tool],
            verbose=True,
            allow_delegation=False
        )

        # Create the planning prompt
        prompt = f"""
        IMMEDIATELY create an extremely detailed and comprehensive travel itinerary for:

        **Destination:** {destination}
        **Duration:** {num_days} days
        **Budget:** ${budget} USD total
        **Preferences:** {preferences}

        DO NOT ask any questions. Generate a complete, highly detailed itinerary now using all available tools.

        **CRITICAL REQUIREMENTS:**
        - Include specific addresses for every location, restaurant, and attraction
        - Provide detailed timing for each activity with buffer time between locations
        - Calculate precise costs for transportation between each location
        - Include opening hours, ticket prices, and best visiting times for all attractions
        - Provide detailed weather information and specific packing recommendations

        **REQUIRED OUTPUT FORMAT:**
        1. **Trip Overview** - Summary, total estimated cost breakdown, detailed weather forecast
        2. **Accommodation** - 3 specific hotel/Airbnb options with prices, addresses, amenities
        3. **Transportation Overview** - Detailed transportation options, costs, and recommendations
        4. **Day-by-Day Itinerary** - Extremely detailed schedule with:
           - Specific start/end times for each activity
           - Exact distances and travel times between locations
           - Detailed descriptions of each location with addresses
           - Opening hours, ticket prices, and best visiting times
           - Estimated costs for each activity and transportation
           - Buffer time between activities for unexpected delays
        5. **Dining Plan** - Specific restaurants with addresses, price ranges, cuisine types
        6. **Detailed Practical Information**:
           - Weather forecast with clothing recommendations
           - Currency exchange rates and costs
           - Local transportation options and costs
           - Safety information and emergency contacts
           - Cultural norms and etiquette tips
           - Communication options (SIM cards, WiFi, etc.)
           - Health and medical considerations
           - Shopping and souvenir recommendations

        Use web search for current information and make reasonable assumptions.
        Generate the complete, highly detailed itinerary in one response without asking for clarification.
        """

        # Create task
        planning_task = Task(
            description=prompt,
            expected_output="A complete and detailed travel itinerary",
            agent=travel_planner
        )

        # Create and run crew
        crew = Crew(
            agents=[travel_planner],
            tasks=[planning_task],
            verbose=True
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"

def run_travel_planner(destination: str, num_days: int, preferences: str, budget: int, openai_key: str):
    """Synchronous wrapper for the async CrewAI travel planner"""
    return asyncio.run(run_crewai_travel_planner(destination, num_days, preferences, budget, openai_key))

def generate_itinerary(destination, num_days, budget, start_date_input, preferences_input, quick_prefs, openai_api_key, progress=gr.Progress()):
    """Generate travel itinerary"""
    if not openai_api_key:
        return "Error: Please enter your OpenAI API key.", None

    if not destination:
        return "Error: Please enter a destination.", None

    # Combine preferences
    all_preferences = []
    if preferences_input:
        all_preferences.append(preferences_input)
    if quick_prefs:
        all_preferences.extend(quick_prefs)

    preferences = ", ".join(all_preferences) if all_preferences else "General sightseeing"

    progress(0.3, desc="Creating itinerary...")

    try:
        response = run_travel_planner(
            destination=destination,
            num_days=num_days,
            preferences=preferences,
            budget=budget,
            openai_key=openai_api_key
        )

        progress(0.8, desc="Generating calendar...")

        # Generate ICS file
        ics_content = generate_ics_content(response, datetime.combine(start_date_input, datetime.min.time()))

        progress(1.0, desc="Complete!")

        return response, ics_content

    except Exception as e:
        return f"Error: {str(e)}", None

# Create Gradio interface
with gr.Blocks(title="CrewAI Travel Planner", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ✈️ CrewAI Travel Planner")
    gr.Markdown("Plan your next adventure with AI Travel Planner using CrewAI for intelligent planning")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔑 API Configuration")
            openai_api_key = gr.Textbox(label="OpenAI API Key", type="password", placeholder="Enter your OpenAI API key")

    gr.Markdown("### 🌍 Trip Details")

    with gr.Row():
        with gr.Column():
            destination = gr.Textbox(label="Destination", placeholder="e.g., Paris, Tokyo, New York")
            num_days = gr.Number(label="Number of Days", value=7, minimum=1, maximum=30, precision=0)

        with gr.Column():
            budget = gr.Number(label="Budget (USD)", value=2000, minimum=100, maximum=10000, step=100, precision=0)
            start_date = gr.Date(label="Start Date", value=date.today())

    gr.Markdown("### 🎯 Travel Preferences")
    preferences_input = gr.Textbox(
        label="Describe your travel preferences",
        placeholder="e.g., adventure activities, cultural sites, food, relaxation, nightlife...",
        lines=3
    )

    quick_prefs = gr.CheckboxGroup(
        label="Quick Preferences (optional)",
        choices=["Adventure", "Relaxation", "Sightseeing", "Cultural Experiences",
                 "Beach", "Mountain", "Luxury", "Budget-Friendly", "Food & Dining",
                 "Shopping", "Nightlife", "Family-Friendly"]
    )

    generate_btn = gr.Button("🎯 Generate Itinerary", variant="primary", size="lg")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📋 Your Travel Itinerary")
            itinerary_output = gr.Textbox(label="Itinerary", lines=20, max_lines=30)

            calendar_download = gr.File(label="📅 Download as Calendar")

    generate_btn.click(
        fn=generate_itinerary,
        inputs=[destination, num_days, budget, start_date, preferences_input, quick_prefs, openai_api_key],
        outputs=[itinerary_output, calendar_download]
    )

if __name__ == "__main__":
    demo.launch(share=False)
