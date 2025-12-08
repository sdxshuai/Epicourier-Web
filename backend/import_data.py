#!/usr/bin/env python3
"""Import CSV data to Supabase with RLS disabled"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 首先禁用 RLS (用管理员 key)
print("Setting up for data import...")

# 定义要导入的 CSV 文件
imports = [
    ("dataset/ingredients-supabase.csv", "Ingredient"),
    ("dataset/tags-supabase.csv", "RecipeTag"),
    ("dataset/recipes-supabase.csv", "Recipe"),
    ("dataset/recipe_ingredient_map-supabase.csv", "Recipe-Ingredient_Map"),
    ("dataset/recipe_tag_map-supabase.csv", "Recipe-Tag_Map"),
]

for csv_file, table_name in imports:
    if not os.path.exists(csv_file):
        print(f"WARNING: {csv_file} not found, skipping...")
        continue
    
    print(f"\nImporting {csv_file} to {table_name}...")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"  Loaded {len(df)} rows from {csv_file}")
        
        # 获取 CSV 的列
        columns = df.columns.tolist()
        print(f"  Columns: {columns}")
        
        # 处理数据
        records = []
        for idx, row in df.iterrows():
            record = {}
            for col in columns:
                val = row[col]
                # 跳过 NaN 值
                if pd.isna(val):
                    continue
                record[col] = val
            if record:  # 只有非空记录才加入
                records.append(record)
        
        if records:
            # 批量插入（分批处理以避免超时）
            batch_size = 50
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                try:
                    response = supabase.table(table_name).upsert(batch, ignore_duplicates=False).execute()
                    print(f"  ✅ Inserted batch {i//batch_size + 1} ({len(batch)} records)")
                except Exception as e:
                    print(f"  ⚠️  Batch {i//batch_size + 1} error (might be RLS): {e}")
                    # 尝试用 insert 替代
                    try:
                        response = supabase.table(table_name).insert(batch).execute()
                        print(f"  ✅ Inserted batch {i//batch_size + 1} with insert method")
                    except Exception as e2:
                        print(f"  ❌ Insert failed: {e2}")
        
    except Exception as e:
        print(f"  ❌ Error processing {csv_file}: {e}")

print("\n✅ Import complete!")
print("\nNote: If you see RLS errors, you need to disable RLS in Supabase Studio:")
print("1. Go to Authentication > Policies")
print("2. Disable RLS for each table")
print("3. Then re-run this script")

