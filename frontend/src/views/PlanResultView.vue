<script setup lang="ts">
import { useRouter } from 'vue-router'

// Sprint 1 不调用任何计划/确认 API（计划生成属 Sprint 2，确认扣减属 Sprint 3）。
const router = useRouter()
</script>

<template>
  <el-empty description="计划结果与确认扣减将在 Sprint 2/3 开放。确认契约（Idempotency-Key + 行级 meal_plan_ingredient_id）已冻结。">
    <el-button type="primary" @click="router.push({ name: 'home' })">
      返回首页
    </el-button>
  </el-empty>
</template>