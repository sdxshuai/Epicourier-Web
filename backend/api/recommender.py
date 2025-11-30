"""
recommender.py — Lazy-load + Render-safe version
"""

import os
from functools import lru_cache

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


client = load_gemini_client()


# --------------------------------------------------
# 4. Gemini-based goal expansion
# --------------------------------------------------
def nutrition_goal(goal_text):
    """Translate a user's goal into target nutritional values using Gemini."""
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
# 6. Inventory-based recommendations
# --------------------------------------------------
@lru_cache()
def load_recipe_ingredient_map():
    """Load recipe-ingredient mappings for coverage calculations."""
    print("Loading recipe-ingredient mappings from Supabase ...")
    supabase = load_supabase()
    ingredients = pd.DataFrame(supabase.table("Ingredient").select("*").execute().data)
    recipe_ing_map = pd.DataFrame(
        supabase.table("Recipe-Ingredient_Map").select("*").execute().data
    )
    return recipe_ing_map, ingredients


def calculate_days_until_expiration(expiration_date_str):
    """Calculate days until expiration from ISO date string."""
    from datetime import date, datetime

    if not expiration_date_str:
        return None
    try:
        exp_date = datetime.fromisoformat(expiration_date_str.replace("Z", "+00:00"))
        if exp_date.tzinfo:
            exp_date = exp_date.replace(tzinfo=None)
        today = date.today()
        return (exp_date.date() - today).days
    except (ValueError, AttributeError):
        return None


def calculate_coverage_and_missing(
    recipe_id, inventory_dict, recipe_ing_map, ingredients
):
    """
    Calculate coverage score and missing ingredients for a recipe.

    Args:
        recipe_id: Recipe ID to evaluate
        inventory_dict: Dict mapping ingredient_id to inventory item info
        recipe_ing_map: DataFrame with recipe-ingredient mappings
        ingredients: DataFrame with ingredient info

    Returns:
        tuple: (coverage_score, missing_ingredients list, available_ingredients list)
    """
    # Get all ingredients for this recipe
    recipe_ingredients = recipe_ing_map[recipe_ing_map["recipe_id"] == recipe_id]
    if len(recipe_ingredients) == 0:
        return 0.0, [], []

    total_ingredients = len(recipe_ingredients)
    available_count = 0
    missing = []
    available = []

    for _, row in recipe_ingredients.iterrows():
        ing_id = row["ingredient_id"]
        if ing_id in inventory_dict:
            available_count += 1
            available.append(ing_id)
        else:
            # Get ingredient name for missing list
            ing_info = ingredients[ingredients["id"] == ing_id]
            if not ing_info.empty:
                missing.append(ing_info.iloc[0]["name"])
            else:
                missing.append(f"Unknown ingredient ({ing_id})")

    coverage = available_count / total_ingredients if total_ingredients > 0 else 0.0
    return coverage, missing, available


def calculate_expiration_bonus(available_ingredients, inventory_dict):
    """
    Calculate bonus score for using expiring ingredients.

    Args:
        available_ingredients: List of ingredient IDs available in inventory
        inventory_dict: Dict mapping ingredient_id to inventory item info

    Returns:
        tuple: (bonus_score, list of expiring ingredient info)
    """
    CRITICAL_DAYS = 2
    WARNING_DAYS = 7
    CRITICAL_BONUS = 0.15
    WARNING_BONUS = 0.05
    MAX_BONUS = 0.3

    bonus = 0.0
    expiring_items = []

    for ing_id in available_ingredients:
        item = inventory_dict.get(ing_id)
        if not item:
            continue

        days_left = item.get("days_until_expiration")
        if days_left is None:
            continue

        if days_left <= CRITICAL_DAYS:
            bonus += CRITICAL_BONUS
            expiring_items.append(
                {"name": item.get("name", "Unknown"), "expires_in_days": days_left}
            )
        elif days_left <= WARNING_DAYS:
            bonus += WARNING_BONUS
            expiring_items.append(
                {"name": item.get("name", "Unknown"), "expires_in_days": days_left}
            )

    return min(bonus, MAX_BONUS), expiring_items


def generate_reasoning(coverage_score, expiring_items, missing_ingredients):
    """Generate human-readable reasoning for recommendation."""
    coverage_pct = int(coverage_score * 100)
    parts = []

    if coverage_pct >= 100:
        parts.append("You have all the ingredients needed")
    elif coverage_pct >= 80:
        parts.append(f"Uses {coverage_pct}% of required ingredients")
    else:
        parts.append(f"Uses {coverage_pct}% of required ingredients")

    if expiring_items:
        expiring_names = [item["name"] for item in expiring_items[:3]]
        if len(expiring_items) == 1:
            parts.append(f"Uses expiring {expiring_names[0]}")
        else:
            parts.append(f"Uses expiring ingredients: {', '.join(expiring_names)}")

    if missing_ingredients:
        if len(missing_ingredients) <= 2:
            parts.append(f"Missing: {', '.join(missing_ingredients)}")
        else:
            parts.append(f"Missing {len(missing_ingredients)} ingredients")

    return ". ".join(parts) + "."


