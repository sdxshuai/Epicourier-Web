#!/usr/bin/env python3
"""Import CSV data using direct PostgreSQL connection"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

# 连接到本地 PostgreSQL (Supabase)
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="postgres",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()

try:
    # 临时禁用 RLS
    print("Disabling RLS temporarily...")
    cur.execute('ALTER TABLE public."Ingredient" DISABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."RecipeTag" DISABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."Recipe" DISABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."Recipe-Ingredient_Map" DISABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."Recipe-Tag_Map" DISABLE ROW LEVEL SECURITY')
    conn.commit()

    # 导入数据
    imports = [
        ("dataset/ingredients-supabase.csv", "Ingredient", 
         ["id", "created_at", "name", "category", "nutritional_info"]),
        ("dataset/tags-supabase.csv", "RecipeTag",
         ["id", "created_at", "name", "description"]),
        ("dataset/recipes-supabase.csv", "Recipe",
         ["id", "created_at", "name", "description", "prep_time", "cook_time", "servings", "difficulty_level", "recipe_text"]),
        ("dataset/recipe_ingredient_map-supabase.csv", "Recipe-Ingredient_Map",
         ["id", "created_at", "recipe_id", "ingredient_id", "quantity", "unit"]),
        ("dataset/recipe_tag_map-supabase.csv", "Recipe-Tag_Map",
         ["id", "created_at", "recipe_id", "tag_id"]),
    ]

    for csv_file, table_name, columns in imports:
        if not os.path.exists(csv_file):
            print(f"WARNING: {csv_file} not found, skipping...")
            continue
        
        print(f"\nImporting {csv_file} to {table_name}...")
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"  Loaded {len(rows)} rows")
            
            if rows:
                # 准备数据
                values = []
                for row in rows:
                    # 按列顺序提取值，处理缺失值
                    row_values = []
                    for col in columns:
                        val = row.get(col, '')
                        # 将空字符串转换为 NULL
                        row_values.append(None if val == '' else val)
                    values.append(tuple(row_values))
                
                # 构建插入语句
                placeholders = ", ".join(["%s"] * len(columns))
                col_names = ", ".join([f'"{col}"' for col in columns])
                insert_sql = f'INSERT INTO public."{table_name}"({col_names}) VALUES %s'
                
                try:
                    execute_values(cur, insert_sql, values)
                    conn.commit()
                    print(f"  ✅ Successfully imported {len(rows)} records")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    conn.rollback()

    # 重新启用 RLS
    print("\nRe-enabling RLS...")
    cur.execute('ALTER TABLE public."Ingredient" ENABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."RecipeTag" ENABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."Recipe" ENABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."Recipe-Ingredient_Map" ENABLE ROW LEVEL SECURITY')
    cur.execute('ALTER TABLE public."Recipe-Tag_Map" ENABLE ROW LEVEL SECURITY')
    conn.commit()

    print("\n✅ Import complete!")

finally:
    cur.close()
    conn.close()
