/** 错误码→中文映射与统一提示。后端 service message 为英文，按 code 分支。归属：A 组。 */
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'

const MESSAGE_MAP: Record<string, string> = {
  VALIDATION_ERROR: '输入信息不符合要求，请检查后重试',
  UNAUTHENTICATED: '登录已过期，请重新登录',
  FORBIDDEN: '账号已被禁用，请联系管理员',
  RESOURCE_NOT_FOUND: '资源不存在或已被删除',
  STATE_CONFLICT: '数据已被其他操作修改，请核对最新值后重试',
  INSUFFICIENT_STOCK: '库存不足，无法扣减',
  NETWORK_ERROR: '网络异常，请稍后重试',
  INTERNAL_SERVER_ERROR: '服务异常，请稍后重试',
}

/** 按 code 映射中文，未知码回退服务端 message。 */
export function mapErrorMessage(err: { code: string; message: string; requestId?: string }): string {
  return MESSAGE_MAP[err.code] ?? err.message ?? '操作失败，请稍后重试'
}

/** 统一错误提示；UNAUTHENTICATED 由全局 401 处理器提示，此处跳过避免重复。 */
export function showErrorToast(err: NormalizedError): void {
  if (err.code === 'UNAUTHENTICATED') {
    return
  }
  ElMessage.error({ message: mapErrorMessage(err), duration: 5000, showClose: true })
}