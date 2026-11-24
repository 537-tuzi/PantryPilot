<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import * as inventoryApi from '@/api/inventory'
import FourState from '@/components/FourState.vue'
import PageHeader from '@/components/PageHeader.vue'
import QuantityText from '@/components/QuantityText.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAsyncState } from '@/composables/useAsyncState'
import type { InventoryItem } from '@/types/api'
import { appToday, daysUntilDatePart } from '@/utils/appToday'

const router = useRouter()
const { data, loading, error, execute } = useAsyncState<InventoryItem[]>(() => inventoryApi.expiring())
const today = appToday()

const items = computed(() => data.value ?? [])
const expiredCount = computed(() => items.value.filter((i) => i.status === 'expired').length)
const expiringCount = computed(() => items.value.filter((i) => i.status === 'expiring').length)

onMounted(() => {
  void execute()
})

function daysLabel(item: InventoryItem): string {
  if (!item.expiry_date) {
    return '未设置到期日'
  }
  const d = daysUntilDatePart(item.expiry_date, today)
  if (d < 0) {
    return `已过期 ${-d} 天`
  }
  if (d === 0) {
    return '今天到期'
  }
  return `${d} 天后到期`
}

function viewInventory(item: InventoryItem): void {
  router.push({ name: 'inventory', query: { name: item.display_name } })
}
function goPlanner(): void {
  router.push({ name: 'planner' })
}
</script>

<template>
  <div>
    <PageHeader title="临期管理" description="临期/过期列表、到期日、剩余天数。状态由服务端按 3 天阈值计算。" page-id="UI-06">
      <template #actions>
        <el-button @click="goPlanner">去规划</el-button>
      </template>
    </PageHeader>
    <FourState
      :loading="loading"
      :error="error"
      :empty="!loading && !error && items.length === 0"
      empty-text="暂无临期或过期食材"
      @retry="execute"
    >
      <div class="expiry-summary">已过期 {{ expiredCount }} 项 · 临期 {{ expiringCount }} 项</div>
      <div class="expiry-list">
        <div v-for="item in items" :key="item.id" class="expiry-row">
          <span class="expiry-name">{{ item.display_name }}</span>
          <QuantityText :quantity="item.quantity" :unit="item.unit" />
          <span>{{ item.expiry_date }}</span>
          <span>{{ daysLabel(item) }}</span>
          <StatusTag :status="item.status" />
          <el-button size="small" @click="viewInventory(item)">查看库存</el-button>
        </div>
      </div>
    </FourState>
  </div>
</template>

<style scoped>
.expiry-summary {
  margin-bottom: 12px;
  color: #64748b;
  font-size: 13px;
}
.expiry-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.expiry-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid var(--pp-line);
  border-radius: 8px;
  padding: 12px 16px;
}
.expiry-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 760px) {
  .expiry-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>