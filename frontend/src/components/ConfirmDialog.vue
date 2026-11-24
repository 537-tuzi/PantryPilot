<script setup lang="ts">
/** 富内容二次确认对话框（扣减确认逐项展示数量+单位）。 */
withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
  }>(),
  { confirmText: '确认', cancelText: '取消', loading: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: boolean]; confirm: []; cancel: [] }>()

function close(): void {
  emit('update:modelValue', false)
}
function onCancel(): void {
  emit('cancel')
  close()
}
function onConfirm(): void {
  emit('confirm')
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    width="420px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <slot />
    <template #footer>
      <el-button @click="onCancel">
        {{ cancelText }}
      </el-button>
      <el-button type="primary" :loading="loading" @click="onConfirm">
        {{ confirmText }}
      </el-button>
    </template>
  </el-dialog>
</template>