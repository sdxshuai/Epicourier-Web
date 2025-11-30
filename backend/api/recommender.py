"""
recommender.py — Lazy-load + Render-safe version
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Optional

import pandas as pd
import torch
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer, util
from sklearn.cluster import KMeans
from supabase import create_client

# --------------------------------------------------
# 1. Global setup
# --------------------------------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")


# --------------------------------------------------
# 2. Lazy loaders
# --------------------------------------------------
@lru_cache()
def load_supabase():
    print("Connecting to Supabase ...")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@lru_cache()
def load_recipe_data():
    """Load and merge recipe data only once."""
    print("Loading recipe data from Supabase ...")
    supabase = load_supabase()

    ingredients = pd.DataFrame(supabase.table("Ingredient").select("*").execute().data)
    recipes = pd.DataFrame(supabase.table("Recipe").select("*").execute().data)
    recipe_ing_map = pd.DataFrame(
        supabase.table("Recipe-Ingredient_Map").select("*").execute().data
    )
    tags = pd.DataFrame(supabase.table("RecipeTag").select("*").execute().data)
    recipe_tag_map = pd.DataFrame(
        supabase.table("Recipe-Tag_Map").select("*").execute().data
    )

    # Merge metadata
    recipe_tags = recipe_tag_map.merge(
        tags, left_on="tag_id", right_on="id", suffixes=("", "_tag")
    )
    recipe_tags = (
        recipe_tags.groupby("recipe_id")["name"].apply(list).reset_index(name="tags")
    )

    recipe_ing = recipe_ing_map.merge(
        ingredients, left_on="ingredient_id", right_on="id", suffixes=("", "_ing")
    )
    recipe_ing = (
        recipe_ing.groupby("recipe_id")["name"]
        .apply(list)
        .reset_index(name="ingredients")
    )

    recipe_data = recipes.merge(
        recipe_tags, left_on="id", right_on="recipe_id", how="left"
    )
    recipe_data = recipe_data.merge(
        recipe_ing, left_on="id", right_on="recipe_id", how="left"
    )

    recipe_data["tags"] = recipe_data["tags"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    recipe_data["ingredients"] = recipe_data["ingredients"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    return recipe_data


@lru_cache()
def load_embedder():
    print("Loading sentence-transformer model ...")
    return SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)


@lru_cache()
def load_gemini_client():
    print("Initializing Gemini client ...")
    if not GEMINI_KEY:
        raise ValueError(
            "GEMINI_KEY environment variable not set. "
            "Please set GEMINI_KEY to use Gemini features."
        )
    return genai.Client(api_key=GEMINI_KEY)


# --------------------------------------------------
# 3. Utility functions
# --------------------------------------------------
def make_recipe_text(row):
    return (
        f"{row.get('description', '')}. "
        f"Ingredients: {', '.join(row['ingredients'])}. "
        f"Tags: {', '.join(row['tags'])}."
    )


def get_recipe_embeddings(recipe_data):
    """Compute embeddings for all recipes (cached)."""
    embedder = load_embedder()
    if "recipe_text" not in recipe_data.columns:
        recipe_data["recipe_text"] = recipe_data.apply(make_recipe_text, axis=1)
    print("Computing recipe embeddings ...")
    embeddings = embedder.encode(
        recipe_data["recipe_text"].tolist(), convert_to_tensor=True
    )
    return embeddings


# --------------------------------------------------
# 4. Gemini-based goal expansion
# --------------------------------------------------
def nutrition_goal(goal_text):
    """Translate a user's goal into target nutritional values using Gemini."""
    client = load_gemini_client()
    prompt = (
        "Your task is to translate a user's specific diet goal into precise, "
        "target nutritional values for a daily meal plan.\n"
        "Just provide the nutritional values without any additional explanation "
        "or context.\n\n"
        f"**GOAL:** {goal_text}\n\n"
        "You may include: calories_kcal, protein_g, carbs_g, sugars_g, total_fats_g, "
        "cholesterol_mg, total_minerals_mg, vit_a_microg, total_vit_b_mg, "
        "vit_c_mg, vit_d_microg, vit_e_mg, vit_k_microg"
    )
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text.strip()


