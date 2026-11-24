/** 首页统计接口封装。归属：A 组。仅计数，过滤 qty>0+未归档。 */
import client from '@/api/client'
import type { DashboardSummary } from '@/types/api'

export function summary(): Promise<DashboardSummary> {
  return client.get<DashboardSummary>('/dashboard/summary').then((r) => r.data)
}