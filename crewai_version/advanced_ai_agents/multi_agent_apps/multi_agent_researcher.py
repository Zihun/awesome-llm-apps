import os
import gradio as gr
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import tool
from dotenv import load_dotenv
import requests
from typing import Dict, List

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@tool("Get HackerNews Top Stories")
def get_hackernews_top_stories(limit: int = 10) -> List[Dict]:
    """Get top stories from HackerNews"""
    try:
        # Get top story IDs
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        story_ids = response.json()[:limit]

        stories = []
        for story_id in story_ids:
            story_response = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            story_data = story_response.json()
            if story_data:
                stories.append({
                    "title": story_data.get("title", ""),
                    "url": story_data.get("url", ""),
                    "score": story_data.get("score", 0),
                    "by": story_data.get("by", ""),
                    "time": story_data.get("time", 0)
                })

        return stories
    except Exception as e:
        return [{"error": f"Failed to fetch HackerNews stories: {str(e)}"}]

@tool("Search HackerNews")
def search_hackernews(query: str, limit: int = 10) -> List[Dict]:
    """Search HackerNews for specific topics"""
    try:
        # Using Algolia HN Search API
        url = "http://hn.algolia.com/api/v1/search"
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": limit
        }

        response = requests.get(url, params=params)
        data = response.json()

        stories = []
        for hit in data.get("hits", []):
            stories.append({
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "points": hit.get("points", 0),
                "author": hit.get("author", ""),
                "created_at": hit.get("created_at", ""),
                "num_comments": hit.get("num_comments", 0)
            })

        return stories
    except Exception as e:
        return [{"error": f"Failed to search HackerNews: {str(e)}"}]

@tool("Read Article")
def read_article(url: str) -> str:
    """Read and extract text from an article URL"""
    try:
        # Simple article reading - in production, use newspaper4k or similar
        response = requests.get(url, timeout=10)
        # Return first 1000 characters as a simple extraction
        return f"Article content from {url}: {response.text[:1000]}..."
    except Exception as e:
        return f"Failed to read article from {url}: {str(e)}"

def create_research_crew(openai_api_key: str):
    """Create HackerNews research crew"""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=openai_api_key,
        temperature=0.7
    )

    # HackerNews Researcher
    hn_researcher = Agent(
        role="HackerNews Researcher",
        goal="Search and retrieve top stories from HackerNews on requested topics",
        backstory="""\
            You are an expert at navigating HackerNews and finding the most relevant
            and interesting stories. You know how to search effectively and identify
            high-quality content that matches user interests.""",
        tools=[get_hackernews_top_stories, search_hackernews],
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

    # Web Searcher
    web_searcher = Agent(
        role="Web Research Specialist",
        goal="Search the web for additional information on topics to provide comprehensive context",
        backstory="""\
            You are a skilled web researcher who excels at finding relevant information
            from across the internet. You provide context and background information
            to complement primary sources.""",
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

    # Article Reader
    article_reader = Agent(
        role="Article Content Analyst",
        goal="Read and summarize articles from provided URLs",
        backstory="""\
            You are an expert at quickly reading and extracting key information from
            articles. You provide concise yet comprehensive summaries that capture
            the essence of the content.""",
        tools=[read_article],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return hn_researcher, web_searcher, article_reader

def research_hackernews(query: str, openai_api_key: str, progress=gr.Progress()) -> str:
    """Research HackerNews and generate report"""

    if not openai_api_key:
        return "Error: Please provide your OpenAI API key."

    if not query:
        return "Error: Please enter a search query."

    try:
        progress(0.1, desc="Initializing research crew...")
        hn_researcher, web_searcher, article_reader = create_research_crew(openai_api_key)

        # Task 1: Search HackerNews
        progress(0.3, desc="Searching HackerNews...")
        hn_search_task = Task(
            description=f"""\
                Search HackerNews for stories related to: {query}

                Find the most relevant and interesting stories. Look for:
                - High-quality discussions
                - Recent and trending topics
                - Articles with good engagement (points and comments)

                Provide a list of the top stories with their titles, URLs, and key details.
            """,
            agent=hn_researcher,
            expected_output="A list of relevant HackerNews stories with titles, URLs, points, and authors"
        )

        # Task 2: Read articles
        progress(0.5, desc="Reading articles...")
        article_reading_task = Task(
            description=f"""\
                From the HackerNews stories found, read the linked articles to get more details.
                Focus on the most upvoted and discussed stories.

                Extract key points, main arguments, and interesting insights from each article.
            """,
            agent=article_reader,
            expected_output="Summaries of key articles with main points and insights"
        )

        # Task 3: Web research for context
        progress(0.7, desc="Gathering additional context...")
        web_research_task = Task(
            description=f"""\
                Search the web for additional context and information about: {query}

                Provide background information, recent developments, and relevant context
                that complements the HackerNews stories.
            """,
            agent=web_searcher,
            expected_output="Additional context and background information from web research"
        )

        # Task 4: Create final report
        progress(0.9, desc="Generating final report...")
        report_task = Task(
            description=f"""\
                Based on all the research gathered, create a comprehensive and engaging report about: {query}

                Your report should include:
                1. Executive Summary
                2. Key Findings from HackerNews discussions
                3. Important insights from the articles
                4. Additional context from web research
                5. Trending topics and discussions
                6. Conclusion and takeaways

                Make the report well-structured, informative, and easy to read.
                Use markdown formatting for better readability.
            """,
            agent=hn_researcher,
            expected_output="A comprehensive, well-structured research report in markdown format"
        )

        # Create and run crew
        crew = Crew(
            agents=[hn_researcher, web_searcher, article_reader],
            tasks=[hn_search_task, article_reading_task, web_research_task, report_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        progress(1.0, desc="Research complete!")

        return str(result)

    except Exception as e:
        return f"Error during research: {str(e)}"

def create_interface():
    """Create Gradio interface"""

    with gr.Blocks(title="Multi-Agent AI Researcher", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # Multi-Agent AI Researcher 🔍🤖
            This app allows you to research top stories and users on HackerNews and generate
            comprehensive blogs, reports, and insights.

            The AI crew consists of:
            - **HackerNews Researcher**: Searches and retrieves relevant HN stories
            - **Article Reader**: Reads and summarizes linked articles
            - **Web Searcher**: Gathers additional context from the web
            - **Report Writer**: Synthesizes everything into a comprehensive report
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    label="Research Query",
                    placeholder="E.g., AI developments, startup trends, programming languages...",
                    lines=3
                )

                research_btn = gr.Button("🔍 Start Research", variant="primary", size="lg")

                output = gr.Markdown(
                    label="Research Report",
                    value="Your research report will appear here..."
                )

            with gr.Column(scale=1):
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="sk-...",
                    value=OPENAI_API_KEY or ""
                )

                gr.Markdown(
                    """
                    ### 📚 Research Topics:
                    - Technology trends
                    - Startup news
                    - Programming discussions
                    - AI/ML developments
                    - Web development
                    - Startup advice
                    - And more!

                    ### 💡 Tips:
                    - Be specific with your query
                    - Research may take 1-2 minutes
                    - Results include HN discussions
                      and web context
                    """
                )

        research_btn.click(
            fn=research_hackernews,
            inputs=[query_input, openai_key],
            outputs=output
        )

        gr.Examples(
            examples=[
                ["Latest developments in AI and machine learning"],
                ["Best practices for startup funding"],
                ["Modern web development frameworks"],
                ["Remote work trends and tools"],
                ["Cryptocurrency and blockchain news"]
            ],
            inputs=query_input
        )

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
