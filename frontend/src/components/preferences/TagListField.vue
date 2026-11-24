<script setup lang="ts">
/** 标签列表输入：trim/拒空白/去重/限长（服务端仅 trim+拒空白，客户端加去重限额）。 */
const props = withDefaults(
  defineProps<{
    modelValue: string[]
    placeholder?: string
    maxItems?: number
    itemMaxLength?: number
  }>(),
  { placeholder: '输入后回车添加', maxItems: 50, itemMaxLength: 50 },
)
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>()

function onChange(tags: string[]): void {
  const cleaned: string[] = []
  for (const tag of tags) {
    const s = tag.trim().slice(0, props.itemMaxLength)
    if (s && !cleaned.includes(s)) {
      cleaned.push(s)
    }
    if (cleaned.length >= props.maxItems) {
      break
    }
  }
  emit('update:modelValue', cleaned)
}
</script>

<template>
  <el-input-tag
    :model-value="modelValue"
    :placeholder="placeholder"
    @update:model-value="onChange"
  />
</template>