def expand_goal(goal_text):
    """Translate a user's goal into nutrition information using Gemini."""
    client = load_gemini_client()
    prompt = (
        "Your task is to translate a user's specific diet goal into precise, "
        "target nutritional values for a daily meal plan.\n\n"
        f"**GOAL:** {goal_text}\n\n"
        "You may include: calories_kcal, protein_g, carbs_g, sugars_g, total_fats_g, "
        "cholesterol_mg, total_minerals_mg, vit_a_microg, total_vit_b_mg, "
        "vit_c_mg, vit_d_microg, vit_e_mg, vit_k_microg"
    )

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text.strip()


# --------------------------------------------------
# 5. Recommendation pipeline
# --------------------------------------------------
def rank_recipes_by_goal(goal_text, top_k=20):
    recipe_data = load_recipe_data()
    recipe_embeddings = get_recipe_embeddings(recipe_data)
    embedder = load_embedder()

    nutri_goal = nutrition_goal(goal_text)
    goal_embedding = embedder.encode(nutri_goal, convert_to_tensor=True)
    scores = util.cos_sim(goal_embedding, recipe_embeddings)[0].cpu().numpy()

    recipe_data = recipe_data.copy()
    recipe_data["similarity"] = scores
    ranked = recipe_data.sort_values(by="similarity", ascending=False).head(top_k)
    return ranked, nutri_goal


def select_diverse_recipes(ranked_df, n_meals=3):
    """Cluster embeddings to ensure diversity among top recipes."""
    embedder = load_embedder()
    n_clusters = min(n_meals, len(ranked_df))
    if len(ranked_df) <= n_meals:
        return ranked_df

    sub_embeds = embedder.encode(ranked_df["recipe_text"].tolist())
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    cluster_labels = kmeans.fit_predict(sub_embeds)

    selected_indices = []
    for c in range(n_clusters):
        cluster_recipes = ranked_df[cluster_labels == c]
        top_one = cluster_recipes.sort_values("similarity", ascending=False).head(1)
        selected_indices.append(top_one.index[0])
    return ranked_df.loc[selected_indices].sort_values("similarity", ascending=False)


# CREATE MEAL PLAN
def create_meal_plan(goal_text, n_meals=3):
    ranked, nutri_goal = rank_recipes_by_goal(goal_text)
    diverse = select_diverse_recipes(ranked, n_meals)
    exp_goal = expand_goal(goal_text)

    meal_plan = []
    for i, row in enumerate(diverse.itertuples(), 1):
        meal_plan.append(
            {
                "meal_number": i,
                "name": row.name,
                "tags": row.tags,
                "key_ingredients": row.ingredients[:10],  # limit to first few
                "reason": (
                    f"Selected because it aligns with goal '{goal_text}' "
                    "and differs from other meals."
                ),
                "similarity_score": round(float(row.similarity), 3),
                "recipe": row.recipe_text,
            }
        )

    # print(f"Expanded goal: {exp_goal}\n")
    return meal_plan, exp_goal


# --------------------------------------------------
# 6. Inventory-based recommendation
# --------------------------------------------------
@dataclass
class CoverageResult:
    """Result of coverage calculation for a recipe."""

    score: float
    missing: list[int] = field(default_factory=list)


def calculate_coverage(
    recipe_ingredient_ids: list[int], inventory: list[dict]
) -> CoverageResult:
    """
    Calculate coverage score based on available ingredients.

    Args:
        recipe_ingredient_ids: List of ingredient IDs required by the recipe
        inventory: List of inventory items with 'ingredient_id' keys

    Returns:
        CoverageResult with score (0.0 to 1.0) and list of missing ingredient IDs
    """
    if not recipe_ingredient_ids:
        return CoverageResult(score=1.0, missing=[])

    inventory_ids = {item.get("ingredient_id") for item in inventory}
    missing = [
        ing_id for ing_id in recipe_ingredient_ids if ing_id not in inventory_ids
    ]

    matched_count = len(recipe_ingredient_ids) - len(missing)
    score = matched_count / len(recipe_ingredient_ids)

    return CoverageResult(score=score, missing=missing)


