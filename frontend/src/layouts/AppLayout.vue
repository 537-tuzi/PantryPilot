<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const navItems = [
  { name: 'home', label: '首页概览' },
  { name: 'inventory', label: '食材库存' },
  { name: 'expiry', label: '临期管理' },
  { name: 'planner', label: 'AI 膳食规划' },
  { name: 'shopping', label: '采购清单' },
  { name: 'preferences', label: '个人偏好' },
]

onMounted(() => {
  if (auth.token && !auth.user) {
    auth.fetchMe().catch(() => {})
  }
})

function onCommand(command: string): void {
  if (command === 'preferences') {
    router.push({ name: 'preferences' })
  } else if (command === 'logout') {
    auth.logout()
    router.push({ name: 'login' })
    ElMessage.success('已退出登录')
  }
}
</script>

<template>
  <div class="layout">
    <header class="header">
      <span class="brand">食刻管家 PantryPilot · AI 家庭食材管理</span>
      <el-dropdown @command="onCommand">
        <span class="user-trigger">
          {{ auth.user?.username ?? '我的账号' }}
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="preferences">
              个人偏好
            </el-dropdown-item>
            <el-dropdown-item command="logout">
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </header>
    <div class="body">
      <aside class="sidebar">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav"
          active-class="nav-active"
        >
          {{ item.label }}
        </RouterLink>
      </aside>
      <main class="main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid var(--pp-line);
  padding: 14px 24px;
}
.brand {
  font-size: 18px;
  font-weight: bold;
  color: var(--pp-navy);
}
.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: var(--pp-ink);
  font-size: 14px;
}
.body {
  display: grid;
  grid-template-columns: 200px 1fr;
  min-height: calc(100vh - 53px);
}
.sidebar {
  background: #fff;
  border-right: 1px solid var(--pp-line);
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.nav {
  display: block;
  padding: 9px 12px;
  border-radius: 8px;
  color: var(--pp-ink);
  text-decoration: none;
  font-size: 14px;
}
.nav:hover {
  background: #eaf1f8;
}
.nav-active {
  background: #eaf1f8;
  color: var(--pp-navy);
  font-weight: 600;
}
.main {
  padding: 24px;
  overflow: auto;
}
@media (max-width: 760px) {
  .body {
    grid-template-columns: 1fr;
  }
  .sidebar {
    flex-direction: row;
    overflow-x: auto;
  }
}
</style>