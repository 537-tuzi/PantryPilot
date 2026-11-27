import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // 根目录 .env 同时提供后端与前端变量
  envDir: '..',
  server: {
    port: 5200,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    // tests/ 是本仓现有的集中放置约定；src/ 覆盖 Vue 生态"就近放 spec"的惯例。
    // 两个都要在：少写 src/ 会让就近放置的 spec 被静默忽略（用例从不执行却显示全绿），
    // 少写 tests/ 会让现有的 20 个测试文件整体不执行。
    include: ['tests/**/*.spec.ts', 'src/**/*.spec.ts'],
    setupFiles: ['./tests/setup.ts'],
  },
})
