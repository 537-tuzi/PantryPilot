/** 响应式断点（matchMedia 可 mock，使 jsdom 可断言窄屏卡片）。归属：A 组。 */
import { onScopeDispose, ref, type Ref } from 'vue'

export function useMediaQuery(query: string): Ref<boolean> {
  const matches = ref(false)
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mql = window.matchMedia(query)
    matches.value = mql.matches
    const handler = (e: MediaQueryListEvent): void => {
      matches.value = e.matches
    }
    mql.addEventListener?.('change', handler)
    onScopeDispose(() => mql.removeEventListener?.('change', handler))
  }
  return matches
}