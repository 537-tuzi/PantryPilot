# Sprint 1 前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 PantryPilot 前端从 10 个占位骨架建成可对接真实后端的 Sprint 1 应用（认证/库存/临期/首页 + 基础设施）。

**Architecture:** 分层 feature 模块（方案 A）：`api/` 按域 typed service → `stores/`(Pinia 共享态) → `composables/` → `components/`(共享四态/数量/状态/确认) → `views/`(薄页面)。嵌套路由挂载 AppLayout，同步 token 守卫，注册式全局 401 处理器。

**Tech Stack:** Vue 3.5 + TS 5.6 + Element Plus 2.14.8(lock) + Pinia 2.2 + vue-router 4.4 + axios 1.7 + Vite 5.4 + Vitest 2.1 + @vue/test-utils 2.4。

**Spec:** `docs/specs/2026-11-24-frontend-development-design.md`（契约/类型/页面详设/偏差登记；执行者两者都读）。原则见根 `CLAUDE.md`。

## Global Constraints

- 后端代码是契约权威；**Sprint 1 校验失败一律 400 VALIDATION_ERROR，无 422、无字段细节** → 客户端校验完整镜像后端。
- Decimal  quantity/budget 全程**字符串**（3dp/2dp），提交不 parseFloat；展示去尾零另用 helper，保留 `formatQuantity` 与现有 8 个 `tests/format.spec.ts` 测试绿。
- 响应 TS 接口用**必填可空键**（`x: T|null`），`?` 仅请求体。按 `code`/`status` 分支，不按 message 文本。
- "今天"=Asia/Shanghai（`appToday`），临期状态用服务端 `item.status`，前端不重算。
- 每页四态（加载/空/错误/权限失效）；权限失效由全局 401 处理器满足。数量+单位同屏；破坏性操作二次确认展示数量单位。
- 请求走 `src/api/` 封装，不在组件直接 fetch；共享态入 Pinia，页面级服务端数据用 composable+本地 ref。
- `<script setup lang="ts">`；组件 PascalCase 文件名同名。中文文案；Element Plus zhCn。
- 库存 PATCH 必带 `expected_version`+方向正确 `reason`；编辑按值 diff 省略未改键；unit 不可改；耗尽=PATCH 0（保留）vs 删除=DELETE 软归档。
- `/inventory/expiring` 裸数组无分页；`/dashboard/summary` 仅计数（qty>0 口径）。偏好 GET 404=首设、PUT 六字段整表。
- CI frontend job 无后端无浏览器 → **所有 CI 测试 mock service 层**（`vi.mock('@/api/...')`）。
- 分支 dev/dyl；小步 PR；commit 用 Conventional Commits（scope: auth/inventory/expiry/dashboard/frontend）。**禁止 push main**。
- 密钥不进前端；不日志 token/密码。

## Review Focus

1. **登录/注册 401 误触发全局会话跳转** → 凭据错误被吞或重定向循环。Task 4/10 测试：`/auth/*` 401 不调 handler；并发业务 401 只跳一次。
2. **库存编辑发送未改字段 / 409 自动重发** → phantom version+流水 / 重复扣减。Task 11/12 测试：未改日期省略键；409 refetch 保留输入不重发。
3. **quantity parseFloat 往返** → 精度漂移、校验失败。Task 3/11/12 测试：字符串提交、整数千分位比较、"0.100"=="0.1" 不发请求。
4. **偏好漏传列表** → 静默清空过敏原硬约束。Task（Sprint 2，本轮冻结类型）；本轮 Review 标注，Sprint 2 计划补测。
5. **expiring 当分页 / 客户端重算 status** → 空列表 / 时区错判。Task 13 测试：无 page 参数、取 item.status、含过期项。

---

### Task 1: 依赖与测试基建

**Files:**
- Modify: `frontend/vite.config.ts`（test.setupFiles）
- Create: `frontend/tests/setup.ts`
- Test: `frontend/tests/setup.smoke.spec.ts`

**Interfaces:**
- Produces: 全局测试环境（ElementPlus+zhCn 注册、pinia、ResizeObserver/matchMedia/IntersectionObserver polyfill、ElMessage/ElMessageBox spy、TZ=Asia/Shanghai）。后续所有组件测试依赖。

- [ ] **Step 1: 安装依赖**

Run: `cd frontend && npm ci`
Expected: node_modules 就绪，无 error。

- [ ] **Step 2: 写失败冒烟测试** `tests/setup.smoke.spec.ts`

