import { expect, it } from 'vitest'

// 回归守卫：vitest 的 include 必须同时覆盖 tests/ 与 src/。
//
// 为什么需要这条用例：include 少写一个目录时，放在该目录下的 spec 会被**静默忽略** ——
// 本地与 CI 都显示"全部通过"，但那些用例从未执行过。于是"修复缺陷必须补一条回归用例"
// 这条团队约定会形同虚设，缺陷会以"已修复"的状态进 Sprint 台账。
//
// 已实测：把 include 收窄成只保留 tests/ 下那一种 glob 时，
// 放在 src/utils/__probe.spec.ts 的用例不会被收集（测试文件数与用例数都不变）。
//
// 两个绕坑说明：
// 1. 这里读配置文件文本而不是 import 它 —— import vite.config 会把 vite/esbuild 拉进
//    jsdom 环境，触发 esbuild 的 TextEncoder 不变量校验，整条用例直接加载失败。
// 2. 用 import.meta.glob 读文件而不是 node:fs —— 本仓未安装 @types/node，
//    node:fs/node:path/process 在 typecheck 下会报 TS2307/TS2591。
// 3. 本说明用 // 注释：glob 里的 "**/" 序列会提前闭合块注释。
const configSources = import.meta.glob('../vite.config.ts', {
  as: 'raw',
  eager: true,
}) as Record<string, string>

function readIncludePatterns(): string[] {
  const source = Object.values(configSources)[0]
  if (!source) {
    throw new Error('未找到 vite.config.ts')
  }
  const match = source.match(/include:\s*\[([^\]]*)\]/)
  if (!match) {
    throw new Error('未在 vite.config.ts 中找到 test.include 配置')
  }
  return [...match[1].matchAll(/'([^']+)'/g)].map((m) => m[1])
}

it('vitest include 同时覆盖 tests/ 与 src/', () => {
  const patterns = readIncludePatterns()
  expect(patterns.some((p) => p.includes('tests/'))).toBe(true)
  expect(patterns.some((p) => p.includes('src/'))).toBe(true)
})
