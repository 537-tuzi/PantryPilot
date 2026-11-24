import { expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton, ElMessage } from 'element-plus'

it('jsdom polyfill：ResizeObserver 与 matchMedia 可用', () => {
  expect(typeof globalThis.ResizeObserver).toBe('function')
  expect(typeof window.matchMedia).toBe('function')
})

it('ElButton 渲染中文内容', () => {
  const w = mount(ElButton, { slots: { default: '按钮' } })
  expect(w.text()).toContain('按钮')
})

it('ElMessage.error 被 mock（测试不弹真实通知）', () => {
  expect(vi.isMockFunction(ElMessage.error)).toBe(true)
})