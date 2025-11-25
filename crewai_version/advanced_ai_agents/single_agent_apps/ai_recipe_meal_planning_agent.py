import os
import random
import gradio as gr
from textwrap import dedent
from typing import Dict, List, Optional
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from crewai_tools import tool
import requests
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@tool("Search Recipes")
def search_recipes_tool(ingredients: str, diet_type: Optional[str] = None) -> Dict:
    """Search for detailed recipes with cooking instructions."""
    if not SPOONACULAR_API_KEY:
        return {"error": "Spoonacular API key not found"}

    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ingredients,
        "number": 5,
        "ranking": 2,
        "ignorePantry": True
    }
    if diet_type:
        params["diet"] = diet_type

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        recipes = response.json()

        detailed_recipes = []
        for recipe in recipes[:3]:
            detail_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
            detail_response = requests.get(detail_url, params={"apiKey": SPOONACULAR_API_KEY}, timeout=10)

            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                detailed_recipes.append({
                    "id": recipe['id'],
                    "title": recipe['title'],
                    "ready_in_minutes": detail_data.get('readyInMinutes', 'N/A'),
                    "servings": detail_data.get('servings', 'N/A'),
                    "health_score": detail_data.get('healthScore', 0),
                    "used_ingredients": [i['name'] for i in recipe['usedIngredients']],
                    "missing_ingredients": [i['name'] for i in recipe['missedIngredients']],
                    "instructions": detail_data.get('instructions', 'Instructions not available')
                })

        return {
            "recipes": detailed_recipes,
            "total_found": len(recipes)
        }
    except Exception as e:
        return {"error": f"Recipe search failed: {str(e)}"}

@tool("Analyze Nutrition")
def analyze_nutrition_tool(recipe_name: str) -> Dict:
    """Get nutrition analysis for a recipe by searching for it."""
    if not SPOONACULAR_API_KEY:
        return {"error": "API key not found"}

    # First search for the recipe
    search_url = "https://api.spoonacular.com/recipes/complexSearch"
    search_params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": recipe_name,
        "number": 1,
        "addRecipeInformation": True,
        "addRecipeNutrition": True
    }

    try:
        search_response = requests.get(search_url, params=search_params, timeout=15)
        search_response.raise_for_status()
        search_data = search_response.json()

        if not search_data.get('results'):
            return {"error": f"No recipe found for '{recipe_name}'"}

        recipe = search_data['results'][0]

        if 'nutrition' not in recipe:
            return {"error": "No nutrition data available for this recipe"}

        nutrients = {n['name']: n['amount'] for n in recipe['nutrition']['nutrients']}
        calories = round(nutrients.get('Calories', 0))
        protein = round(nutrients.get('Protein', 0), 1)
        carbs = round(nutrients.get('Carbohydrates', 0), 1)
        fat = round(nutrients.get('Fat', 0), 1)
        fiber = round(nutrients.get('Fiber', 0), 1)
        sodium = round(nutrients.get('Sodium', 0), 1)

        # Health insights
        health_insights = []
        if protein > 25:
            health_insights.append("High protein - great for muscle building")
        if fiber > 5:
            health_insights.append("High fiber - supports digestive health")
        if sodium < 600:
            health_insights.append("Low sodium - heart-friendly")
        if calories < 400:
            health_insights.append("Low calorie - good for weight management")

        return {
            "recipe_title": recipe.get('title', 'Recipe'),
            "servings": recipe.get('servings', 1),
            "ready_in_minutes": recipe.get('readyInMinutes', 'N/A'),
            "health_score": recipe.get('healthScore', 0),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "fiber": fiber,
            "sodium": sodium,
            "health_insights": health_insights
        }
    except Exception as e:
        return {"error": f"Nutrition analysis failed: {str(e)}"}

@tool("Estimate Costs")
def estimate_costs_tool(ingredients: str, servings: int = 4) -> Dict:
    """Detailed cost estimation with budget tips."""
    ingredients_list = [i.strip() for i in ingredients.split(",")]

    prices = {
        "chicken breast": 6.99, "ground beef": 5.99, "salmon": 12.99,
        "rice": 2.99, "pasta": 1.99, "broccoli": 2.99, "tomatoes": 3.99,
        "cheese": 5.99, "onion": 1.49, "garlic": 2.99, "olive oil": 7.99
    }

    cost_breakdown = []
    total_cost = 0

    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower().strip()
        cost = 3.99  # default

        for key, price in prices.items():
            if key in ingredient_lower or any(word in ingredient_lower for word in key.split()):
                cost = price
                break

        adjusted_cost = (cost * servings) / 4
        total_cost += adjusted_cost
        cost_breakdown.append({
            "name": ingredient.title(),
            "cost": round(adjusted_cost, 2)
        })

    # Budget tips
    budget_tips = []
    if total_cost > 30:
        budget_tips.append("Consider buying in bulk for better prices")
    if total_cost > 40:
        budget_tips.append("Look for seasonal alternatives to reduce costs")
    budget_tips.append("Shop at local markets for fresher, cheaper produce")

    return {
        "total_cost": round(total_cost, 2),
        "cost_per_serving": round(total_cost / servings, 2),
        "servings": servings,
        "breakdown": cost_breakdown,
        "budget_tips": budget_tips
    }

