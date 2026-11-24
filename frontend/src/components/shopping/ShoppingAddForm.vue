<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import * as shoppingApi from '@/api/shopping'
import DecimalInput from '@/components/DecimalInput.vue'
import { compareDecimal, isValidDecimal } from '@/utils/decimal'
import { mapErrorMessage } from '@/utils/errorMap'

const emit = defineEmits<{ created: [] }>()
const form = reactive({ display_name: '', quantity: '', unit: '' })
const submitting = ref(false)
const error = ref('')

async function onSubmit(event?: Event): Promise<void> {
  event?.preventDefault()
  if (submitting.value) {
    return
  }
  error.value = ''
  const name = form.display_name.trim()
  const unit = form.unit.trim()
  if (name.length < 1 || name.length > 200) {
    error.value = '名称需 1~200 字'
    return
  }
  if (!isValidDecimal(form.quantity, 3, 9) || compareDecimal(form.quantity, '0') <= 0) {
    error.value = '数量需大于 0 且最多 3 位小数'
    return
  }
  if (unit.length < 1 || unit.length > 32) {
    error.value = '单位需 1~32 字'
    return
  }
  submitting.value = true
  try {
    await shoppingApi.create({ display_name: name, quantity: form.quantity, unit })
    ElMessage.success('已新增')
    form.display_name = ''
    form.quantity = ''
    form.unit = ''
    emit('created')
  } catch (e) {
    error.value = mapErrorMessage(e as NormalizedError)
  } finally {
    submitting.value = false
  }
}

defineExpose({ form, onSubmit, error })
</script>

<template>
  <el-form label-position="top" novalidate class="shopping-add" @submit.prevent="onSubmit">
    <el-form-item label="名称">
      <el-input v-model="form.display_name" maxlength="200" show-word-limit />
    </el-form-item>
    <el-form-item label="数量">
      <DecimalInput v-model="form.quantity" />
    </el-form-item>
    <el-form-item label="单位">
      <el-input v-model="form.unit" maxlength="32" />
    </el-form-item>
    <el-alert v-if="error" type="error" :title="error" :closable="false" class="shopping-add-error" />
    <el-button type="primary" native-type="submit" :loading="submitting" :disabled="submitting">
      新增
    </el-button>
  </el-form>
</template>

<style scoped>
.shopping-add {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  margin-bottom: 16px;
}
.shopping-add-error {
  width: 100%;
}
</style>