<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-03"
    title="食材库存"
    desc="搜索、分类/状态筛选、分页。"
    :ops="['新增', '编辑', '耗尽']"
    todo="接入 /inventory；数量与单位同时展示；耗尽与删除需二次确认并保留流水（FR-006~FR-008）。"
  />
</template>