def recommend_from_inventory(inventory_items, preferences=None, num_recipes=5):
    """
    Recommend recipes based on user's available inventory.

    Args:
        inventory_items: List of dicts with ingredient_id, quantity, expiration_date
        preferences: Optional string with user preferences (e.g., "low carb")
        num_recipes: Number of recipes to return

    Returns:
        tuple: (list of recipe recommendations, summary string)
    """
    recipe_data = load_recipe_data()
    recipe_ing_map, ingredients = load_recipe_ingredient_map()

    # Build inventory dict for quick lookup
    inventory_dict = {}
    for item in inventory_items:
        ing_id = item.get("ingredient_id")
        if ing_id:
            days_left = calculate_days_until_expiration(item.get("expiration_date"))
            # Get ingredient name
            ing_info = ingredients[ingredients["id"] == ing_id]
            ing_name = ing_info.iloc[0]["name"] if not ing_info.empty else "Unknown"
            inventory_dict[ing_id] = {
                "quantity": item.get("quantity", 0),
                "expiration_date": item.get("expiration_date"),
                "days_until_expiration": days_left,
                "name": ing_name,
            }

    if not inventory_dict:
        return [], "No valid inventory items provided."

    # Calculate scores for all recipes
    scored_recipes = []
    for _, recipe in recipe_data.iterrows():
        recipe_id = recipe["id"]
        coverage, missing, available = calculate_coverage_and_missing(
            recipe_id, inventory_dict, recipe_ing_map, ingredients
        )

        # Skip recipes with no ingredient match
        if coverage == 0:
            continue

        exp_bonus, expiring_items = calculate_expiration_bonus(
            available, inventory_dict
        )
        total_score = coverage + exp_bonus

        scored_recipes.append(
            {
                "recipe_id": recipe_id,
                "recipe_name": recipe["name"],
                "recipe_image": recipe.get("image_url"),
                "coverage_score": coverage,
                "total_score": total_score,
                "missing_ingredients": missing,
                "uses_expiring": expiring_items,
                "available_ingredients": available,
                "tags": recipe.get("tags", []),
            }
        )

    if not scored_recipes:
        return [], "No recipes found matching your inventory."

    # Sort by total score (coverage + expiration bonus)
    scored_recipes.sort(key=lambda x: x["total_score"], reverse=True)

    # Optional: Apply preferences filter via Gemini
    if preferences and scored_recipes:
        scored_recipes = filter_by_preferences(scored_recipes, preferences)

    # Use KMeans for diversity if we have enough recipes
    top_candidates = scored_recipes[: min(20, len(scored_recipes))]
    if len(top_candidates) >= num_recipes and len(top_candidates) > num_recipes:
        diverse_recipes = select_diverse_inventory_recipes(
            top_candidates, recipe_data, num_recipes
        )
    else:
        diverse_recipes = top_candidates[:num_recipes]

    # Build final recommendations
    recommendations = []
    for recipe in diverse_recipes:
        reasoning = generate_reasoning(
            recipe["coverage_score"],
            recipe["uses_expiring"],
            recipe["missing_ingredients"],
        )
        recommendations.append(
            {
                "recipe_id": recipe["recipe_id"],
                "recipe_name": recipe["recipe_name"],
                "recipe_image": recipe.get("recipe_image"),
                "coverage_score": round(recipe["coverage_score"], 2),
                "missing_ingredients": recipe["missing_ingredients"],
                "uses_expiring": recipe["uses_expiring"],
                "reasoning": reasoning,
            }
        )

    # Generate summary
    avg_coverage = (
        sum(r["coverage_score"] for r in recommendations) / len(recommendations)
        if recommendations
        else 0
    )
    total_expiring_used = sum(len(r["uses_expiring"]) for r in recommendations)
    summary = (
        f"Found {len(recommendations)} recipes with {int(avg_coverage * 100)}% "
        f"average ingredient coverage"
    )
    if total_expiring_used > 0:
        summary += f", using {total_expiring_used} expiring ingredients"

    return recommendations, summary


def filter_by_preferences(recipes, preferences):
    """
    Filter recipes by user preferences using Gemini.
    Falls back to returning all recipes if Gemini fails.
    """
    if not preferences or not recipes:
        return recipes

    try:
        recipe_info = "\n".join(
            [
                f"- {r['recipe_name']} (tags: {', '.join(r.get('tags', []))})"
                for r in recipes[:15]
            ]
        )
        prompt = (
            f"Given these recipes:\n{recipe_info}\n\n"
            f"Filter to only include recipes that match: '{preferences}'\n"
            f"Return ONLY the recipe names that match, one per line."
        )

        client = load_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        matched_names = set(
            line.strip().lower().lstrip("- ")
            for line in response.text.strip().split("\n")
            if line.strip()
        )

        filtered = [r for r in recipes if r["recipe_name"].lower() in matched_names]
        return filtered if filtered else recipes

    except Exception:
        # On any error, return original list
        return recipes


def select_diverse_inventory_recipes(candidates, recipe_data, n_recipes):
    """
    Select diverse recipes from candidates using KMeans clustering.
    Reuses embedding approach from main recommender.
    """
    if len(candidates) <= n_recipes:
        return candidates

    try:
        embedder = load_embedder()

        # Get recipe texts for candidates
        recipe_texts = []
        for c in candidates:
            recipe_row = recipe_data[recipe_data["id"] == c["recipe_id"]]
            if not recipe_row.empty:
                text = make_recipe_text(recipe_row.iloc[0])
            else:
                text = c["recipe_name"]
            recipe_texts.append(text)

        # Compute embeddings
        embeddings = embedder.encode(recipe_texts)

        # Cluster
        n_clusters = min(n_recipes, len(candidates))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        cluster_labels = kmeans.fit_predict(embeddings)

        # Select best from each cluster
        selected = []
        for cluster_id in range(n_clusters):
            cluster_indices = [
                i for i, label in enumerate(cluster_labels) if label == cluster_id
            ]
            if cluster_indices:
                # Pick highest scored recipe in this cluster
                best_idx = max(
                    cluster_indices, key=lambda i: candidates[i]["total_score"]
                )
                selected.append(candidates[best_idx])

        # Sort selected by total_score
        selected.sort(key=lambda x: x["total_score"], reverse=True)
        return selected[:n_recipes]

    except Exception:
        # Fallback to simple selection
        return candidates[:n_recipes]
