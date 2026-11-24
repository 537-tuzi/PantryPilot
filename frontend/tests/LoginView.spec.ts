import { beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/auth', () => ({ login: vi.fn(), register: vi.fn() }))
import * as authApi from '@/api/auth'
import LoginView from '@/views/LoginView.vue'
import type { TokenResponse } from '@/types/api'

const tokenResp: TokenResponse = {
  access_token: 't',
  token_type: 'bearer',
  expires_in: 3600,
  user: { id: 'u', username: 'n', email: 'e@x.com', is_active: true },
}

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: LoginView },
      { path: '/', name: 'home', component: { render: () => null } },
      { path: '/inventory', name: 'inventory', component: { render: () => null } },
    ],
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

async function mountLogin(query: Record<string, string> = {}) {
  const router = makeRouter()
  router.push({ name: 'login', query })
  await router.isReady()
  const w = mount(LoginView, { global: { plugins: [router] } })
  await flushPromises()
  return { w, router }
}

async function fillLogin(w: VueWrapper, email: string, password: string) {
  const inputs = w.findAll('input')
  await inputs[0].setValue(email)
  await inputs[1].setValue(password)
}

it('登录 401 显示统一错误不泄露账号存在', async () => {
  vi.mocked(authApi.login).mockRejectedValue({ code: 'UNAUTHENTICATED', message: 'Invalid email or password', requestId: 'r', status: 401 })
  const { w } = await mountLogin()
  await fillLogin(w, 'e@x.com', '12345678')
  await w.find('form').trigger('submit')
  await vi.waitFor(() => expect(w.text()).toContain('邮箱或密码错误'))
  expect(w.text()).not.toContain('未注册')
})

it('登录成功跳转 redirect', async () => {
  vi.mocked(authApi.login).mockResolvedValue(tokenResp)
  const { w, router } = await mountLogin({ redirect: '/inventory' })
  await fillLogin(w, 'e@x.com', '12345678')
  await w.find('form').trigger('submit')
  await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('inventory'))
})

it('非法 redirect 回退首页', async () => {
  vi.mocked(authApi.login).mockResolvedValue(tokenResp)
  const { w, router } = await mountLogin({ redirect: '//evil.com' })
  await fillLogin(w, 'e@x.com', '12345678')
  await w.find('form').trigger('submit')
  await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('home'))
})

it('登录密码仅长度校验不校验强度', async () => {
  vi.mocked(authApi.login).mockResolvedValue(tokenResp)
  const { w } = await mountLogin()
  await fillLogin(w, 'e@x.com', 'abcd1234')
  await w.find('form').trigger('submit')
  await vi.waitFor(() => expect(authApi.login).toHaveBeenCalled())
})

it('注册密码缺大写阻止提交', async () => {
  const { w } = await mountLogin()
  const tabs = w.findAll('.el-tabs__item')
  await tabs[1].trigger('click')
  await flushPromises()
  const inputs = w.findAll('input')
  await inputs[0].setValue('newuser')
  await inputs[1].setValue('new@x.com')
  await inputs[2].setValue('abcd1234')
  await inputs[3].setValue('abcd1234')
  await w.find('form').trigger('submit')
  await flushPromises()
  expect(authApi.register).not.toHaveBeenCalled()
})