<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import type { NormalizedError } from '@/api/client'
import * as shoppingApi from '@/api/shopping'
import FourState from '@/components/FourState.vue'
import PageHeader from '@/components/PageHeader.vue'
import ShoppingAddForm from '@/components/shopping/ShoppingAddForm.vue'
import ShoppingItemRow from '@/components/shopping/ShoppingItemRow.vue'
import { useConfirm } from '@/composables/useConfirm'
import { usePagination } from '@/composables/usePagination'
import type { ShoppingItem, ShoppingStatus } from '@/types/api'
import { formatQuantityDisplay } from '@/utils/formatDisplay'
import { mapErrorMessage } from '@/utils/errorMap'

const statusFilter = ref<ShoppingStatus | undefined>(undefined)
const { items, total, page, pageSize, loading, error, load, setPage, setPageSize, refresh } =
  usePagination<ShoppingItem>((p) => shoppingApi.list({ ...p, status: statusFilter.value }))
const pendingIds = ref<Set<string>>(new Set())

onMounted(() => {
  void load()
})

function onFilter(value: ShoppingStatus | undefined): void {
  statusFilter.value = value
  setPage(1)
}

async function patchStatus(item: ShoppingItem, status: ShoppingStatus): Promise<void> {
  pendingIds.value.add(item.id)
  try {
    const updated = await shoppingApi.updateStatus(item.id, status)
    const idx = items.value.findIndex((i) => i.id === item.id)
    if (idx >= 0) {
      items.value[idx] = updated
    }
  } catch (e) {
    const err = e as NormalizedError
    if (err.code === 'RESOURCE_NOT_FOUND') {
      items.value = items.value.filter((i) => i.id !== item.id)
      void refresh()
      ElMessage.info('条目不存在，可能已被删除')
    } else {
      ElMessage.error(mapErrorMessage(err))
    }
  } finally {
    pendingIds.value.delete(item.id)
  }
}

function onToggle(item: ShoppingItem): void {
  const target: ShoppingStatus = item.status === 'purchased' ? 'pending' : 'purchased'
  void patchStatus(item, target).then(() => {
    ElMessage.success(target === 'purchased' ? '已标记为已购' : '已标记为待购')
  })
}
function onCancel(item: ShoppingItem): void {
  void patchStatus(item, 'cancelled')
}
function onRestore(item: ShoppingItem): void {
  void patchStatus(item, 'pending')
}

async function onRemove(item: ShoppingItem): Promise<void> {
  const ok = await useConfirm({
    title: '删除采购条目',
    message: `删除「${item.display_name}（${formatQuantityDisplay(item.quantity, item.unit)}）」后不可恢复。确认删除？`,
    type: 'warning',
  })
  if (!ok) {
    return
  }
  try {
    await shoppingApi.remove(item.id)
    items.value = items.value.filter((i) => i.id !== item.id)
    if (items.value.length === 0 && page.value > 1) {
      setPage(page.value - 1)
    } else {
      void refresh()
    }
    ElMessage.success('已删除')
  } catch (e) {
    const err = e as NormalizedError
    if (err.code === 'RESOURCE_NOT_FOUND') {
      items.value = items.value.filter((i) => i.id !== item.id)
      void refresh()
    } else {
      ElMessage.error(mapErrorMessage(err))
    }
  }
}

function onCreated(): void {
  statusFilter.value = undefined
  setPage(1)
}
</script>

<template>
  <div>
    <PageHeader
      title="采购清单"
      description="手动维护待购条目；勾选仅更新状态，不会自动入库或下单。"
      page-id="UI-09"
    />
    <ShoppingAddForm @created="onCreated" />
    <el-radio-group :model-value="statusFilter" class="shop-filter" @change="onFilter">
      <el-radio-button :value="undefined">
        全部
      </el-radio-button>
      <el-radio-button value="pending">
        待购
      </el-radio-button>
      <el-radio-button value="purchased">
        已购
      </el-radio-button>
      <el-radio-button value="cancelled">
        已取消
      </el-radio-button>
    </el-radio-group>
    <FourState
      :loading="loading && items.length === 0"
      :error="error"
      :empty="!loading && !error && items.length === 0"
      :empty-text="statusFilter ? '该状态下暂无条目' : '采购清单还是空的'"
      @retry="load"
    >
      <div class="shop-list">
        <ShoppingItemRow
          v-for="item in items"
          :key="item.id"
          :item="item"
          :pending="pendingIds.has(item.id)"
          @toggle="onToggle"
          @cancel="onCancel"
          @restore="onRestore"
          @remove="onRemove"
        />
      </div>
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        class="shop-pagination"
        @update:current-page="setPage"
        @update:page-size="setPageSize"
      />
    </FourState>
  </div>
</template>

<style scoped>
.shop-filter {
  margin-bottom: 16px;
}
.shop-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.shop-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>