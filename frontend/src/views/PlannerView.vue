<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-07"
    title="AI 膳食规划"
    desc="人数、预算、时间、偏好、补充要求。"
    :ops="['生成', '重新生成']"
    todo="接入 /ai/meal-plans；人数 1~12、预算非负、时间正整数；生成期间展示加载态（FR-012）。"
  />
</template>
