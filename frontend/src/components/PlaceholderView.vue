<script setup lang="ts">
/**
 * 页面骨架占位组件。
 * 每个页面的完整规格见 文档/03 §3，开发时替换为真实实现。
 */
defineProps<{
  pageId: string
  title: string
  desc: string
  ops: string[]
  todo: string
}>()
</script>

<template>
  <section class="pp-page">
    <h1 class="pp-page-title">
      {{ title }}
    </h1>
    <p class="pp-page-desc">
      {{ desc }}
    </p>
    <div class="panel">
      <p class="muted">
        {{ pageId }} · 待实现
      </p>
      <h3>关键操作</h3>
      <ul>
        <li v-for="op in ops" :key="op">
          {{ op }}
        </li>
      </ul>
      <h3>待办</h3>
      <p class="todo">
        {{ todo }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e3eaf2;
  border-radius: 12px;
  padding: 16px;
}

.muted {
  color: #64748b;
  font-size: 12px;
}

.todo {
  background: #fff8e8;
  border-left: 3px solid #e0a800;
  padding: 8px 12px;
  font-size: 13px;
}
</style>
