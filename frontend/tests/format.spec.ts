import { describe, expect, it } from 'vitest'

import { daysUntil, expiryStatus, formatQuantity } from '@/utils/format'

describe('formatQuantity', () => {
  it('数量与单位同时展示', () => {
    expect(formatQuantity('500', 'g')).toBe('500g')
  })

  it('数量为空时只显示单位', () => {
    expect(formatQuantity(null, 'g')).toBe('g')
  })
})

describe('expiryStatus', () => {
  const today = '2026-11-14'

  it('到期日早于今天为过期', () => {
    expect(expiryStatus('2026-11-13', today).status).toBe('expired')
  })

  it('今天到期为临期且剩余 0 天', () => {
    const result = expiryStatus('2026-11-14', today)
    expect(result.status).toBe('expiring')
    expect(result.daysLeft).toBe(0)
  })

  it('3 天后到期为临期', () => {
    expect(expiryStatus('2026-11-17', today).status).toBe('expiring')
  })

  it('4 天后到期为正常', () => {
    expect(expiryStatus('2026-11-18', today).status).toBe('normal')
  })

  it('未设置到期日时不做判定', () => {
    expect(expiryStatus(null, today).status).toBe('normal')
  })
})

describe('daysUntil', () => {
  it('按自然日计算差值', () => {
    expect(daysUntil('2026-11-18', '2026-11-14')).toBe(4)
  })
})
