<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{ success: []; error: [err: NormalizedError] }>()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const form = reactive({ email: '', password: '' })

// 登录密码仅长度 8~128（强度校验只在注册）。
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度 8~128 位', trigger: 'blur' },
  ],
}

async function onSubmit(event?: Event): Promise<void> {
  event?.preventDefault()
  if (submitting.value) {
    return
  }
  formRef.value?.validate().catch(() => {})
  // 确定性守卫：登录密码仅长度 8~128（强度只在注册）；邮箱格式。
  const email = form.email.trim()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || form.password.length < 8 || form.password.length > 128) {
    return
  }
  submitting.value = true
  try {
    await auth.login(email, form.password)
    emit('success')
  } catch (e) {
    emit('error', e as NormalizedError)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-position="top" novalidate @submit.prevent="onSubmit">
    <el-form-item label="邮箱" prop="email">
      <el-input v-model="form.email" autocomplete="username" placeholder="you@example.com" />
    </el-form-item>
    <el-form-item label="密码" prop="password">
      <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="submitting" :disabled="submitting" class="submit-btn">
      登录
    </el-button>
  </el-form>
</template>

<style scoped>
.submit-btn {
  width: 100%;
}
</style>