import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client

from api.recommender import create_meal_plan, recommend_from_inventory

load_dotenv()

url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or ""
key: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or ""

supabase: Client = create_client(url, key)

app = FastAPI()

# Allow frontend (Next.js) to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test")
def test_endpoint():
    data = supabase.table("Recipe").select("*").limit(5).execute()
    return {"message": data.data}


class RecommendRequest(BaseModel):
    goal: str
    num_meals: int = Field(..., alias="numMeals")

    model_config = {"populate_by_name": True}


@app.post("/recommender")
def recommend_meals(req: RecommendRequest):
    """Main recommender endpoint with input validation."""
    # Validate goal
    if not req.goal or not req.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")

    # Validate number of meals
    if req.num_meals not in [3, 5, 7]:
        raise HTTPException(
            status_code=400, detail="numMeals must be one of 3, 5, or 7"
        )

    plan, expanded_goal = create_meal_plan(req.goal, n_meals=req.num_meals)
    return {"recipes": plan, "goal_expanded": expanded_goal}


# --------------------------------------------------
# Inventory-based recommendations
# --------------------------------------------------
class InventoryItem(BaseModel):
    """Single inventory item for recommendation request."""

    ingredient_id: int
    quantity: Optional[float] = None
    expiration_date: Optional[str] = None


class InventoryRecommendRequest(BaseModel):
    """Request body for inventory-based recommendations."""

    inventory: list[InventoryItem]
    preferences: Optional[str] = None
    num_recipes: int = Field(default=5, alias="numRecipes")

    model_config = {"populate_by_name": True}


class ExpiringIngredientInfo(BaseModel):
    """Info about expiring ingredient in recommendation."""

    name: str
    expires_in_days: int


class InventoryRecipeRecommendation(BaseModel):
    """Single recipe recommendation from inventory."""

    recipe_id: int
    recipe_name: str
    recipe_image: Optional[str] = None
    coverage_score: float
    missing_ingredients: list[str]
    uses_expiring: list[ExpiringIngredientInfo]
    reasoning: str


class InventoryRecommendResponse(BaseModel):
    """Response for inventory-based recommendations."""

    recipes: list[InventoryRecipeRecommendation]
    summary: str


@app.post("/inventory-recommend", response_model=InventoryRecommendResponse)
def inventory_recommend(req: InventoryRecommendRequest):
    """
    Recommend recipes based on user's available inventory.

    Algorithm:
    1. Calculate coverage score for each recipe (ingredients available / total needed)
    2. Apply expiration urgency bonus for recipes using soon-to-expire items
    3. Optional: Filter by preferences via Gemini
    4. Use KMeans clustering for diverse suggestions
    5. Return top N recipes with reasoning
    """
    # Validate inventory
    if not req.inventory:
        raise HTTPException(status_code=400, detail="Inventory cannot be empty")

    # Validate num_recipes
    if req.num_recipes < 1 or req.num_recipes > 20:
        raise HTTPException(
            status_code=400, detail="numRecipes must be between 1 and 20"
        )

    # Convert to dict format for the recommender
    inventory_items = [
        {
            "ingredient_id": item.ingredient_id,
            "quantity": item.quantity,
            "expiration_date": item.expiration_date,
        }
        for item in req.inventory
    ]

    recipes, summary = recommend_from_inventory(
        inventory_items=inventory_items,
        preferences=req.preferences,
        num_recipes=req.num_recipes,
    )

    return InventoryRecommendResponse(recipes=recipes, summary=summary)
