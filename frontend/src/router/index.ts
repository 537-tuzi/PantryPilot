import { createRouter, createWebHistory } from 'vue-router'

/**
 * 路由与 文档/03 §3 的页面清单一一对应。
 * 归属：A 组（前端/产品协调）。
 */
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { pageId: 'UI-01' } },
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { pageId: 'UI-02' } },
    { path: '/inventory', name: 'inventory', component: () => import('@/views/InventoryView.vue'), meta: { pageId: 'UI-03' } },
    { path: '/inventory/new', name: 'ingredient-form', component: () => import('@/views/IngredientFormView.vue'), meta: { pageId: 'UI-04' } },
    { path: '/ai-entry', name: 'ai-entry', component: () => import('@/views/AiEntryView.vue'), meta: { pageId: 'UI-05' } },
    { path: '/expiry', name: 'expiry', component: () => import('@/views/ExpiryView.vue'), meta: { pageId: 'UI-06' } },
    { path: '/planner', name: 'planner', component: () => import('@/views/PlannerView.vue'), meta: { pageId: 'UI-07' } },
    { path: '/plans/:id', name: 'plan-result', component: () => import('@/views/PlanResultView.vue'), meta: { pageId: 'UI-08' } },
    { path: '/shopping', name: 'shopping', component: () => import('@/views/ShoppingView.vue'), meta: { pageId: 'UI-09' } },
    { path: '/preferences', name: 'preferences', component: () => import('@/views/PreferencesView.vue'), meta: { pageId: 'UI-10' } },
  ],
})

export default router
