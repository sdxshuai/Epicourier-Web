#!/usr/bin/env python3
"""Create sample recipes in the database for testing"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Sample recipes matching actual Recipe table schema
# Columns: id, created_at, name, description, image_url, min_prep_time, green_score, updated_at, owner_id
sample_recipes = [
    {
        "id": 1,
        "name": "Grilled Chicken Breast",
        "description": "Lean protein source, perfect for muscle building",
        "image_url": "https://example.com/chicken.jpg",
        "min_prep_time": 15,
        "green_score": 85.5,
        "owner_id": 1,
    },
    {
        "id": 2,
        "name": "Greek Salad with Feta",
        "description": "Fresh vegetables with Mediterranean flavors",
        "image_url": "https://example.com/salad.jpg",
        "min_prep_time": 10,
        "green_score": 95.0,
        "owner_id": 1,
    },
    {
        "id": 3,
        "name": "Salmon with Broccoli",
        "description": "Omega-3 rich fish with nutrient-dense vegetables",
        "image_url": "https://example.com/salmon.jpg",
        "min_prep_time": 10,
        "green_score": 88.0,
        "owner_id": 1,
    },
    {
        "id": 4,
        "name": "Quinoa Bowl",
        "description": "Complete protein with whole grains",
        "image_url": "https://example.com/quinoa.jpg",
        "min_prep_time": 15,
        "green_score": 92.0,
        "owner_id": 1,
    },
    {
        "id": 5,
        "name": "Egg White Omelet",
        "description": "High protein, low fat breakfast",
        "image_url": "https://example.com/omelet.jpg",
        "min_prep_time": 10,
        "green_score": 80.0,
        "owner_id": 1,
    },
]

print("Creating sample recipes...")
for recipe in sample_recipes:
    try:
        # Try to insert, if exists ignore
        response = supabase.table("Recipe").upsert(recipe, ignore_duplicates=True).execute()
        print(f"✅ Created recipe: {recipe['name']} (ID: {recipe['id']})")
    except Exception as e:
        print(f"⚠️ Error with {recipe['name']}: {e}")

print("\n✅ Sample recipes created!")
