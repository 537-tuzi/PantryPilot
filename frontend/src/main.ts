import ElementPlus, { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { setupGuards } from './router/guards'
import { setUnauthorizedHandler } from './api/client'
import { useAuthStore } from './stores/auth'
import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

setupGuards(router)

// 全局 401：清 token + 提示 + 跳登录（保留 intended redirect）。注册式避免循环依赖。
setUnauthorizedHandler(() => {
  const auth = useAuthStore()
  const hadToken = auth.isAuthenticated
  auth.clear()
  if (hadToken) {
    ElMessage.warning('登录已过期，请重新登录')
  }
  const cur = router.currentRoute.value
  if (cur.name !== 'login') {
    router.replace({ name: 'login', query: { redirect: cur.fullPath } })
  }
})

app.config.errorHandler = (err) => {
  console.error('[app error]', err)
}
window.addEventListener('unhandledrejection', (event) => {
  console.error('[unhandled rejection]', event.reason)
})

app.mount('#app')