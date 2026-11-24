<script setup lang="ts">
import { reactive } from 'vue'

import type { InventoryFilters } from '@/api/inventory'
import type { InventoryStatus } from '@/types/api'

const props = defineProps<{ modelValue: InventoryFilters }>()
const emit = defineEmits<{ change: [filters: InventoryFilters]; create: [] }>()

const local = reactive<InventoryFilters>({ ...props.modelValue })
let timer: ReturnType<typeof setTimeout> | undefined

function emitChange(): void {
  emit('change', { ...local })
}
function onNameInput(value: string): void {
  clearTimeout(timer)
  timer = setTimeout(() => {
    local.name = value.trim() || undefined
    emitChange()
  }, 300)
}
function onCategory(value: string): void {
  local.category = value || undefined
  emitChange()
}
function onStatus(value: InventoryStatus | ''): void {
  local.status = value || undefined
  emitChange()
}
function onArchived(value: boolean): void {
  local.include_archived = value
  emitChange()
}
</script>

<template>
  <div class="toolbar">
    <el-input
      :model-value="local.name"
      placeholder="搜索名称"
      clearable
      class="toolbar-search"
      @input="onNameInput"
    />
    <el-select :model-value="local.category" placeholder="分类" clearable @change="onCategory">
      <el-option label="乳制品" value="乳制品" />
      <el-option label="蔬菜" value="蔬菜" />
      <el-option label="蛋类" value="蛋类" />
      <el-option label="肉类" value="肉类" />
    </el-select>
    <el-select :model-value="local.status" placeholder="状态" clearable @change="onStatus">
      <el-option label="正常" value="normal" />
      <el-option label="临期" value="expiring" />
      <el-option label="过期" value="expired" />
    </el-select>
    <el-checkbox :model-value="local.include_archived" @change="onArchived">
      显示已归档
    </el-checkbox>
    <el-button type="primary" @click="emit('create')">
      新增
    </el-button>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar-search {
  width: 200px;
}
</style>