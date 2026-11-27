<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{ success: []; error: [err: NormalizedError] }>()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const validationError = ref('')
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })

// 镜像后端 Unicode-aware 强度（str.islower/isupper/isdigit）；confirmPassword 仅前端。
const lengthOk = computed(() => form.password.length >= 8 && form.password.length <= 128)
const hasLower = computed(() => /\p{Ll}/u.test(form.password))
const hasUpper = computed(() => /\p{Lu}/u.test(form.password))
const hasDigit = computed(() => /\p{Nd}/u.test(form.password))
const emailOk = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim()))
const usernameOk = computed(() => {
  const t = form.username.trim()
  return t.length >= 1 && t.length <= 100
})
const passwordOk = computed(() => lengthOk.value && hasLower.value && hasUpper.value && hasDigit.value)

// el-form 规则用于生产字段级 UX；提交门禁由 onSubmit 确定性守卫保证。
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }],
}

async function onSubmit(event?: Event): Promise<void> {
  event?.preventDefault()
  if (submitting.value) {
    return
  }
  formRef.value?.validate().catch(() => {})
  // 确定性守卫：后端 400 无字段细节，前端必须完整镜像规则；失败给内联反馈。
  validationError.value = ''
  if (!usernameOk.value) {
    validationError.value = '用户名需 1~100 字'
    return
  }
  if (!emailOk.value) {
    validationError.value = '邮箱格式不正确'
    return
  }
  if (!passwordOk.value) {
    validationError.value = '密码需 8~128 位且含大小写字母与数字'
    return
  }
  if (form.confirmPassword !== form.password) {
    validationError.value = '两次密码不一致'
    return
  }
  submitting.value = true
  try {
    await auth.register(form.username.trim(), form.email.trim(), form.password)
    emit('success')
  } catch (e) {
    emit('error', e as NormalizedError)
  } finally {
    submitting.value = false
  }
}

defineExpose({ form, onSubmit, validationError })
</script>

<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-position="top" novalidate @submit.prevent="onSubmit">
    <el-form-item label="用户名" prop="username">
      <el-input v-model="form.username" maxlength="100" autocomplete="nickname" />
    </el-form-item>
    <el-form-item label="邮箱" prop="email">
      <el-input v-model="form.email" autocomplete="username" />
    </el-form-item>
    <el-form-item label="密码" prop="password">
      <el-input v-model="form.password" type="password" show-password autocomplete="new-password" />
    </el-form-item>
    <ul class="pwd-checklist">
      <li :class="{ ok: lengthOk }">
        8~128 位
      </li>
      <li :class="{ ok: hasLower }">
        含小写字母
      </li>
      <li :class="{ ok: hasUpper }">
        含大写字母
      </li>
      <li :class="{ ok: hasDigit }">
        含数字
      </li>
    </ul>
    <el-form-item label="确认密码" prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" show-password autocomplete="new-password" />
    </el-form-item>
    <el-alert
      v-if="validationError"
      type="error"
      :title="validationError"
      :closable="false"
      class="register-error"
    />
    <el-button type="primary" native-type="submit" :loading="submitting" :disabled="submitting" class="submit-btn">
      注册
    </el-button>
  </el-form>
</template>

<style scoped>
.submit-btn {
  width: 100%;
}
.pwd-checklist {
  list-style: none;
  padding: 0;
  margin: 0 0 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}
.pwd-checklist li.ok {
  color: #2b8a3e;
}
</style>