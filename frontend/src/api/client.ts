import axios, { type AxiosError, type AxiosInstance } from 'axios'

/** 本地存储的令牌键名。 */
export const TOKEN_KEY = 'pantrypilot.token'

/** 后端统一错误结构（文档/05 §5）。 */
export interface ApiError {
  code: string
  message: string
  request_id: string
  details?: Record<string, unknown>
}

/** 归一化后的错误，供页面统一提示。 */
export interface NormalizedError {
  code: string
  message: string
  requestId: string
}

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api/v1',
  timeout: 15000,
})

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
    const normalized: NormalizedError = {
      code: payload?.code ?? 'NETWORK_ERROR',
      message: payload?.message ?? '网络异常，请稍后重试',
      requestId: payload?.request_id ?? '',
    }
    return Promise.reject(normalized)
  },
)

export default client
