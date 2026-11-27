/** 分页状态：pageSize/筛选变更重置 page=1，序号守卫丢弃过期响应。归属：A 组。 */
import { ref, type Ref } from 'vue'

import type { NormalizedError } from '@/api/client'
import type { PageResult } from '@/types/api'

export interface Pagination<T> {
  items: Ref<T[]>
  total: Ref<number>
  page: Ref<number>
  pageSize: Ref<number>
  loading: Ref<boolean>
  error: Ref<NormalizedError | null>
  load: () => Promise<void>
  setPage: (p: number) => void
  setPageSize: (s: number) => void
  refresh: () => Promise<void>
}

export function usePagination<T>(
  fetcher: (params: { page: number; page_size: number }) => Promise<PageResult<T>>,
  opts: { pageSize?: number } = {},
): Pagination<T> {
  const items = ref<T[]>([]) as Ref<T[]>
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(opts.pageSize ?? 20)
  const loading = ref(false)
  const error = ref<NormalizedError | null>(null)
  let seq = 0

  async function load(): Promise<void> {
    const current = ++seq
    loading.value = true
    error.value = null
    try {
      const result = await fetcher({ page: page.value, page_size: pageSize.value })
      if (current !== seq) {
        return
      }
      items.value = result.items
      total.value = result.total
    } catch (e) {
      if (current !== seq) {
        return
      }
      error.value = e as NormalizedError
    } finally {
      if (current === seq) {
        loading.value = false
      }
    }
  }

  function setPage(p: number): void {
    page.value = p
    void load()
  }

  function setPageSize(s: number): void {
    pageSize.value = s
    page.value = 1
    void load()
  }

  async function refresh(): Promise<void> {
    await load()
  }

  return { items, total, page, pageSize, loading, error, load, setPage, setPageSize, refresh }
}