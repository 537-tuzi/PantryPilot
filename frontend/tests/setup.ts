import { beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

// jsdom 缺失的浏览器 API polyfill（el-table/el-select/el-pagination 依赖）
globalThis.ResizeObserver = class {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
} as unknown as typeof ResizeObserver

globalThis.IntersectionObserver = class {
  root = null
  rootMargin = ''
  thresholds: number[] = []
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): [] {
    return []
  }
} as unknown as typeof IntersectionObserver

window.matchMedia = ((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => false,
})) as unknown as typeof window.matchMedia

// 保留 Element Plus 组件，仅 mock 通知/确认框（测试不弹真实 UI）
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>()
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
      closeAll: vi.fn(),
    },
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue('confirm'),
      alert: vi.fn().mockResolvedValue('confirm'),
      prompt: vi.fn().mockResolvedValue({ value: '' }),
      close: vi.fn(),
    },
  }
})

// 组件测试全局注册 Element Plus（el-skeleton/el-empty/el-input 等需解析）
config.global.plugins.push(ElementPlus)

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubEnv('TZ', 'Asia/Shanghai')
})