def calculate_expiration_urgency(expiration_date: Optional[str]) -> float:
    """
    Calculate expiration urgency score.

    Args:
        expiration_date: ISO 8601 format date string or None

    Returns:
        Urgency score from 0.0 (not urgent) to 1.0 (expired or very urgent)
    """
    if expiration_date is None:
        return 0.0

    try:
        # Parse ISO 8601 date (handle both date-only and datetime formats)
        if "T" in expiration_date:
            exp_dt = datetime.fromisoformat(expiration_date.replace("Z", "+00:00"))
            now = datetime.now(exp_dt.tzinfo) if exp_dt.tzinfo else datetime.now()
        else:
            exp_dt = datetime.fromisoformat(expiration_date)
            now = datetime.now()

        days_until_expiry = (exp_dt - now).days

        # Already expired
        if days_until_expiry < 0:
            return 1.0

        # Expiring within 2 days - critical
        if days_until_expiry <= 2:
            return 0.9 - (days_until_expiry * 0.05)

        # Expiring within a week
        if days_until_expiry <= 7:
            return 0.6 - (days_until_expiry - 2) * 0.05

        # Expiring within 2 weeks
        if days_until_expiry <= 14:
            return 0.3 - (days_until_expiry - 7) * 0.02

        # Not urgent
        return 0.0

    except (ValueError, TypeError):
        return 0.0


def combined_score(coverage: float, expiration: float) -> float:
    """
    Calculate combined recommendation score.

    Coverage is weighted higher (70%) than expiration urgency (30%).

    Args:
        coverage: Coverage score (0.0 to 1.0)
        expiration: Expiration urgency score (0.0 to 1.0)

    Returns:
        Combined score (0.0 to 1.0)
    """
    coverage_weight = 0.7
    expiration_weight = 0.3

    return coverage * coverage_weight + expiration * expiration_weight


def get_inventory_expiration_urgency(inventory: list[dict]) -> float:
    """
    Calculate average expiration urgency for inventory items.

    Args:
        inventory: List of inventory items with optional 'expiration_date' keys

    Returns:
        Average urgency score across all inventory items
    """
    if not inventory:
        return 0.0

    urgencies = [
        calculate_expiration_urgency(item.get("expiration_date"))
        for item in inventory
    ]
    return sum(urgencies) / len(urgencies) if urgencies else 0.0


def recommend_by_inventory(
    inventory: list[dict], num_recipes: int = 5
) -> list[dict]:
    """
    Recommend recipes based on available inventory.

    Args:
        inventory: List of inventory items with ingredient_id, quantity, and
                   optional expiration_date
        num_recipes: Maximum number of recipes to return

    Returns:
        List of recommended recipes with scores and metadata
    """
    if not inventory:
        return []

    recipe_data = load_recipe_data()
    supabase = load_supabase()

    # Get recipe-ingredient mappings
    recipe_ing_map = pd.DataFrame(
        supabase.table("Recipe-Ingredient_Map").select("*").execute().data
    )

    # Group ingredients by recipe
    recipe_ingredients = (
        recipe_ing_map.groupby("recipe_id")["ingredient_id"]
        .apply(list)
        .to_dict()
    )

    # Calculate average inventory expiration urgency
    avg_expiration = get_inventory_expiration_urgency(inventory)

    recommendations = []
    for _, recipe in recipe_data.iterrows():
        recipe_id = recipe["id"]
        ingredient_ids = recipe_ingredients.get(recipe_id, [])

        # Calculate coverage
        coverage_result = calculate_coverage(ingredient_ids, inventory)

        # Skip recipes with zero coverage
        if coverage_result.score == 0:
            continue

        # Calculate combined score
        score = combined_score(coverage_result.score, avg_expiration)

        recommendations.append({
            "recipe_id": recipe_id,
            "name": recipe.get("name", ""),
            "description": recipe.get("description", ""),
            "coverage_score": round(coverage_result.score, 3),
            "expiration_urgency": round(avg_expiration, 3),
            "combined_score": round(score, 3),
            "missing_ingredients": coverage_result.missing,
            "ingredients": recipe.get("ingredients", []),
            "tags": recipe.get("tags", []),
        })

    # Sort by combined score (descending)
    recommendations.sort(key=lambda x: x["combined_score"], reverse=True)

    return recommendations[:num_recipes]
