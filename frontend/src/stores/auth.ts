import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { TOKEN_KEY } from '@/api/client'
import * as authApi from '@/api/auth'
import * as usersApi from '@/api/users'
import type { UserResponse } from '@/types/api'

export type { TokenResponse, UserResponse } from '@/types/api'

/** 登录态。归属：A 组。登出仅客户端清态（无服务端登出端点）；router.push 由调用方执行。 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) ?? '')
  const user = ref<UserResponse | null>(null)
  const isAuthenticated = computed(() => !!token.value)

  function setToken(value: string): void {
    token.value = value
    localStorage.setItem(TOKEN_KEY, value)
  }

  function clear(): void {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  /** 登录使用 email（后端 LoginRequest 要求 email + password）。捕获响应中的 user。 */
  async function login(email: string, password: string): Promise<UserResponse> {
    const data = await authApi.login({ email, password })
    setToken(data.access_token)
    user.value = data.user
    return data.user
  }

  /** 注册需要 username + email + password（密码需含大小写字母与数字）。 */
  async function register(username: string, email: string, password: string): Promise<UserResponse> {
    const data = await authApi.register({ username, email, password })
    setToken(data.access_token)
    user.value = data.user
    return data.user
  }

  /** 应用启动时拉取当前用户（GET /users/me）。 */
  async function fetchMe(): Promise<void> {
    user.value = await usersApi.getMe()
  }

  /** 仅清态；跳转由 AppLayout 下拉处理器执行，避免 store→router 循环。 */
  function logout(): void {
    clear()
  }

  return { token, user, isAuthenticated, setToken, clear, login, register, fetchMe, logout }
})