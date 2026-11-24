<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { NormalizedError } from '@/api/client'
import LoginForm from '@/components/auth/LoginForm.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'
import { sanitizeRedirect } from '@/router/guards'
import { mapErrorMessage } from '@/utils/errorMap'

const route = useRoute()
const router = useRouter()
const mode = ref<'login' | 'register'>('login')
const apiError = ref<NormalizedError | null>(null)

// 认证错误专用文案：登录 401 统一"邮箱或密码错误"（不泄露账号是否存在）；注册 409 统一冲突。
const errorText = computed(() => {
  const err = apiError.value
  if (!err) {
    return ''
  }
  if (mode.value === 'login' && err.code === 'UNAUTHENTICATED') {
    return '邮箱或密码错误'
  }
  if (mode.value === 'login' && err.code === 'FORBIDDEN') {
    return '账号已被禁用，请联系管理员'
  }
  if (mode.value === 'register' && err.code === 'STATE_CONFLICT') {
    return '用户名或邮箱已被注册'
  }
  return mapErrorMessage(err)
})

function onSuccess(): void {
  apiError.value = null
  router.push(sanitizeRedirect(route.query.redirect))
}

function onError(err: NormalizedError): void {
  apiError.value = err
}

function onTabChange(): void {
  apiError.value = null
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h1 class="auth-title">食刻管家 PantryPilot</h1>
      <el-tabs v-model="mode" @tab-change="onTabChange">
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>
      <el-alert
        v-if="apiError"
        type="error"
        :title="errorText"
        :closable="true"
        role="alert"
        class="auth-error"
        @close="apiError = null"
      />
      <LoginForm v-if="mode === 'login'" @success="onSuccess" @error="onError" />
      <RegisterForm v-else @success="onSuccess" @error="onError" />
    </el-card>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--pp-bg);
  padding: 16px;
}
.auth-card {
  width: 420px;
  max-width: 100%;
}
.auth-title {
  color: var(--pp-navy);
  text-align: center;
  font-size: 20px;
  margin: 0 0 12px;
}
.auth-error {
  margin-bottom: 12px;
}
</style>