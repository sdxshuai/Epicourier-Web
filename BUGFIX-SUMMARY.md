# 外键约束错误修复总结

## 问题
用户添加推荐的食谱到日历时出现错误：
```
insert or update on table 'Calendar' violates foreign key constraint 'calendar_recipe_id_fkey'
```

## 根本原因分析
1. 后端推荐器返回样本食谱，ID 为 1-5
2. 这些 ID 在数据库的 Recipe 表中不存在
3. Calendar 表有外键约束，要求 recipe_id 必须存在于 Recipe 表中
4. 当前端尝试插入日历条目时，外键约束被违反

## 解决方案
实现自动创建缺失食谱的机制：

### 1. 前端 API 路由修改 (`web/src/app/api/events/route.ts`)
```typescript
// 在插入日历条目前检查食谱是否存在
const { data: existingRecipe } = await supabase
  .from("Recipe")
  .select("id")
  .eq("id", numericRecipeId)
  .maybeSingle();

// 如果不存在，使用认证用户的身份自动创建
if (!existingRecipe) {
  const { error: insertError } = await supabase
    .from("Recipe")
    .insert([
      {
        id: numericRecipeId,
        name: recipe_name || `Recipe ${numericRecipeId}`,
        description: `Auto-created from meal recommendation`,
        image_url: null,
        min_prep_time: 30,
        green_score: 75.0,
        owner_id: publicUserId,
      },
    ]);
}
```

### 2. 组件修改
- **AddMealModal**: 现在发送 `recipe_name` 到 API
- **Recommender Page**: 正确传递食谱名称和 ID fallback 逻辑

### 3. 后端修改
- **recommender.py**: 确保返回食谱的 `id` 字段
- **index.py**: 添加食谱可用性验证

## 工作流程
1. 用户请求推荐meals
2. 后端返回样本食谱（带 ID 和名称）
3. 用户选择食谱并点击"添加到日历"
4. 前端发送请求到 `/api/events`
5. API 检查食谱是否存在
6. 如果不存在，自动创建占位符食谱
7. 创建日历条目
8. 返回成功响应

## 额外修复
- 修复 SmartCartWidget 导入错误
- 修复 TypeScript 类型错误
- 重命名文件以修复 JSX/TSX 扩展名问题
- 修复未使用变量的 ESLint 警告

## 验证
所有服务已启动并运行：
- ✅ 后端 (localhost:8000)
- ✅ 前端 (localhost:3000)
- ✅ Supabase (localhost:54321)

## 测试步骤
1. 打开 http://localhost:3000
2. 登录/注册
3. 导航到"Personalized Meal Recommendations"
4. 输入目标（如"High protein diet"）
5. 点击"Get My Daily Plan"
6. 点击"+ Add to Calendar"
7. 选择日期和餐型
8. 确认 - 应该成功添加到日历，无外键错误
