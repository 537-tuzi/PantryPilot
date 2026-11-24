import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
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
import ConsumeDialog from '@/components/inventory/ConsumeDialog.vue'
import InventoryTable from '@/components/inventory/InventoryTable.vue'
import type { InventoryItem } from '@/types/api'

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

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

it('ConsumeDialog 耗尽提交 PATCH quantity 0 reason consume 带 expected_version', async () => {
  vi.mocked(api.update).mockResolvedValue(item({ quantity: '0.000', version: 2 }))
  const w = mount(ConsumeDialog, { props: { modelValue: true, item: item() } })
  await flushPromises()
  const btn = w.findAll('button').find((b) => b.text().includes('确认耗尽'))
  await btn!.trigger('click')
  await flushPromises()
  expect(api.update).toHaveBeenCalledWith('i1', { expected_version: 1, quantity: '0', reason: 'consume' })
})

it('ConsumeDialog 目标等于当前不发请求', async () => {
  const w = mount(ConsumeDialog, { props: { modelValue: true, item: item() } })
  await flushPromises()
  await w.find('input').setValue('1.000')
  const btn = w.findAll('button').find((b) => b.text().includes('确认耗尽'))
  await btn!.trigger('click')
  await flushPromises()
  expect(api.update).not.toHaveBeenCalled()
})

it('ConsumeDialog 409 后 refetch 保留输入不自动重发', async () => {
  vi.mocked(api.update).mockRejectedValue({ code: 'STATE_CONFLICT', message: 'modified', requestId: 'r', status: 409 })
  vi.mocked(api.get).mockResolvedValue(item({ version: 5, quantity: '0.500' }))
  const w = mount(ConsumeDialog, { props: { modelValue: true, item: item() } })
  await flushPromises()
  const btn = w.findAll('button').find((b) => b.text().includes('确认耗尽'))
  await btn!.trigger('click')
  await flushPromises()
  expect(api.get).toHaveBeenCalledWith('i1')
  expect(api.update).toHaveBeenCalledTimes(1)
  expect(w.text()).toContain('修改')
})

it('InventoryTable 数量单位同屏且状态取服务端', () => {
  const w = mount(InventoryTable, { props: { items: [item({ status: 'expired' })] } })
  expect(w.text()).toContain('1盒')
  expect(w.text()).toContain('已过期')
})

it('InventoryTable 已归档行禁用编辑/耗尽', () => {
  const w = mount(InventoryTable, { props: { items: [item({ archived_at: '2026-11-24T00:00:00Z' })] } })
  const btns = w.findAll('button')
  const edit = btns.find((b) => b.text().includes('编辑'))
  const consume = btns.find((b) => b.text().includes('耗尽'))
  expect(edit!.attributes('disabled')).toBeDefined()
  expect(consume!.attributes('disabled')).toBeDefined()
})

it('InventoryTable 数量为 0 行禁用耗尽', () => {
  const w = mount(InventoryTable, { props: { items: [item({ quantity: '0.000' })] } })
  const consume = w.findAll('button').find((b) => b.text().includes('耗尽'))
  expect(consume!.attributes('disabled')).toBeDefined()
})