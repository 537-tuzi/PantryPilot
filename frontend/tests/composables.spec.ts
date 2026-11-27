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

it('useAsyncState 丢弃过期响应（后发先到的旧请求不覆盖新数据）', async () => {
  let resolveFirst: (v: string) => void = () => {}
  const fn = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise<string>((r) => {
          resolveFirst = r
        }),
    )
    .mockImplementationOnce(() => Promise.resolve('fresh'))
  const { data, error, execute } = useAsyncState(fn)
  const first = execute()
  const second = execute()
  await second
  expect(data.value).toBe('fresh')
  resolveFirst('stale')
  await first
  expect(data.value).toBe('fresh')
  expect(error.value).toBeNull()
})

it('useAsyncState 过期请求失败不覆盖新请求的成功结果', async () => {
  const staleErr = { code: 'NETWORK_ERROR', message: 'stale failed', requestId: '', status: 0 }
  let rejectFirst: (e: unknown) => void = () => {}
  const fn = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise<string>((_r, reject) => {
          rejectFirst = reject
        }),
    )
    .mockImplementationOnce(() => Promise.resolve('fresh'))
  const { data, error, loading, execute } = useAsyncState(fn)
  const first = execute()
  const second = execute()
  await second
  expect(data.value).toBe('fresh')
  expect(loading.value).toBe(false)
  rejectFirst(staleErr)
  await first
  // 旧请求的失败不应把界面打成错误态
  expect(error.value).toBeNull()
  expect(data.value).toBe('fresh')
  expect(loading.value).toBe(false)
})

it('useAsyncState reset 让在途请求失效', async () => {
  let resolveFirst: (v: string) => void = () => {}
  const fn = vi.fn().mockImplementationOnce(
    () =>
      new Promise<string>((r) => {
        resolveFirst = r
      }),
  )
  const { data, loading, execute, reset } = useAsyncState(fn)
  const pending = execute()
  reset()
  expect(data.value).toBeNull()
  expect(loading.value).toBe(false)
  resolveFirst('late')
  await pending
  // reset 之后旧响应不应把数据写回来
  expect(data.value).toBeNull()
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