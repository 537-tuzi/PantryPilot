<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import * as dashboardApi from '@/api/dashboard'
import * as inventoryApi from '@/api/inventory'
import PageHeader from '@/components/PageHeader.vue'
import QuantityText from '@/components/QuantityText.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAsyncState } from '@/composables/useAsyncState'
import type { DashboardSummary, InventoryItem } from '@/types/api'
import { daysUntilDatePart } from '@/utils/appToday'

const router = useRouter()
const summaryState = useAsyncState<DashboardSummary>(() => dashboardApi.summary())
const expiringState = useAsyncState<InventoryItem[]>(() => inventoryApi.expiring())

const summary = computed(() => summaryState.data.value)
// "今天"取服务端 statistics_date（应用时区），不用客户端时钟；summary 失败时抑制天数文案。
const today = computed(() => summary.value?.statistics_date ?? '')
const expiringCards = computed(() =>
  (expiringState.data.value ?? []).filter((i) => i.status === 'expiring').slice(0, 6),
)

onMounted(() => {
  void summaryState.execute()
  void expiringState.execute()
})

function daysLabel(item: InventoryItem): string {
  if (!today.value || !item.expiry_date) {
    return ''
  }
  const d = daysUntilDatePart(item.expiry_date, today.value)
  if (d < 0) {
    return `已过期 ${-d} 天`
  }
  return d === 0 ? '今天到期' : `${d} 天后到期`
}
</script>

<template>
  <div>
    <PageHeader title="首页概览" description="库存统计、临期卡片、快捷入口。" page-id="UI-02" />

    <div class="stat-cards">
      <div class="stat-card" @click="router.push({ name: 'inventory' })">
        <span class="stat-label">库存总数</span>
        <strong class="stat-value">{{ summary?.inventory_count ?? '—' }}</strong>
        <span class="stat-hint">列表含已耗尽条目，与统计口径不同</span>
      </div>
      <div class="stat-card" @click="router.push({ name: 'expiry' })">
        <span class="stat-label">临期</span>
        <strong class="stat-value">{{ summary?.expiring_count ?? '—' }}</strong>
      </div>
      <div class="stat-card" @click="router.push({ name: 'expiry' })">
        <span class="stat-label">过期</span>
        <strong class="stat-value">{{ summary?.expired_count ?? '—' }}</strong>
      </div>
    </div>
    <p v-if="summary" class="stat-date">
      统计日期 {{ summary.statistics_date }}
    </p>

    <div class="quick-actions">
      <el-button type="primary" @click="router.push({ name: 'ingredient-form' })">
        新增食材
      </el-button>
      <el-button @click="router.push({ name: 'expiry' })">
        查看临期
      </el-button>
      <el-tooltip content="AI 膳食规划将在 Sprint 2 开放" placement="top">
        <span>
          <el-button disabled>
            开始规划
          </el-button>
        </span>
      </el-tooltip>
    </div>

    <section class="expiring-section">
      <h2>待消耗食材</h2>
      <div v-if="expiringState.loading.value" class="muted">
        加载中…
      </div>
      <div v-else-if="expiringState.error.value" class="muted">
        加载失败
        <el-button size="small" @click="expiringState.execute()">
          重试
        </el-button>
      </div>
      <div v-else-if="expiringCards.length === 0" class="muted">
        暂无临期食材
      </div>
      <div v-else>
        <div class="expiring-cards">
          <div v-for="item in expiringCards" :key="item.id" class="expiring-card">
            <span class="expiring-name">{{ item.display_name }}</span>
            <QuantityText :quantity="item.quantity" :unit="item.unit" />
            <span>{{ daysLabel(item) }}</span>
            <StatusTag :status="item.status" />
          </div>
        </div>
        <el-button size="small" @click="router.push({ name: 'expiry' })">
          查看全部
        </el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 8px;
}
.stat-card {
  background: #fff;
  border: 1px solid var(--pp-line);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-label {
  color: #64748b;
  font-size: 13px;
}
.stat-value {
  font-size: 28px;
  color: var(--pp-navy);
}
.stat-hint {
  color: #94a3b8;
  font-size: 11px;
}
.stat-date {
  color: #64748b;
  font-size: 12px;
  margin: 0 0 16px;
}
.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}
.expiring-section h2 {
  font-size: 16px;
  color: var(--pp-ink);
}
.expiring-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.expiring-card {
  background: #fff;
  border: 1px solid var(--pp-line);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.expiring-name {
  font-weight: 600;
}
.muted {
  color: #64748b;
}
</style>