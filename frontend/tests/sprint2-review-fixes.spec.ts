import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage } from 'element-plus'

vi.mock('@/api/preferences', () => ({ getPreferences: vi.fn(), putPreferences: vi.fn() }))
vi.mock('@/api/shopping', () => ({ list: vi.fn(), create: vi.fn(), updateStatus: vi.fn(), remove: vi.fn() }))
import * as prefApi from '@/api/preferences'
import * as shopApi from '@/api/shopping'
import PreferencesView from '@/views/PreferencesView.vue'
import ShoppingView from '@/views/ShoppingView.vue'
import type { ShoppingItem, UserPreferences } from '@/types/api'

const prefs: UserPreferences = {
  dietary_preferences: [],
  allergens: ['花生'],
  disliked_ingredients: [],
  default_servings: 2,
  default_budget: '120.50',
  default_cooking_minutes: 30,
}

function shopItem(over: Partial<ShoppingItem> = {}): ShoppingItem {
  return {
    id: 's1', display_name: '番茄', ingredient_id: null, quantity: '500.000', unit: 'g',
    status: 'pending', source_meal_plan_id: null,
    created_at: '2026-11-24T00:00:00Z', updated_at: '2026-11-24T00:00:00Z', ...over,
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

it('采购勾选失败只弹错误、不弹成功', async () => {
  vi.mocked(shopApi.list).mockResolvedValue({ items: [shopItem()], total: 1, page: 1, page_size: 20 })
  vi.mocked(shopApi.updateStatus).mockRejectedValue({ code: 'INTERNAL_SERVER_ERROR', message: 'boom', requestId: 'r', status: 500 })
  const w = mount(ShoppingView)
  await flushPromises()
  await w.find('input[type="checkbox"]').setValue(true)
  await flushPromises()
  expect(vi.mocked(ElMessage.error)).toHaveBeenCalled()
  expect(vi.mocked(ElMessage.success)).not.toHaveBeenCalled()
})

it('偏好重置后 dirty 归 false（不误弹脏守卫）', async () => {
  vi.mocked(prefApi.getPreferences).mockResolvedValue(prefs)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/preferences', name: 'preferences', component: PreferencesView },
      { path: '/', name: 'home', component: { render: () => null } },
    ],
  })
  router.push({ name: 'preferences' })
  await router.isReady()
  const w = mount(PreferencesView, { global: { plugins: [router] } })
  await flushPromises()
  const vm = w.vm as unknown as { form: { default_servings: number }; onReset: () => Promise<void>; dirty: boolean }
  vm.form.default_servings = 5
  await flushPromises()
  expect(vm.dirty).toBe(true)
  await vm.onReset()
  await flushPromises()
  expect(vm.dirty).toBe(false)
})