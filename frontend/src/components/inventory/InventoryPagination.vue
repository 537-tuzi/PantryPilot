<script setup lang="ts">
defineProps<{ page: number; pageSize: number; total: number }>()
const emit = defineEmits<{ 'update:page': [p: number]; 'update:pageSize': [s: number] }>()
</script>

<template>
  <el-pagination
    :current-page="page"
    :page-size="pageSize"
    :total="total"
    :page-sizes="[10, 20, 50, 100]"
    layout="total, sizes, prev, pager, next"
    class="inv-pagination"
    @update:current-page="emit('update:page', $event)"
    @update:page-size="emit('update:pageSize', $event)"
  />
</template>

<style scoped>
.inv-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>