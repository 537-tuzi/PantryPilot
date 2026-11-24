/** 与后端契约对应的类型定义。归属：A 组。后端代码为权威（schemas/），字段变更同步文档/05。 */

/** 库存/临期状态（服务端读取时派生，应用时区）。 */
export type InventoryStatus = 'normal' | 'expiring' | 'expired'
export type ExpiryStatus = InventoryStatus
export type InventoryReason = 'add' | 'adjust' | 'consume'
export type ShoppingStatus = 'pending' | 'purchased' | 'cancelled'
export type MealPlanStatus = 'draft' | 'confirmed'
export type RecipeSourceType = 'manual' | 'ai' | 'import'
export type StorageLocation = '冷藏' | '冷冻' | '常温' | '自定义'

/** 库存批次（InventoryResponse，schemas/inventory.py:64-85）。Decimal 序列化为字符串。 */
export interface InventoryItem {
  id: string
  ingredient_id: string | null
  display_name: string
  quantity: string
  unit: string
  purchase_date: string | null
  expiry_date: string | null
  storage_location: string | null
  status: InventoryStatus
  version: number
  archived_at: string | null
  created_at: string
  updated_at: string
}

/** 新增库存请求（schemas/inventory.py:14-39）。Sprint 1 省略 ingredient_id（无 catalog 端点）。 */
export interface InventoryCreateRequest {
  display_name: string
  quantity: string
  unit: string
  purchase_date?: string | null
  expiry_date?: string | null
  storage_location?: string | null
}

/** 编辑库存请求（schemas/inventory.py:42-61）。PATCH 省略键=不变，null=清空。unit/ingredient_id 不可改。 */
export interface InventoryUpdateRequest {
  expected_version: number
  display_name?: string
  quantity?: string
  purchase_date?: string | null
  expiry_date?: string | null
  storage_location?: string | null
  reason?: InventoryReason
}

/** 分页结果（InventoryListResponse / ShoppingItemListResponse）。 */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 首页统计（DashboardSummaryResponse，schemas/dashboard.py:8-12）。仅计数，过滤 qty>0+未归档。 */
export interface DashboardSummary {
  statistics_date: string
  inventory_count: number
  expiring_count: number
  expired_count: number
}

/** 用户饮食偏好（PreferenceResponse，schemas/preference.py:8-31）。budget 为 Decimal 字符串。 */
export interface UserPreferences {
  dietary_preferences: string[]
  allergens: string[]
  disliked_ingredients: string[]
  default_servings: number
  default_budget: string
  default_cooking_minutes: number
}
export type PreferencesPutRequest = UserPreferences

/** 用户信息（UserResponse，schemas/auth.py:49-57）。 */
export interface UserResponse {
  id: string
  username: string
  email: string
  is_active: boolean
}

/** 令牌响应（TokenResponse，schemas/auth.py:60-67）。登录/注册均含 user；expires_in 为秒。 */
export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserResponse
}

/** 采购条目（ShoppingItemResponse，schemas/shopping.py:32-47）。 */
export interface ShoppingItem {
  id: string
  display_name: string
  ingredient_id: string | null
  quantity: string
  unit: string
  status: ShoppingStatus
  source_meal_plan_id: string | null
  created_at: string
  updated_at: string
}
export interface ShoppingItemCreateRequest {
  display_name: string
  quantity: string
  unit: string
  ingredient_id?: string | null
}
export interface ShoppingStatusUpdateRequest {
  status: ShoppingStatus
}
export interface ShoppingImportRequest {
  meal_plan_id: string
}
export interface ShoppingImportResult {
  meal_plan_id: string
  created_count: number
  skipped_count: number
}

/* ===== Sprint 2/3 冻结契约（定义类型，本轮不实现 UI） ===== */

/** AI 录入草稿（ai/contracts.py:23-33，文档06 §4）。无 id；字段名 name。 */
export interface AiIngredientDraft {
  name: string
  quantity: string | null
  unit: string | null
  category: string | null
  purchase_date: string | null
  expiry_date: string | null
  storage_location: StorageLocation | null
  uncertainties: string[]
}

/** AI 缺失食材（ai/contracts.py:55-60）。 */
export interface AiMissingIngredient {
  name: string
  quantity: string | null
  unit: string | null
}

/** AI 候选菜谱用料（ai/contracts.py:36-42）。 */
export interface AiRecipeIngredient {
  name: string
  quantity: string | null
  unit: string | null
  optional: boolean
}

/** AI 候选菜谱（ai/contracts.py:45-52）。 */
export interface AiRecipeCandidate {
  name: string
  servings: number
  estimated_minutes: number
  ingredients: AiRecipeIngredient[]
  steps: string[]
}

/** AI 膳食计划草稿（ai/contracts.py:63-70）。无 id。 */
export interface AiMealPlanDraft {
  title: string
  recipes: AiRecipeCandidate[]
  missing_items: AiMissingIngredient[]
  constraint_notes: string[]
  warnings: string[]
}

/** 持久化菜谱（RecipeResponse，schemas/meal_plan.py:88-99）。无 steps/ingredients。 */
export interface Recipe {
  id: string
  user_id: string | null
  name: string
  description: string
  servings: number
  estimated_minutes: number
  source_type: RecipeSourceType
}

/** 计划用料行（schemas/meal_plan.py:102-119）。id 即 confirm 的 meal_plan_ingredient_id。 */
export interface MealPlanIngredientDetail {
  id: string
  inventory_item_id: string | null
  display_name: string
  required_quantity: string
  actual_quantity: string | null
  unit: string
  is_missing: boolean
}

/** 计划项（schemas/meal_plan.py:122-131）。recipe_snapshot 为 JSONB，渲染前运行时守卫。 */
export interface MealPlanItemDetail {
  id: string
  recipe_id: string | null
  recipe_snapshot: unknown
  sort_order: number
  recipe: Recipe | null
  ingredients: MealPlanIngredientDetail[]
}

/** 持久化计划详情（GET /meal-plans/{id}，schemas/meal_plan.py:134-146）。 */
export interface MealPlanDetail {
  id: string
  plan_date: string
  title: string
  request_constraints: unknown
  status: MealPlanStatus
  ai_provider: string
  confirmed_at: string | null
  created_at: string
  updated_at: string
  items: MealPlanItemDetail[]
}

/** 确认扣减项（schemas/meal_plan.py:13-27）。需头 Idempotency-Key(UUID)。 */
export interface MealPlanConfirmItem {
  meal_plan_ingredient_id: string
  inventory_item_id: string
  actual_quantity: string
  unit: string
}
export interface MealPlanConfirmRequest {
  items: MealPlanConfirmItem[]
}
export interface DeductedItem {
  inventory_item_id: string
  delta_quantity: string
  unit: string
}
export interface MealPlanMissingItem {
  meal_plan_ingredient_id: string
  display_name: string
  required_quantity: string
  actual_quantity: string | null
  unit: string
}
export interface MealPlanConfirmResult {
  meal_plan_id: string
  status: MealPlanStatus
  confirmed_at: string
  deducted: DeductedItem[]
  missing: MealPlanMissingItem[]
}