```ts
import { mount } from '@vue/test-utils'
import { ElButton } from 'element-plus'
it('Element Plus 在 jsdom 渲染且中文 locale', () => {
  const w = mount(ElButton, { slots: { default: '按钮' } })
  expect(w.text()).toContain('按钮')
})
```

- [ ] **Step 3: 运行验证失败**

Run: `cd frontend && npx vitest run tests/setup.smoke.spec.ts`
Expected: FAIL（ResizeObserver/matchMedia 未定义或无 setup）。

- [ ] **Step 4: 实现 setup.ts + 接线**

`tests/setup.ts`：polyfill `ResizeObserver`/`matchMedia`/`IntersectionObserver`（class 桩）；`vi.mock('element-plus', async orig => {...})` 保留组件但 spy `ElMessage`/`ElMessageBox`（confirm resolve）；`beforeEach` `setActivePinia(createPinia())`；`vi.stubEnv('TZ','Asia/Shanghai')`。`vite.config.ts` `test.setupFiles: ['./tests/setup.ts']`。组件测试按需 `app.use(ElementPlus)` 或全局注册。

- [ ] **Step 5: 运行验证通过 + 现有测试绿**

Run: `cd frontend && npx vitest run`
Expected: setup.smoke PASS，format.spec.ts 8 用例仍 PASS。

- [ ] **Step 6: Commit**

```bash
git add frontend/tests/setup.ts frontend/tests/setup.smoke.spec.ts frontend/vite.config.ts frontend/package-lock.json
git commit -m "test(frontend): 测试基建 setupFiles 与 jsdom polyfill"
```

---

### Task 2: 类型对齐

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/stores/auth.ts`（类型迁出，Task 6 再改逻辑）
- Test: `frontend/tests/types.contract.spec.ts`

**Interfaces:**
- Produces: spec §5 全部接口（InventoryItem/InventoryCreateRequest/InventoryUpdateRequest/PageResult/DashboardSummary/UserPreferences/TokenResponse/UserResponse/ShoppingItem + 状态联合 + Sprint2/3 冻结类型）。后续所有 task 消费这些精确类型。

- [ ] **Step 1: 写失败契约 fixture 测试** `tests/types.contract.spec.ts`

```ts
import type { InventoryItem, ShoppingItem, UserPreferences, TokenResponse } from '@/types/api'
it('InventoryItem 含服务端全部字段', () => {
  const sample: InventoryItem = { id:'x', ingredient_id:null, display_name:'牛奶', quantity:'1.000', unit:'盒', purchase_date:null, expiry_date:'2026-11-25', storage_location:'冷藏', status:'expiring', version:1, archived_at:null, created_at:'2026-11-24T00:00:00Z', updated_at:'2026-11-24T00:00:00Z' }
  expect(sample.version).toBe(1)
})
it('ShoppingItem.status 含 cancelled', () => { const s: ShoppingItem['status'] = 'cancelled'; expect(s).toBe('cancelled') })
it('UserPreferences.budget 必填字符串', () => { const p: UserPreferences = { dietary_preferences:[], allergens:[], disliked_ingredients:[], default_servings:2, default_budget:'0.00', default_cooking_minutes:30 }; expect(typeof p.default_budget).toBe('string') })
it('TokenResponse 含 user', () => { const t: TokenResponse = { access_token:'a', token_type:'bearer', expires_in:3600, user:{ id:'u', username:'n', email:'e@x.com', is_active:true } }; expect(t.user.is_active).toBe(true) })
```

- [ ] **Step 2: 运行验证失败**

Run: `cd frontend && npx vitest run tests/types.contract.spec.ts`
Expected: FAIL（类型缺字段，vue-tsc/vitest 报错）。

- [ ] **Step 3: 按 spec §5 重写 types/api.ts**

精确照抄 spec §5 接口（必填可空键）。删除 InventoryItem.category。新增 DashboardSummary、状态联合、Sprint2/3 冻结类型（AiIngredientDraft/AiMealPlanDraft/MealPlanDetail/MealPlanConfirm* 等）。TokenResponse/UserResponse 移入 types，stores/auth.ts re-export。

- [ ] **Step 4: 运行验证通过**

Run: `cd frontend && npx vitest run tests/types.contract.spec.ts`
Expected: PASS。（全量 `npm run typecheck` 门禁在 Task 6 store 改造后与 Task 9 统一跑，避免旧 store 引用误报。）

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/stores/auth.ts frontend/tests/types.contract.spec.ts
git commit -m "feat(frontend): 类型对齐后端契约（补 status/version/user/cancelled）"
```

