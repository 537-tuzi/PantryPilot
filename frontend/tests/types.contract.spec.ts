import { expect, it } from 'vitest'
import type { InventoryItem, ShoppingItem, TokenResponse, UserPreferences } from '@/types/api'

it('InventoryItem 含服务端全部字段', () => {
  const sample: InventoryItem = {
    id: 'x',
    ingredient_id: null,
    display_name: '牛奶',
    quantity: '1.000',
    unit: '盒',
    purchase_date: null,
    expiry_date: '2026-11-25',
    storage_location: '冷藏',
    status: 'expiring',
    version: 1,
    archived_at: null,
    created_at: '2026-11-24T00:00:00Z',
    updated_at: '2026-11-24T00:00:00Z',
  }
  expect(sample.version).toBe(1)
})

it('ShoppingItem.status 含 cancelled', () => {
  const s: ShoppingItem['status'] = 'cancelled'
  expect(s).toBe('cancelled')
})

it('UserPreferences.budget 必填字符串', () => {
  const p: UserPreferences = {
    dietary_preferences: [],
    allergens: [],
    disliked_ingredients: [],
    default_servings: 2,
    default_budget: '0.00',
    default_cooking_minutes: 30,
  }
  expect(typeof p.default_budget).toBe('string')
})

it('TokenResponse 含 user', () => {
  const t: TokenResponse = {
    access_token: 'a',
    token_type: 'bearer',
    expires_in: 3600,
    user: { id: 'u', username: 'n', email: 'e@x.com', is_active: true },
  }
  expect(t.user.is_active).toBe(true)
})