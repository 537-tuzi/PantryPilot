import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/dashboard', () => ({ summary: vi.fn() }))
vi.mock('@/api/inventory', () => ({ expiring: vi.fn() }))
import * as dash from '@/api/dashboard'
import * as inv from '@/api/inventory'
import HomeView from '@/views/HomeView.vue'
import type { DashboardSummary, InventoryItem } from '@/types/api'

const summary: DashboardSummary = { statistics_date: '2026-11-24', inventory_count: 6, expiring_count: 3, expired_count: 1 }

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
      { path: '/', name: 'home', component: HomeView },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
      { path: '/inventory/new', name: 'ingredient-form', component: { render: () => null } },
      { path: '/expiry', name: 'expiry', component: { render: () => null } },
    ],
  })
}

async function mountHome() {
  const router = makeRouter()
  router.push({ name: 'home' })
  await router.isReady()
  const w = mount(HomeView, { global: { plugins: [router] } })
  await flushPromises()
  return { w, router }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

it('两独立请求一区失败不拖垮另一区', async () => {
  vi.mocked(dash.summary).mockRejectedValue({ code: 'NETWORK_ERROR', message: 'x', requestId: '', status: 0 })
  vi.mocked(inv.expiring).mockResolvedValue([item()])
  const { w } = await mountHome()
  expect(w.text()).toContain('牛奶')
})

it('临期卡排除过期项', async () => {
  vi.mocked(dash.summary).mockResolvedValue(summary)
  vi.mocked(inv.expiring).mockResolvedValue([
    item({ status: 'expired', display_name: '酸奶', expiry_date: '2026-11-20' }),
    item({ id: 'i2', status: 'expiring', display_name: '牛奶' }),
  ])
  const { w } = await mountHome()
  const cards = w.findAll('.expiring-card')
  expect(cards.length).toBe(1)
  expect(cards[0].text()).toContain('牛奶')
})

it('今天用 statistics_date 而非客户端时钟', async () => {
  vi.mocked(dash.summary).mockResolvedValue(summary)
  vi.mocked(inv.expiring).mockResolvedValue([item({ expiry_date: '2026-11-24' })])
  const { w } = await mountHome()
  expect(w.text()).toContain('今天到期')
})

it('库存卡注明口径差异', async () => {
  vi.mocked(dash.summary).mockResolvedValue(summary)
  vi.mocked(inv.expiring).mockResolvedValue([])
  const { w } = await mountHome()
  expect(w.text()).toContain('已耗尽')
})

it('开始规划禁用且 Sprint 2 提示', async () => {
  vi.mocked(dash.summary).mockResolvedValue(summary)
  vi.mocked(inv.expiring).mockResolvedValue([])
  const { w } = await mountHome()
  const btn = w.findAll('button').find((b) => b.text().includes('开始规划'))
  expect(btn!.attributes('disabled')).toBeDefined()
})

it('过期卡跳 expiry', async () => {
  vi.mocked(dash.summary).mockResolvedValue(summary)
  vi.mocked(inv.expiring).mockResolvedValue([])
  const { w, router } = await mountHome()
  const card = w.findAll('.stat-card').find((c) => c.text().includes('过期'))
  await card!.trigger('click')
  await flushPromises()
  expect(router.currentRoute.value.name).toBe('expiry')
})