---

### Task 3: 工具层（decimal/显示/时区/错误映射）

**Files:**
- Create: `frontend/src/utils/decimal.ts`, `frontend/src/utils/formatDisplay.ts`, `frontend/src/utils/appToday.ts`, `frontend/src/utils/errorMap.ts`
- Test: `frontend/tests/utils.spec.ts`

**Interfaces:**
- Produces:
  - `toMilliunits(s: string): number` / `compareDecimal(a: string, b: string): number` / `isValidDecimal(s: string, scale: number, maxInt: number): boolean`
  - `formatQuantityDisplay(quantity?: string|number|null, unit?: string|null): string`（"0.000"→"0"，"1.500"→"1.5"，不改原始串）
  - `appToday(): string`（Asia/Shanghai YYYY-MM-DD）/ `daysUntilDatePart(target: string, today: string): number`
  - `mapErrorMessage(err: NormalizedError): string`（code→中文）/ `showErrorToast(err): void`（跳过 UNAUTHENTICATED，预期业务码内联不 toast）

- [ ] **Step 1: 写失败测试** `tests/utils.spec.ts`

```ts
it('compareDecimal 0.100 等于 0.1', () => expect(compareDecimal('0.100','0.1')).toBe(0))
it('toMilliunits 1.5 -> 1500', () => expect(toMilliunits('1.5')).toBe(1500))
it('isValidDecimal 拒绝 4 位小数', () => expect(isValidDecimal('1.2345',3,9)).toBe(false))
it('formatQuantityDisplay 去尾零', () => { expect(formatQuantityDisplay('1.500','g')).toBe('1.5g'); expect(formatQuantityDisplay('0.000','盒')).toBe('0盒') })
it('daysUntilDatePart 纯日期部件', () => expect(daysUntilDatePart('2026-11-17','2026-11-14')).toBe(3))
it('mapErrorMessage STATE_CONFLICT 中文', () => expect(mapErrorMessage({ code:'STATE_CONFLICT', message:'Inventory item was modified by another request', requestId:'r' })).toContain('修改'))
```

- [ ] **Step 2: 运行验证失败**

Run: `cd frontend && npx vitest run tests/utils.spec.ts`
Expected: FAIL（函数未定义）。

- [ ] **Step 3: 实现四个 util**

decimal 用整数千分位（scale 3）/百分位（scale 2）parse 比较，不用 parseFloat 做提交值。formatQuantityDisplay 仅展示去尾零。appToday 用 `Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai'})`；daysUntilDatePart 拆 Y/M/D 做 UTC 部件差。errorMap code→中文 + 通用回退；showErrorToast 用 ElMessage.error 带 requestId，跳过 UNAUTHENTICATED。

- [ ] **Step 4: 运行验证通过 + format 旧测试绿**

Run: `cd frontend && npx vitest run tests/utils.spec.ts tests/format.spec.ts`
Expected: 全 PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/decimal.ts frontend/src/utils/formatDisplay.ts frontend/src/utils/appToday.ts frontend/src/utils/errorMap.ts frontend/tests/utils.spec.ts
git commit -m "feat(frontend): decimal/显示去尾零/应用时区/错误中文映射工具"
```

---

### Task 4: API client 增强（status + 注册式 401）

**Files:**
- Modify: `frontend/src/api/client.ts`
- Test: `frontend/tests/client.401.spec.ts`

**Interfaces:**
- Consumes: NormalizedError（Task 2 类型）。
- Produces: `NormalizedError` 增 `status: number`；`setUnauthorizedHandler(fn: () => void): void`；拦截器对业务 401（非 /auth/*）调 handler 且并发去重。

- [ ] **Step 1: 写失败测试** `tests/client.401.spec.ts`（mock axios adapter）

```ts
it('业务 401 触发 handler 且并发只一次', async () => { /* 3 个 401 响应，handler spy 调用 1 次 */ })
it('/auth/login 401 不触发 handler', async () => { /* url '/auth/login' 401，handler 未调用，错误 reject 到调用方 */ })
it('归一化含 status/code/requestId', async () => { /* 409 响应 -> { code:'STATE_CONFLICT', status:409, requestId } */ })
it('超时归一化 NETWORK_ERROR', async () => { /* 无 response -> code NETWORK_ERROR, status 0 */ })
```

- [ ] **Step 2: 运行验证失败**

Run: `cd frontend && npx vitest run tests/client.401.spec.ts`
Expected: FAIL（无 status/handler）。

- [ ] **Step 3: 实现 client.ts**

NormalizedError 加 `status`（`error.response?.status ?? 0`）。模块级 `let onUnauthorized: (()=>void)|null`、`let handling401=false`；`export function setUnauthorizedHandler(fn)`。拦截器 reject 前：`if (status===401 && !url.startsWith('/auth/') && !handling401) { handling401=true; onUnauthorized?.() }`。保留归一化。**不静态 import router/store**。

- [ ] **Step 4: 运行验证通过**

Run: `cd frontend && npx vitest run tests/client.401.spec.ts`
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/client.ts frontend/tests/client.401.spec.ts
git commit -m "feat(frontend): client 增 status 与注册式全局 401 处理器"
```

