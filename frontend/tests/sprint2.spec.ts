import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/preferences', () => ({ getPreferences: vi.fn(), putPreferences: vi.fn() }))
vi.mock('@/api/shopping', () => ({ list: vi.fn(), create: vi.fn(), updateStatus: vi.fn(), remove: vi.fn() }))
import * as prefApi from '@/api/preferences'
import * as shopApi from '@/api/shopping'
import PreferencesView from '@/views/PreferencesView.vue'
import ShoppingView from '@/views/ShoppingView.vue'
import ShoppingAddForm from '@/components/shopping/ShoppingAddForm.vue'
import type { ShoppingItem, UserPreferences } from '@/types/api'

const prefs: UserPreferences = {
  dietary_preferences: ['素食'],
  allergens: ['花生'],
  disliked_ingredients: ['香菜'],
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

function prefRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/preferences', name: 'preferences', component: PreferencesView },
      { path: '/', name: 'home', component: { render: () => null } },
    ],
  })
}

async function mountPrefs() {
  const router = prefRouter()
  router.push({ name: 'preferences' })
  await router.isReady()
  const w = mount(PreferencesView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

it('偏好 404 渲染首设态而非错误', async () => {
  vi.mocked(prefApi.getPreferences).mockRejectedValue({ code: 'RESOURCE_NOT_FOUND', message: 'unset', requestId: '', status: 404 })
  const w = await mountPrefs()
  expect(w.text()).toContain('尚未设置偏好')
  expect((w.vm as unknown as { firstRun: boolean }).firstRun).toBe(true)
})

it('偏好 200 填充六字段（budget 字符串转 number）', async () => {
  vi.mocked(prefApi.getPreferences).mockResolvedValue(prefs)
  const w = await mountPrefs()
  const vm = w.vm as unknown as { form: { allergens: string[]; default_budget: number } }
  expect(vm.form.allergens).toEqual(['花生'])
  expect(vm.form.default_budget).toBe(120.5)
})

it('偏好保存 PUT 六字段整表（budget 2 位小数字符串）', async () => {
  vi.mocked(prefApi.getPreferences).mockResolvedValue(prefs)
  vi.mocked(prefApi.putPreferences).mockResolvedValue(prefs)
  const w = await mountPrefs()
  await (w.vm as unknown as { onSave: () => Promise<void> }).onSave()
  expect(prefApi.putPreferences).toHaveBeenCalledWith({
    dietary_preferences: ['素食'],
    allergens: ['花生'],
    disliked_ingredients: ['香菜'],
    default_servings: 2,
    default_budget: '120.50',
    default_cooking_minutes: 30,
  })
})

it('偏好人数越界阻止提交', async () => {
  vi.mocked(prefApi.getPreferences).mockResolvedValue(prefs)
  const w = await mountPrefs()
  const vm = w.vm as unknown as { form: { default_servings: number }; onSave: () => Promise<void>; saveError: string }
  vm.form.default_servings = 0
  await vm.onSave()
  expect(prefApi.putPreferences).not.toHaveBeenCalled()
  expect(vm.saveError).toContain('1~100')
})

it('采购列表全部省略 status 参数', async () => {
  vi.mocked(shopApi.list).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
  mount(ShoppingView)
  await flushPromises()
  expect(shopApi.list).toHaveBeenCalledWith({ page: 1, page_size: 20, status: undefined })
})

it('采购勾选仅 PATCH status（不入库不下单）', async () => {
  const item = shopItem()
  vi.mocked(shopApi.list).mockResolvedValue({ items: [item], total: 1, page: 1, page_size: 20 })
  vi.mocked(shopApi.updateStatus).mockResolvedValue({ ...item, status: 'purchased' })
  const w = mount(ShoppingView)
  await flushPromises()
  await w.find('input[type="checkbox"]').setValue(true)
  await flushPromises()
  expect(shopApi.updateStatus).toHaveBeenCalledWith('s1', 'purchased')
  expect(shopApi.create).not.toHaveBeenCalled()
})

it('采购删除二次确认后硬删除', async () => {
  const item = shopItem()
  vi.mocked(shopApi.list).mockResolvedValue({ items: [item], total: 1, page: 1, page_size: 20 })
  vi.mocked(shopApi.remove).mockResolvedValue(undefined)
  const w = mount(ShoppingView)
  await flushPromises()
  const del = w.findAll('button').find((b) => b.text().includes('删除'))
  await del!.trigger('click')
  await flushPromises()
  expect(shopApi.remove).toHaveBeenCalledWith('s1')
})

it('采购新增数量 0 阻止提交', async () => {
  const w = mount(ShoppingAddForm)
  await flushPromises()
  const vm = w.vm as unknown as { form: { display_name: string; quantity: string; unit: string }; onSubmit: () => Promise<void> }
  vm.form.display_name = '番茄'
  vm.form.quantity = '0'
  vm.form.unit = 'g'
  await vm.onSubmit()
  expect(shopApi.create).not.toHaveBeenCalled()
})

it('采购空态文案', async () => {
  vi.mocked(shopApi.list).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
  const w = mount(ShoppingView)
  await flushPromises()
  expect(w.text()).toContain('采购清单还是空的')
})