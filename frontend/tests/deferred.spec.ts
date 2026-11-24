import { expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'

vi.mock('@/api/inventory', () => ({ expiring: vi.fn(), list: vi.fn(), get: vi.fn() }))
import * as api from '@/api/inventory'
import AiEntryView from '@/views/AiEntryView.vue'
import PlannerView from '@/views/PlannerView.vue'
import PlanResultView from '@/views/PlanResultView.vue'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { render: () => null } },
      { path: '/plans/:id', name: 'plan-result', component: PlanResultView },
    ],
  })
}

it('AI 三桩渲染 Sprint 2 未开放且不调任何 API', async () => {
  for (const C of [AiEntryView, PlannerView, PlanResultView]) {
    const router = makeRouter()
    router.push('/')
    await router.isReady()
    const w = mount(C, { global: { plugins: [router] } })
    expect(w.text()).toContain('Sprint 2')
  }
  expect(api.expiring).not.toHaveBeenCalled()
  expect(api.list).not.toHaveBeenCalled()
  expect(api.get).not.toHaveBeenCalled()
})