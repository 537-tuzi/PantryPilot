<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-08"
    title="计划结果"
    desc="菜谱、用量、步骤、缺失项、约束说明。"
    :ops="['确认用量', '加采购清单']"
    todo="确认时携带 Idempotency-Key 调用 /meal-plans/{id}/confirm；确认前不得改动库存（FR-014/015）。"
  />
</template>
