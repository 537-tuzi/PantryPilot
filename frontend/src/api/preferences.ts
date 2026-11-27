/** 偏好接口封装。GET 未设置时 404（首设态）；PUT 全量替换 upsert（首次也 200）。 */
import client from '@/api/client'
import type { UserPreferences } from '@/types/api'

export function getPreferences(): Promise<UserPreferences> {
  return client.get<UserPreferences>('/users/me/preferences').then((r) => r.data)
}

export function putPreferences(payload: UserPreferences): Promise<UserPreferences> {
  return client.put<UserPreferences>('/users/me/preferences', payload).then((r) => r.data)
}