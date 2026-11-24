<script setup lang="ts">
import { computed } from 'vue'

import type { InventoryStatus } from '@/types/api'

const props = defineProps<{ status: InventoryStatus; label?: string }>()

const DEFAULT: Record<InventoryStatus, string> = { normal: '正常', expiring: '临期', expired: '已过期' }
const text = computed(() => props.label ?? DEFAULT[props.status])
</script>

<template>
  <span class="pp-status" :class="`pp-status--${status}`">{{ text }}</span>
</template>