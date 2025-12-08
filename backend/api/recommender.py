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
    try:
        supabase = load_supabase()

        # Load all tables
        print("Loading Recipe...")
        recipes_raw = supabase.table("Recipe").select("*").execute().data
        print(f"Loaded {len(recipes_raw)} recipes")
        
        # If no recipes, return empty dataframe (will be handled by API)
        if not recipes_raw:
            print("WARNING: No recipes found in database. Returning empty data.")
            return pd.DataFrame()
        
        recipes = pd.DataFrame(recipes_raw)
        
        print("Loading Ingredient...")
        ingredients_raw = supabase.table("Ingredient").select("*").execute().data
        print(f"Loaded {len(ingredients_raw)} ingredients")
        ingredients = pd.DataFrame(ingredients_raw) if ingredients_raw else pd.DataFrame()
        
        print("Loading Recipe-Ingredient_Map...")
        recipe_ing_map_raw = supabase.table("Recipe-Ingredient_Map").select("*").execute().data
        print(f"Loaded {len(recipe_ing_map_raw)} recipe-ingredient mappings")
        recipe_ing_map = pd.DataFrame(recipe_ing_map_raw) if recipe_ing_map_raw else pd.DataFrame()
        
        print("Loading RecipeTag...")
        tags_raw = supabase.table("RecipeTag").select("*").execute().data
        print(f"Loaded {len(tags_raw)} tags")
        tags = pd.DataFrame(tags_raw) if tags_raw else pd.DataFrame()
        
        print("Loading Recipe-Tag_Map...")
        recipe_tag_map_raw = supabase.table("Recipe-Tag_Map").select("*").execute().data
        print(f"Loaded {len(recipe_tag_map_raw)} recipe-tag mappings")
        recipe_tag_map = pd.DataFrame(recipe_tag_map_raw) if recipe_tag_map_raw else pd.DataFrame()

        # Merge metadata
        if not recipe_tag_map.empty and not tags.empty:
            recipe_tags = recipe_tag_map.merge(
                tags, left_on="tag_id", right_on="id", suffixes=("", "_tag")
            )
            recipe_tags = (
                recipe_tags.groupby("recipe_id")["name"].apply(list).reset_index(name="tags")
            )
        else:
            recipe_tags = recipes[["id"]].rename(columns={"id": "recipe_id"})
            recipe_tags["tags"] = [[]] * len(recipe_tags)

        if not recipe_ing_map.empty and not ingredients.empty:
            recipe_ing = recipe_ing_map.merge(
                ingredients, left_on="ingredient_id", right_on="id", suffixes=("", "_ing")
            )
            recipe_ing = (
                recipe_ing.groupby("recipe_id")["name"]
                .apply(list)
                .reset_index(name="ingredients")
            )
        else:
            recipe_ing = recipes[["id"]].rename(columns={"id": "recipe_id"})
            recipe_ing["ingredients"] = [[]] * len(recipe_ing)
        else:
            recipe_ing = recipes[["id"]].rename(columns={"id": "recipe_id"})
            recipe_ing["ingredients"] = [[]] * len(recipe_ing)

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
        print(f"Successfully loaded {len(recipe_data)} recipes")
        return recipe_data
    except Exception as e:
        print(f"ERROR loading recipe data: {e}")
        print("Falling back to sample data...")
        import traceback
        traceback.print_exc()
        return create_sample_recipe_data()


def create_sample_recipe_data():
    """Create sample recipe data for testing when database is empty."""
    sample_recipes = [
        {
            "id": 1,
            "name": "Grilled Chicken Breast",
            "description": "Lean protein source, perfect for muscle building",
            "recipe_text": "Season chicken breasts with herbs. Grill for 6-7 minutes per side at medium-high heat until internal temp reaches 165F.",
            "tags": ["protein", "low-fat", "healthy"],
            "ingredients": ["chicken breast", "olive oil", "lemon", "garlic", "herbs"],
            "similarity": 0.95
        },
        {
            "id": 2,
            "name": "Greek Salad with Feta",
            "description": "Fresh vegetables with Mediterranean flavors, low calorie",
            "recipe_text": "Combine tomatoes, cucumbers, olives, and feta cheese. Dress with olive oil and vinegar.",
            "tags": ["vegetable", "low-calorie", "healthy"],
            "ingredients": ["tomatoes", "cucumber", "olives", "feta cheese", "olive oil"],
            "similarity": 0.92
        },
        {
            "id": 3,
            "name": "Salmon with Broccoli",
            "description": "Omega-3 rich fish with nutrient-dense vegetables",
            "recipe_text": "Bake salmon at 400F for 12-15 minutes. Steam broccoli and serve alongside.",
            "tags": ["protein", "omega-3", "healthy"],
            "ingredients": ["salmon", "broccoli", "lemon", "olive oil", "garlic"],
            "similarity": 0.90
        },
        {
            "id": 4,
            "name": "Quinoa Bowl",
            "description": "Complete protein with whole grains and vegetables",
            "recipe_text": "Cook quinoa according to package. Top with roasted vegetables and chickpeas.",
            "tags": ["vegetarian", "complete-protein", "healthy"],
            "ingredients": ["quinoa", "chickpeas", "vegetables", "tahini", "lemon"],
            "similarity": 0.88
        },
        {
            "id": 5,
            "name": "Egg White Omelet",
            "description": "High protein, low fat breakfast option",
            "recipe_text": "Whisk egg whites with vegetables. Cook in non-stick pan with minimal oil.",
            "tags": ["protein", "low-fat", "breakfast"],
            "ingredients": ["egg whites", "vegetables", "olive oil", "herbs", "salt"],
            "similarity": 0.85
        },
    ]
    return pd.DataFrame(sample_recipes)


