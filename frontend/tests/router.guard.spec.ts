import { beforeEach, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

import { sanitizeRedirect, setupGuards } from '@/router/guards'
import { useAuthStore } from '@/stores/auth'

const Stub = { render: () => null }

function makeRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: Stub },
      { path: '/', name: 'home', component: Stub },
      { path: '/inventory', name: 'inventory', component: Stub },
    ],
  })
  setupGuards(router)
  return router
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
})

it('无 token 访问 /inventory 重定向 login 带 redirect', async () => {
  const router = makeRouter()
  await router.push('/inventory')
  expect(router.currentRoute.value.name).toBe('login')
  expect(router.currentRoute.value.query.redirect).toBe('/inventory')
})

it('已登录访问 /login 重定向 home', async () => {
  const router = makeRouter()
  useAuthStore().setToken('t')
  await router.push('/login')
  expect(router.currentRoute.value.name).toBe('home')
})

it('已登录访问受保护页放行', async () => {
  const router = makeRouter()
  useAuthStore().setToken('t')
  await router.push('/inventory')
  expect(router.currentRoute.value.name).toBe('inventory')
})

it('sanitizeRedirect 拒绝 // 与绝对 URL 与 /login', () => {
  expect(sanitizeRedirect('//evil.com')).toBe('/')
  expect(sanitizeRedirect('https://evil.com')).toBe('/')
  expect(sanitizeRedirect('/login')).toBe('/')
  expect(sanitizeRedirect('/inventory')).toBe('/inventory')
  expect(sanitizeRedirect(undefined)).toBe('/')
})