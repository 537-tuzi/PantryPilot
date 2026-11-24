import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/inventory', () => ({
  list: vi.fn(),
  create: vi.fn(),
  get: vi.fn(),
  update: vi.fn(),
  archive: vi.fn(),
  expiring: vi.fn(),
}))
import * as api from '@/api/inventory'
import IngredientFormView from '@/views/IngredientFormView.vue'
import type { InventoryItem, InventoryReason } from '@/types/api'

interface Exposed {
  form: {
    display_name: string
    quantity: string
    unit: string
    purchase_date: string
    expiry_date: string
    storage_location: string
    reason: InventoryReason
  }
  onSubmit: () => Promise<void>
}

function item(over: Partial<InventoryItem> = {}): InventoryItem {
  return {
    id: 'i1',
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
    ...over,
  }
}

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/inventory/new', name: 'ingredient-form', component: IngredientFormView },
      { path: '/inventory/:id/edit', name: 'ingredient-edit', component: IngredientFormView },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
    ],
  })
}

async function mountForm(name: string, params: Record<string, string> = {}) {
  const router = makeRouter()
  router.push({ name, params })
  await router.isReady()
  const w = mount(IngredientFormView, { global: { plugins: [router] } })
  await flushPromises()
  return { w, router, vm: w.vm as unknown as Exposed }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

it('创建必填校验阻止提交', async () => {
  const { vm } = await mountForm('ingredient-form')
  vm.form.display_name = ''
  vm.form.quantity = '1.000'
  vm.form.unit = '盒'
  await vm.onSubmit()
  expect(api.create).not.toHaveBeenCalled()
})

it('创建数量拒绝 0 与 4 位小数', async () => {
  const { vm } = await mountForm('ingredient-form')
  vm.form.display_name = '牛奶'
  vm.form.unit = '盒'
  vm.form.quantity = '0'
  await vm.onSubmit()
  vm.form.quantity = '1.2345'
  await vm.onSubmit()
  expect(api.create).not.toHaveBeenCalled()
})

it('创建合法提交', async () => {
  vi.mocked(api.create).mockResolvedValue(item())
  const { vm } = await mountForm('ingredient-form')
  vm.form.display_name = '牛奶'
  vm.form.quantity = '1.000'
  vm.form.unit = '盒'
  await vm.onSubmit()
  expect(api.create).toHaveBeenCalledWith(expect.objectContaining({ display_name: '牛奶', quantity: '1.000', unit: '盒' }))
})

it('编辑仅发送变更字段且带 expected_version 与 reason', async () => {
  vi.mocked(api.get).mockResolvedValue(item())
  vi.mocked(api.update).mockResolvedValue(item({ quantity: '0.500', version: 2 }))
  const { vm } = await mountForm('ingredient-edit', { id: 'i1' })
  await flushPromises()
  vm.form.quantity = '0.500'
  await vm.onSubmit()
  expect(api.update).toHaveBeenCalledWith('i1', { expected_version: 1, quantity: '0.500', reason: 'consume' })
})

it('编辑数量增加默认 reason add', async () => {
  vi.mocked(api.get).mockResolvedValue(item())
  vi.mocked(api.update).mockResolvedValue(item())
  const { vm } = await mountForm('ingredient-edit', { id: 'i1' })
  await flushPromises()
  vm.form.quantity = '2.000'
  await vm.onSubmit()
  expect(api.update).toHaveBeenCalledWith('i1', { expected_version: 1, quantity: '2.000', reason: 'add' })
})

it('编辑无变更不发请求', async () => {
  vi.mocked(api.get).mockResolvedValue(item())
  const { vm } = await mountForm('ingredient-edit', { id: 'i1' })
  await flushPromises()
  await vm.onSubmit()
  expect(api.update).not.toHaveBeenCalled()
})

it('编辑 body 不含 unit（不可改）', async () => {
  vi.mocked(api.get).mockResolvedValue(item())
  vi.mocked(api.update).mockResolvedValue(item())
  const { vm } = await mountForm('ingredient-edit', { id: 'i1' })
  await flushPromises()
  vm.form.quantity = '0.500'
  vm.form.unit = 'kg'
  await vm.onSubmit()
  const body = vi.mocked(api.update).mock.calls[0][1]
  expect(body).not.toHaveProperty('unit')
})

it('编辑仅改日期发送 null 清空与 reason adjust', async () => {
  vi.mocked(api.get).mockResolvedValue(item())
  vi.mocked(api.update).mockResolvedValue(item())
  const { vm } = await mountForm('ingredient-edit', { id: 'i1' })
  await flushPromises()
  vm.form.expiry_date = ''
  await vm.onSubmit()
  expect(api.update).toHaveBeenCalledWith('i1', { expected_version: 1, expiry_date: null, reason: 'adjust' })
})