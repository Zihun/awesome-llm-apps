import asyncio
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create specialized translation agents
spanish_translator = Agent(
    role="Spanish Translator",
    goal="Translate messages to Spanish with natural, fluent translations",
    backstory="You are an expert Spanish translator who provides natural and fluent translations.",
    llm=llm,
    verbose=True
)

translation_quality_picker = Agent(
    role="Translation Quality Picker",
    goal="Select the best Spanish translation from multiple options",
    backstory="""
    You are an expert in Spanish translations.
    Given multiple Spanish translation options, pick the most natural, accurate, and fluent one.
    Explain briefly why you chose that translation.
    """,
    llm=llm,
    verbose=True
)

# Example 1: Parallel translation with quality selection
async def parallel_translation_example():
    """Demonstrates running multiple translations in parallel for quality"""

    print("=== Parallel Translation with Quality Selection ===")

    msg = "Hello, how are you today? I hope you're having a wonderful time!"
    print(f"Original message: {msg}")

    print("Running 3 parallel translation attempts...")

    # Create three translation tasks
    task1 = Task(
        description=f"Translate this to Spanish: {msg}",
        expected_output="A natural Spanish translation",
        agent=spanish_translator
    )

    task2 = Task(
        description=f"Translate this to Spanish: {msg}",
        expected_output="A natural Spanish translation",
        agent=spanish_translator
    )

    task3 = Task(
        description=f"Translate this to Spanish: {msg}",
        expected_output="A natural Spanish translation",
        agent=spanish_translator
    )

    # Run translations in parallel using asyncio
    async def run_crew(task):
        crew = Crew(agents=[spanish_translator], tasks=[task], verbose=False)
        return await asyncio.to_thread(crew.kickoff)

    results = await asyncio.gather(
        run_crew(task1),
        run_crew(task2),
        run_crew(task3)
    )

    # Combine all translations
    translations = "\n\n".join([f"Translation {i+1}: {result}" for i, result in enumerate(results)])
    print(f"\nAll translations:\n{translations}")

    # Use picker agent to select best translation
    picker_task = Task(
        description=f"Original English: {msg}\n\nTranslations to choose from:\n{translations}",
        expected_output="The best translation with explanation",
        agent=translation_quality_picker
    )

    picker_crew = Crew(
        agents=[translation_quality_picker],
        tasks=[picker_task],
        verbose=False
    )

    best_translation = picker_crew.kickoff()
    print(f"\nBest translation selected: {best_translation}")

    return best_translation

# Example 2: Parallel execution with different specialized agents
async def parallel_specialized_agents():
    """Shows parallel execution with different agents for diverse perspectives"""

    print("\n=== Parallel Execution with Specialized Agents ===")

    # Create different specialized agents
    formal_translator = Agent(
        role="Formal Spanish Translator",
        goal="Translate to formal, polite Spanish using 'usted' forms",
        backstory="You specialize in formal Spanish translations with respectful language.",
        llm=llm,
        verbose=True
    )

    casual_translator = Agent(
        role="Casual Spanish Translator",
        goal="Translate to casual, friendly Spanish using 'tú' forms",
        backstory="You specialize in casual, friendly Spanish translations.",
        llm=llm,
        verbose=True
    )

    regional_translator = Agent(
        role="Mexican Spanish Translator",
        goal="Translate to Mexican Spanish with regional expressions and vocabulary",
        backstory="You specialize in Mexican Spanish with regional expressions.",
        llm=llm,
        verbose=True
    )

    msg = "Hey friend, want to grab some coffee later?"
    print(f"Original message: {msg}")

    print("Running parallel translations with different styles...")

    # Create tasks for each style
    formal_task = Task(
        description=f"Translate this to formal Spanish: {msg}",
        expected_output="A formal Spanish translation",
        agent=formal_translator
    )

    casual_task = Task(
        description=f"Translate this to casual Spanish: {msg}",
        expected_output="A casual Spanish translation",
        agent=casual_translator
    )

    regional_task = Task(
        description=f"Translate this to Mexican Spanish: {msg}",
        expected_output="A Mexican Spanish translation",
        agent=regional_translator
    )

    # Run in parallel
    async def run_crew_single(agent, task):
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        return await asyncio.to_thread(crew.kickoff)

    formal_result, casual_result, regional_result = await asyncio.gather(
        run_crew_single(formal_translator, formal_task),
        run_crew_single(casual_translator, casual_task),
        run_crew_single(regional_translator, regional_task)
    )

    print(f"\nFormal style: {formal_result}")
    print(f"Casual style: {casual_result}")
    print(f"Regional style: {regional_result}")

    # Get style recommendation
    style_comparison = f"""
    Original: {msg}

    Formal Spanish: {formal_result}
    Casual Spanish: {casual_result}
    Mexican Spanish: {regional_result}
    """

    recommendation_task = Task(
        description=f"Compare these translation styles and recommend which is most appropriate for the context: {style_comparison}",
        expected_output="A recommendation with explanation",
        agent=translation_quality_picker
    )

    recommendation_crew = Crew(
        agents=[translation_quality_picker],
        tasks=[recommendation_task],
        verbose=False
    )

    style_recommendation = recommendation_crew.kickoff()
    print(f"\nStyle recommendation: {style_recommendation}")

    return style_recommendation

