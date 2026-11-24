import { defineStore } from 'pinia'
import { ref } from 'vue'

import client, { TOKEN_KEY } from '@/api/client'

import type { TokenResponse } from '@/types/api'

export type { TokenResponse, UserResponse } from '@/types/api'

/** 登录态。归属：A 组。 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) ?? '')

  function setToken(value: string): void {
    token.value = value
    localStorage.setItem(TOKEN_KEY, value)
  }

  function clear(): void {
    token.value = ''
    localStorage.removeItem(TOKEN_KEY)
  }

  /** 登录使用 email（后端 LoginRequest 要求 email + password）。 */
  async function login(email: string, password: string): Promise<void> {
    const response = await client.post<TokenResponse>('/auth/login', { email, password })
    setToken(response.data.access_token)
  }

  /** 注册需要 username + email + password（密码需含大小写字母与数字）。 */
  async function register(username: string, email: string, password: string): Promise<void> {
    const response = await client.post<TokenResponse>('/auth/register', { username, email, password })
    setToken(response.data.access_token)
  }

  return { token, setToken, clear, login, register }
})
