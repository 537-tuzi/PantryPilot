<script setup lang="ts">
/** 字符串模型 Decimal 输入（避免 el-input-number 的 IEEE-754 伪影）。校验由父表单用 isValidDecimal 执行。 */
withDefaults(
  defineProps<{ modelValue: string; scale?: number; allowZero?: boolean; placeholder?: string }>(),
  { scale: 3, allowZero: false, placeholder: '' },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

function onInput(value: string): void {
  emit('update:modelValue', value)
}
</script>

<template>
  <el-input :model-value="modelValue" inputmode="decimal" :placeholder="placeholder" @input="onInput" />
</template>