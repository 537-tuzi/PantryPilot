import { expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import StatusTag from '@/components/StatusTag.vue'
import QuantityText from '@/components/QuantityText.vue'
import DecimalInput from '@/components/DecimalInput.vue'
import FourState from '@/components/FourState.vue'

it('StatusTag 渲染文字非纯色', () => {
  const w = mount(StatusTag, { props: { status: 'expired' } })
  expect(w.text()).toContain('已过期')
  expect(w.classes()).toContain('pp-status--expired')
})

it('StatusTag 支持自定义 label', () => {
  const w = mount(StatusTag, { props: { status: 'expiring', label: '3 天后到期' } })
  expect(w.text()).toBe('3 天后到期')
})

it('QuantityText 数量单位同屏去尾零', () => {
  const w = mount(QuantityText, { props: { quantity: '1.500', unit: 'g' } })
  expect(w.text()).toBe('1.5g')
})

it('DecimalInput 发射字符串', async () => {
  const w = mount(DecimalInput, { props: { modelValue: '' } })
  await w.find('input').setValue('1.5')
  expect(w.emitted('update:modelValue')?.[0]).toEqual(['1.5'])
})

it('FourState loading 渲染骨架', () => {
  const w = mount(FourState, { props: { loading: true } })
  expect(w.findComponent({ name: 'ElSkeleton' }).exists()).toBe(true)
})

it('FourState error 渲染重试', async () => {
  const w = mount(FourState, {
    props: { loading: false, error: { code: 'NETWORK_ERROR', message: '网络异常', requestId: 'r', status: 0 } },
  })
  const btn = w.findAll('button').find((b) => b.text().includes('重试'))
  await btn!.trigger('click')
  expect(w.emitted('retry')).toHaveLength(1)
})

it('FourState empty 渲染空态', () => {
  const w = mount(FourState, { props: { loading: false, empty: true } })
  expect(w.findComponent({ name: 'ElEmpty' }).exists()).toBe(true)
})