# 数据集构建完全指南

## 📊 数据集构建流程概述

Epicourier 使用 **Gemini AI** 将原始食谱数据转换为结构化格式，然后导入到 Supabase 数据库。

```
原始CSV (recipes.csv)
    ↓
Gemini 处理 (llama_recipe_pipeline.py)
    ↓
缓存的 JSON 文件 (cache/)
    ↓
转换为 CSV (cache_to_csv.py)
    ↓
导入到 Supabase (import_to_supabase.py)
    ↓
数据库中的表 (Recipe, Ingredient, Tags 等)
```

---

## 🔧 前置准备

### 1. 获取源数据
下载食谱数据：
```bash
# 访问 gist 链接获取 recipes.csv
https://gist.github.com/SeojinSeojin/e09119e728826ff07e5f9ba4d39a4648
```

将 `recipes.csv` 放在 `/data` 目录下。

### 2. 配置 Gemini API
```bash
cd /home/zhendong/Epicourier-Web/data

# 创建 .env 文件
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 3. 安装依赖
```bash
cd /home/zhendong/Epicourier-Web/data
uv pip install -r requirements.txt
```

---

## 📝 数据流处理详解

### 阶段 1: 原始数据结构

**输入文件**: `recipes.csv`
```
idMeal | strMeal | strCategory | strArea | strTags | strInstructions | strMealThumb | strSource | strYoutube | strIngredient1-20 | strMeasure1-20
52768  | Arrabiata | Pasta | Italian | ... | Cook pasta... | [image] | ... | ... | Tomato, Garlic... | 400g, 4 cloves...
```

### 阶段 2: AI 处理 (Gemini)

**脚本**: `llama_recipe_pipeline.py`

```python
# 处理流程：
1. 读取 CSV 中的每一行
2. 提取食材列表 (最多20个)
3. 使用系统提示 + 用户提示调用 Gemini
4. Gemini 返回结构化 JSON
5. 保存到 cache/{recipe_id}.json
```

**生成的 JSON 结构** (`cache/52768.json`):
```json
{
  "ingredients": [
    {
      "id": 1,
      "name": "Tomato",
      "unit": "g",
      "calories_kcal": 18,
      "protein_g": 0.88,
      "carbs_g": 3.89,
      "sugars_g": 2.63,
      "agg_fats_g": 0.2,
      "cholesterol_mg": 0,
      "agg_minerals_mg": 12,
      "vit_a_microg": 42,
      "agg_vit_b_mg": 0.037,
      "vit_c_mg": 12.7,
      "vit_d_microg": 0,
      "vit_e_mg": 0.54,
      "vit_k_microg": 7.9
    }
  ],
  "recipe": {
    "id": 52768,
    "name": "Arrabiata",
    "description": "Classic Italian pasta...",
    "min_prep_time": 20,
    "green_score": 85,
    "image_url": "https://..."
  },
  "map": [
    {
      "id": 1,
      "recipe_id": 52768,
      "ingredient_id": 1,
      "relative_unit_100": 100
    }
  ]
}
```

**关键特性**:
- 自动缓存: 已处理的食谱不会重新处理
- 错误处理: JSON 解析失败时保存原始响应
- 重试机制: 3次重试后才放弃

### 阶段 3: 转换为 CSV 格式

**脚本**: `cache_to_csv.py`

将所有 JSON 文件合并为 5 个 CSV 文件:

#### 1️⃣ `ingredients-supabase.csv`
```
id | name | unit | calories_kcal | protein_g | ... | vit_k_microg
1  | Tomato | g | 18 | 0.88 | ... | 7.9
2  | Garlic | clove | 149 | 6.63 | ... | 1.7
```

#### 2️⃣ `recipes-supabase.csv`
```
id | name | description | min_prep_time | green_score | image_url
52768 | Arrabiata | Classic Italian... | 20 | 85 | https://...
52769 | Pad Thai | Thai stir-fry... | 15 | 78 | https://...
```

#### 3️⃣ `recipe_ingredient_map-supabase.csv`
```
id | recipe_id | ingredient_id | relative_unit_100
1  | 52768 | 1 | 400
2  | 52768 | 2 | 25
```
(映射食谱和食材的关系，以及用量比例)

#### 4️⃣ `tags-supabase.csv`
```
id | name | description
1  | Italian | Italian cuisine
2  | Pasta | Pasta dishes
3  | Vegetarian | No meat
```

#### 5️⃣ `recipe_tag_map-supabase.csv`
```
id | recipe_id | tag_id
1  | 52768 | 1
2  | 52768 | 2
3  | 52768 | 3
```

**数据聚合逻辑**:
```
- 去重食材（通过 name + unit 组合）
- 自动生成标签和食谱-标签映射
- 计算总数摘要
```

### 阶段 4: 导入到 Supabase

**脚本**: `import_to_supabase.py`

导入顺序（考虑外键约束）:
```
1. RecipeTag (tags) - 无依赖
2. Ingredient (ingredients) - 无依赖
3. Recipe (recipes) - 无依赖
4. Recipe-Ingredient_Map - 需要 Recipe 和 Ingredient
5. Recipe-Tag_Map - 需要 Recipe 和 RecipeTag
```

**导入特性**:
- 批量导入 (每次 100 行)
- 使用 `upsert` 处理重复
- 失败时逐行重试并报告错误

---

## 🚀 完整执行流程

### 第 1 步: 运行 Gemini 处理
```bash
cd /home/zhendong/Epicourier-Web/data

# 开始处理所有食谱
# 首次运行会调用 Gemini API，之后会缓存结果
python llama_recipe_pipeline.py

