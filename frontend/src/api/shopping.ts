/** 采购清单接口封装。勾选仅 PATCH status；DELETE 硬删除非幂等；import 需 confirmed 计划（冻结）。 */
import client from '@/api/client'
import type {
  PageResult,
  ShoppingItem,
  ShoppingItemCreateRequest,
  ShoppingStatus,
} from '@/types/api'

export interface ShoppingListParams {
  page?: number
  page_size?: number
  status?: ShoppingStatus
}

export function list(params: ShoppingListParams = {}): Promise<PageResult<ShoppingItem>> {
  return client.get<PageResult<ShoppingItem>>('/shopping-items', { params }).then((r) => r.data)
}

export function create(payload: ShoppingItemCreateRequest): Promise<ShoppingItem> {
  return client.post<ShoppingItem>('/shopping-items', payload).then((r) => r.data)
}

export function updateStatus(id: string, status: ShoppingStatus): Promise<ShoppingItem> {
  return client.patch<ShoppingItem>(`/shopping-items/${id}`, { status }).then((r) => r.data)
}

export function remove(id: string): Promise<void> {
  return client.delete(`/shopping-items/${id}`).then(() => undefined)
}