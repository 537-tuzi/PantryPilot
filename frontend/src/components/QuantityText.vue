<script setup lang="ts">
import { computed } from 'vue'

import { formatQuantityDisplay } from '@/utils/formatDisplay'

const props = withDefaults(
  defineProps<{ quantity?: string | number | null; unit?: string | null; fallback?: string }>(),
  { quantity: null, unit: null, fallback: '—' },
)

const text = computed(() =>
  props.quantity === null || props.quantity === undefined || props.quantity === ''
    ? props.fallback
    : formatQuantityDisplay(props.quantity, props.unit),
)
</script>

<template>
  <span>{{ text }}</span>
</template>