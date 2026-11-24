/** 同步 token 守卫 + redirect 净化 + 401 标志重置。归属：A 组。 */
import type { Router } from 'vue-router'

import { resetUnauthorizedFlag } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

/** 仅接受站内相对路径，拒绝协议相对/绝对 URL 与 /login，防开放重定向。 */
export function sanitizeRedirect(redirect: unknown): string {
  if (typeof redirect !== 'string') {
    return '/'
  }
  if (!redirect.startsWith('/') || redirect.startsWith('//') || redirect.startsWith('/login')) {
    return '/'
  }
  return redirect
}

export function setupGuards(router: Router): void {
  router.beforeEach((to) => {
    const auth = useAuthStore()
    if (to.name === 'login') {
      return auth.isAuthenticated ? { name: 'home' } : true
    }
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    return true
  })

  router.afterEach((to) => {
    document.title = `${(to.meta.title as string | undefined) ?? ''} · 食刻管家`
    resetUnauthorizedFlag()
  })
}