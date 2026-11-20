<script setup lang="ts">
import PlaceholderView from '@/components/PlaceholderView.vue'
</script>

<template>
  <PlaceholderView
    page-id="UI-01"
    title="登录 / 注册"
    desc="账号、密码、错误提示。"
    :ops="['登录', '注册', '退出']"
    todo="接入 /auth/register、/auth/login；令牌存入 store；错误提示不得泄露账号是否存在。"
  />
</template>
