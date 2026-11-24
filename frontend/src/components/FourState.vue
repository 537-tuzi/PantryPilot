<script setup lang="ts">
/** 四态容器：加载/错误/空/默认。权限失效由全局 401 处理器满足，不在此内联。 */
import type { NormalizedError } from '@/api/client'

withDefaults(
  defineProps<{
    loading: boolean
    error?: NormalizedError | null
    empty?: boolean
    emptyText?: string
    loadingRows?: number
  }>(),
  { error: null, empty: false, emptyText: '暂无数据', loadingRows: 3 },
)

defineEmits<{ retry: [] }>()
</script>

<template>
  <el-skeleton v-if="loading" :rows="loadingRows" animated />
  <div v-else-if="error" class="pp-four-state-error">
    <el-alert type="error" :title="error.message" :closable="false" />
    <el-button type="primary" @click="$emit('retry')">重试</el-button>
    <span class="muted">request_id: {{ error.requestId }}</span>
  </div>
  <el-empty v-else-if="empty" :description="emptyText" />
  <slot v-else />
</template>

<style scoped>
.pp-four-state-error {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}
.muted {
  color: #64748b;
  font-size: 12px;
}
</style>