---

### Task 5: API service 层

**Files:**
- Create: `frontend/src/api/{auth,users,inventory,dashboard}.ts`
- Test: `frontend/tests/api.services.spec.ts`

**Interfaces:**
- Consumes: client（Task 4）、types（Task 2）。
- Produces:
  - `auth.login({email,password}): Promise<TokenResponse>` / `auth.register({username,email,password}): Promise<TokenResponse>`
  - `users.getMe(): Promise<UserResponse>`
  - `inventory.list(params): Promise<PageResult<InventoryItem>>` / `create(body): Promise<InventoryItem>` / `get(id): Promise<InventoryItem>` / `update(id, body: InventoryUpdateRequest): Promise<InventoryItem>` / `archive(id): Promise<void>` / `expiring(): Promise<InventoryItem[]>`
  - `dashboard.summary(): Promise<DashboardSummary>`
  - 解包 response.data；错误以 NormalizedError 传播；不 toast。

- [ ] **Step 1: 写失败测试**（mock client）

```ts
it('inventory.expiring 返回裸数组', async () => { /* client.get  resolving [] -> expiring() === [] */ })
it('inventory.update 携带 expected_version', async () => { /* spy client.patch 收到 { expected_version:1, ... } */ })
it('users.getMe 路径无尾斜杠', async () => { /* spy client.get 收到 '/users/me' */ })
it('auth.login 提交 email+password', async () => { /* spy client.post '/auth/login' { email, password } */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/api.services.spec.ts` → FAIL。

