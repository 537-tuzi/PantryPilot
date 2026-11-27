<script setup lang="ts">
/** 硬约束告知：不宣称"现已拦截"（confirm 尚无过敏原校验），也不降级为"仅提示"。 */
</script>

<template>
  <el-alert
    type="warning"
    :closable="false"
    title="过敏原与忌口是服务端校验的硬约束，将参与 AI 膳食规划校验（Sprint 2 上线），请如实填写。"
  />
</template>