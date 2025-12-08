# 📚 数据集构建文档索引

## 🎯 快速导航

根据你的需要选择合适的文档:

### 🚀 想快速开始?
→ **[QUICK-START.md](QUICK-START.md)**
- 3 步快速启动
- 常见问题解答
- 性能参数参考

### 📊 想了解完整细节?
→ **[DATA-PIPELINE-GUIDE.md](DATA-PIPELINE-GUIDE.md)**
- 4 个处理阶段详解
- 数据转换逻辑
- 完整执行流程
- 故障排查指南

### 🏗️ 想理解架构?
→ **[ARCHITECTURE.md](ARCHITECTURE.md)**
- 可视化数据流图
- 数据库关系模型
- 缓存机制
- 性能指标分析

### 💻 想立即运行?
```bash
# 使用自动化脚本 (推荐)
./build_dataset.sh

# 或分步运行:
python llama_recipe_pipeline.py    # Gemini 处理
python cache_to_csv.py             # CSV 转换
python import_to_supabase.py       # 数据库导入
```

---

## 📁 文件结构

```
data/
├─ build_dataset.sh                 # 🤖 一键执行脚本
├─ QUICK-START.md                   # ⚡ 快速参考
├─ DATA-PIPELINE-GUIDE.md           # 📖 完整指南
├─ ARCHITECTURE.md                  # 🏗️  架构图解
│
├─ llama_recipe_pipeline.py         # 第1步: Gemini 处理
├─ cache_to_csv.py                  # 第2步: CSV 转换
├─ import_to_supabase.py            # 第3步: 数据库导入
│
├─ recipes.csv                      # 输入: 原始食谱数据
├─ cache/                           # 中间: JSON 缓存
│  └─ *.json                        # 结构化食谱数据
├─ *-supabase.csv                   # 输出: 5 个 CSV 文件
│
├─ prompts/
│  ├─ system_prompt.txt             # AI 系统提示
│  └─ user_prompt.txt               # AI 用户模板
│
├─ .env                             # 环境配置 (GEMINI_API_KEY)
├─ requirements.txt                 # Python 依赖
├─ pyproject.toml                   # 项目配置
└─ ...
```

---

## 🔄 处理流程概览

```
Step 1: Gemini Processing (30-60 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
recipes.csv 
    ↓
llama_recipe_pipeline.py
    ├─ 缓存检查
    ├─ Gemini API 调用
    └─ 保存 JSON
cache/ (50+ JSON files)

Step 2: CSV Conversion (< 1 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cache/
    ↓
cache_to_csv.py
    ├─ 合并数据
    ├─ 去重处理
    └─ 生成映射
*-supabase.csv (5 files, 1099 rows)

Step 3: Database Import (2-5 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*-supabase.csv
    ↓
import_to_supabase.py
    ├─ 批量导入
    ├─ 外键排序
    └─ 错误重试
Supabase ✅
    ├─ Recipe (50 rows)
    ├─ Ingredient (247 rows)
    ├─ RecipeTag (35 rows)
    └─ Mappings (737 rows)
```

---

## ⚙️ 环境配置

### 必需的文件

1. **recipes.csv** (原始数据)
   ```bash
   # 从 gist 下载
   https://gist.github.com/SeojinSeojin/e09119e728826ff07e5f9ba4d39a4648
   ```

2. **.env** (API 密钥)
   ```bash
   echo "GEMINI_API_KEY=your_key_here" > .env
   ```

3. **prompts/** (AI 提示)
   ```
   prompts/
   ├─ system_prompt.txt
   └─ user_prompt.txt
   ```

### Python 依赖
```bash
pip install -r requirements.txt
# 或使用 UV (更快):
uv pip install -r requirements.txt
```

---

## 📊 输出数据统计

处理完 50 个食谱后:

| 资源 | 数量 | CSV 文件 |
|------|------|---------|
| 食谱 | 50 | recipes-supabase.csv |
| 食材 | 247 | ingredients-supabase.csv |
| 标签 | 35 | tags-supabase.csv |
| 食谱-食材映射 | 645 | recipe_ingredient_map-supabase.csv |
| 食谱-标签映射 | 92 | recipe_tag_map-supabase.csv |
| **总行数** | **1099** | |

---

## 🎓 学习路径

### 初学者 (想快速尝试)
1. 阅读 [QUICK-START.md](QUICK-START.md) - 5 分钟
2. 运行 `./build_dataset.sh` - 40 分钟
3. 在应用中验证数据 - 5 分钟

### 中级 (想理解工作原理)
1. 阅读 [DATA-PIPELINE-GUIDE.md](DATA-PIPELINE-GUIDE.md) - 15 分钟
2. 查看脚本代码 - 15 分钟
3. 分步运行脚本 - 观察输出

### 高级 (想修改或优化)
1. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) - 理解设计
2. 修改提示文件 - 调整 AI 输出
3. 调整参数 - 优化性能
4. 自定义脚本 - 实现新功能

---

## 🔍 常见问题

### Q: 处理需要多长时间?
**A:** 
- 首次运行: 35-70 分钟 (主要等待 Gemini API)
- 增量运行: < 5 分钟 (有缓存)

### Q: 可以中途停止吗?
**A:** 
- 第1步: 已处理的食谱缓存到 `cache/`，可随时继续
- 第2步: 只处理 `cache/` 中的文件，重新运行即可
- 第3步: 已导入的数据不会重复 (upsert 机制)

### Q: 如何只处理部分食谱?
**A:** 
编辑 `cache_to_csv.py`:
```python
for json_file in sorted(json_files)[:10]:  # 只处理前 10 个
```

### Q: 如何增加新食谱?
**A:** 
1. 将新食谱添加到 `recipes.csv`
2. 运行 `python llama_recipe_pipeline.py` (自动只处理新的)
3. 运行 `python cache_to_csv.py` 和 `python import_to_supabase.py`

### Q: 出错了怎么办?
**A:** 查看 [DATA-PIPELINE-GUIDE.md](DATA-PIPELINE-GUIDE.md) 的故障排查部分

---

## 🚀 Next Steps

完成数据导入后:

1. **启动后端服务**
   ```bash
   cd ../backend
   uv run uvicorn api.index:app --reload
   ```

2. **启动前端应用**
   ```bash
   cd ../web
   npm run dev
   ```

3. **访问应用**
   ```
   http://localhost:3000
   ```

4. **测试推荐系统**
   - 导航到 "Personalized Meal Recommendations"
   - 输入目标 (如 "High protein diet")
   - 查看推荐的食谱

---

## 📞 技术支持

遇到问题?

1. 检查 **[QUICK-START.md](QUICK-START.md)** 中的常见问题
2. 查看 **[DATA-PIPELINE-GUIDE.md](DATA-PIPELINE-GUIDE.md)** 的故障排查
3. 查看日志输出 (每个脚本都有详细的输出信息)
4. 检查 `.env` 和文件权限

---

## 📈 性能优化

### 加速处理

1. **使用 UV 代替 pip**
   ```bash
   uv run python llama_recipe_pipeline.py  # 快 2-3 倍
   ```

2. **增加批量导入大小**
   编辑 `import_to_supabase.py`:
   ```python
   import_table(supabase, table_name, data, batch_size=500)
   ```

3. **并行处理 (高级)**
   修改 Gemini 处理脚本以支持并发调用

---

## 📚 相关资源

- Gemini API: https://ai.google.dev/
- Supabase: https://supabase.com/
- Python csv: https://docs.python.org/3/library/csv.html

---

**更新时间**: 2024-12-06
**版本**: 1.0
**作者**: Epicourier Team
