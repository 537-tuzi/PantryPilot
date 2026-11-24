import { expect, it, vi } from 'vitest'
import { ElMessageBox } from 'element-plus'

import { useAsyncState } from '@/composables/useAsyncState'
import { usePagination } from '@/composables/usePagination'
import { useConfirm } from '@/composables/useConfirm'
import type { PageResult } from '@/types/api'

it('useAsyncState execute 成功写 data', async () => {
  const { data, loading, error, execute } = useAsyncState(async () => 42)
  const result = await execute()
  expect(result).toBe(42)
  expect(data.value).toBe(42)
  expect(loading.value).toBe(false)
  expect(error.value).toBeNull()
})

it('useAsyncState 失败写 error', async () => {
  const err = { code: 'NETWORK_ERROR', message: 'x', requestId: '', status: 0 }
  const { data, error, execute } = useAsyncState(async () => {
    throw err
  })
  const result = await execute()
  expect(result).toBeNull()
  expect(data.value).toBeNull()
  expect(error.value).toEqual(err)
})

it('usePagination setPageSize 重置 page=1', () => {
  const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 })
  const { page, setPageSize } = usePagination(fetcher)
  page.value = 3
  setPageSize(50)
  expect(page.value).toBe(1)
  expect(fetcher).toHaveBeenCalledWith({ page: 1, page_size: 50 })
})

it('usePagination 丢弃过期响应', async () => {
  let resolveFirst: (v: PageResult<string>) => void = () => {}
  const fetcher = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise<PageResult<string>>((r) => {
          resolveFirst = r
        }),
    )
    .mockImplementationOnce(() =>
      Promise.resolve({ items: ['fast'], total: 1, page: 1, page_size: 20 }),
    )
  const { items, load } = usePagination<string>(fetcher)
  const first = load()
  const second = load()
  await second
  expect(items.value).toEqual(['fast'])
  resolveFirst({ items: ['slow'], total: 1, page: 1, page_size: 20 })
  await first
  expect(items.value).toEqual(['fast'])
})

it('useConfirm 取消 resolve false', async () => {
  vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce('cancel')
  const result = await useConfirm({ title: 't', message: 'm' })
  expect(result).toBe(false)
})

it('useConfirm 确认 resolve true', async () => {
  vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm' as never)
  const result = await useConfirm({ title: 't', message: 'm' })
  expect(result).toBe(true)
})