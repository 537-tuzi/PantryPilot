/** 异步状态桥接 FourState；序号守卫丢弃过期响应。归属：A 组。 */
import { ref, type Ref } from 'vue'

import type { NormalizedError } from '@/api/client'

export interface AsyncState<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<NormalizedError | null>
  execute: () => Promise<T | null>
  reset: () => void
}

export function useAsyncState<T>(fn: () => Promise<T>, opts: { immediate?: boolean } = {}): AsyncState<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<NormalizedError | null>(null)
  // 序号守卫：并发 execute() 时只有最后一次可以写 data/error/loading，
  // 避免先发后到的旧响应覆盖新数据（旧响应失败时也不应把新成功结果打成错误态）。
  // 与 usePagination 的守卫同一套约定。
  let seq = 0

  async function execute(): Promise<T | null> {
    const current = ++seq
    loading.value = true
    error.value = null
    try {
      const result = await fn()
      if (current !== seq) {
        return null
      }
      data.value = result
      return result
    } catch (e) {
      if (current !== seq) {
        return null
      }
      error.value = e as NormalizedError
      return null
    } finally {
      if (current === seq) {
        loading.value = false
      }
    }
  }

  function reset(): void {
    // 让在途请求失效，否则 reset 之后旧响应仍会把数据写回来
    seq += 1
    data.value = null
    error.value = null
    loading.value = false
  }

  if (opts.immediate) {
    void execute()
  }

  return { data, loading, error, execute, reset }
}
