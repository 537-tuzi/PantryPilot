<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-05"
    title="AI 自然语言录入"
    desc="自然语言输入、解析草稿、字段编辑。"
    :ops="['解析', '确认', '取消']"
    todo="接入 /ai/ingredient-drafts；草稿必须显式标注为草稿；确认后才写入库存（FR-011）。"
  />
</template>
