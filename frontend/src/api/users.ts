/** 用户接口封装。归属：A 组。/users/me 精确路径无尾斜杠。 */
import client from '@/api/client'
import type { UserResponse } from '@/types/api'

export function getMe(): Promise<UserResponse> {
  return client.get<UserResponse>('/users/me').then((r) => r.data)
}