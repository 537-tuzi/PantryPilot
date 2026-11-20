<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-10"
    title="个人偏好"
    desc="过敏原、忌口、喜欢/不喜欢、默认人数。"
    :ops="['保存']"
    todo="接入 /users/me/preferences；过敏原与忌口为服务端硬约束，前端不得仅做提示（FR-004）。"
  />
</template>
