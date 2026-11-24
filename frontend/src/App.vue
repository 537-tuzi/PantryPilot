<script setup lang="ts">
import { RouterView } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import { appError, clearAppError } from '@/utils/appError'
</script>

<template>
  <el-config-provider :locale="zhCn">
    <el-alert
      v-if="appError"
      type="error"
      :title="appError.message"
      :closable="true"
      class="app-error-banner"
      @close="clearAppError"
    >
      <span v-if="appError.requestId">request_id: {{ appError.requestId }}</span>
    </el-alert>
    <RouterView />
  </el-config-provider>
</template>

<style scoped>
.app-error-banner {
  margin: 8px 16px;
}
</style>