from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
import gradio as gr
from langchain_openai import ChatOpenAI
import re
from icalendar import Calendar, Event
from datetime import datetime, timedelta

def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """Generate an ICS calendar file from a travel itinerary text."""
    cal = Calendar()
    cal.add('prodid', '-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # Split the plan into days
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days:
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)
    else:
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)

            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()

def generate_itinerary(openai_key, serper_key, destination, num_days):
    if not all([openai_key, serper_key, destination]):
        return "Please provide all required inputs", None

    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key)
        search_tool = SerperDevTool(api_key=serper_key)

        # Research agent
        researcher = Agent(
            role="Travel Researcher",
            goal="Search for travel destinations, activities, and accommodations based on user preferences",
            backstory="""You are a world-class travel researcher. Given a travel destination
            and the number of days, you generate search queries and find the 10 most
            relevant travel activities and accommodations.""",
            llm=llm,
            tools=[search_tool],
            verbose=True
        )

        # Planner agent
        planner = Agent(
            role="Travel Planner",
            goal="Generate a draft itinerary based on user preferences and research results",
            backstory="""You are a senior travel planner who creates well-structured,
            informative, and engaging itineraries with suggested activities and accommodations.""",
            llm=llm,
            verbose=True
        )

        # Research task
        research_task = Task(
            description=f"Research {destination} for a {num_days} day trip. Find the best activities, accommodations, and attractions.",
            agent=researcher,
            expected_output="List of 10 most relevant travel activities and accommodations"
        )

        # Planning task
        planning_task = Task(
            description=f"""Create a detailed {num_days}-day itinerary for {destination}.
            Use the research results to create a day-by-day plan.
            Format each day as 'Day X: ' followed by activities.
            Include accommodations, activities, and dining suggestions.""",
            agent=planner,
            expected_output="Detailed day-by-day travel itinerary",
            context=[research_task]
        )

        # Create crew and execute
        crew = Crew(
            agents=[researcher, planner],
            tasks=[research_task, planning_task],
            verbose=True
        )

        result = crew.kickoff()
        itinerary = result.raw if hasattr(result, 'raw') else str(result)

        # Generate ICS file
        ics_content = generate_ics_content(itinerary)
        ics_path = "/tmp/travel_itinerary.ics"
        with open(ics_path, "wb") as f:
            f.write(ics_content)

        return itinerary, ics_path

    except Exception as e:
        return f"Error: {str(e)}", None

def create_app():
    with gr.Blocks(title="AI Travel Planner") as app:
        gr.Markdown("# AI Travel Planner")
        gr.Markdown("Plan your next adventure with AI Travel Planner by researching and planning a personalized itinerary on autopilot using GPT-4o")

        with gr.Row():
            with gr.Column():
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API Key"
                )
                serper_key = gr.Textbox(
                    label="Serper API Key",
                    type="password",
                    placeholder="Enter your Serper API Key for search"
                )
                destination = gr.Textbox(
                    label="Where do you want to go?",
                    placeholder="e.g., Paris, France"
                )
                num_days = gr.Slider(
                    minimum=1,
                    maximum=30,
                    value=7,
                    step=1,
                    label="How many days?"
                )
                generate_btn = gr.Button("Generate Itinerary", variant="primary")

        with gr.Row():
            with gr.Column():
                itinerary_output = gr.Textbox(label="Your Itinerary", lines=20)
                download_btn = gr.File(label="Download Calendar (.ics)")

        generate_btn.click(
            fn=generate_itinerary,
            inputs=[openai_key, serper_key, destination, num_days],
            outputs=[itinerary_output, download_btn]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
