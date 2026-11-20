/** 与后端契约对应的类型定义。归属：A 组，字段变更需同步 文档/05。 */

/** 库存状态。 */
export type ExpiryStatus = 'normal' | 'expiring' | 'expired'

/** 库存批次。 */
export interface InventoryItem {
  id: string
  display_name: string
  quantity: string
  unit: string
  category?: string | null
  storage_location?: string | null
  purchase_date?: string | null
  expiry_date?: string | null
}

/** 分页结果。 */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 自然语言录入草稿（文档/06 §4）。 */
export interface IngredientDraft {
  name: string
  quantity?: string | null
  unit?: string | null
  category?: string | null
  purchase_date?: string | null
  expiry_date?: string | null
  storage_location?: string | null
  uncertainties: string[]
}

/** 膳食计划（文档/06 §4）。 */
export interface MealPlan {
  id: string
  title: string
  recipes: RecipeCandidate[]
  missing_items: { name: string; quantity?: string | null; unit?: string | null }[]
  constraint_notes: string[]
  warnings: string[]
}

/** 候选菜谱。 */
export interface RecipeCandidate {
  name: string
  servings: number
  estimated_minutes: number
  ingredients: { name: string; quantity?: string | null; unit?: string | null; optional: boolean }[]
  steps: string[]
}

/** 采购条目。 */
export interface ShoppingItem {
  id: string
  display_name: string
  quantity?: string | null
  unit?: string | null
  status: 'pending' | 'purchased'
}

/** 用户饮食偏好。 */
export interface UserPreferences {
  allergens: string[]
  disliked_ingredients: string[]
  dietary_preferences: string[]
  default_servings: number
  default_budget?: string | null
  default_cooking_minutes?: number | null
}
