from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
import gradio as gr
from langchain_community.llms import Ollama
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

def generate_itinerary(serper_key, destination, num_days):
    if not all([serper_key, destination]):
        return "Please provide all required inputs", None

    try:
        llm = Ollama(model="llama3.2")
        search_tool = SerperDevTool(api_key=serper_key)

        planner = Agent(
            role="Travel Planner",
            goal="Generate travel itinerary using local Llama model",
            backstory="""You are a travel planner who creates detailed itineraries.""",
            llm=llm,
            tools=[search_tool],
            verbose=True
        )

        task = Task(
            description=f"Create a {num_days} day itinerary for {destination}",
            agent=planner,
            expected_output="Detailed day-by-day itinerary"
        )

        crew = Crew(agents=[planner], tasks=[task], verbose=True)
        result = crew.kickoff()

        itinerary = result.raw if hasattr(result, 'raw') else str(result)

        ics_content = generate_ics_content(itinerary)
        ics_path = "/tmp/travel_itinerary.ics"
        with open(ics_path, "wb") as f:
            f.write(ics_content)

        return itinerary, ics_path

    except Exception as e:
        return f"Error: {str(e)}", None

def create_app():
    with gr.Blocks(title="AI Travel Planner - Local Llama") as app:
        gr.Markdown("# AI Travel Planner using Llama-3.2")
        gr.Markdown("Plan with local Llama model. Make sure Ollama is running!")

        with gr.Row():
            with gr.Column():
                serper_key = gr.Textbox(
                    label="Serper API Key",
                    type="password",
                    placeholder="Enter Serper API Key"
                )
                destination = gr.Textbox(label="Destination")
                num_days = gr.Slider(1, 30, 7, step=1, label="Days")
                generate_btn = gr.Button("Generate", variant="primary")

        with gr.Row():
            itinerary_output = gr.Textbox(label="Itinerary", lines=20)
            download_btn = gr.File(label="Download Calendar")

        generate_btn.click(
            fn=generate_itinerary,
            inputs=[serper_key, destination, num_days],
            outputs=[itinerary_output, download_btn]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()
