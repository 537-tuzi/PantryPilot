/** 认证接口封装。归属：A 组。登录用 email（BUG-002）。 */
import client from '@/api/client'
import type { TokenResponse } from '@/types/api'

export function login(payload: { email: string; password: string }): Promise<TokenResponse> {
  return client.post<TokenResponse>('/auth/login', payload).then((r) => r.data)
}

export function register(payload: { username: string; email: string; password: string }): Promise<TokenResponse> {
  return client.post<TokenResponse>('/auth/register', payload).then((r) => r.data)
}