# 输出示例:
# ✅ Cached: 52768
# 💾 Saved: cache/52769.json
# ...
# (依赖网络速度，可能需要 30-60 分钟)
```

**检查进度**:
```bash
ls cache/ | wc -l  # 查看处理的食谱数量
```

### 第 2 步: 转换为 CSV
```bash
# 将缓存的 JSON 文件转换为 CSV 格式
python cache_to_csv.py

# 输出示例:
# ✓ ingredients-supabase.csv created (247 rows)
# ✓ recipes-supabase.csv created (50 rows)
# ✓ recipe_ingredient_map-supabase.csv created (645 rows)
# ✓ tags-supabase.csv created (35 rows)
# ✓ recipe_tag_map-supabase.csv created (92 rows)

# 摘要：
# - Unique ingredients: 247
# - Recipes: 50
# - Recipe-Ingredient mappings: 645
# - Unique tags: 35
# - Recipe-Tag mappings: 92
```

### 第 3 步: 启动 Supabase
```bash
cd /home/zhendong/Epicourier-Web

# 在另一个终端启动本地 Supabase
supabase start
# 输出: Supabase 会在 localhost:54321 启动
```

### 第 4 步: 导入到数据库
```bash
cd /home/zhendong/Epicourier-Web/data

# 导入 CSV 数据到 Supabase
python import_to_supabase.py

# 输出示例:
# 🚀 Starting Supabase data import...
# 📡 Connecting to: http://127.0.0.1:54321
#
# 📄 Processing tags-supabase.csv -> RecipeTag
#   📊 Found 35 rows
#   📥 RecipeTag: 35/35 rows imported
#   ✅ Completed: 35 rows imported to RecipeTag
#
# 📄 Processing ingredients-supabase.csv -> Ingredient
#   📊 Found 247 rows
#   📥 Ingredient: 247/247 rows imported
#   ✅ Completed: 247 rows imported to Ingredient
# ...
# 🎉 Data import completed!
```

---

## 📊 数据库最终结构

### 表关系图
```
Recipe ─┬─→ Recipe-Ingredient_Map ─→ Ingredient
        │
        └─→ Recipe-Tag_Map ─→ RecipeTag
```

### 各表字段

**Recipe**
```
id (bigint PK)
name (text)
description (text)
min_prep_time (integer)
green_score (numeric)
image_url (text)
created_at (timestamp)
```

**Ingredient**
```
id (bigint PK)
name (text)
unit (text)
calories_kcal (numeric)
protein_g (numeric)
carbs_g (numeric)
[... 其他营养字段 ...]
```

**RecipeTag**
```
id (bigint PK)
name (text)
description (text)
```

**Recipe-Ingredient_Map**
```
id (bigint PK)
recipe_id (bigint FK)
ingredient_id (bigint FK)
relative_unit_100 (numeric)
```

**Recipe-Tag_Map**
```
id (bigint PK)
recipe_id (bigint FK)
tag_id (bigint FK)
```

---

## ⚙️ 自定义配置

### 修改处理参数
编辑 `llama_recipe_pipeline.py`:
```python
MODEL_NAME = "gemini-2.0-flash-exp"  # 更改模型
CACHE_DIR = Path("cache")            # 缓存目录
CSV_FILE = "recipes.csv"             # 输入文件
```

### 修改处理数量
编辑 `cache_to_csv.py`:
```python
for json_file in sorted(json_files)[:50]:  # 只处理前50个
    # ...
```

改为:
```python
for json_file in sorted(json_files):  # 处理所有
    # ...
```

---

## 🔍 故障排查

### 问题 1: Gemini API 错误
```
[Retry 1] Gemini request failed: ...
```
**解决**: 检查 `.env` 文件中的 `GEMINI_API_KEY` 是否有效

### 问题 2: JSON 解析失败
```
⚠️ JSON parsing failed for recipe 52768
```
**解决**: Gemini 返回了非 JSON 内容，已保存原始响应到缓存

### 问题 3: Supabase 连接错误
```
❌ Error importing to Recipe: ...
```
**解决**: 
- 检查 Supabase 是否运行: `supabase start`
- 验证 `SUPABASE_URL` 和 `SUPABASE_KEY`

### 问题 4: 外键约束错误
```
violates foreign key constraint
```
**解决**: 确保导入顺序正确（参见阶段 4）

---

## 📈 性能优化

### 处理速度提升
```bash
# 使用 UV (更快的包管理器)
uv run python llama_recipe_pipeline.py

# 而不是
python llama_recipe_pipeline.py
```

### 批量导入优化
修改 `import_to_supabase.py`:
```python
import_table(supabase, table_name, data, batch_size=500)  # 增加批量大小
```

---

## ✅ 验证导入成功

### 查询数据库
```bash
# 打开 Supabase Studio
supabase studio

# 或直接查询
supabase query "SELECT COUNT(*) FROM Recipe;"
# 应该显示食谱数量
```

### 在应用中验证
1. 启动前端: `npm run dev`
2. 访问 http://localhost:3000
3. 检查推荐页面是否显示食谱

---

## 📌 总结

| 步骤 | 脚本 | 输入 | 输出 | 时间 |
|------|------|------|------|------|
| 1 | `llama_recipe_pipeline.py` | `recipes.csv` | `cache/*.json` | 30-60min |
| 2 | `cache_to_csv.py` | `cache/*.json` | `*-supabase.csv` | < 1min |
| 3 | `import_to_supabase.py` | `*-supabase.csv` | 数据库表 | 2-5min |

**完整流程总耗时**: 约 35-70 分钟 (主要取决于 Gemini API 响应速度)
