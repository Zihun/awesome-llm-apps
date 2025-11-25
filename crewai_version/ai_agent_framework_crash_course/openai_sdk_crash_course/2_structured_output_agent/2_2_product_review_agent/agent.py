from typing import List, Optional
from enum import Enum
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json

class Sentiment(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class ProductReview(BaseModel):
    product_name: Optional[str] = Field(description="Product name if mentioned", default=None)
    rating: int = Field(description="Star rating (1-5)", ge=1, le=5)
    sentiment: Sentiment = Field(description="Overall sentiment of the review")
    main_positives: List[str] = Field(description="Main positive points mentioned", default=[])
    main_negatives: List[str] = Field(description="Main negative points mentioned", default=[])
    would_recommend: Optional[bool] = Field(description="Whether reviewer would recommend", default=None)
    summary: str = Field(description="Brief summary of the review")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.3)

# Create agent for product review analysis
product_review_agent = Agent(
    role="Product Review Analyzer",
    goal="Extract structured data from customer product reviews",
    backstory="""
    You are a product review analysis expert that extracts structured data
    from customer product reviews.

    Analyze the review text and extract:
    - Product name if mentioned
    - Star rating (1-5) based on review tone
    - Sentiment classification (very_positive to very_negative)
    - Main positive and negative points
    - Whether they would recommend (if stated or implied)
    - Brief summary

    RATING GUIDELINES:
    - 5 stars: Excellent, highly satisfied, "amazing", "perfect"
    - 4 stars: Good, satisfied, minor issues
    - 3 stars: Okay, mixed feelings, "decent"
    - 2 stars: Poor, unsatisfied, significant issues
    - 1 star: Terrible, very unsatisfied, "worst"

    IMPORTANT: You must respond with valid JSON matching this schema:
    {
        "product_name": "string or null",
        "rating": 1-5,
        "sentiment": "very_positive|positive|neutral|negative|very_negative",
        "main_positives": ["string"],
        "main_negatives": ["string"],
        "would_recommend": true/false/null,
        "summary": "string"
    }
    """,
    llm=llm,
    verbose=True
)

def analyze_product_review(review_text: str) -> ProductReview:
    """Analyze product review and return structured data"""
    task = Task(
        description=f"""
        Analyze this product review and extract structured information:

        {review_text}

        Return ONLY a valid JSON object matching the ProductReview schema.
        """,
        expected_output="A valid JSON object representing the analyzed product review",
        agent=product_review_agent
    )

    crew = Crew(
        agents=[product_review_agent],
        tasks=[task],
        verbose=False
    )

    result = crew.kickoff()

    # Parse the JSON response into ProductReview model
    try:
        result_str = str(result)
        if '{' in result_str:
            json_start = result_str.index('{')
            json_end = result_str.rindex('}') + 1
            json_str = result_str[json_start:json_end]
            review_data = json.loads(json_str)
            return ProductReview(**review_data)
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response was: {result}")
        raise

root_agent = product_review_agent
