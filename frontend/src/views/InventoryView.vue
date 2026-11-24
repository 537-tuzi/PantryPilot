<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import * as inventoryApi from '@/api/inventory'
import type { InventoryFilters } from '@/api/inventory'
import FourState from '@/components/FourState.vue'
import PageHeader from '@/components/PageHeader.vue'
import ConsumeDialog from '@/components/inventory/ConsumeDialog.vue'
import InventoryPagination from '@/components/inventory/InventoryPagination.vue'
import InventoryTable from '@/components/inventory/InventoryTable.vue'
import InventoryToolbar from '@/components/inventory/InventoryToolbar.vue'
import { useConfirm } from '@/composables/useConfirm'
import { usePagination } from '@/composables/usePagination'
import type { InventoryItem, InventoryStatus } from '@/types/api'
import { formatQuantityDisplay } from '@/utils/formatDisplay'
import { showErrorToast } from '@/utils/errorMap'

const route = useRoute()
const router = useRouter()
const filters = ref<InventoryFilters>({})

const { items, total, page, pageSize, loading, error, load, setPage, setPageSize, refresh } = usePagination<InventoryItem>(
  (params) => inventoryApi.list({ ...params, ...filters.value }),
)

const consumeVisible = ref(false)
const consumeItem = ref<InventoryItem | null>(null)

onMounted(() => {
  if (route.query.name) {
    filters.value.name = String(route.query.name)
  }
  if (route.query.status) {
    filters.value.status = String(route.query.status) as InventoryStatus
  }
  void load()
})

function onFilterChange(f: InventoryFilters): void {
  filters.value = f
  setPage(1)
}

function onEdit(item: InventoryItem): void {
  router.push({ name: 'ingredient-edit', params: { id: item.id } })
}

function onConsume(item: InventoryItem): void {
  consumeItem.value = item
  consumeVisible.value = true
}

async function onArchive(item: InventoryItem): Promise<void> {
  const ok = await useConfirm({
    title: '删除食材',
    message: `删除后「${item.display_name}（${formatQuantityDisplay(item.quantity, item.unit)}）将归档，不再出现在默认列表，流水保留。确认删除？`,
    type: 'warning',
  })
  if (!ok) {
    return
  }
  try {
    await inventoryApi.archive(item.id)
    ElMessage.success('已归档')
    await refresh()
    if (items.value.length === 0 && page.value > 1) {
      setPage(page.value - 1)
    }
  } catch (e) {
    showErrorToast(e as NormalizedError)
  }
}

function onConfirmed(updated: InventoryItem): void {
  const idx = items.value.findIndex((i) => i.id === updated.id)
  if (idx >= 0) {
    items.value[idx] = updated
  }
}

function onRemoved(id: string): void {
  items.value = items.value.filter((i) => i.id !== id)
  void refresh()
}
</script>

<template>
  <div>
    <PageHeader title="食材库存" description="搜索、分类/状态筛选、分页。耗尽与删除需二次确认并保留流水。" page-id="UI-03" />
    <InventoryToolbar :model-value="filters" @change="onFilterChange" @create="router.push({ name: 'ingredient-form' })" />
    <FourState
      :loading="loading && items.length === 0"
      :error="error"
      :empty="!loading && !error && items.length === 0"
      empty-text="暂无食材"
      @retry="load"
    >
      <InventoryTable :items="items" @edit="onEdit" @consume="onConsume" @archive="onArchive" />
      <InventoryPagination
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="setPage"
        @update:page-size="setPageSize"
      />
    </FourState>
    <ConsumeDialog v-model="consumeVisible" :item="consumeItem" @confirmed="onConfirmed" @removed="onRemoved" />
  </div>
</template>