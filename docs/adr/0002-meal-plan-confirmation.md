# ADR 0002：膳食计划确认与库存扣减契约

- 状态：已采纳
- 日期：2026-11-20
- 范围：第四阶段 B（后端 / 数据）

## 背景

05 文档定义的确认接口以 `inventory_item_id` 定位扣减对象，但一个库存批次可能被多个菜品的用料行共用。仅凭 `inventory_item_id` 无法区分应该修改哪一行 `meal_plan_ingredients`，也无法保证同一批次只扣一次。

## 决策

### 1. 请求体新增 `meal_plan_ingredient_id`

```json
{
  "items": [
    {
      "meal_plan_ingredient_id": "UUID",
      "inventory_item_id": "UUID",
      "actual_quantity": "2.000",
      "unit": "个"
    }
  ]
}
```

- `meal_plan_ingredient_id` 必须属于路径中的计划，否则 400
- `inventory_item_id` 必须与该用料记录当前绑定的批次一致，否则 400
- 同一 `meal_plan_ingredient_id` 在一次请求中不得重复，否则 400
- 同一 `inventory_item_id` 可出现在多行，服务端按批次汇总后只扣一次

### 2. 扣减与流水

- 按 `inventory_item_id` 汇总 `actual_quantity`
- 每个批次只锁一次，锁定顺序按 `inventory_item_id` 升序
- 每个批次只更新一次 `quantity` / `version`
- 每个批次只写一条 `inventory_transactions`，`delta_quantity` 为汇总后的负值
- 同一次确认产生的所有流水共享 `operation_id = meal_plan_confirmations.id`

### 3. `source_type` 由服务端推导

客户端不得传入。取值来源 `meal_plans.ai_provider`：

| `ai_provider` | `source_type` |
|---|---|
| `manual` | `manual` |
| `import` | `import` |
| 其他（模型名） | `ai` |

> 这是在不新增字段前提下对「计划来源」的约定，需要在 05 文档中同步说明。

### 4. 幂等

- `request_hash` = SHA256(规范化 JSON)，包含 `meal_plan_id` 与排序后的 items，
  数量统一 quantize 到三位小数后再取字符串
- 幂等检查在计划状态检查之前，保证成功后的重试能拿到首次结果而非 409
- 同 Key 不同内容 → 409；不同 Key 确认已 confirmed 计划 → 409
- `result_snapshot` 只存业务结果，不含 `idempotent_replay` 等易变字段

### 5. 缺失与单位

- 未出现在请求中的用料：`actual_quantity = NULL`、`is_missing = true`
- 部分满足：记录实际用量，`is_missing = true`
- 达到或超过 `required_quantity`：`is_missing = false`
- 缺失食材不自动写入 `shopping_items`
- MVP 不做单位换算，请求单位必须同时等于用料单位与库存单位，否则 400

## 影响

- **前端（A）**：确认页必须提交 `meal_plan_ingredient_id`
- **AI（C）**：候选计划输出必须为每个用料生成稳定 id 并绑定 `inventory_item_id`
- **数据库**：无结构变更，复用现有 12 张表
- **权限**：应用账号对 `inventory_transactions` 仅有 SELECT / INSERT

## 未采纳的方案

- 仅用 `inventory_item_id` 定位：无法处理共享批次与多行映射
- 客户端传 `source_type`：不可信
- 单位自动换算：缺少权威换算表，MVP 不做
