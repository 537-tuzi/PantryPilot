<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <el-empty description="AI 膳食规划将在 Sprint 2 开放（后端 /ai/meal-plans 待实现）。">
    <el-button type="primary" @click="router.push({ name: 'home' })">
      返回首页
    </el-button>
  </el-empty>
</template>