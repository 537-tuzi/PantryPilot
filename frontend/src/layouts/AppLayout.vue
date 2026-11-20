<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { name: 'home', label: '首页概览' },
  { name: 'inventory', label: '食材库存' },
  { name: 'expiry', label: '临期管理' },
  { name: 'planner', label: 'AI 膳食规划' },
  { name: 'shopping', label: '采购清单' },
  { name: 'preferences', label: '个人偏好' },
]
</script>

<template>
  <div class="layout">
    <header class="header">
      食刻管家 PantryPilot · AI 家庭食材管理
    </header>
    <div class="body">
      <aside class="sidebar">
        <RouterLink v-for="item in navItems" :key="item.name" :to="{ name: item.name }" class="nav">
          {{ item.label }}
        </RouterLink>
      </aside>
      <main class="main">
        <RouterView v-if="route.name !== 'login'" />
        <RouterView v-else />
      </main>
    </div>
  </div>
</template>

<style scoped>
.header {
  background: #fff;
  border-bottom: 1px solid #e3eaf2;
  padding: 14px 24px;
  font-size: 18px;
  font-weight: bold;
  color: #2b4c7e;
}

.body {
  display: grid;
  grid-template-columns: 200px 1fr;
  min-height: calc(100vh - 53px);
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e3eaf2;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav {
  display: block;
  padding: 9px 12px;
  border-radius: 8px;
  color: #0d1b2a;
  text-decoration: none;
  font-size: 14px;
}

.nav:hover {
  background: #eaf1f8;
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
