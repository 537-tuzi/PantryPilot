import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/inventory', () => ({ list: vi.fn(), create: vi.fn(), get: vi.fn(), update: vi.fn(), archive: vi.fn(), expiring: vi.fn(), categories: vi.fn() }))
vi.mock('@/api/dashboard', () => ({ summary: vi.fn() }))
import * as api from '@/api/inventory'
import * as dash from '@/api/dashboard'
import IngredientFormView from '@/views/IngredientFormView.vue'
import ConsumeDialog from '@/components/inventory/ConsumeDialog.vue'
import InventoryToolbar from '@/components/inventory/InventoryToolbar.vue'
import FourState from '@/components/FourState.vue'
import HomeView from '@/views/HomeView.vue'
import { appError, clearAppError, setAppError } from '@/utils/appError'
import type { InventoryItem } from '@/types/api'

function item(over: Partial<InventoryItem> = {}): InventoryItem {
  return {
    id: 'i1', ingredient_id: null, display_name: '牛奶', quantity: '1.000', unit: '盒',
    purchase_date: null, expiry_date: '2026-11-25', storage_location: '冷藏', status: 'expiring',
    version: 1, archived_at: null, created_at: '2026-11-24T00:00:00Z', updated_at: '2026-11-24T00:00:00Z', ...over,
  }
}

function formRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/inventory/new', name: 'ingredient-form', component: IngredientFormView },
      { path: '/inventory/:id/edit', name: 'ingredient-edit', component: IngredientFormView },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
    ],
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(api.categories).mockResolvedValue([])
  clearAppError()
})

it('#1 编辑载入后 dirty 为 false（未触碰不弹脏守卫）', async () => {
  vi.mocked(api.get).mockResolvedValue(item())
  const router = formRouter()
  router.push({ name: 'ingredient-edit', params: { id: 'i1' } })
  await router.isReady()
  const w = mount(IngredientFormView, { global: { plugins: [router] } })
  await flushPromises()
  expect((w.vm as unknown as { dirty: boolean }).dirty).toBe(false)
})

it('#2 创建数量 0 显示校验反馈而非静默', async () => {
  const router = formRouter()
  router.push({ name: 'ingredient-form' })
  await router.isReady()
  const w = mount(IngredientFormView, { global: { plugins: [router] } })
  await flushPromises()
  const vm = w.vm as unknown as { form: { display_name: string; quantity: string; unit: string }; onSubmit: () => Promise<void>; validationError: string }
  vm.form.display_name = '牛奶'
  vm.form.unit = '盒'
  vm.form.quantity = '0'
  await vm.onSubmit()
  expect(vm.validationError).toContain('大于 0')
})

it('#3 ConsumeDialog 409 后 refetch 再 404 → 关闭移除', async () => {
  vi.mocked(api.update).mockRejectedValue({ code: 'STATE_CONFLICT', message: 'modified', requestId: 'r', status: 409 })
  vi.mocked(api.get).mockRejectedValue({ code: 'RESOURCE_NOT_FOUND', message: 'gone', requestId: 'r', status: 404 })
  const w = mount(ConsumeDialog, { props: { modelValue: true, item: item() } })
  await flushPromises()
  const btn = w.findAll('button').find((b) => b.text().includes('确认耗尽'))
  await btn!.trigger('click')
  await flushPromises()
  expect(w.emitted('removed')).toBeTruthy()
})

it('#4 toolbar 同步父级 modelValue（深链筛选可见）', async () => {
  const w = mount(InventoryToolbar, { props: { modelValue: { name: '牛奶' } } })
  await flushPromises()
  expect((w.find('input').element as HTMLInputElement).value).toBe('牛奶')
})

it('#5 FourState 错误经中文映射不渲染英文', () => {
  const w = mount(FourState, {
    props: { loading: false, error: { code: 'STATE_CONFLICT', message: 'Inventory item was modified by another request', requestId: 'r', status: 409 } },
  })
  expect(w.text()).toContain('修改')
  expect(w.text()).not.toContain('Inventory item')
})

it('#6 分类筛选诚实提示', () => {
  const w = mount(InventoryToolbar, { props: { modelValue: {} } })
  expect(w.text()).toContain('仅匹配已关联食材库')
})

it('#6b 分类选项来自后端真实端点（无硬编码）', async () => {
  vi.mocked(api.categories).mockResolvedValue(['乳制品', '蔬菜'])
  mount(InventoryToolbar, { props: { modelValue: {} } })
  await flushPromises()
  expect(api.categories).toHaveBeenCalled()
})

it('#7 首页禁用规划按钮由 span 包裹（tooltip 可显示）', async () => {
  vi.mocked(dash.summary).mockResolvedValue({ statistics_date: '2026-11-24', inventory_count: 0, expiring_count: 0, expired_count: 0 })
  vi.mocked(api.expiring).mockResolvedValue([])
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: HomeView },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
      { path: '/inventory/new', name: 'ingredient-form', component: { render: () => null } },
      { path: '/expiry', name: 'expiry', component: { render: () => null } },
    ],
  })
  router.push({ name: 'home' })
  await router.isReady()
  const w = mount(HomeView, { global: { plugins: [router] } })
  await flushPromises()
  const btn = w.findAll('button').find((b) => b.text().includes('开始规划'))
  expect(btn!.element.parentElement?.tagName).toBe('SPAN')
})

it('#8 全局错误状态可设置/清除', () => {
  setAppError({ message: '渲染异常', requestId: 'req-9' })
  expect(appError.value?.message).toBe('渲染异常')
  expect(appError.value?.requestId).toBe('req-9')
  clearAppError()
  expect(appError.value).toBeNull()
})