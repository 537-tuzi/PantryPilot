import { expect, it } from 'vitest'
import type { AxiosAdapter } from 'axios'

import client from '@/api/client'
import * as auth from '@/api/auth'
import * as inventory from '@/api/inventory'
import * as users from '@/api/users'
import * as dashboard from '@/api/dashboard'

let lastConfig: { url?: string; data?: string; params?: Record<string, unknown> } = {}

function captureAdapter(data: unknown): AxiosAdapter {
  return ((config: { url?: string; data?: string; params?: Record<string, unknown> }) => {
    lastConfig = config
    return Promise.resolve({ data, status: 200, statusText: 'OK', headers: {}, config })
  }) as unknown as AxiosAdapter
}

it('inventory.expiring 返回裸数组且路径正确', async () => {
  client.defaults.adapter = captureAdapter([])
  const result = await inventory.expiring()
  expect(result).toEqual([])
  expect(lastConfig.url).toBe('/inventory/expiring')
})

it('inventory.update 携带 expected_version', async () => {
  client.defaults.adapter = captureAdapter({})
  await inventory.update('x', { expected_version: 1, quantity: '0', reason: 'consume' })
  expect(lastConfig.url).toBe('/inventory/x')
  expect(JSON.parse(lastConfig.data ?? '{}')).toEqual({ expected_version: 1, quantity: '0', reason: 'consume' })
})

it('inventory.list 传递筛选参数', async () => {
  client.defaults.adapter = captureAdapter({ items: [], total: 0, page: 1, page_size: 20 })
  await inventory.list({ page: 2, status: 'expiring' })
  expect(lastConfig.url).toBe('/inventory')
  expect(lastConfig.params).toMatchObject({ page: 2, status: 'expiring' })
})

it('users.getMe 路径无尾斜杠', async () => {
  client.defaults.adapter = captureAdapter({})
  await users.getMe()
  expect(lastConfig.url).toBe('/users/me')
})

it('auth.login 提交 email+password', async () => {
  client.defaults.adapter = captureAdapter({})
  await auth.login({ email: 'a@b.com', password: '12345678' })
  expect(lastConfig.url).toBe('/auth/login')
  expect(JSON.parse(lastConfig.data ?? '{}')).toEqual({ email: 'a@b.com', password: '12345678' })
})

it('dashboard.summary 路径正确', async () => {
  client.defaults.adapter = captureAdapter({ statistics_date: '2026-11-24', inventory_count: 0, expiring_count: 0, expired_count: 0 })
  const result = await dashboard.summary()
  expect(lastConfig.url).toBe('/dashboard/summary')
  expect(result.statistics_date).toBe('2026-11-24')
})