@lru_cache()
def load_embedder():
    print("Loading sentence-transformer model ...")
    return SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)


@lru_cache()
def load_gemini_client():
    print("Initializing Gemini client ...")
    if not GEMINI_KEY or GEMINI_KEY == "your_gemini_api_key":
        print("WARNING: GEMINI_KEY not set. Gemini features will be unavailable.")
        return None
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
    if not client:
        return "Using default nutritional targets based on your goal."
    
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
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Warning: Gemini API error: {e}")
        return "Using default nutritional targets based on your goal."


def expand_goal(goal_text):
    """Translate a user's goal into nutrition information using Gemini."""
    client = load_gemini_client()
    if not client:
        return "Meal plan personalized for your goal: " + goal_text

    prompt = (
        "Your task is to translate a user's specific diet goal into precise, "
        "target nutritional values for a daily meal plan.\n\n"
        f"**GOAL:** {goal_text}\n\n"
        "You may include: calories_kcal, protein_g, carbs_g, sugars_g, total_fats_g, "
        "cholesterol_mg, total_minerals_mg, vit_a_microg, total_vit_b_mg, "
        "vit_c_mg, vit_d_microg, vit_e_mg, vit_k_microg"
    )

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Warning: Gemini API error: {e}")
        return "Meal plan personalized for your goal: " + goal_text


# --------------------------------------------------
# 5. Recommendation pipeline
# --------------------------------------------------
def rank_recipes_by_goal(goal_text, top_k=20):
    try:
        print(f"Ranking recipes for goal: {goal_text}")
        recipe_data = load_recipe_data()
        print(f"Loaded {len(recipe_data)} recipes")
        
        # Check if we have any recipes
        if recipe_data.empty:
            print("WARNING: No recipe data available")
            return pd.DataFrame(), "No recipes available"
        
        recipe_embeddings = get_recipe_embeddings(recipe_data)
        embedder = load_embedder()

        nutri_goal = nutrition_goal(goal_text)
        goal_embedding = embedder.encode(nutri_goal, convert_to_tensor=True)
        scores = util.cos_sim(goal_embedding, recipe_embeddings)[0].cpu().numpy()

        recipe_data = recipe_data.copy()
        recipe_data["similarity"] = scores
        ranked = recipe_data.sort_values(by="similarity", ascending=False).head(top_k)
        print(f"Ranked {len(ranked)} top recipes")
        return ranked, nutri_goal
    except Exception as e:
        print(f"ERROR in rank_recipes_by_goal: {e}")
        import traceback
        traceback.print_exc()
        raise


def select_diverse_recipes(ranked_df, n_meals=3):
    """Cluster embeddings to ensure diversity among top recipes."""
    try:
        print(f"Selecting {n_meals} diverse recipes from {len(ranked_df)} candidates")
        embedder = load_embedder()
        n_clusters = min(n_meals, len(ranked_df))
        if len(ranked_df) <= n_meals:
            print(f"Only {len(ranked_df)} recipes available, returning all")
            return ranked_df

        sub_embeds = embedder.encode(ranked_df["recipe_text"].tolist())
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        cluster_labels = kmeans.fit_predict(sub_embeds)

        selected_indices = []
        for c in range(n_clusters):
            cluster_recipes = ranked_df[cluster_labels == c]
            top_one = cluster_recipes.sort_values("similarity", ascending=False).head(1)
            selected_indices.append(top_one.index[0])
        result = ranked_df.loc[selected_indices].sort_values("similarity", ascending=False)
        print(f"Selected {len(result)} diverse recipes")
        return result
    except Exception as e:
        print(f"ERROR in select_diverse_recipes: {e}")
        import traceback
        traceback.print_exc()
        raise


# CREATE MEAL PLAN
def create_meal_plan(goal_text, n_meals=3):
    try:
        print(f"\n=== Creating meal plan for: {goal_text} (n_meals={n_meals}) ===")
        ranked, nutri_goal = rank_recipes_by_goal(goal_text)
        diverse = select_diverse_recipes(ranked, n_meals)
        exp_goal = expand_goal(goal_text)

        meal_plan = []
        for i, row in enumerate(diverse.itertuples(), 1):
            meal_plan.append(
                {
                    "id": int(row.id) if hasattr(row, 'id') and row.id else i,  # Use recipe ID or fallback to meal_number
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

        print(f"Successfully created meal plan with {len(meal_plan)} meals\n")
        return meal_plan, exp_goal
    except Exception as e:
        print(f"ERROR in create_meal_plan: {e}")
        import traceback
        traceback.print_exc()
        raise
