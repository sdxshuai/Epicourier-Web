#!/bin/bash

# 快速创建所有 5 个 PR 的脚本
# 使用 GitHub CLI (gh) 自动创建 PR

set -e

echo "========================================="
echo "创建 5 个新 Sprint Task PR"
echo "========================================="
echo ""

# 检查 gh 是否安装
if ! command -v gh &> /dev/null; then
    echo "❌ 错误: 未安装 GitHub CLI"
    echo "请先安装: https://cli.github.com"
    exit 1
fi

# 检查认证
if ! gh auth status &> /dev/null; then
    echo "❌ 错误: 未认证 GitHub"
    echo "请运行: gh auth login"
    exit 1
fi

REPO="sdxshuai/Epicourier-Web"
BASE="main"

echo "📚 目标仓库: $REPO"
echo "🎯 基分支: $BASE"
echo ""

# PR #111
echo "创建 PR #111: Dashboard Smart Cart Widget..."
gh pr create \
  --repo "$REPO" \
  --title "feat: #111 - Dashboard Smart Cart Widget" \
  --body "## 描述
实现完整的 Smart Cart 仪表板小部件，提供实时库存概览。

## 功能
- ✅ 实时库存状态概览（总项目数）
- ✅ 快速过期提醒（按紧急程度编码：关键/警告/信息）
- ✅ 购物清单摘要（挂起的列表）
- ✅ 低库存指示器
- ✅ 快速操作按钮
- ✅ 响应式设计（移动/平板/桌面）
- ✅ Neo-Brutalism UI 设计

## 技术
- React 19 with Hooks
- Tailwind CSS 4.1
- Lucide React 图标
- useMemo 优化

## 相关 Issue
Closes #111" \
  --base "$BASE" \
  --head "feat/issue-111-dashboard-widget" \
  --draft=false

# PR #112
echo "创建 PR #112: Shopping List Transfer..."
gh pr create \
  --repo "$REPO" \
  --title "feat: #112 - Shopping List to Inventory Transfer" \
  --body "## 描述
实现购物清单到库存的自动转移工作流。

## 功能
- ✅ 批量转移已勾选的项目
- ✅ 基于类别的过期日期自动计算
- ✅ 智能位置分配（冰箱/冷柜/食品储藏室）
- ✅ 撤销功能
- ✅ 转移历史跟踪

## 数据库
- 新表: shopping_list_transfers
- RLS 策略: 用户隔离
- 自动清理: 30 天前的记录

## 相关 Issue
Closes #112" \
  --base "$BASE" \
  --head "feat/issue-112-shopping-transfer" \
  --draft=false

# PR #113
echo "创建 PR #113: Performance Optimization..."
gh pr create \
  --repo "$REPO" \
  --title "feat: #113 - Advanced Performance Optimization" \
  --body "## 描述
高级性能优化，目标减少 40% 包大小，改进 50% FCP。

## 功能
- ✅ 智能缓存策略 (5-30 分钟 TTL)
- ✅ 虚拟化列表 (100+ 项目)
- ✅ 代码分割和懒加载
- ✅ 图片优化 (LQIP)
- ✅ 内存监控

## 性能目标
- FCP: < 2.5s
- LCP: < 4.5s
- TTI: < 3.5s
- Bundle: < 200KB

## 相关 Issue
Closes #113" \
  --base "$BASE" \
  --head "feat/issue-113-performance-optimization" \
  --draft=false

# PR #114
echo "创建 PR #114: E2E Tests..."
gh pr create \
  --repo "$REPO" \
  --title "feat: #114 - E2E Smart Cart Tests" \
  --body "## 描述
40+ 综合端到端测试覆盖整个 Smart Cart 工作流。

## 测试套件
- 库存管理 (CRUD、过滤、过期)
- 购物清单 (创建、项目管理、转移)
- 过期警报 (紧急程度、聚合)
- 分析和指标
- 性能 (大列表、缓存)
- 数据持久化

## 覆盖范围
- 40+ 测试用例
- 所有主要功能
- 边界情况处理

## 相关 Issue
Closes #114" \
  --base "$BASE" \
  --head "feat/issue-114-e2e-tests" \
  --draft=false

# PR #115
echo "创建 PR #115: Cart Analytics..."
gh pr create \
  --repo "$REPO" \
  --title "feat: #115 - Cart Analytics & Insights Dashboard" \
  --body "## 描述
完整的购物车分析和洞察仪表板。

## 功能
- ✅ 支出分析和投影
- ✅ 食物浪费追踪
- ✅ 购物模式分析
- ✅ 每餐成本计算
- ✅ 存储效率指标
- ✅ AI 支持的建议
- ✅ 历史数据可视化

## 指标
- 库存总值
- 月度支出
- 浪费百分比
- 过期率
- 购物频率
- 每餐成本
- 存储效率

## 相关 Issue
Closes #115" \
  --base "$BASE" \
  --head "feat/issue-115-cart-analytics" \
  --draft=false

echo ""
echo "========================================="
echo "✅ 所有 5 个 PR 已创建!"
echo "========================================="
echo ""
echo "🔗 查看 PR:"
echo "   https://github.com/$REPO/pulls"
echo ""
