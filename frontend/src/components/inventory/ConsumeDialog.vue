<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import * as inventoryApi from '@/api/inventory'
import DecimalInput from '@/components/DecimalInput.vue'
import QuantityText from '@/components/QuantityText.vue'
import type { InventoryItem } from '@/types/api'
import { compareDecimal, isValidDecimal } from '@/utils/decimal'

const props = defineProps<{ modelValue: boolean; item: InventoryItem | null }>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirmed: [item: InventoryItem]
  removed: [id: string]
}>()

const target = ref('0')
const submitting = ref(false)
const conflict = ref('')
const currentItem = ref<InventoryItem | null>(null)

watch(
  () => props.item,
  (it) => {
    currentItem.value = it
    target.value = '0'
    conflict.value = ''
  },
  { immediate: true },
)

const noChange = computed(
  () => currentItem.value !== null && compareDecimal(target.value, currentItem.value.quantity) === 0,
)

function deplete(): void {
  target.value = '0'
}

async function onConfirm(): Promise<void> {
  const it = currentItem.value
  if (!it || submitting.value) {
    return
  }
  if (!isValidDecimal(target.value, 3, 9)) {
    conflict.value = '数量格式不正确（最多 3 位小数）'
    return
  }
  if (compareDecimal(target.value, it.quantity) > 0) {
    conflict.value = '耗尽目标不得大于当前数量'
    return
  }
  if (noChange.value) {
    emit('update:modelValue', false)
    return
  }
  submitting.value = true
  conflict.value = ''
  try {
    const updated = await inventoryApi.update(it.id, {
      expected_version: it.version,
      quantity: target.value,
      reason: 'consume',
    })
    ElMessage.success('已更新库存')
    emit('confirmed', updated)
    emit('update:modelValue', false)
  } catch (e) {
    const err = e as NormalizedError
    if (err.code === 'STATE_CONFLICT') {
      const fresh = await inventoryApi.get(it.id)
      currentItem.value = fresh
      conflict.value = '该食材已被其他操作修改，请核对最新数量后重试'
    } else if (err.code === 'RESOURCE_NOT_FOUND') {
      emit('removed', it.id)
      emit('update:modelValue', false)
    } else {
      conflict.value = err.message
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="耗尽食材"
    width="420px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="currentItem" class="consume-body">
      <p class="consume-name">{{ currentItem.display_name }}</p>
      <p>当前数量：<QuantityText :quantity="currentItem.quantity" :unit="currentItem.unit" /></p>
      <p class="consume-target">
        目标数量：
        <DecimalInput v-model="target" />
        <el-button size="small" @click="deplete">一键耗尽</el-button>
      </p>
      <el-alert v-if="conflict" type="warning" :title="conflict" :closable="false" />
    </div>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onConfirm">确认耗尽</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.consume-name {
  font-weight: 600;
}
.consume-target {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>