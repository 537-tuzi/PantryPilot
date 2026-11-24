import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/inventory', () => ({
  list: vi.fn(), create: vi.fn(), get: vi.fn(), update: vi.fn(), archive: vi.fn(), expiring: vi.fn(), categories: vi.fn(),
}))
vi.mock('@/api/dashboard', () => ({ summary: vi.fn() }))
vi.mock('@/api/auth', () => ({ login: vi.fn(), register: vi.fn() }))
import * as api from '@/api/inventory'
import * as dash from '@/api/dashboard'
import IngredientFormView from '@/views/IngredientFormView.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'
import HomeView from '@/views/HomeView.vue'
import ConsumeDialog from '@/components/inventory/ConsumeDialog.vue'
import type { InventoryItem } from '@/types/api'

function item(over: Partial<InventoryItem> = {}): InventoryItem {
  return {
    id: 'i1', ingredient_id: null, display_name: '牛奶', quantity: '1.000', unit: '盒',
    purchase_date: null, expiry_date: '2026-11-25', storage_location: '冷藏', status: 'expiring',
    version: 1, archived_at: null, created_at: '2026-11-24T00:00:00Z', updated_at: '2026-11-24T00:00:00Z', ...over,
  }
}

function editRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/inventory/:id/edit', name: 'ingredient-edit', component: IngredientFormView },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
    ],
  })
}

function homeRouter() {
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

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(api.categories).mockResolvedValue([])
})

it('#1 编辑载入失败后重试成功清除错误态（表单可达）', async () => {
  vi.mocked(api.get).mockRejectedValueOnce({ code: 'NETWORK_ERROR', message: 'x', requestId: '', status: 0 })
  const router = editRouter()
  router.push({ name: 'ingredient-edit', params: { id: 'i1' } })
  await router.isReady()
  const w = mount(IngredientFormView, { global: { plugins: [router] } })
  await flushPromises()
  expect(w.find('form').exists()).toBe(false)
  vi.mocked(api.get).mockResolvedValue(item())
  await (w.vm as unknown as { loadItem: () => Promise<void> }).loadItem()
  await flushPromises()
  expect(w.find('form').exists()).toBe(true)
})

it('#2 注册确认密码不一致给内联反馈', async () => {
  const w = mount(RegisterForm)
  await flushPromises()
  const vm = w.vm as unknown as {
    form: { username: string; email: string; password: string; confirmPassword: string }
    onSubmit: () => Promise<void>
    validationError: string
  }
  vm.form.username = 'newuser'
  vm.form.email = 'new@x.com'
  vm.form.password = 'Abcd1234'
  vm.form.confirmPassword = 'Abcd1234X'
  await vm.onSubmit()
  expect(vm.validationError).toContain('两次密码不一致')
  expect(w.text()).toContain('两次密码不一致')
})

it('#3 首页 summary 失败显示错误态与重试', async () => {
  vi.mocked(dash.summary).mockRejectedValue({ code: 'NETWORK_ERROR', message: 'x', requestId: 'r', status: 0 })
  vi.mocked(api.expiring).mockResolvedValue([])
  const router = homeRouter()
  router.push({ name: 'home' })
  await router.isReady()
  const w = mount(HomeView, { global: { plugins: [router] } })
  await flushPromises()
  expect(w.text()).toContain('网络异常')
  expect(w.findAll('button').some((b) => b.text().includes('重试'))).toBe(true)
})

it('#5 耗尽对话框重开同一行重置目标数量', async () => {
  const w = mount(ConsumeDialog, { props: { modelValue: true, item: item() } })
  await flushPromises()
  await w.find('input').setValue('2')
  await w.setProps({ modelValue: false })
  await w.setProps({ modelValue: true })
  await flushPromises()
  expect((w.find('input').element as HTMLInputElement).value).toBe('0')
})