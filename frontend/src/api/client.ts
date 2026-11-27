import axios, { type AxiosError, type AxiosInstance } from 'axios'

/** 本地存储的令牌键名。 */
export const TOKEN_KEY = 'pantrypilot.token'

/** 后端统一错误结构（文档/05 §5，core/errors.py）。 */
export interface ApiError {
  code: string
  message: string
  request_id: string
  details?: Record<string, unknown>
}

/** 归一化后的错误，供页面统一提示。status 供 403/401 等分支。 */
export interface NormalizedError {
  code: string
  message: string
  requestId: string
  status: number
  details?: Record<string, unknown>
}

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api/v1',
  timeout: 15000,
})

// 注册式全局 401 处理器：避免 client 静态 import router/store 造成循环依赖。
let onUnauthorized: (() => void) | null = null
let handling401 = false

/** 由 main.ts 接线（清 token + 提示 + 跳登录）。 */
export function setUnauthorizedHandler(fn: (() => void) | null): void {
  onUnauthorized = fn
}

/** 重置并发去重标志（router.afterEach 调用；测试 beforeEach 调用）。 */
export function resetUnauthorizedFlag(): void {
  handling401 = false
}

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const payload = error.response?.data
    const status = error.response?.status ?? 0
    const normalized: NormalizedError = {
      code: payload?.code ?? 'NETWORK_ERROR',
      message: payload?.message ?? '网络异常，请稍后重试',
      requestId: payload?.request_id ?? '',
      status,
      details: payload?.details,
    }
    // 业务 401（非 /auth/*）触发全局会话失效处理；并发去重。
    const url = error.config?.url ?? ''
    if (status === 401 && !url.startsWith('/auth/') && !handling401) {
      handling401 = true
      onUnauthorized?.()
    }
    return Promise.reject(normalized)
  },
)

export default client