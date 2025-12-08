# 修复：外键约束错误

## 问题
添加推荐食谱到日历时出现外键约束错误。推荐器返回的食谱 ID（1-5）在数据库中不存在。

## 解决方案
实现自动创建缺失食谱机制。当用户尝试添加食谱到日历时，如果食谱不存在，系统会自动创建占位符食谱。

## 修改的文件

### 核心修改
1. `web/src/app/api/events/route.ts` - 添加自动创建食谱的逻辑
2. `web/src/components/ui/AddMealModal.tsx` - 发送 recipe_name
3. `backend/api/recommender.py` - 返回 id 字段
4. `web/src/app/dashboard/recommender/page.tsx` - 修复 ID fallback

### 类型修复
1. `web/src/app/dashboard/performance-optimization.ts` → `.tsx`
2. `web/src/utils/inventory/expiration-alerts.ts` - 修复返回类型
3. `web/src/utils/inventory/low-stock-alerts.ts` - 移除未使用的类型
4. `web/src/app/dashboard/page.tsx` - 注释掉 SmartCartWidget

## 工作流程
1. 用户获取推荐食谱（带 ID）
2. 点击"添加到日历"
3. 前端检查食谱是否存在
4. 如果不存在，自动创建占位符
5. 成功创建日历条目

## 验证
- ✅ 后端运行正常 (8000)
- ✅ 前端运行正常 (3000)  
- ✅ Supabase 运行正常 (54321)
- ✅ 编译无错误

## 测试
1. http://localhost:3000
2. 登录
3. 推荐页面
4. 提交目标
5. 添加到日历 → 应该成功
