# 数据集构建快速参考

## 🎯 3 步快速开始

```bash
# 步骤 1: 准备环境
cd /home/zhendong/Epicourier-Web/data

# 确保有以下文件:
# ✅ recipes.csv (原始食谱数据)
# ✅ .env (包含 GEMINI_API_KEY)
# ✅ prompts/ (system_prompt.txt 和 user_prompt.txt)

# 步骤 2: 运行完整流程
./build_dataset.sh

# 或分步运行:
python llama_recipe_pipeline.py    # Gemini 处理 (30-60 min)
python cache_to_csv.py             # 转换为 CSV (< 1 min)
python import_to_supabase.py       # 导入数据库 (2-5 min)
```

---

## 📊 数据流概览

```
步骤 1: Gemini 处理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
recipes.csv (原始 CSV)
  ↓ 读取每一行
  ↓ 提取食材和信息
  ↓ 调用 Gemini API
  ↓ 返回结构化 JSON
  ↓ 保存到 cache/
cache/ (JSON 缓存)
  └─ 52768.json (食谱 ID)
  └─ 52769.json
  └─ ...

步骤 2: 转换格式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cache/ (所有 JSON 文件)
  ↓ 合并所有数据
  ↓ 去重食材
  ↓ 生成关联映射
  ↓ 输出 CSV 格式
CSV 文件:
  ├─ ingredients-supabase.csv (247 行)
  ├─ recipes-supabase.csv (50 行)
  ├─ recipe_ingredient_map-supabase.csv (645 行)
  ├─ tags-supabase.csv (35 行)
  └─ recipe_tag_map-supabase.csv (92 行)

步骤 3: 数据库导入
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CSV 文件
  ↓ 按正确顺序导入
  ↓ RecipeTag ← 无依赖
  ↓ Ingredient ← 无依赖
  ↓ Recipe ← 无依赖
  ↓ Recipe-Ingredient_Map ← 需要 Recipe + Ingredient
  ↓ Recipe-Tag_Map ← 需要 Recipe + RecipeTag
Supabase 数据库
  └─ 可用于推荐系统
```

---

## 🔑 核心配置

### .env 文件
```bash
# /home/zhendong/Epicourier-Web/data/.env
GEMINI_API_KEY=your_api_key_here
```

### 提示文件结构

**system_prompt.txt**: 定义 AI 的角色和输出格式
- 告诉 Gemini 返回 JSON 格式
- 指定所需的字段

**user_prompt.txt**: 每个食谱的处理模板
- {strMeal}: 食谱名称
- {strCategory}: 分类
- {strArea}: 地区
- {strTags}: 标签
- {strInstructions}: 做法
- {ingredient_list}: 食材列表

---

## 📈 数据量参考

基于当前配置处理 50 个食谱的数据量:

| 资源 | 数量 | 备注 |
|------|------|------|
| 食谱 | 50 | 来自 CSV |
| 食材 | 247 | 去重后 |
| 映射 | 645 | 食谱-食材关系 |
| 标签 | 35 | 去重后 |
| 标签映射 | 92 | 食谱-标签关系 |

---

## ⚙️ 性能参数

### 处理速度
- Gemini 处理: ~2-4 秒/食谱
- CSV 转换: ~0.5 秒 (50 个食谱)
- 数据库导入: ~2-3 秒 (50 个食谱)

### 优化建议
```python
# 增加批量导入大小 (import_to_supabase.py)
import_table(supabase, table_name, data, batch_size=500)  # 默认 100

# 使用 UV 加速 Python 运行
uv run python llama_recipe_pipeline.py  # 比 python 快 2-3 倍
```

---

## 🔍 Gemini JSON 响应结构

Gemini 返回的每个食谱 JSON:

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
    "description": "Classic Italian pasta with tomato sauce",
    "min_prep_time": 20,
    "green_score": 85,
    "image_url": "https://..."
  },
  "map": [
    {
      "id": 1,
      "recipe_id": 52768,
      "ingredient_id": 1,
      "relative_unit_100": 400
    }
  ]
}
```

---

## 🛠️ 故障排查

### 问题: Gemini API 超时
```bash
# 增加重试次数 (llama_recipe_pipeline.py)
def query_gemini(..., max_retries=5):  # 默认 3
```

### 问题: 内存不足
```bash
# 分批处理 (cache_to_csv.py)
for json_file in sorted(json_files)[:20]:  # 先处理 20 个
```

### 问题: 导入失败
```bash
# 查看详细日志
python import_to_supabase.py 2>&1 | tee import.log

# 手动检查 CSV 格式
head recipes-supabase.csv
```

---

## ✅ 验证清单

完成后检查:

- [ ] `cache/` 目录有 50+ JSON 文件
- [ ] 5 个 CSV 文件已生成
- [ ] Supabase 中的 Recipe 表有 50+ 条记录
- [ ] Ingredient 表有 247+ 条记录
- [ ] Recipe-Ingredient_Map 有 645+ 条记录
- [ ] 前端推荐页面可以获取食谱

---

## 💡 使用建议

### 首次运行
```bash
# 只处理部分食谱测试
# 编辑 cache_to_csv.py
for json_file in sorted(json_files)[:5]:  # 只处理 5 个
```

### 完整运行
```bash
# 处理所有食谱
# 编辑 cache_to_csv.py
for json_file in sorted(json_files):  # 处理所有
```

### 增量更新
```bash
# 只处理新食谱（已缓存的会跳过）
python llama_recipe_pipeline.py  # 自动只处理新的

# 更新数据库
python cache_to_csv.py
python import_to_supabase.py
```

---

## 📞 相关文件

- 详细指南: `DATA-PIPELINE-GUIDE.md`
- 脚本脚本: `build_dataset.sh`
- 主要脚本:
  - `llama_recipe_pipeline.py` - Gemini 处理
  - `cache_to_csv.py` - CSV 转换
  - `import_to_supabase.py` - 数据库导入
