from __future__ import annotations

import asyncio
from collections.abc import Sequence
from crewai import Crew, Task
from langchain_openai import ChatOpenAI

from agent import (
    History, historical_agent,
    Culinary, culinary_agent,
    Culture, culture_agent,
    Architecture, architecture_agent,
    Planner, planner_agent,
    FinalTour, orchestrator_agent,
    create_historical_agent,
    create_culinary_agent,
    create_culture_agent,
    create_architecture_agent,
    create_planner_agent,
    create_orchestrator_agent
)

class TourManager:
    """
    Orchestrates the full flow using CrewAI
    """

    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini") -> None:
        self.llm = ChatOpenAI(model=model, api_key=openai_api_key)

    async def run(self, query: str, interests: list, duration: str) -> str:
        print("Starting tour research...")

        # Get plan based on selected interests
        planner_data = await self._get_plan(query, interests, duration)

        # Initialize research results
        research_results = {}

        # Calculate word limits based on duration
        words_per_minute = 150
        total_words = int(duration) * words_per_minute
        words_per_section = total_words // len(interests)

        # Only research selected interests
        if "Architecture" in interests:
            research_results["architecture"] = await self._get_architecture(query, interests, words_per_section)

        if "History" in interests:
            research_results["history"] = await self._get_history(query, interests, words_per_section)

        if "Culinary" in interests:
            research_results["culinary"] = await self._get_culinary(query, interests, words_per_section)

        if "Culture" in interests:
            research_results["culture"] = await self._get_culture(query, interests, words_per_section)

        # Get final tour with only selected interests
        final_tour = await self._get_final_tour(
            query,
            interests,
            duration,
            research_results
        )

        print("Final tour created!")

        # Build final tour content based on selected interests
        sections = []

        # Add selected interest sections without headers
        if "Architecture" in interests:
            sections.append(final_tour.get('architecture', ''))
        if "History" in interests:
            sections.append(final_tour.get('history', ''))
        if "Culture" in interests:
            sections.append(final_tour.get('culture', ''))
        if "Culinary" in interests:
            sections.append(final_tour.get('culinary', ''))

        # Format final tour with natural transitions
        final = ""
        for i, content in enumerate(sections):
            if i > 0:
                final += "\n\n"
            final += content

        return final

    async def _get_plan(self, query: str, interests: list, duration: str) -> dict:
        print("Planning your personalized tour...")

        planner_agent = create_planner_agent(self.llm)

        task = Task(
            description=f"Query: {query} Interests: {', '.join(interests)} Duration: {duration}",
            expected_output="A time allocation plan in JSON format",
            agent=planner_agent
        )

        crew = Crew(
            agents=[planner_agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        print("Completed planning")
        return result

    async def _get_history(self, query: str, interests: list, word_limit: int) -> str:
        print("Researching historical highlights...")

        historical_agent_obj = create_historical_agent(self.llm)

        task = Task(
            description=f"Query: {query} Interests: {', '.join(interests)} Word Limit: {word_limit} - {word_limit + 20}\n\nInstructions: Create engaging historical content for an audio tour. Focus on interesting stories and personal connections. Make it conversational and include specific details that would be interesting to hear while walking. Include specific locations and landmarks where possible. The content should be approximately {word_limit} words when spoken at a natural pace.",
            expected_output="Historical content for the audio tour",
            agent=historical_agent_obj
        )

        crew = Crew(
            agents=[historical_agent_obj],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        print("Completed history research")
        return result

    async def _get_architecture(self, query: str, interests: list, word_limit: int) -> str:
        print("Exploring architectural wonders...")

        architecture_agent_obj = create_architecture_agent(self.llm)

        task = Task(
            description=f"Query: {query} Interests: {', '.join(interests)} Word Limit: {word_limit} - {word_limit + 20}\n\nInstructions: Create engaging architectural content for an audio tour. Focus on visual descriptions and interesting design details. Make it conversational and include specific buildings and their unique features. Describe what visitors should look for and why it matters. The content should be approximately {word_limit} words when spoken at a natural pace.",
            expected_output="Architectural content for the audio tour",
            agent=architecture_agent_obj
        )

        crew = Crew(
            agents=[architecture_agent_obj],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        print("Completed architecture research")
        return result

    async def _get_culinary(self, query: str, interests: list, word_limit: int) -> str:
        print("Discovering local flavors...")

        culinary_agent_obj = create_culinary_agent(self.llm)

        task = Task(
            description=f"Query: {query} Interests: {', '.join(interests)} Word Limit: {word_limit} - {word_limit + 20}\n\nInstructions: Create engaging culinary content for an audio tour. Focus on local specialties, food history, and interesting stories about restaurants and dishes. Make it conversational and include specific recommendations. Describe the flavors and cultural significance of the food. The content should be approximately {word_limit} words when spoken at a natural pace.",
            expected_output="Culinary content for the audio tour",
            agent=culinary_agent_obj
        )

        crew = Crew(
            agents=[culinary_agent_obj],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        print("Completed culinary research")
        return result

    async def _get_culture(self, query: str, interests: list, word_limit: int) -> str:
        print("Exploring cultural highlights...")

        culture_agent_obj = create_culture_agent(self.llm)

        task = Task(
            description=f"Query: {query} Interests: {', '.join(interests)} Word Limit: {word_limit} - {word_limit + 20}\n\nInstructions: Create engaging cultural content for an audio tour. Focus on local traditions, arts, and community life. Make it conversational and include specific cultural venues and events. Describe the atmosphere and significance of cultural landmarks. The content should be approximately {word_limit} words when spoken at a natural pace.",
            expected_output="Cultural content for the audio tour",
            agent=culture_agent_obj
        )

        crew = Crew(
            agents=[culture_agent_obj],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        print("Completed culture research")
        return result

    async def _get_final_tour(self, query: str, interests: list, duration: float, research_results: dict) -> dict:
        print("Creating your personalized tour...")

        orchestrator_agent_obj = create_orchestrator_agent(self.llm)

        # Build content sections based on selected interests
        content_sections = []
        for interest in interests:
            if interest.lower() in research_results:
                content_sections.append(research_results[interest.lower()])

        # Calculate total words based on duration
        words_per_minute = 150
        total_words = int(duration) * words_per_minute

        # Create the prompt
        prompt = (
            f"Query: {query}\n"
            f"Selected Interests: {', '.join(interests)}\n"
            f"Total Tour Duration (in minutes): {duration}\n"
            f"Target Word Count: {total_words}\n\n"
            f"Content Sections:\n{chr(10).join(content_sections)}\n\n"
            f"Instructions: Create a natural, conversational audio tour that focuses only on the selected interests. "
            f"Make it feel like a friendly guide walking alongside the visitor, sharing interesting stories and insights. "
            f"Use natural transitions between topics and maintain an engaging but relaxed pace. "
            f"Include specific locations and landmarks where possible. "
            f"Add natural pauses and transitions as if walking between locations. "
            f"Use phrases like 'as we walk', 'look to your left', 'notice how', etc. "
            f"Make it interactive and engaging, as if the guide is actually there with the visitor. "
            f"Start with a warm welcome and end with a natural closing thought. "
            f"The total content should be approximately {total_words} words when spoken at a natural pace of 150 words per minute. "
            f"This will ensure the tour lasts approximately {duration} minutes."
        )

        task = Task(
            description=prompt,
            expected_output="A complete final tour with introduction, content sections, and conclusion",
            agent=orchestrator_agent_obj
        )

        crew = Crew(
            agents=[orchestrator_agent_obj],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        print("Completed Final Tour Guide Creation")

        # Parse result into dictionary format
        final_tour_dict = {
            'introduction': '',
            'architecture': research_results.get('architecture', ''),
            'history': research_results.get('history', ''),
            'culture': research_results.get('culture', ''),
            'culinary': research_results.get('culinary', ''),
            'conclusion': ''
        }

        return final_tour_dict
