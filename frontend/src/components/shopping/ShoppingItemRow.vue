<script setup lang="ts">
import { computed } from 'vue'

import QuantityText from '@/components/QuantityText.vue'
import type { ShoppingItem, ShoppingStatus } from '@/types/api'

const props = withDefaults(defineProps<{ item: ShoppingItem; pending?: boolean }>(), { pending: false })
const emit = defineEmits<{
  toggle: [item: ShoppingItem]
  cancel: [item: ShoppingItem]
  restore: [item: ShoppingItem]
  remove: [item: ShoppingItem]
}>()

const STATUS_TEXT: Record<ShoppingStatus, string> = { pending: '待购', purchased: '已购', cancelled: '已取消' }
const checked = computed(() => props.item.status === 'purchased')
const checkboxDisabled = computed(() => props.item.status === 'cancelled' || props.pending)
</script>

<template>
  <div class="shop-row">
    <el-checkbox :model-value="checked" :disabled="checkboxDisabled" @change="emit('toggle', item)" />
    <span class="shop-name" :class="{ done: checked }">{{ item.display_name }}</span>
    <QuantityText :quantity="item.quantity" :unit="item.unit" />
    <span class="shop-status" :class="`shop-status--${item.status}`">{{ STATUS_TEXT[item.status] }}</span>
    <span class="shop-actions">
      <el-button v-if="item.status !== 'cancelled'" size="small" @click="emit('cancel', item)">取消</el-button>
      <el-button v-else size="small" @click="emit('restore', item)">恢复</el-button>
      <el-button size="small" type="danger" @click="emit('remove', item)">删除</el-button>
    </span>
  </div>
</template>

<style scoped>
.shop-row {
  display: grid;
  grid-template-columns: auto 2fr 1fr 1fr auto;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid var(--pp-line);
  border-radius: 8px;
  padding: 12px 16px;
}
.shop-name.done {
  text-decoration: line-through;
  color: #94a3b8;
}
.shop-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
}
.shop-status--pending {
  background: #eef4fb;
  color: #2b4c7e;
}
.shop-status--purchased {
  background: #e8f5e9;
  color: #2b8a3e;
}
.shop-status--cancelled {
  background: #f1f5f9;
  color: #64748b;
}
.shop-actions {
  display: flex;
  gap: 4px;
}
@media (max-width: 760px) {
  .shop-row {
    grid-template-columns: auto 1fr;
  }
  .shop-actions {
    grid-column: 1 / -1;
  }
}
</style>