def create_meal_planning_agent(openai_api_key: str):
    """Create the meal planning agent using CrewAI"""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=openai_api_key,
        temperature=0.7
    )

    agent = Agent(
        role="Meal Planning Expert",
        goal="Provide detailed, helpful responses for recipe searches, nutrition analysis, cost estimation, and meal planning",
        backstory=dedent("""\
            You are an expert meal planning assistant with years of experience in nutrition,
            cooking, and budget management. You provide detailed, helpful responses with:
            - Recipe Searches: Include cooking time, health scores, ingredient lists, and instructions
            - Nutrition Analysis: Provide health insights, nutritional breakdowns, and dietary advice
            - Cost Estimation: Include budget tips and cost per serving breakdowns
            - Meal Planning: Create detailed weekly plans with nutritional balance and shopping lists

            Always use clear headings and bullet points, include practical cooking tips,
            consider dietary restrictions and budgets, and be encouraging and supportive.
        """),
        tools=[search_recipes_tool, analyze_nutrition_tool, estimate_costs_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return agent

def process_query(query: str, openai_api_key: str, chat_history: List) -> tuple:
    """Process user query using CrewAI"""
    if not openai_api_key:
        return chat_history + [[query, "Please provide your OpenAI API key."]], chat_history + [[query, "Please provide your OpenAI API key."]]

    try:
        agent = create_meal_planning_agent(openai_api_key)

        task = Task(
            description=query,
            agent=agent,
            expected_output="A comprehensive response to the user's query about recipes, nutrition, meal planning, or costs"
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()
        response = str(result)

        chat_history.append([query, response])
        return chat_history, chat_history

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        chat_history.append([query, error_msg])
        return chat_history, chat_history

def create_interface():
    """Create Gradio interface"""
    with gr.Blocks(title="AI Meal Planning Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # AI Meal Planning Agent
            *Your intelligent companion for recipes, nutrition, and meal planning*

            I can help you with:
            - Recipe Discovery - Find recipes based on your ingredients
            - Nutrition Analysis - Get detailed nutritional insights
            - Cost Estimation - Smart budget planning with money-saving tips
            - Meal Planning - Complete weekly meal plans with shopping lists

            **Try asking:**
            - "Find healthy chicken recipes for dinner"
            - "What's the nutrition info for chicken teriyaki?"
            - "Estimate costs for pasta, tomatoes, cheese, and basil for 4 servings"
            """
        )

        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    label="Chat with Meal Planning Expert",
                    height=500,
                    show_label=True
                )

                with gr.Row():
                    query_input = gr.Textbox(
                        placeholder="Ask about recipes, nutrition, meal planning, or costs...",
                        label="Your Question",
                        lines=2,
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)

                clear_btn = gr.Button("Clear Chat")

            with gr.Column(scale=1):
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="sk-...",
                    value=OPENAI_API_KEY or ""
                )

                spoon_key = gr.Textbox(
                    label="Spoonacular API Key (Optional)",
                    type="password",
                    placeholder="For recipe search",
                    value=SPOONACULAR_API_KEY or "",
                    info="Required for recipe search and nutrition features"
                )

                gr.Markdown(
                    """
                    ### Example Queries:
                    - Find vegan recipes with tofu
                    - Analyze nutrition for Greek salad
                    - Estimate costs for chicken, rice, broccoli for 6 servings
                    - Create a keto meal plan for 2 people for 5 days
                    """
                )

        chat_state = gr.State([])

        submit_btn.click(
            fn=process_query,
            inputs=[query_input, openai_key, chat_state],
            outputs=[chatbot, chat_state]
        ).then(
            lambda: "",
            outputs=[query_input]
        )

        query_input.submit(
            fn=process_query,
            inputs=[query_input, openai_key, chat_state],
            outputs=[chatbot, chat_state]
        ).then(
            lambda: "",
            outputs=[query_input]
        )

        clear_btn.click(
            lambda: ([], []),
            outputs=[chatbot, chat_state]
        )

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
