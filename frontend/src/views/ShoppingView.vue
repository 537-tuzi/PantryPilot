<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-09"
    title="采购清单"
    desc="待购/已购条目。"
    :ops="['新增', '勾选', '删除']"
    todo="接入 /shopping-items；勾选只改状态，不自动入库、不自动下单（FR-016）。"
  />
</template>
