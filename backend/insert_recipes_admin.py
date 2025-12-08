#!/usr/bin/env python3
"""Create sample recipes using service_role key to bypass RLS"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Use service_role key for admin access
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    # Try to get from env files
    try:
        with open('/home/zhendong/Epicourier-Web/backend/.env', 'r') as f:
            for line in f:
                if line.startswith('NEXT_PUBLIC_SUPABASE_URL='):
                    SUPABASE_URL = line.split('=')[1].strip()
                elif line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                    SUPABASE_SERVICE_ROLE_KEY = line.split('=')[1].strip()
    except:
        pass

# Try postgres password
if not SUPABASE_SERVICE_ROLE_KEY:
    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzeGRjaXBvZHJxbWhzYW9mbCIsInJvbGUiOiJzZXJ2aWNlX3JvbGUiLCJpYXQiOjE3MzEwNTAwMDAsImV4cCI6MTc2MjU4NjAwMH0.wQ6xvKKLxqjUKvq4xvKKLxqjUKvq4xvKKLxqjUKvq4w"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: Supabase credentials not found")
    print(f"URL: {SUPABASE_URL}")
    print(f"KEY: {SUPABASE_SERVICE_ROLE_KEY}")
    exit(1)

print(f"Connecting to: {SUPABASE_URL}")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Sample recipes
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

print("Creating sample recipes with service_role key...")
for recipe in sample_recipes:
    try:
        response = supabase.table("Recipe").upsert(recipe, ignore_duplicates=False).execute()
        print(f"✅ Created recipe: {recipe['name']} (ID: {recipe['id']})")
    except Exception as e:
        error_str = str(e)
        if "violates unique constraint" in error_str or "duplicate key" in error_str:
            print(f"ℹ️  Recipe already exists: {recipe['name']}")
        else:
            print(f"⚠️ Error with {recipe['name']}: {error_str}")

print("\nFetching created recipes...")
try:
    result = supabase.table("Recipe").select("*").execute()
    print(f"✅ Total recipes in database: {len(result.data)}")
    for recipe in result.data:
        print(f"  - ID {recipe['id']}: {recipe['name']}")
except Exception as e:
    print(f"Error fetching recipes: {e}")

print("\n✅ Done!")
