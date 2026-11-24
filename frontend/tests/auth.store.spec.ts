import { beforeEach, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/auth', () => ({ login: vi.fn(), register: vi.fn() }))
vi.mock('@/api/users', () => ({ getMe: vi.fn() }))

import * as authApi from '@/api/auth'
import * as usersApi from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import { TOKEN_KEY } from '@/api/client'
import type { TokenResponse } from '@/types/api'

const tokenResp: TokenResponse = {
  access_token: 'tok',
  token_type: 'bearer',
  expires_in: 3600,
  user: { id: 'u1', username: 'n', email: 'e@x.com', is_active: true },
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

it('login 存 token 与 user', async () => {
  vi.mocked(authApi.login).mockResolvedValue(tokenResp)
  const store = useAuthStore()
  await store.login('e@x.com', '12345678')
  expect(store.token).toBe('tok')
  expect(store.user?.id).toBe('u1')
  expect(localStorage.getItem(TOKEN_KEY)).toBe('tok')
})

it('register 存 token 与 user', async () => {
  vi.mocked(authApi.register).mockResolvedValue(tokenResp)
  const store = useAuthStore()
  await store.register('n', 'e@x.com', '12345678')
  expect(store.token).toBe('tok')
  expect(store.user?.id).toBe('u1')
})

it('fetchMe 写 user', async () => {
  vi.mocked(usersApi.getMe).mockResolvedValue(tokenResp.user)
  const store = useAuthStore()
  await store.fetchMe()
  expect(store.user?.id).toBe('u1')
})

it('logout 清 token/user/localStorage', async () => {
  vi.mocked(authApi.login).mockResolvedValue(tokenResp)
  const store = useAuthStore()
  await store.login('e@x.com', '12345678')
  store.logout()
  expect(store.token).toBe('')
  expect(store.user).toBeNull()
  expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
})

it('isAuthenticated 随 token', () => {
  const store = useAuthStore()
  expect(store.isAuthenticated).toBe(false)
  store.setToken('t')
  expect(store.isAuthenticated).toBe(true)
  store.clear()
  expect(store.isAuthenticated).toBe(false)
})