import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/inventory', () => ({ expiring: vi.fn() }))
import * as api from '@/api/inventory'
import ExpiryView from '@/views/ExpiryView.vue'
import type { InventoryItem } from '@/types/api'

function item(over: Partial<InventoryItem> = {}): InventoryItem {
  return {
    id: 'i1',
    ingredient_id: null,
    display_name: '牛奶',
    quantity: '1.000',
    unit: '盒',
    purchase_date: null,
    expiry_date: '2026-11-26',
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
      { path: '/expiry', name: 'expiry', component: ExpiryView },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
    ],
  })
}

async function mountExpiry() {
  const router = makeRouter()
  router.push({ name: 'expiry' })
  await router.isReady()
  const w = mount(ExpiryView, { global: { plugins: [router] } })
  await flushPromises()
  return { w, router }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})
afterEach(() => {
  vi.useRealTimers()
})

it('请求不携带 page/page_size', async () => {
  vi.mocked(api.expiring).mockResolvedValue([])
  await mountExpiry()
  expect(api.expiring).toHaveBeenCalledWith()
})

it('按服务端顺序渲染且含过期项不过滤', async () => {
  vi.mocked(api.expiring).mockResolvedValue([
    item({ status: 'expired', expiry_date: '2026-11-20' }),
    item({ id: 'i2', status: 'expiring', expiry_date: '2026-11-26' }),
  ])
  const { w } = await mountExpiry()
  const rows = w.findAll('.expiry-row')
  expect(rows.length).toBe(2)
  expect(rows[0].text()).toContain('已过期')
})

it('状态取 item.status 不客户端重算', async () => {
  vi.mocked(api.expiring).mockResolvedValue([item({ status: 'normal', expiry_date: '2026-11-26' })])
  const { w } = await mountExpiry()
  expect(w.text()).toContain('正常')
})

it('剩余天数用应用时区今天', async () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-11-24T00:00:00Z'))
  vi.mocked(api.expiring).mockResolvedValue([item({ expiry_date: '2026-11-24', status: 'expiring' })])
  const { w } = await mountExpiry()
  expect(w.text()).toContain('今天到期')
})

it('空数组友好空态', async () => {
  vi.mocked(api.expiring).mockResolvedValue([])
  const { w } = await mountExpiry()
  expect(w.text()).toContain('暂无临期或过期食材')
})

it('查看库存携带 name 筛选', async () => {
  vi.mocked(api.expiring).mockResolvedValue([item()])
  const { w, router } = await mountExpiry()
  const btn = w.findAll('button').find((b) => b.text().includes('查看库存'))
  await btn!.trigger('click')
  await flushPromises()
  expect(router.currentRoute.value.query.name).toBe('牛奶')
})