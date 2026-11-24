<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import * as preferencesApi from '@/api/preferences'
import FourState from '@/components/FourState.vue'
import PageHeader from '@/components/PageHeader.vue'
import ConstraintNotice from '@/components/preferences/ConstraintNotice.vue'
import TagListField from '@/components/preferences/TagListField.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useUnsavedGuard } from '@/composables/useUnsavedGuard'
import type { UserPreferences } from '@/types/api'
import { mapErrorMessage } from '@/utils/errorMap'

const loading = ref(false)
const loadError = ref<NormalizedError | null>(null)
const firstRun = ref(false)
const saving = ref(false)
const saveError = ref('')
const baseline = ref<UserPreferences | null>(null)
const dirty = ref(false)

const form = reactive({
  dietary_preferences: [] as string[],
  allergens: [] as string[],
  disliked_ingredients: [] as string[],
  default_servings: 2,
  default_budget: 0 as number | null,
  default_cooking_minutes: 30,
})

useUnsavedGuard(dirty)
watch(
  form,
  () => {
    if (!loading.value) {
      dirty.value = true
    }
  },
  { deep: true },
)

function applyBaseline(p: UserPreferences): void {
  form.dietary_preferences = [...p.dietary_preferences]
  form.allergens = [...p.allergens]
  form.disliked_ingredients = [...p.disliked_ingredients]
  form.default_servings = p.default_servings
  form.default_budget = Number(p.default_budget)
  form.default_cooking_minutes = p.default_cooking_minutes
}

function applyDefaults(): void {
  form.dietary_preferences = []
  form.allergens = []
  form.disliked_ingredients = []
  form.default_servings = 2
  form.default_budget = 0
  form.default_cooking_minutes = 30
}

async function load(): Promise<void> {
  loading.value = true
  loadError.value = null
  try {
    const p = await preferencesApi.getPreferences()
    baseline.value = p
    firstRun.value = false
    applyBaseline(p)
    await nextTick()
    dirty.value = false
  } catch (e) {
    const err = e as NormalizedError
    if (err.code === 'RESOURCE_NOT_FOUND') {
      // 首设态：非错误，UI 默认值 + info 提示
      firstRun.value = true
      baseline.value = null
      applyDefaults()
      await nextTick()
      dirty.value = false
    } else {
      loadError.value = err
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

function budgetDecimalsOk(): boolean {
  if (form.default_budget === null) {
    return false
  }
  const parts = String(form.default_budget).split('.')
  return (parts[1]?.length ?? 0) <= 2
}

async function onSave(event?: Event): Promise<void> {
  // el-form 组件 fallthrough 会丢失 .prevent 修饰符，显式阻止默认提交（防页面 reload/凭据进 URL）
  event?.preventDefault()
  if (saving.value) {
    return
  }
  saveError.value = ''
  if (form.default_servings < 1 || form.default_servings > 100) {
    saveError.value = '默认人数需 1~100'
    return
  }
  if (form.default_cooking_minutes < 1 || form.default_cooking_minutes > 1440) {
    saveError.value = '烹饪时间需 1~1440 分钟'
    return
  }
  if (form.default_budget === null || form.default_budget < 0 || form.default_budget > 99999999.99 || !budgetDecimalsOk()) {
    saveError.value = '预算需在 0~99999999.99 且最多 2 位小数'
    return
  }
  // 清空原本非空的过敏原 = 移除硬约束，二次确认
  if (baseline.value && baseline.value.allergens.length > 0 && form.allergens.length === 0) {
    const ok = await useConfirm({
      title: '清空过敏原',
      message: '清空过敏原将移除对应硬约束，确认保存？',
      type: 'warning',
    })
    if (!ok) {
      return
    }
  }
  const payload: UserPreferences = {
    dietary_preferences: form.dietary_preferences,
    allergens: form.allergens,
    disliked_ingredients: form.disliked_ingredients,
    default_servings: form.default_servings,
    default_budget: form.default_budget.toFixed(2),
    default_cooking_minutes: form.default_cooking_minutes,
  }
  saving.value = true
  try {
    const resp = await preferencesApi.putPreferences(payload)
    baseline.value = resp
    applyBaseline(resp)
    firstRun.value = false
    await nextTick()
    dirty.value = false
    ElMessage.success('偏好已保存')
  } catch (e) {
    saveError.value = mapErrorMessage(e as NormalizedError)
  } finally {
    saving.value = false
  }
}

async function onReset(): Promise<void> {
  if (baseline.value) {
    applyBaseline(baseline.value)
  } else {
    applyDefaults()
  }
  // 表单更新触发的深度 watcher 是 pre-flush 异步的，需等其 flush 后再清 dirty
  await nextTick()
  dirty.value = false
}

defineExpose({ form, onSave, onReset, load, firstRun, baseline, dirty, saveError })
</script>

<template>
  <div>
    <PageHeader title="个人偏好" description="过敏原、忌口、饮食偏好与默认人数/预算/时间。" page-id="UI-10" />
    <FourState :loading="loading" :error="loadError" @retry="load">
      <el-alert
        v-if="firstRun"
        type="info"
        :closable="false"
        title="尚未设置偏好，保存后生效。"
        class="pref-firstrun"
      />
      <el-form label-position="top" novalidate class="pref-form" @submit.prevent="onSave">
        <el-form-item label="过敏原（硬约束）">
          <TagListField v-model="form.allergens" placeholder="如 花生、海鲜，回车添加" />
        </el-form-item>
        <el-form-item label="忌口（硬约束）">
          <TagListField v-model="form.disliked_ingredients" placeholder="如 香菜、内脏，回车添加" />
        </el-form-item>
        <ConstraintNotice />
        <el-form-item label="饮食偏好">
          <TagListField v-model="form.dietary_preferences" placeholder="如 素食、低糖，回车添加" />
        </el-form-item>
        <el-form-item label="默认人数">
          <el-input-number v-model="form.default_servings" :min="1" :max="100" :step="1" :precision="0" />
        </el-form-item>
        <el-form-item label="默认预算">
          <el-input-number v-model="form.default_budget" :min="0" :max="99999999.99" :step="0.01" :precision="2" />
        </el-form-item>
        <el-form-item label="默认烹饪时间（分钟）">
          <el-input-number v-model="form.default_cooking_minutes" :min="1" :max="1440" :step="1" :precision="0" />
        </el-form-item>
        <el-alert v-if="saveError" type="error" :title="saveError" :closable="false" class="pref-save-error" />
        <div class="pref-actions">
          <el-button :disabled="!dirty" @click="onReset">
            重置
          </el-button>
          <el-button type="primary" native-type="submit" :loading="saving" :disabled="saving">
            保存
          </el-button>
        </div>
      </el-form>
    </FourState>
  </div>
</template>

<style scoped>
.pref-form {
  max-width: 640px;
}
.pref-firstrun,
.pref-save-error {
  margin-bottom: 12px;
}
.pref-actions {
  display: flex;
  gap: 8px;
}
</style>