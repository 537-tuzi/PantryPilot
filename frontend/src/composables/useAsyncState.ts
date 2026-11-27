/** 异步状态桥接 FourState。归属：A 组。 */
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

  async function execute(): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await fn()
      data.value = result
      return result
    } catch (e) {
      error.value = e as NormalizedError
      return null
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    data.value = null
    error.value = null
    loading.value = false
  }

  if (opts.immediate) {
    void execute()
  }

  return { data, loading, error, execute, reset }
}