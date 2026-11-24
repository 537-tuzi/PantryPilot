<script setup lang="ts">
defineProps<{ title: string; description?: string; pageId?: string }>()
</script>

<template>
  <div class="pp-page-header">
    <div>
      <h1 class="pp-page-title">
        {{ title }}
      </h1>
      <p v-if="description" class="pp-page-desc">
        {{ description }}
      </p>
    </div>
    <div class="pp-page-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.pp-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}
.pp-page-actions {
  display: flex;
  gap: 8px;
}
</style>