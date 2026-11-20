<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-02"
    title="首页概览"
    desc="库存统计、临期卡片、快捷入口。"
    :ops="['新增食材', '查看临期', '开始规划']"
    todo="接入 /dashboard/summary；统计口径必须与列表一致（FR-010）；待消耗食材按剩余天数升序。"
  />
</template>
