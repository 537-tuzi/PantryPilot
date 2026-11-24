import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'

/**
 * 路由与 文档/03 §3 的页面清单一一对应。归属：A 组。
 * login 为公开兄弟路由；其余套 AppLayout 壳。catch-all 置最后。
 */
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { pageId: 'UI-01', public: true, title: '登录' },
    },
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { pageId: 'UI-02', title: '首页概览' } },
        { path: 'inventory', name: 'inventory', component: () => import('@/views/InventoryView.vue'), meta: { pageId: 'UI-03', title: '食材库存' } },
        { path: 'inventory/new', name: 'ingredient-form', component: () => import('@/views/IngredientFormView.vue'), meta: { pageId: 'UI-04', title: '新增食材' } },
        { path: 'inventory/:id/edit', name: 'ingredient-edit', component: () => import('@/views/IngredientFormView.vue'), meta: { pageId: 'UI-04', title: '编辑食材' } },
        { path: 'ai-entry', name: 'ai-entry', component: () => import('@/views/AiEntryView.vue'), meta: { pageId: 'UI-05', title: 'AI 录入', deferred: true } },
        { path: 'expiry', name: 'expiry', component: () => import('@/views/ExpiryView.vue'), meta: { pageId: 'UI-06', title: '临期管理' } },
        { path: 'planner', name: 'planner', component: () => import('@/views/PlannerView.vue'), meta: { pageId: 'UI-07', title: 'AI 膳食规划', deferred: true } },
        { path: 'plans/:id', name: 'plan-result', component: () => import('@/views/PlanResultView.vue'), meta: { pageId: 'UI-08', title: '计划结果', deferred: true } },
        { path: 'shopping', name: 'shopping', component: () => import('@/views/ShoppingView.vue'), meta: { pageId: 'UI-09', title: '采购清单' } },
        { path: 'preferences', name: 'preferences', component: () => import('@/views/PreferencesView.vue'), meta: { pageId: 'UI-10', title: '个人偏好' } },
        { path: ':pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue'), meta: { title: '页面不存在' } },
      ],
    },
  ],
})

export default router