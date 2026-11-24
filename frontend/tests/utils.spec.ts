import { expect, it } from 'vitest'
import { compareDecimal, isValidDecimal, toMilliunits } from '@/utils/decimal'
import { formatQuantityDisplay } from '@/utils/formatDisplay'
import { daysUntilDatePart } from '@/utils/appToday'
import { mapErrorMessage } from '@/utils/errorMap'

it('compareDecimal 0.100 等于 0.1', () => {
  expect(compareDecimal('0.100', '0.1')).toBe(0)
})

it('compareDecimal 区分大小', () => {
  expect(compareDecimal('1.5', '1.500')).toBe(0)
  expect(compareDecimal('2', '1.999')).toBe(1)
  expect(compareDecimal('0.1', '0.2')).toBe(-1)
})

it('toMilliunits 1.5 -> 1500', () => {
  expect(toMilliunits('1.5')).toBe(1500)
  expect(toMilliunits('0.001')).toBe(1)
  expect(toMilliunits('999999999.999')).toBe(999999999999)
})

it('isValidDecimal 拒绝 4 位小数', () => {
  expect(isValidDecimal('1.2345', 3, 9)).toBe(false)
  expect(isValidDecimal('1.234', 3, 9)).toBe(true)
  expect(isValidDecimal('0', 3, 9)).toBe(true)
  expect(isValidDecimal('-1', 3, 9)).toBe(false)
  expect(isValidDecimal('1234567890', 3, 9)).toBe(false)
})

it('formatQuantityDisplay 去尾零', () => {
  expect(formatQuantityDisplay('1.500', 'g')).toBe('1.5g')
  expect(formatQuantityDisplay('0.000', '盒')).toBe('0盒')
  expect(formatQuantityDisplay('500', 'g')).toBe('500g')
  expect(formatQuantityDisplay(null, 'g')).toBe('g')
})

it('daysUntilDatePart 纯日期部件', () => {
  expect(daysUntilDatePart('2026-11-17', '2026-11-14')).toBe(3)
  expect(daysUntilDatePart('2026-11-13', '2026-11-14')).toBe(-1)
  expect(daysUntilDatePart('2026-11-14', '2026-11-14')).toBe(0)
})

it('mapErrorMessage STATE_CONFLICT 中文', () => {
  expect(
    mapErrorMessage({ code: 'STATE_CONFLICT', message: 'Inventory item was modified by another request', requestId: 'r' }),
  ).toContain('修改')
})

it('mapErrorMessage NETWORK_ERROR 中文', () => {
  expect(mapErrorMessage({ code: 'NETWORK_ERROR', message: '', requestId: '' })).toContain('网络')
})