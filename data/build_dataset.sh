#!/bin/bash

# 📊 Epicourier 数据集构建脚本
# 完整流程: CSV → Gemini AI → JSON → CSV → Supabase

set -e

cd /home/zhendong/Epicourier-Web/data

echo "==================================="
echo "🚀 Epicourier 数据集构建程序"
echo "==================================="
echo ""

# 检查前置条件
echo "📋 检查前置条件..."

if [ ! -f "recipes.csv" ]; then
    echo "❌ 错误: recipes.csv 未找到"
    echo "📥 请从以下链接下载:"
    echo "   https://gist.github.com/SeojinSeojin/e09119e728826ff07e5f9ba4d39a4648"
    exit 1
fi
echo "✅ recipes.csv 已找到"

if [ ! -f ".env" ]; then
    echo "❌ 错误: .env 文件未找到"
    echo "📝 请创建 .env 文件并配置 GEMINI_API_KEY"
    echo "   echo \"GEMINI_API_KEY=your_key\" > .env"
    exit 1
fi
echo "✅ .env 文件已找到"

if [ ! -f "prompts/system_prompt.txt" ] || [ ! -f "prompts/user_prompt.txt" ]; then
    echo "❌ 错误: 提示文件未找到"
    exit 1
fi
echo "✅ 提示文件已找到"

echo ""
echo "=== 阶段 1/3: 用 Gemini 处理食谱 ==="
echo "（这可能需要 30-60 分钟）"
echo ""

read -p "继续? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

echo "🔄 处理食谱数据..."
if command -v uv &> /dev/null; then
    uv run python llama_recipe_pipeline.py
else
    python llama_recipe_pipeline.py
fi

echo ""
echo "✅ 阶段 1 完成"
echo ""

# 检查缓存
CACHE_COUNT=$(ls cache/*.json 2>/dev/null | wc -l)
if [ $CACHE_COUNT -eq 0 ]; then
    echo "❌ 错误: 没有生成缓存文件"
    exit 1
fi
echo "📊 生成了 $CACHE_COUNT 个缓存文件"

echo ""
echo "=== 阶段 2/3: 转换为 CSV 格式 ==="
echo ""

echo "🔄 转换数据..."
if command -v uv &> /dev/null; then
    uv run python cache_to_csv.py
else
    python cache_to_csv.py
fi

echo ""
echo "✅ 阶段 2 完成"
echo ""

# 检查 CSV 文件
if [ ! -f "recipes-supabase.csv" ]; then
    echo "❌ 错误: recipes-supabase.csv 未生成"
    exit 1
fi

echo ""
echo "=== 阶段 3/3: 导入到 Supabase ==="
echo ""

# 检查 Supabase 是否运行
if ! curl -s http://localhost:54321 > /dev/null 2>&1; then
    echo "⚠️  Supabase 未运行"
    echo "📝 请在另一个终端运行:"
    echo "   cd /home/zhendong/Epicourier-Web"
    echo "   supabase start"
    echo ""
    read -p "Supabase 已启动? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 已取消"
        exit 1
    fi
fi

echo "🔄 导入数据到 Supabase..."
if command -v uv &> /dev/null; then
    uv run python import_to_supabase.py
else
    python import_to_supabase.py
fi

echo ""
echo "==================================="
echo "🎉 数据集构建完成！"
echo "==================================="
echo ""
echo "📊 数据库已成功填充"
echo ""
echo "✨ 后续步骤:"
echo "1. 启动后端: cd /home/zhendong/Epicourier-Web/backend"
echo "               uv run uvicorn api.index:app --reload"
echo ""
echo "2. 启动前端: cd /home/zhendong/Epicourier-Web/web"
echo "              npm run dev"
echo ""
echo "3. 打开应用: http://localhost:3000"
echo ""
echo "🎯 现在可以使用推荐系统了！"
echo ""
