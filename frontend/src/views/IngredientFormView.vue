<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import * as inventoryApi from '@/api/inventory'
import DecimalInput from '@/components/DecimalInput.vue'
import FourState from '@/components/FourState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useUnsavedGuard } from '@/composables/useUnsavedGuard'
import type { InventoryItem, InventoryUpdateRequest } from '@/types/api'
import { compareDecimal, isValidDecimal } from '@/utils/decimal'
import { mapErrorMessage, showErrorToast } from '@/utils/errorMap'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string | undefined)
const isEdit = computed(() => Boolean(id.value))

const form = reactive({
  display_name: '',
  quantity: '',
  unit: '',
  purchase_date: '',
  expiry_date: '',
  storage_location: '',
})
const snapshot = ref<InventoryItem | null>(null)
const loading = ref(false)
const submitting = ref(false)
const loadError = ref<NormalizedError | null>(null)
const conflict = ref('')
const validationError = ref('')
const dirty = ref(false)

useUnsavedGuard(dirty)
watch(form, () => {
  if (!loading.value) {
    dirty.value = true
  }
})

async function loadItem(): Promise<void> {
  if (isEdit.value && id.value) {
    loading.value = true
    loadError.value = null
    try {
      const it = await inventoryApi.get(id.value)
      snapshot.value = it
      form.display_name = it.display_name
      form.quantity = it.quantity
      form.unit = it.unit
      form.purchase_date = it.purchase_date ?? ''
      form.expiry_date = it.expiry_date ?? ''
      form.storage_location = it.storage_location ?? ''
      await nextTick()
      dirty.value = false
    } catch (e) {
      loadError.value = e as NormalizedError
    } finally {
      loading.value = false
    }
  }
}

onMounted(loadItem)

/** 编辑按值 diff：仅发送变更字段，省略未改键（避免 phantom version+流水）。 */
function buildDiff(): InventoryUpdateRequest {
  const s = snapshot.value as InventoryItem
  const body: InventoryUpdateRequest = { expected_version: s.version }
  const name = form.display_name.trim()
  if (name !== s.display_name) {
    body.display_name = name
  }
  const cmp = compareDecimal(form.quantity, s.quantity)
  if (cmp !== 0) {
    body.quantity = form.quantity
    body.reason = cmp > 0 ? 'add' : 'consume'
  }
  if ((form.purchase_date || null) !== s.purchase_date) {
    body.purchase_date = form.purchase_date || null
  }
  if ((form.expiry_date || null) !== s.expiry_date) {
    body.expiry_date = form.expiry_date || null
  }
  if ((form.storage_location || null) !== s.storage_location) {
    body.storage_location = form.storage_location || null
  }
  const metadataChanged =
    body.display_name !== undefined ||
    body.purchase_date !== undefined ||
    body.expiry_date !== undefined ||
    body.storage_location !== undefined
  if (cmp === 0 && metadataChanged) {
    body.reason = 'adjust'
  }
  return body
}

async function onSubmit(): Promise<void> {
  if (submitting.value) {
    return
  }
  conflict.value = ''
  validationError.value = ''
  const name = form.display_name.trim()
  const nameMax = isEdit.value ? 200 : 80
  if (name.length < 1 || name.length > nameMax) {
    validationError.value = `名称需 1~${nameMax} 字`
    return
  }
  if (!isEdit.value && !form.unit.trim()) {
    validationError.value = '请填写单位'
    return
  }
  if (!isValidDecimal(form.quantity, 3, 9)) {
    validationError.value = '数量格式不正确（最多 3 位小数、9 位整数）'
    return
  }
  if (!isEdit.value && compareDecimal(form.quantity, '0') <= 0) {
    validationError.value = '数量需大于 0'
    return
  }
  if (form.purchase_date && form.expiry_date && form.expiry_date < form.purchase_date) {
    const ok = await useConfirm({ title: '日期确认', message: '到期日早于购买日，确认保存？', type: 'warning' })
    if (!ok) {
      return
    }
  }
  submitting.value = true
  try {
    if (isEdit.value && snapshot.value && id.value) {
      const body = buildDiff()
      if (Object.keys(body).length === 1) {
        dirty.value = false
        router.push({ name: 'inventory' })
        return
      }
      await inventoryApi.update(id.value, body)
      ElMessage.success('已保存')
      dirty.value = false
      router.push({ name: 'inventory' })
    } else {
      await inventoryApi.create({
        display_name: name,
        quantity: form.quantity,
        unit: form.unit.trim(),
        purchase_date: form.purchase_date || null,
        expiry_date: form.expiry_date || null,
        storage_location: form.storage_location || null,
      })
      ElMessage.success('已新增')
      dirty.value = false
      router.push({ name: 'inventory' })
    }
  } catch (e) {
    const err = e as NormalizedError
    if (err.code === 'STATE_CONFLICT' && id.value) {
      try {
        const fresh = await inventoryApi.get(id.value)
        snapshot.value = fresh
        conflict.value = '该食材已被其他操作修改，请核对最新值后重试'
      } catch (e2) {
        const err2 = e2 as NormalizedError
        if (err2.code === 'RESOURCE_NOT_FOUND') {
          router.push({ name: 'inventory' })
        } else {
          conflict.value = mapErrorMessage(err2)
        }
      }
    } else {
      showErrorToast(err)
    }
  } finally {
    submitting.value = false
  }
}

function onCancel(): void {
  router.push({ name: 'inventory' })
}

defineExpose({ form, onSubmit, dirty, validationError, loadItem })
</script>

<template>
  <div>
    <PageHeader :title="isEdit ? '编辑食材' : '新增食材'" page-id="UI-04" />
    <FourState :loading="loading" :error="loadError" @retry="loadItem">
      <el-form label-position="top" class="ingredient-form" @submit.prevent="onSubmit">
        <el-form-item label="名称" required>
          <el-input v-model="form.display_name" :maxlength="isEdit ? 200 : 80" show-word-limit />
        </el-form-item>
        <el-form-item label="数量" required>
          <DecimalInput v-model="form.quantity" />
        </el-form-item>
        <el-form-item label="单位" required>
          <el-input v-model="form.unit" :disabled="isEdit" maxlength="32" />
          <span v-if="isEdit" class="hint">单位创建后不可修改</span>
        </el-form-item>
        <el-form-item label="购买日期">
          <el-input v-model="form.purchase_date" type="date" />
        </el-form-item>
        <el-form-item label="到期日期">
          <el-input v-model="form.expiry_date" type="date" />
        </el-form-item>
        <el-form-item label="存储位置">
          <el-input v-model="form.storage_location" maxlength="100" placeholder="冷藏/冷冻/常温/自定义" />
        </el-form-item>
        <el-alert v-if="validationError" type="error" :title="validationError" :closable="false" />
        <el-alert v-if="conflict" type="warning" :title="conflict" :closable="false" />
        <div class="form-actions">
          <el-button @click="onCancel">
            取消
          </el-button>
          <el-button type="primary" native-type="submit" :loading="submitting" :disabled="submitting">
            保存
          </el-button>
        </div>
      </el-form>
    </FourState>
  </div>
</template>

<style scoped>
.ingredient-form {
  max-width: 560px;
}
.hint {
  color: #64748b;
  font-size: 12px;
  margin-left: 8px;
}
.form-actions {
  display: flex;
  gap: 8px;
}
</style>