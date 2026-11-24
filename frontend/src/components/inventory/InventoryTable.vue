<script setup lang="ts">
import QuantityText from '@/components/QuantityText.vue'
import StatusTag from '@/components/StatusTag.vue'
import type { InventoryItem } from '@/types/api'

defineProps<{ items: InventoryItem[] }>()
const emit = defineEmits<{
  edit: [item: InventoryItem]
  consume: [item: InventoryItem]
  archive: [item: InventoryItem]
}>()

function isArchived(item: InventoryItem): boolean {
  return item.archived_at !== null
}
function isDepleted(item: InventoryItem): boolean {
  return Number(item.quantity) === 0
}
</script>

<template>
  <div class="inv-list">
    <div v-for="item in items" :key="item.id" class="inv-row">
      <span class="inv-name" :title="item.display_name">{{ item.display_name }}</span>
      <span class="inv-qty"><QuantityText :quantity="item.quantity" :unit="item.unit" /></span>
      <span class="inv-status"><StatusTag :status="item.status" /></span>
      <span class="inv-date">{{ item.expiry_date ?? '—' }}</span>
      <span class="inv-actions">
        <el-button size="small" :disabled="isArchived(item)" @click="emit('edit', item)">编辑</el-button>
        <el-button size="small" :disabled="isArchived(item) || isDepleted(item)" @click="emit('consume', item)">
          耗尽
        </el-button>
        <el-button size="small" type="danger" @click="emit('archive', item)">删除</el-button>
      </span>
    </div>
  </div>
</template>

<style scoped>
.inv-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.inv-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr auto;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid var(--pp-line);
  border-radius: 8px;
  padding: 12px 16px;
}
.inv-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inv-actions {
  display: flex;
  gap: 4px;
}
@media (max-width: 760px) {
  .inv-row {
    grid-template-columns: 1fr 1fr;
  }
  .inv-actions {
    grid-column: 1 / -1;
  }
}
</style>