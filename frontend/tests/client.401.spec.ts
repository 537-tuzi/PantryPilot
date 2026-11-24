import { beforeEach, expect, it, vi } from 'vitest'
import type { AxiosAdapter } from 'axios'

import client, { resetUnauthorizedFlag, setUnauthorizedHandler } from '@/api/client'

function adapter(status: number | null, data: unknown): AxiosAdapter {
  return ((config: { url?: string }) =>
    Promise.reject({
      config,
      response: status === null ? undefined : { status, data },
    })) as unknown as AxiosAdapter
}

beforeEach(() => {
  resetUnauthorizedFlag()
  localStorage.clear()
  setUnauthorizedHandler(null)
})

it('业务 401 触发 handler 且并发只一次', async () => {
  const handler = vi.fn()
  setUnauthorizedHandler(handler)
  client.defaults.adapter = adapter(401, { code: 'UNAUTHENTICATED', message: 'x', request_id: 'r' })
  await Promise.allSettled([
    client.get('/inventory'),
    client.get('/dashboard/summary'),
    client.get('/shopping-items'),
  ])
  expect(handler).toHaveBeenCalledTimes(1)
})

it('/auth/login 的 401 不触发 handler（凭据错误须到达表单）', async () => {
  const handler = vi.fn()
  setUnauthorizedHandler(handler)
  client.defaults.adapter = adapter(401, { code: 'UNAUTHENTICATED', message: 'Invalid email or password', request_id: 'r' })
  await expect(client.post('/auth/login', { email: 'a@b.com', password: '12345678' })).rejects.toMatchObject({
    code: 'UNAUTHENTICATED',
  })
  expect(handler).not.toHaveBeenCalled()
})

it('归一化含 status/code/requestId', async () => {
  client.defaults.adapter = adapter(409, { code: 'STATE_CONFLICT', message: 'modified', request_id: 'req-1' })
  await expect(client.patch('/inventory/x', {})).rejects.toMatchObject({
    code: 'STATE_CONFLICT',
    status: 409,
    requestId: 'req-1',
  })
})

it('超时/无响应归一化为 NETWORK_ERROR status 0', async () => {
  client.defaults.adapter = adapter(null, undefined)
  await expect(client.get('/inventory')).rejects.toMatchObject({ code: 'NETWORK_ERROR', status: 0 })
})