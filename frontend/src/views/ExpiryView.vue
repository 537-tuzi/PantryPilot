<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-06"
    title="临期管理"
    desc="临期/过期列表、到期日、剩余天数。"
    :ops="['查看库存', '去规划']"
    todo="接入 /inventory/expiring；状态由服务端按 3 天阈值计算，前端不自行判定（FR-009）。"
  />
</template>
