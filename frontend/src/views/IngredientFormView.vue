<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-04"
    title="食材表单"
    desc="名称、数量、单位、日期、存储位置。"
    :ops="['保存', '取消']"
    todo="按 文档/03 §5 校验：名称 1~80 字；数量 >0 且最多 3 位小数；到期日早于购买日需提示确认。"
  />
</template>