- [ ] **Step 3: 实现四个 service**（薄封装，签名见 Interfaces；inventory.list params: page/page_size/name/category/status/include_archived）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/api.services.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/auth.ts frontend/src/api/users.ts frontend/src/api/inventory.ts frontend/src/api/dashboard.ts frontend/tests/api.services.spec.ts
git commit -m "feat(frontend): 按域 API service 封装（auth/users/inventory/dashboard）"
```

---

### Task 6: auth store 增强

**Files:**
- Modify: `frontend/src/stores/auth.ts`
- Test: `frontend/tests/auth.store.spec.ts`

**Interfaces:**
- Consumes: api/auth、api/users（Task 5）、types（Task 2）。
- Produces: `useAuthStore()` → `{ token, user, isAuthenticated, setToken, clear, login, register, fetchMe, logout }`。login/register 存 token+user；fetchMe 写 user；logout 清 token+user+localStorage（不 import router）；isAuthenticated=computed(!!token)。

- [ ] **Step 1: 写失败测试**（mock @/api/auth、@/api/users）

```ts
it('login 存 token 与 user', async () => { /* login 后 store.user.id + localStorage[TOKEN_KEY] */ })
it('register 存 token 与 user', async () => { /* 201 含 user */ })
it('fetchMe 写 user', async () => { /* getMe resolve -> store.user */ })
it('logout 清 token/user/localStorage', () => { /* clear 后三者空 */ })
it('isAuthenticated 随 token', () => { /* setToken -> true; clear -> false */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/auth.store.spec.ts` → FAIL。

- [ ] **Step 3: 实现 store**（login/register 经 service 且 `user.value=data.user`；fetchMe；logout 仅清态；isAuthenticated computed）。

- [ ] **Step 4: 运行验证通过 + typecheck** → Run: `npx vitest run tests/auth.store.spec.ts && npm run typecheck` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/auth.ts frontend/tests/auth.store.spec.ts
git commit -m "feat(frontend): auth store 补 user/fetchMe/logout/isAuthenticated"
```

---

### Task 7: composables

**Files:**
- Create: `frontend/src/composables/{useAsyncState,usePagination,useMediaQuery,useUnsavedGuard,useConfirm}.ts`
- Test: `frontend/tests/composables.spec.ts`

**Interfaces:**
- Produces:
  - `useAsyncState<T>(fn, {immediate?}): { data: Ref<T|null>, loading: Ref<boolean>, error: Ref<NormalizedError|null>, execute(): Promise<T|null>, reset(): void }`
  - `usePagination<T>(fetcher, {pageSize?}): { items, total, page, pageSize, loading, error, load(), setPage(p), setPageSize(s), refresh() }`（setPageSize/筛选重置 page=1；序号守卫丢过期响应）
  - `useMediaQuery(query): Ref<boolean>`
  - `useUnsavedGuard(dirty: Ref<boolean>): void`（onBeforeRouteLeave 确认）
  - `useConfirm(opts): Promise<boolean>`（ElMessageBox.confirm，取消 resolve false）

- [ ] **Step 1: 写失败测试**

```ts
it('useAsyncState execute 成功写 data', async () => { /* fn resolve -> data, loading false */ })
it('useAsyncState 失败写 error', async () => { /* fn reject NormalizedError -> error */ })
it('usePagination setPageSize 重置 page=1', async () => { /* page=3 -> setPageSize(50) -> page 1 */ })
it('usePagination 丢弃过期响应', async () => { /* 慢请求后发快请求，items 取快请求 */ })
it('useConfirm 取消 resolve false', async () => { /* ElMessageBox reject -> false */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/composables.spec.ts` → FAIL。

- [ ] **Step 3: 实现五个 composable**（usePagination 用递增 seq 守卫；useMediaQuery 用 matchMedia+listener）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/composables.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/ frontend/tests/composables.spec.ts
git commit -m "feat(frontend): useAsyncState/usePagination/useMediaQuery/useUnsavedGuard/useConfirm"
```

---

### Task 8: 共享组件

**Files:**
- Create: `frontend/src/components/{PageHeader,StatusTag,QuantityText,DecimalInput,FourState,ConfirmDialog}.vue`
- Test: `frontend/tests/shared.components.spec.ts`

**Interfaces:**
- Consumes: utils（Task 3）、types、useConfirm（Task 7）。
- Produces: spec §4.6 六组件精确 props/emits/slots。StatusTag 取服务端 status+文字；QuantityText 数量+单位；DecimalInput 字符串模型；FourState loading/error/empty + retry，权限失效全局满足。

- [ ] **Step 1: 写失败测试**

```ts
it('StatusTag 渲染文字非纯色', () => { /* status expired -> text 含 '已过期' + class pp-status--expired */ })
it('QuantityText 数量单位同屏', () => { /* quantity '1.500' unit 'g' -> '1.5g' */ })
it('DecimalInput 发射字符串', async () => { /* 输入 -> update:modelValue 为 string */ })
it('FourState loading 渲染骨架', () => { /* loading true -> el-skeleton */ })
it('FourState error 渲染重试', async () => { /* error -> 重试按钮 click emit retry */ })
it('FourState empty 渲染空态', () => { /* empty true -> el-empty */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/shared.components.spec.ts` → FAIL。

- [ ] **Step 3: 实现六组件**（props 见 spec §4.6；StatusTag 用 main.css .pp-status--*；DecimalInput 用 el-input string + isValidDecimal 守卫）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/shared.components.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ frontend/tests/shared.components.spec.ts
git commit -m "feat(frontend): 共享组件 PageHeader/StatusTag/QuantityText/DecimalInput/FourState/ConfirmDialog"
```

---

### Task 9: 路由/守卫/壳接线

**Files:**
- Modify: `frontend/src/router/index.ts`, `frontend/src/layouts/AppLayout.vue`, `frontend/src/App.vue`, `frontend/src/main.ts`
- Create: `frontend/src/router/guards.ts`, `frontend/src/views/NotFoundView.vue`
- Test: `frontend/tests/router.guard.spec.ts`

**Interfaces:**
- Consumes: auth store（Task 6）、client setUnauthorizedHandler（Task 4）。
- Produces: 嵌套路由（login 公开兄弟；/ 壳父含 home/inventory/inventory/new/inventory/:id/edit/expiry/shopping/preferences/deferred AI；catch-all 最后）；`setupGuards(router)`；AppLayout 单 RouterView+用户下拉+登出；App zhCn；main 接线 handler+errorHandler。

- [ ] **Step 1: 写失败测试** `tests/router.guard.spec.ts`（createMemoryHistory）

```ts
it('无 token 访问 /inventory 重定向 login 带 redirect', async () => { /* router.push('/inventory') -> currentRoute.name login, query.redirect '/inventory' */ })
it('已登录访问 /login 重定向 home', async () => { /* setToken -> push login -> home */ })
it('redirect 拒绝 // 与绝对 URL', () => { /* sanitize('//evil') -> '/' */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/router.guard.spec.ts` → FAIL。

- [ ] **Step 3: 实现路由嵌套 + guards.ts（同步 token 守卫，回调内 useAuthStore）+ AppLayout（单 RouterView、用户下拉、登出 push login、var 色）+ App zhCn + main 接线 setUnauthorizedHandler（clear+toast+replace login）+ errorHandler + afterEach title/重置标志 + NotFoundView**。

- [ ] **Step 4: 运行验证通过 + typecheck + build** → Run: `npx vitest run tests/router.guard.spec.ts && npm run typecheck && npm run build` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/ frontend/src/layouts/AppLayout.vue frontend/src/App.vue frontend/src/main.ts frontend/src/views/NotFoundView.vue frontend/tests/router.guard.spec.ts
git commit -m "feat(frontend): 嵌套路由挂载 AppLayout + 守卫 + 401 接线 + zhCn"
```

---

### Task 10: UI-01 认证

**Files:**
- Modify: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/components/auth/{LoginForm,RegisterForm}.vue`
- Test: `frontend/tests/LoginView.spec.ts`

**Interfaces:**
- Consumes: auth store、api/auth、utils/errorMap、types。
- Produces: 登录(email,password 长度 8~128)/注册(username,email,password 强度+confirmPassword)；错误不泄露账号存在；redirect sanitization；成功 push redirect||'/'。

- [ ] **Step 1: 写失败测试**（mock @/api/auth）

```ts
it('登录 401 显示统一错误不泄露存在', async () => { /* 401 -> text '邮箱或密码错误'，不含 '未注册' */ })
it('注册密码缺大写校验失败', async () => { /* password 'abcd1234' -> 表单校验阻止提交 */ })
it('注册 confirmPassword 不一致阻止', async () => { /* mismatch -> 不发请求 */ })
it('登录成功跳 redirect', async () => { /* query.redirect '/inventory' -> push '/inventory' */ })
it('非法 redirect 回退首页', async () => { /* redirect '//evil' -> push '/' */ })
it('登录密码仅长度不校验强度', async () => { /* 'abcd1234' 登录可提交 */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/LoginView.spec.ts` → FAIL。

- [ ] **Step 3: 实现 LoginView + LoginForm/RegisterForm**（注册强度用 /\p{Ll}/u /\p{Lu}/u /\p{Nd}/u 实时 checklist；登录仅长度；409 统一冲突文案；提交中禁用防双提交）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/LoginView.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/LoginView.vue frontend/src/components/auth/ frontend/tests/LoginView.spec.ts
git commit -m "feat(auth): UI-01 登录注册页（镜像后端校验、不泄露账号存在）"
```

---

### Task 11: UI-03 库存列表 + 耗尽/归档

**Files:**
- Modify: `frontend/src/views/InventoryView.vue`
- Create: `frontend/src/components/inventory/{InventoryToolbar,InventoryTable,InventoryPagination,ConsumeDialog}.vue`
- Test: `frontend/tests/InventoryView.spec.ts`

**Interfaces:**
- Consumes: api/inventory、usePagination、共享组件、decimal utils。
- Produces: 搜索/筛选/分页列表；耗尽 ConsumeDialog（PATCH 0 reason consume）；归档 DELETE 二次确认；409 refetch 不重发。

- [ ] **Step 1: 写失败测试**（mock @/api/inventory）

```ts
it('数量与单位同屏且状态取服务端', () => { /* item.status expired -> StatusTag 文字 */ })
it('筛选变更重置 page=1', async () => { /* status 切换 -> list 调用 page 1 */ })
it('耗尽提交 PATCH quantity 0 reason consume 带 expected_version', async () => { /* ConsumeDialog 确认 -> update(id,{expected_version,quantity:'0',reason:'consume'}) */ })
it('目标等于当前不发请求', async () => { /* target==current -> update 未调用 */ })
it('409 后 refetch 保留输入不自动重发', async () => { /* update reject 409 -> get(id) 调用，update 仅 1 次 */ })
it('删除需二次确认取消不发', async () => { /* confirm cancel -> archive 未调用 */ })
it('已归档行禁用编辑/耗尽', () => { /* archived_at != null -> 按钮 disabled */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/InventoryView.spec.ts` → FAIL。

- [ ] **Step 3: 实现 InventoryView + 四组件**（Toolbar 静态分类选项+诚实提示；Table 桌面表格/≤760 卡片用 useMediaQuery；ConsumeDialog 展示当前+目标数量单位、一键耗尽、409 refetch；归档文案区分耗尽；分页 page-sizes [10,20,50,100]；筛选镜像 query）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/InventoryView.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/InventoryView.vue frontend/src/components/inventory/ frontend/tests/InventoryView.spec.ts
git commit -m "feat(inventory): UI-03 库存列表/筛选/分页/耗尽/归档（乐观锁+409 refetch）"
```

---

### Task 12: UI-04 食材表单（创建/编辑）

**Files:**
- Modify: `frontend/src/views/IngredientFormView.vue`
- Test: `frontend/tests/IngredientForm.spec.ts`

**Interfaces:**
- Consumes: api/inventory、DecimalInput、useUnsavedGuard、decimal utils。
- Produces: create/edit 双模式（:id）；编辑按值 diff 省略未改键 + expected_version + reason 方向守卫；unit 编辑禁用；到期<购买确认。

- [ ] **Step 1: 写失败测试**（mock @/api/inventory）

```ts
it('创建必填校验阻止提交', async () => { /* 空名称 -> create 未调用 */ })
it('创建名称 trim 后 1~80', async () => { /* 81 字 -> 校验失败 */ })
it('创建数量拒绝 0/负/4 位小数', async () => { /* '0' -> 失败 */ })
it('编辑仅发送变更字段', async () => { /* 仅改 quantity -> update body 无 expiry_date 键 */ })
it('编辑携带 expected_version 与 reason', async () => { /* 减量 -> reason consume */ })
it('编辑单位禁用且 body 不含 unit', async () => { /* update body 无 unit */ })
it('到期早于购买弹确认取消不提交', async () => { /* confirm cancel -> create 未调用 */ })
it('无变更不发请求直接返回', async () => { /* snapshot 相同 -> update 未调用 */ })
it('409 refetch 保留输入', async () => { /* update 409 -> get 调用 */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/IngredientForm.spec.ts` → FAIL。

- [ ] **Step 3: 实现 IngredientFormView**（GET/{id} 预填+snapshot；diff 省略未改键、清空发 null；reason 智能默认+方向守卫；unit 编辑禁用；到期<购买 useConfirm；创建 80/编辑 200；脏表单离开确认）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/IngredientForm.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/IngredientFormView.vue frontend/tests/IngredientForm.spec.ts
git commit -m "feat(inventory): UI-04 食材表单（按值 diff/expected_version/reason 方向/unit 不可改）"
```

---

### Task 13: UI-06 临期

**Files:**
- Modify: `frontend/src/views/ExpiryView.vue`
- Create: `frontend/src/components/expiry/{ExpirySummary,ExpiryList}.vue`
- Test: `frontend/tests/ExpiryView.spec.ts`

**Interfaces:**
- Consumes: api/inventory.expiring（裸数组）、useAsyncState、StatusTag、appToday。
- Produces: 服务端顺序渲染（含过期）；status 取 item.status；剩余天数 appToday；无分页；查看库存深链。

- [ ] **Step 1: 写失败测试**（mock @/api/inventory）

```ts
it('请求不携带 page/page_size', async () => { /* expiring spy 无参数 */ })
it('按服务端顺序渲染含过期项', () => { /* [expired, expiring] -> 过期在前，不被过滤 */ })
it('状态取 item.status 不客户端重算', () => { /* item.status normal 即使日期近 -> 正常 */ })
it('剩余天数用 appToday', () => { /* vi.setSystemTime -> 今天到期文案 */ })
it('空数组友好空态', () => { /* [] -> el-empty + 查看库存 */ })
it('查看库存携带 name 筛选', async () => { /* click -> push /inventory?name=... */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/ExpiryView.spec.ts` → FAIL。

- [ ] **Step 3: 实现 ExpiryView + 两组件**（useAsyncState(expiring)；不重排不过滤；ExpirySummary 按 status 计数；行操作查看库存/去规划 stub/可选耗尽 refetch）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/ExpiryView.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/ExpiryView.vue frontend/src/components/expiry/ frontend/tests/ExpiryView.spec.ts
git commit -m "feat(expiry): UI-06 临期管理（裸数组/服务端 status/应用时区）"
```

---

### Task 14: UI-02 首页

**Files:**
- Modify: `frontend/src/views/HomeView.vue`
- Create: `frontend/src/components/home/{StatCard,ExpiringSection,ExpiringItemCard,QuickActions}.vue`
- Test: `frontend/tests/HomeView.spec.ts`

**Interfaces:**
- Consumes: api/dashboard.summary、api/inventory.expiring、useAsyncState、StatusTag、appToday。
- Produces: 两独立请求；临期卡排除过期（==expiring_count）；统计卡跳转口径修正；今天取 statistics_date；开始规划禁用 tooltip。

- [ ] **Step 1: 写失败测试**（mock @/api/dashboard、@/api/inventory）

```ts
it('两独立请求一区失败不拖垮另一区', async () => { /* summary reject -> expiring 区仍渲染 */ })
it('临期卡排除过期项', () => { /* feed [expired, expiring] -> 卡片仅 expiring */ })
it('今天用 statistics_date 非客户端时钟', () => { /* vi.setSystemTime 偏移 -> 文案仍按 statistics_date */ })
it('过期卡跳 /expiry', async () => { /* click 过期卡 -> push /expiry */ })
it('库存卡注明口径差异', () => { /* tooltip/脚注含 '已耗尽' */ })
it('开始规划禁用且无导航', async () => { /* disabled + tooltip Sprint 2，click 不 push */ })
it('零库存空态新增 CTA', () => { /* inventory_count 0 -> el-empty + /inventory/new */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/HomeView.spec.ts` → FAIL。

- [ ] **Step 3: 实现 HomeView + 四组件**（Promise.allSettled 两区；临期卡 status==='expiring' 过滤+daysLeft 升序+截 6+查看全部；统计卡跳转 §6 口径；statistics_date 原样渲染、失败抑制天数文案；开始规划禁用 tooltip；响应式 grid）。

- [ ] **Step 4: 运行验证通过** → Run: `npx vitest run tests/HomeView.spec.ts` → PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/HomeView.vue frontend/src/components/home/ frontend/tests/HomeView.spec.ts
git commit -m "feat(dashboard): UI-02 首页（统计口径修正/临期卡排除过期/规划入口禁用）"
```

---

### Task 15: 暂缓桩 + 全量门禁 + 集成清单

**Files:**
- Modify: `frontend/src/views/{AiEntryView,PlannerView,PlanResultView}.vue`（ explicit "Sprint 2 未开放"态，无 /ai/* 调用）
- Create: `docs/specs/sprint1-manual-integration-checklist.md`
- Test: `frontend/tests/deferred.spec.ts`

**Interfaces:**
- Consumes: 全部前序 task。
- Produces: AI 三桩明确未开放态；人工集成清单（demo 登录、409 双标签、prefs 首设、响应式 375/768/1280）。

- [ ] **Step 1: 写失败测试**

```ts
it('AI 桩渲染未开放且不调 API', () => { /* mount PlannerView -> text 'Sprint 2'，无 client 调用 */ })
```

- [ ] **Step 2: 运行验证失败** → Run: `npx vitest run tests/deferred.spec.ts` → FAIL。

- [ ] **Step 3: 改三桩为 el-empty "Sprint 2 未开放" + 返回入口；写人工集成清单**（demo@example.com/demo12345 登录、库存 CRUD+409 双标签、临期午夜边界、响应式浏览器验证、nginx 深链刷新）。

- [ ] **Step 4: 全量门禁**

Run: `cd frontend && npm run lint && npm run typecheck && npx vitest run && npm run build`
Expected: 全绿（lint/typecheck/所有测试/build）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/AiEntryView.vue frontend/src/views/PlannerView.vue frontend/src/views/PlanResultView.vue frontend/tests/deferred.spec.ts docs/specs/sprint1-manual-integration-checklist.md
git commit -m "feat(frontend): AI 桩标 Sprint 2 未开放 + 人工集成清单 + 全量门禁绿"
```

---

## 实现顺序与依赖

Task 1→2→3→4→5→6→7→8→9（Phase 0 基础设施，顺序，共享契约冻结）→ 10（认证垂直切片）→ 11→12（库存，最难写契约，参考实现）→ 13→14（临期/首页，可并行）→ 15（桩+门禁）。**Task 9 前不铺页面**（防共享组件冲突）。

## 范围外（后续计划）

UI-10 偏好（Sprint 2）、UI-05/07 AI（Sprint 2，后端待启动）、UI-08 确认扣减（Sprint 3）、UI-09 采购（Sprint 3）。类型已冻结（Task 2）。Review Focus #4（偏好漏传列表）在 Sprint 2 计划补测。