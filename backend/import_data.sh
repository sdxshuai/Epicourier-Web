#!/bin/bash
# Import CSV data directly using psql

echo "Connecting to local Supabase database..."

# 禁用 RLS 临时导入数据
psql -h 127.0.0.1 -U postgres -d postgres <<EOF
-- Disable RLS temporarily
ALTER TABLE public."Ingredient" DISABLE ROW LEVEL SECURITY;
ALTER TABLE public."RecipeTag" DISABLE ROW LEVEL SECURITY;
ALTER TABLE public."Recipe" DISABLE ROW LEVEL SECURITY;
ALTER TABLE public."Recipe-Ingredient_Map" DISABLE ROW LEVEL SECURITY;
ALTER TABLE public."Recipe-Tag_Map" DISABLE ROW LEVEL SECURITY;

-- Import data from CSV files
\COPY public."Ingredient"(id, created_at, name, category, nutritional_info) FROM '/home/zhendong/Epicourier-Web/backend/dataset/ingredients-supabase.csv' CSV HEADER;
\COPY public."RecipeTag"(id, created_at, name, description) FROM '/home/zhendong/Epicourier-Web/backend/dataset/tags-supabase.csv' CSV HEADER;
\COPY public."Recipe"(id, created_at, name, description, prep_time, cook_time, servings, difficulty_level, recipe_text) FROM '/home/zhendong/Epicourier-Web/backend/dataset/recipes-supabase.csv' CSV HEADER;
\COPY public."Recipe-Ingredient_Map"(id, created_at, recipe_id, ingredient_id, quantity, unit) FROM '/home/zhendong/Epicourier-Web/backend/dataset/recipe_ingredient_map-supabase.csv' CSV HEADER;
\COPY public."Recipe-Tag_Map"(id, created_at, recipe_id, tag_id) FROM '/home/zhendong/Epicourier-Web/backend/dataset/recipe_tag_map-supabase.csv' CSV HEADER;

-- Re-enable RLS
ALTER TABLE public."Ingredient" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."RecipeTag" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."Recipe" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."Recipe-Ingredient_Map" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."Recipe-Tag_Map" ENABLE ROW LEVEL SECURITY;

SELECT 'Data import complete!' as status;
EOF
