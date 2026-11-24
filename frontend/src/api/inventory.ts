/** 库存接口封装。归属：A 组。expiring 为裸数组无分页。 */
import client from '@/api/client'
import type {
  InventoryCreateRequest,
  InventoryItem,
  InventoryStatus,
  InventoryUpdateRequest,
  PageResult,
} from '@/types/api'

export interface InventoryListParams {
  page?: number
  page_size?: number
  name?: string
  category?: string
  status?: InventoryStatus
  include_archived?: boolean
}

export function list(params: InventoryListParams = {}): Promise<PageResult<InventoryItem>> {
  return client.get<PageResult<InventoryItem>>('/inventory', { params }).then((r) => r.data)
}

export function create(body: InventoryCreateRequest): Promise<InventoryItem> {
  return client.post<InventoryItem>('/inventory', body).then((r) => r.data)
}

export function get(id: string): Promise<InventoryItem> {
  return client.get<InventoryItem>(`/inventory/${id}`).then((r) => r.data)
}

export function update(id: string, body: InventoryUpdateRequest): Promise<InventoryItem> {
  return client.patch<InventoryItem>(`/inventory/${id}`, body).then((r) => r.data)
}

/** 软归档（204 无 body，幂等）。 */
export function archive(id: string): Promise<void> {
  return client.delete(`/inventory/${id}`).then(() => undefined)
}

export function expiring(): Promise<InventoryItem[]> {
  return client.get<InventoryItem[]>('/inventory/expiring').then((r) => r.data)
}