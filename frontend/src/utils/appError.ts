/** 全局应用错误状态（渲染级异常横幅，NFR-008）。归属：A 组。 */
import { ref } from 'vue'

export interface AppError {
  message: string
  requestId?: string
}

export const appError = ref<AppError | null>(null)

export function setAppError(err: unknown): void {
  const e = err as { message?: string; requestId?: string } | null
  appError.value = { message: e?.message ?? '应用发生未知错误，请刷新重试', requestId: e?.requestId }
}

export function clearAppError(): void {
  appError.value = null
}