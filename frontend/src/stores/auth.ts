import { defineStore } from 'pinia'
import { ref } from 'vue'

import client, { TOKEN_KEY } from '@/api/client'

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

  async function login(username: string, password: string): Promise<void> {
    const response = await client.post<{ access_token: string }>('/auth/login', { username, password })
    setToken(response.data.access_token)
  }

  async function register(username: string, password: string): Promise<void> {
    const response = await client.post<{ access_token: string }>('/auth/register', { username, password })
    setToken(response.data.access_token)
  }

  return { token, setToken, clear, login, register }
})
