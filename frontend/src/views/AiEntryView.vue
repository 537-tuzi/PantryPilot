<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <el-empty description="AI 自然语言录入将在 Sprint 2 开放（后端 /ai/ingredient-drafts 待实现）。库存手动录入请前往食材库存。">
    <el-button type="primary" @click="router.push({ name: 'inventory' })">
      前往食材库存
    </el-button>
  </el-empty>
</template>