# Example 3: Parallel content generation for diversity
async def parallel_content_generation():
    """Demonstrates parallel content generation for creative diversity"""

    print("\n=== Parallel Content Generation for Diversity ===")

    # Create content generation agents with different approaches
    creative_agent = Agent(
        role="Creative Writer",
        goal="Write creative, engaging content with vivid imagery and storytelling",
        backstory="You are a creative writer who uses vivid imagery and storytelling techniques.",
        llm=llm,
        verbose=True
    )

    informative_agent = Agent(
        role="Informative Writer",
        goal="Write clear, factual, informative content focused on key information",
        backstory="You are an informative writer who focuses on clarity and key facts.",
        llm=llm,
        verbose=True
    )

    persuasive_agent = Agent(
        role="Persuasive Writer",
        goal="Write compelling, persuasive content that motivates action",
        backstory="You are a persuasive writer who creates compelling content that motivates action.",
        llm=llm,
        verbose=True
    )

    topic = "The benefits of learning a new language"
    print(f"Content topic: {topic}")

    print("Generating content with different writing styles in parallel...")

    # Create tasks for each writing style
    creative_task = Task(
        description=f"Write a short paragraph about: {topic}",
        expected_output="A creative paragraph with vivid imagery",
        agent=creative_agent
    )

    informative_task = Task(
        description=f"Write a short paragraph about: {topic}",
        expected_output="An informative paragraph with key facts",
        agent=informative_agent
    )

    persuasive_task = Task(
        description=f"Write a short paragraph about: {topic}",
        expected_output="A persuasive paragraph that motivates action",
        agent=persuasive_agent
    )

    # Run in parallel
    async def run_crew_single(agent, task):
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        return await asyncio.to_thread(crew.kickoff)

    creative_result, informative_result, persuasive_result = await asyncio.gather(
        run_crew_single(creative_agent, creative_task),
        run_crew_single(informative_agent, informative_task),
        run_crew_single(persuasive_agent, persuasive_task)
    )

    print(f"\nCreative approach:\n{creative_result}")
    print(f"\nInformative approach:\n{informative_result}")
    print(f"\nPersuasive approach:\n{persuasive_result}")

    # Synthesize best elements
    synthesis_agent = Agent(
        role="Content Synthesizer",
        goal="Combine the best elements from multiple content pieces into one cohesive paragraph",
        backstory="You are an expert at synthesizing multiple perspectives into cohesive content.",
        llm=llm,
        verbose=True
    )

    combined_content = f"""
    Topic: {topic}

    Creative version: {creative_result}

    Informative version: {informative_result}

    Persuasive version: {persuasive_result}
    """

    synthesis_task = Task(
        description=f"Create the best possible paragraph by combining elements from these approaches: {combined_content}",
        expected_output="A synthesized paragraph combining the best elements",
        agent=synthesis_agent
    )

    synthesis_crew = Crew(
        agents=[synthesis_agent],
        tasks=[synthesis_task],
        verbose=False
    )

    synthesized_result = synthesis_crew.kickoff()
    print(f"\nSynthesized content: {synthesized_result}")

    return synthesized_result

# Main execution
async def main():
    print("🎼 CrewAI - Parallel Multi-Agent Execution")
    print("=" * 60)

    await parallel_translation_example()
    await parallel_specialized_agents()
    await parallel_content_generation()

    print("\n✅ Parallel execution tutorial complete!")
    print("Parallel execution enables quality improvement through diversity and selection")

if __name__ == "__main__":
    asyncio.run(main())
