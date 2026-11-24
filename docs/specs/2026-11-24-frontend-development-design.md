# PantryPilot 前端开发设计规格

> 版本：0.1（待评审） 日期：2026-11-24 作者：A2（dyl） 归属：A 组前端
> 依据：`文档/01~09`、`10_工程管理台账.xlsx`（Backlog/Sprint计划/RTM/RACI）、`开发规范.md`、`README.md`、`docs/adr/0001|0002`，以及后端代码（契约权威）。
> 本文是前端工作设计稿，非 `文档/` 基线；按开发规范 §8 经团队评审后同步 RTM 与台账。

---

## 0. 核心原则（不可违背）

1. **AI 只给建议，事实与库存变更由确定性程序 + 用户确认完成**（README:9）。前端不执行可信业务规则（04 §3 表现层约束）。
2. **后端代码是契约权威**，文档滞后处以代码为准并登记偏差（见 §9）。
3. **严格锚定规划**：任务范围来自台账 Backlog Sprint 列 + 01 §5 + RTM，不擅自超范围。
4. 开发规范 §5.3 强制：`<script setup lang="ts">`；请求走 `src/api/` 封装、不在组件直接 fetch；状态放 Pinia；**每页四态（加载/空/错误/权限失效）**；数量+单位同时展示；日期按应用时区；破坏性操作二次确认且展示数量单位；AI 内容标注"建议/草稿"。

---

## 1. 目标与范围

**本轮交付 = Sprint 1 前端**（台账 Backlog Sprint 列 + 01 §5 + README 三源一致）：
基础设施 + **UI-01 认证、UI-03 库存列表、UI-04 食材表单、UI-06 临期、UI-02 首页**，以及 FR-003 隔离的前端表现。

**不在本轮**（按 Backlog Sprint 列留待后续，仅冻结契约）：UI-10 偏好（Sprint 2）、UI-05/07 AI（Sprint 2，后端待启动）、UI-08 确认扣减（Sprint 3）、UI-09 采购（Sprint 3）、FR-017 菜谱收藏（候选不做）。

**架构方案 A（分层 feature 模块）**：`api/` 按域 typed service → `stores/`（Pinia，auth 等共享态）→ `composables/`（异步/分页/确认）→ `components/`（共享四态/数量/状态/确认）→ `views/`（薄页面）。符合开发规范 §5.3 与 NFR-006 模块分层。

---

## 2. 全程路线图（到项目结束，01 §5 时间线）

| 阶段 | 时间 | 前端任务（FR·UI） | 依赖 | 出口门禁 |
|---|---|---|---|---|
| **Sprint 1** | D4–10 | 基础设施 + UI-01/03/04/06/02 + FR-003 前端表现 | 后端 Sprint 1 已合入 main | 认证/库存/临期/首页可运行；前端组件测试；CI 绿；AT-01/02/03 前端部分 |
| **Sprint 2** | D11–18 | UI-10 偏好（FR-004，后端已就绪）；UI-05 AI 录入（FR-011）；UI-07 AI 规划（FR-012/013）；FR-018 失败降级前端；AI 标注 + 隐私说明 + AI 关闭入口（R-08） | **C 组后端 AI 待启动**；模型选型须 Sprint 2 前实测完成（02 §10）；前端先按 06 §4 契约 + Mock | AI 结构化草稿可用；TC-AI-01—03 / TC-MEAL-01/02；AT-04/05 |
| **Sprint 3** | D19–25 | UI-08 计划结果 + 确认扣减（FR-014/015）；UI-09 采购手动 + 导入（FR-016）；端到端核心闭环配合 | UI-08 需计划数据（Sprint 2 AI 生成或补 seed）；confirm 需 `Idempotency-Key` + 行级 `meal_plan_ingredient_id`（后端已实现）；导入需 confirmed 计划 | 端到端闭环通过；TC-STOCK-01—04 / TC-SHOP-01；AT-06/07 |
| **收尾** | D26–30 | **操作视频（A 组负责，09 §3）**；响应式浏览器验证 375/768/1280；易用性走查；源代码可构建/无密钥；前端已知限制披露；配合开源 Tag/README/PPT/部署持久化复测 | 全部真实页面就绪 | AT-01~08；Must 完成率 100%；P0 用例 100%；S1/S2 清零；干净环境部署 + 持久化（TC-DEP-01） |

**项目末端硬门禁（07 §5 + 09 §5）**：Must 完成率 100%、P0 用例通过率 100%、S1/S2 缺陷清零、核心闭环端到端通过、AI 禁忌/库存不足/非法输出/超时有测试证据、干净环境部署 + 数据持久化。

---

## 3. 契约总则（后端代码权威，已逐字核验）

- 前缀 `/api/v1`（`backend/app/core/config.py:40`）；Bearer 认证；错误信封 `{code, message, request_id, details?}` + 响应头 `X-Request-ID`（`core/errors.py:107-120`）。`details` 仅非空时出现，**Sprint 1 无任何代码填充 details，前端不得依赖它分支**。
- **所有请求校验失败 → 400 `VALIDATION_ERROR`，message 固定 "Request validation failed"，无字段细节**（`core/errors.py:123-127`）。**Sprint 1 不存在 422**（422 仅 Sprint 2 业务码 `AI_OUTPUT_INVALID`）。→ 前端客户端校验必须完整镜像后端规则。
- 错误码：`VALIDATION_ERROR`(400)、`UNAUTHENTICATED`(401)、`FORBIDDEN`(403)、`RESOURCE_NOT_FOUND`(404)、`STATE_CONFLICT`(409)、`INSUFFICIENT_STOCK`(409，confirm 专用)、`INTERNAL_SERVER_ERROR`(500)。**按 code/status 分支，绝不按 message 文本**（401 有 3 种不同 message）。
- Decimal → **JSON 字符串**（`format(v,'f')`，固定 3 位小数如 "1.500"/"0.000"；预算 Numeric(10,2) 如 "50.00"）。**提交也用字符串，绝不 parseFloat 往返**；展示可去尾零，原始串保留。
- date → "YYYY-MM-DD"；datetime → ISO 8601 带时区；UUID → 小写连字符串。
- **"今天" = 应用时区 Asia/Shanghai**（`config.py:36`，ADR-0001），非浏览器本地。`status` 服务端读取时派生，前端**渲染 response.status，不重算**。
- Pydantic v2 响应**始终输出全部字段**（默认值/null 显式）→ 响应接口用**必填可空键**（`x: T | null`），`?` 仅用于请求体（PATCH 省略键 = 不变）。
- JWT HS256 载荷仅 `{sub, exp}`，默认 60 分钟，`expires_in` 是**秒**（3600）。**无刷新端点、无服务端登出**（`api/v1/router.py:19-26`）→ 登出仅客户端清 token，不得宣称服务端失效。

---

## 4. Sprint 1 基础设施详设

### 4.1 路由与壳（`router/index.ts`、`layouts/AppLayout.vue`、`App.vue`、`main.ts`）
- **嵌套路由挂载孤儿 AppLayout**：`/login` 为独立公开兄弟路由（`meta.public:true`）；`/` 为壳父路由（component=AppLayout），children：home('')、inventory、inventory/new、**inventory/:id/edit（新增，name=ingredient-edit，UI-04）**、expiry、shopping、preferences、ai-entry/planner/plans/:id（`meta.deferred:true`）。保留现有 `meta.pageId`，每路由加 `meta.title`。**catch-all `/:pathMatch(.*)*` 置最后**渲染 404 el-empty。
- AppLayout：删除死逻辑双 RouterView（:28-29），改**单个 `<RouterView/>`**；保留 6 项导航 + @media 760px 横向导航（已满足 03 §4）；加 active-link 样式、header 用户下拉（`auth.user?.username`，菜单：个人偏好→/preferences、退出登录）；硬编码色改 `var(--pp-navy)/var(--pp-line)`。
- App.vue：`<el-config-provider :locale="zhCn">` 包裹（Element Plus 默认英文）。
- main.ts：`app.use(createPinia())` → `app.use(router)` 后 `setupGuards(router)` + `setUnauthorizedHandler(...)`；加 `app.config.errorHandler` + `window.addEventListener('unhandledrejection')` → 通用错误面板 + console requestId（NFR-008）。

### 4.2 路由守卫（`router/guards.ts`，同步）
```
beforeEach((to) => {
  const auth = useAuthStore()          // 必须在回调内调用（import 时无 active pinia）
  if (to.name === 'login') return auth.isAuthenticated ? { name:'home' } : true
  if (!auth.isAuthenticated) return { name:'login', query:{ redirect: to.fullPath } }
  return true
})
afterEach: document.title = `${to.meta.title ?? ''} · 食刻管家`；重置 401 重入标志
```
- `isAuthenticated = computed(() => !!token)`。**守卫只查 token（同步）**；user 引导在 AppLayout.onMounted `fetchMe()`，避免守卫与 401 处理器 redirect 竞态。
- redirect  sanitization：仅接受以 `/` 开头且非 `//` 的值，拒绝绝对 URL 与 `/login`，防开放重定向。

### 4.3 全局 401 处理器（`api/client.ts`）
- **client.ts 不得静态 import router/store**（循环 router→views→client→router）。用注册式：`setUnauthorizedHandler(fn)`，main.ts 接线。
- 响应拦截器 reject 前：`status===401 && !url.startsWith('/auth/') && !handling401` → 置标志 + 调 handler。handler：`auth.clear()`；若 hadToken → `ElMessage.warning('登录已过期，请重新登录')`；若当前非 login → `router.replace({name:'login', query:{redirect:cur.fullPath}})`。
- **排除 /auth/*（登录/注册 401 是凭据错误，须到达表单）**；并发 401 去重（标志在 afterEach + queueMicrotask 双重重置，防导航中止卡死）；已在 login 不跳。
- `NormalizedError` 扩展 `status: number`（`error.response?.status ?? 0`）；保留 code/message/requestId；超时/无响应 → `NETWORK_ERROR`。

### 4.4 auth store（`stores/auth.ts`）
- `TokenResponse` **补 `user: UserResponse`**（F4：登录/注册都返回 nested user，`schemas/auth.py:66`）；类型移入 `types/api.ts` 再 re-export。
- 新增 `user = ref<UserResponse|null>(null)`、`isAuthenticated` computed。
- `login(email,password)` / `register(username,email,password)`：经 `api/auth.ts`，成功 `setToken` **且 `user.value = data.user`**。
- `fetchMe()`：GET `/users/me`（**精确路径无尾斜杠**）→ user。
- `logout()`：仅清 token+user+localStorage（store 不 import router）；router.push 由 AppLayout 下拉处理器执行 + `ElMessage.success('已退出登录')`。**无服务端调用**。
- 可选：跨标签 `storage` 事件同步清除；`expiresAt = Date.now() + expires_in*1000`（秒×1000）。**不做静默刷新**。

### 4.5 API service 层（`api/{auth,users,inventory,dashboard,preferences,shopping,mealPlans}.ts`）
typed 薄封装，解包 `response.data`，错误以 NormalizedError 传播，**service 不 toast**（调用方决定 inline/toast）。Sprint 1 实装 auth/users/inventory/dashboard；preferences/shopping/mealPlans 先定义签名（Sprint 2/3 用），mealPlans.confirm 与 shopping.import 冻结。

### 4.6 共享组件（`components/`，Phase 0 冻结一次，防 5 套重复）
| 组件 | props / 契约 |
|---|---|
| `PageHeader.vue` | `{title, description?, pageId?}` + slot #actions；渲染 .pp-page-title/.pp-page-desc |
| `StatusTag.vue` | `{status: InventoryStatus, label?}`；.pp-status--{status} + **文字**（正常/临期/已过期），绝不纯色；**取服务端 status** |
| `QuantityText.vue` | `{quantity?: string\|number\|null, unit?, fallback='—'}`；数量+单位同屏；用 formatQuantityDisplay |
| `DecimalInput.vue` | **字符串模型** `{modelValue: string, scale: 3\|2, min?, max?, allowZero?}`；emit update:modelValue(string)；**不用 el-input-number（IEEE-754 伪影）** |
| `FourState.vue` | `{loading, error?: NormalizedError\|null, empty?, emptyText?, loadingRows?}`；emit retry；slots #default/#empty/#error；loading→el-skeleton，error→el-alert+requestId+重试，empty→el-empty。**权限失效由全局 401 处理器满足，不内联分支** |
| `ConfirmDialog.vue` + `useConfirm` | 二次确认；扣减确认**逐项展示数量+单位**；useConfirm 包 ElMessageBox.confirm，取消 resolve false 不 throw |

### 4.7 composables（`composables/`）
- `useAsyncState<T>(fn, {immediate?})` → `{data, loading, error, execute, reset}`（统一用 **execute**）。
- `usePagination<T>(fetcher, {pageSize=20})` → `{items, total, page, pageSize, loading, error, load, setPage, setPageSize, refresh}`；**setPageSize/筛选变更重置 page=1**；**请求序号守卫丢弃过期响应**；total=0 隐藏分页。用于 inventory/shopping 列表，**不用于 expiring（裸数组用 useAsyncState）**。
- `useUnsavedGuard`（脏表单离开确认，preferences/ingredient-form 共用）。
- `useMediaQuery`（matchMedia 可 mock，驱动响应式卡片/表格切换，使 jsdom 可断言）。

### 4.8 工具（`utils/`）
- `formatQuantityDisplay`：展示去尾零（"0.000"→"0"，"1.500"→"1.5"），**不改原始提交串**；保留 formatQuantity + 现有 8 测试绿。
- `decimal`：整数千分位 parse/compare（toMilliunits），共享给库存/采购/扣减。
- `appToday`：`Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai'})` + **纯日期部件运算**（修 daysUntil 负时区 off-by-one）。
- `errorMap`/`errorToast`：code→中文映射（后端 service message 是英文）；**预期业务错误内联不 toast**（prefs GET 404 首设、409 冲突、404 陈旧行、register 409）；跳过 UNAUTHENTICATED（全局已处理）；ElMessage.error 带 requestId；绝不 toast 原始 axios。
- 统一单位预设常量（g/kg/个/盒/杯/份 等，对齐 seed）。

### 4.9 测试基建（`tests/setup.ts` + vite.config.ts `test.setupFiles`）
注册 ElementPlus + zhCn + createPinia/setActivePinia；polyfill ResizeObserver/matchMedia/IntersectionObserver（el-table/el-select/el-pagination 需要）；统一 ElMessage/ElMessageBox spy；**pin TZ**（CI frontend job 跑 UTC）。

---

## 5. 类型对齐（`types/api.ts`，必填可空键）

```ts
export type InventoryStatus = 'normal' | 'expiring' | 'expired'
export type ExpiryStatus = InventoryStatus            // 保留旧别名
export type InventoryReason = 'add' | 'adjust' | 'consume'
export type ShoppingStatus = 'pending' | 'purchased' | 'cancelled'
export type MealPlanStatus = 'draft' | 'confirmed'
export type StorageLocation = '冷藏' | '冷冻' | '常温' | '自定义'

export interface InventoryItem {
  id: string; ingredient_id: string | null; display_name: string
  quantity: string; unit: string
  purchase_date: string | null; expiry_date: string | null; storage_location: string | null
  status: InventoryStatus; version: number; archived_at: string | null
  created_at: string; updated_at: string
}                                                    // 删除幻影 category（仅查询参数）
export interface InventoryCreateRequest {
  display_name: string; quantity: string; unit: string
  purchase_date?: string | null; expiry_date?: string | null; storage_location?: string | null
}                                                    // Sprint 1 省略 ingredient_id（无 catalog 端点）
export interface InventoryUpdateRequest {
  expected_version: number                           // 必填 ≥1
  display_name?: string; quantity?: string
  purchase_date?: string | null; expiry_date?: string | null; storage_location?: string | null
  reason?: InventoryReason                           // 任何有效变更必填，方向校验
}                                                    // 无 unit/ingredient_id（不可改）
export interface PageResult<T> { items: T[]; total: number; page: number; page_size: number }
export interface DashboardSummary { statistics_date: string; inventory_count: number; expiring_count: number; expired_count: number }
export interface UserPreferences {
  dietary_preferences: string[]; allergens: string[]; disliked_ingredients: string[]
  default_servings: number; default_budget: string; default_cooking_minutes: number
}                                                    // budget/minutes 改必填
export interface TokenResponse { access_token: string; token_type: string; expires_in: number; user: UserResponse }
export interface UserResponse { id: string; username: string; email: string; is_active: boolean }
export interface ShoppingItem {
  id: string; display_name: string; ingredient_id: string | null
  quantity: string; unit: string; status: ShoppingStatus
  source_meal_plan_id: string | null; created_at: string; updated_at: string
}
```
**Sprint 2/3 冻结类型**（定义不实现 UI）：`AiIngredientDraft`/`AiMealPlanDraft`/`AiRecipeCandidate`（06 §4，无 id）；持久化 `MealPlanDetail`/`MealPlanItemDetail`/`MealPlanIngredientDetail`（`items[].ingredients[].id` = confirm 的 `meal_plan_ingredient_id`）/`Recipe`；`MealPlanConfirmItem`/`MealPlanConfirmRequest`/`MealPlanConfirmResult`/`DeductedItem`/`MealPlanMissingItem`；`ShoppingItemCreateRequest`/`ShoppingStatusUpdateRequest`/`ShoppingImportResult`。`recipe_snapshot`/`request_constraints` 类型 `unknown` 渲染前运行时守卫。

---

## 6. Sprint 1 页面详设

### UI-01 认证（`views/LoginView.vue` 重写 + `components/auth/{LoginForm,RegisterForm}.vue`）
- 独立居中 auth 卡（不在壳内）；el-tabs 登录/注册；读 `route.query.redirect`，成功 push 校验后 redirect || '/'。
- **登录**：{email, password}，密码**仅长度 8~128**（不校验字符类，强度只在注册）。401→统一"邮箱或密码错误"（**不泄露账号是否存在**）；403→"账号已被禁用"（仅正确凭据后返回）。
- **注册**：{username, email, password}，confirmPassword 仅前端不提交。username trim 1~100 非空白（不小写）；email 格式；password 8~128 + 含小写/大写/数字（**实时 checklist**，后端 400 无字段细节故必须前端镜像）。强度用 `/\p{Ll}/u /\p{Lu}/u /\p{Nd}/u` 近似后端 Unicode-aware（`str.islower/isupper/isdigit`），**登记残余差异**（后端 isdigit ⊃ Nd）。409→统一"用户名或邮箱已被注册"（不拆分）。
- 四态：loading=按钮 :loading + 输入禁用防双提交；empty=纯净表单本身（**不渲染 el-empty**）；error=字段级 + AuthErrorAlert；auth-expired=全局 401 跳转目的地，保留 redirect。
- 测试：auth.store / router.guard / client.401 / LoginView（见 §8）。

### UI-03 库存列表（`views/InventoryView.vue` + `components/inventory/{InventoryToolbar,InventoryTable,InventoryPagination,ConsumeDialog}.vue`）
- Toolbar：name 搜索（trim，300ms 防抖，空省略）、category（**静态选项 乳制品/蔬菜/蛋类/肉类**，无 catalog API，提示"仅匹配已关联食材库的条目"）、status、include_archived、新增→/inventory/new。**筛选变更重置 page=1**；筛选+页码镜像 route query（供 UI-06 深链恢复）。
- Table：桌面 el-table（名称/数量 QuantityText/状态 StatusTag+ExpiryText/到期日/存储位置/操作 编辑·耗尽·删除）；**≤760px 卡片列表**（useMediaQuery）。已归档行禁用编辑/耗尽（会 404）；quantity "0.000" 行禁用耗尽显示已耗尽。服务端固定排序（expiry ASC NULLS LAST, created_at DESC），**不做客户端排序列**。
- 分页：el-pagination page-sizes [10,20,50,100]（上限 100）。
- **耗尽 ConsumeDialog**：展示当前+目标数量单位；目标 string 0..current ≤3dp；一键耗尽 preset "0"；提交 PATCH `{expected_version, quantity:target, reason:'consume'}`；target==current 不发请求；200→**用响应替换行（新 version）**；target 0 条目保留。**409→GET/{id} 刷新行+保留用户输入+提示，绝不自动重发**；404→关闭移除行刷新。
- **删除（归档）**：二次确认文案区分"归档隐藏、流水保留" vs 耗尽"数量归零、条目保留"；DELETE 204→刷新当前页，页空且 page>1 回退一页。
- 四态 + 边界：首屏骨架；refetch 保旧行 v-loading；空态新增 CTA / 筛选空态清空筛选；错误 requestId+重试；last-row 删除回退页；双提交禁用。

### UI-04 食材表单（`views/IngredientFormView.vue`，create/edit 双模式 keyed by :id）
- 字段：display_name（创建 trim **1~80** 按 03 §5；编辑若载入 >80 按后端 200 放行，登记偏差）；quantity（DecimalInput string，创建 >0 ≤3dp ≤9 整数位；编辑 ≥0 但耗尽走 ConsumeDialog）；unit（创建 el-select filterable allow-create 1~32；**编辑禁用**"单位创建后不可修改"）；purchase/expiry_date（el-date-picker YYYY-MM-DD clearable，**到期<购买弹确认**，后端无此检查）；storage_location（预设 冷藏/冷冻/常温 + 自定义 ≤100，清空→null）；**ingredient_id 省略**。
- reason（编辑，数量/日期/位置变更时显示）：adjust/add/consume，智能默认（增→add，减→consume，仅元数据→adjust），**前端方向守卫**镜像 service。
- **编辑按值 diff**：GET/{id} 预填 + snapshot{version,fields}；**仅发送变更字段**（未改日期/位置**省略键**，避免 phantom version+流水）；清空日期发 null；无变更不发请求直接返回；提交带 `expected_version=snapshot.version` + reason。
- 200→替换本地 item；409→refetch + 冲突 banner + 保留输入；400→通用 message+requestId。创建 201→push /inventory 保留 query。脏表单取消二次确认。

### UI-06 临期（`views/ExpiryView.vue` + `components/expiry/{ExpirySummary,ExpiryList}.vue`）
- GET /inventory/expiring **裸数组**（useAsyncState，**无分页参数/UI**）；**按服务端顺序渲染**（expiry ASC，过期在前），不重排不重过滤；**含过期项**（无下界），排除 archived+qty0（服务端已做，前端不"修正"）。
- StatusTag **取 item.status**（不客户端 expiryStatus 判定）；ExpiryText 剩余天数用 appToday + 日期部件运算；summary 计数按 item.status 统计。
- 行操作：查看库存→/inventory?name=...；去规划→/planner（Sprint 2 桩，仅导航）；可选耗尽复用 ConsumeDialog（耗尽后条目服务端消失→refetch）。
- 空态友好"暂无临期或过期食材"+查看库存；大数组客户端渲染上限（仅性能，不过滤状态）。

### UI-02 首页（`views/HomeView.vue` + `components/home/{StatCard,ExpiringSection,ExpiringItemCard,QuickActions}.vue`）
- onMounted `Promise.allSettled` 两独立请求：GET /dashboard/summary（统计）+ GET /inventory/expiring（卡片）；**一区失败不拖垮另一区**；序号守卫丢过期响应。
- "今天"取 `summary.statistics_date`（原样渲染 YYYY-MM-DD，**不 new Date() 再格式化**）；**summary 失败时抑制天数文案（仅显示 expiry_date），不用客户端本地回退**（ADR-0001，批评 G23）。
- 临期卡片：按服务端 `status==='expiring'` 过滤（**排除过期**，保证卡片数==expiring_count，FR-010），daysLeft 升序，截前 6 + 查看全部→/expiry；过期项单独紧凑条→见下。
- **统计卡跳转口径修正（FR-010，批评 G1/T3）**：dashboard 三计数均过滤 qty>0+未归档，但 GET /inventory 列表**不过滤数量**。故：库存总数卡→/inventory **并显式注明"列表含已耗尽条目，总数口径不同"**（或加客户端"仅显示有库存"开关，非服务端 total）；临期卡→/expiry（feed 排除 qty0，==expiring_count）；**过期卡→/expiry 并定位过期分组**（使目的地过期计数==expired_count），**不跳 /inventory?status=expired**（其 total 含 qty0 过期行 ≠ expired_count）。
- 快捷入口：新增→/inventory/new；查看临期→/expiry；**开始规划→禁用 el-button + tooltip"AI 膳食规划将在 Sprint 2 开放"**（不调任何 /ai/* 或计划生成；不静默移除入口，03 §6）。
- 只读页无二次确认；四态分区；响应式 grid auto-fill minmax(240px,1fr) 手机单列。

---

## 7. 错误与四态策略

- **四态映射**：loading/empty/error 由 FourState 承载；**权限失效（auth-expired）= 全局 401 处理器 toast+redirect /login?redirect=...**，不在每页内联重复（03 §4 要求该态存在，全局跳转即是）。表单页 empty=纯净表单（不 el-empty）；prefs empty=404 首设态。
- **错误表面**：表单页（login/register/ingredient-form/preferences）**内联** el-alert/el-form-item，预期业务错误不 toast；列表/动作页 toast 意外失败 + FourState 重试。**每错误类一个表面，防双 toast**。
- **预期业务错误内联清单**：prefs GET 404（首设）、inventory/shopping 409（冲突）、inventory/shopping 404（陈旧行）、register 409（重复）。
- **英文→中文 messageMap**：后端 service message 英文（"Inventory item was modified by another request" 等），映射中文 + 通用回退；带 requestId（NFR-008）。
- 客户端校验完整镜像后端（400 无字段细节）；按 code/status 分支不按 message。

---

## 8. 测试策略与 CI 门禁

**CI 门禁已存在（保持绿，不重造）**：`.github/workflows/ci.yml` frontend job = node20 → npm ci → lint → typecheck(vue-tsc) → test(vitest run) → build。**frontend job 无后端无浏览器 → 所有 CI 测试必须 mock-based**。

- **mock 在 service 层**（`vi.mock('@/api/inventory')` 等），非 axios；client.401.spec mock axios adapter。纯工具（decimal/formatQuantityDisplay/appToday/errorMap）无 Vue 单测。
- **组件测试**（@vue/test-utils 已装）：auth.store / router.guard / client.401 / LoginView / InventoryToolbar / InventoryTable / ConsumeDialog / InventoryView / IngredientForm / ExpiryView / HomeView（各页关键用例见核验详设，含：409 refetch 保留输入不重发、编辑按值 diff 省略未改键、耗尽 0.100==0.1 不发请求、分页 pageSize 重置 page、裸数组无分页参数、首页卡片排除过期+口径一致、statistics_date 非客户端时钟、注册密码强度三案、redirect sanitization）。
- **保留现有 8 个 format 测试绿**；可选契约 fixture 测试（quantity "2.500"、shopping 'cancelled'、prefs budget "120.50"）使漂移 fail CI。
- **响应式**：useMediaQuery 可 mock 断言窄屏卡片；真实 375/768/1280 布局 + ElMessageBox 焦点陷阱留浏览器/人工。
- **需真实后端（人工/dev，非 CI）**：真实 401 过期、真实 409 双标签竞态、prefs 404→PUT→200 往返、expiring 应用时区午夜边界、**demo 登录 `demo@example.com / demo12345`（seed.py:46-48，登录非注册——demo12345 无大写过不了注册强度）**、proxy/CORS 路径、nginx SPA 深链刷新。提供人工集成清单；可选本地 Playwright 冒烟（不入 CI）。后端契约正确性已由 backend pytest（93 函数）覆盖，前端只测对码/状态的处理。

---

## 9. 偏差与风险登记（从真实出发，不擅自抹平，待 PO/团队确认）

| # | 偏差/风险 | 处理 | 依据 |
|---|---|---|---|
| D1 | **FR-005 分类 Must 不可实现**：无 category 列/catalog 端点，seed 不写 ingredient_id → 分类筛选 demo 必空 | 静态选项 + 诚实空态提示；**PO 签字部分交付** | DS-06/F22 |
| D2 | **FR-010 统计与列表口径不一致**：dashboard 过滤 qty>0，列表不过滤 | 首页跳转目标修正（§6 UI-02）+ 显式口径说明 | 批评 G1/T3 |
| D3 | 名称长度 03 §5 1~80 vs 后端 1~200 | 创建 80、编辑容忍 200；登记文档同步 | G21 |
| D4 | **台账 Sprint计划 row3 vs Backlog Sprint 列矛盾**（确认扣减/采购 Sprint1 vs Sprint3） | 以 Backlog+01+README 三源为准；登记待 PO 确认 | F16 |
| D5 | Backlog "已完成"实指后端，前端全占位 | 本 spec 即前端真实起点 | F2 |
| D6 | 文档"用户时区" vs ADR-0001 应用时区 | 以 ADR-0001 为准（appToday）；登记 | F10 |
| D7 | 05 §7 confirm 示例缺 meal_plan_ingredient_id（P0） | Sprint 3 实现前必须修文档；types 已冻结正确契约 | F1/ADR-0002 |
| D8 | 05 §10 认证契约漏 user/is_active | types 以代码为准补全；登记文档同步 | F4 |
| D9 | 注册密码强度 Unicode vs ASCII 残余差异 | 用 Unicode property escapes 近似 + 登记 | 批评 W3 |
| D10 | R-08 隐私信任差异 | 前端隐私说明 + AI 关闭入口（Sprint 2）；不宣称"数据不出户" | R-08 |
| D11 | 无服务端登出/刷新，token localStorage XSS 可读 | 客户端登出 + 不日志 token + 无 v-html；登记限制 | DS-07 |
| D12 | Sprint 2 AI 依赖 C 组后端 + 模型选型前置 | 前端 Mock 先行，契约按 06 §4 冻结 | 02 §10 |

---

## 10. 验收映射（Sprint 1，RTM）

| FR | UI | API | TC | AT |
|---|---|---|---|---|
| FR-001/002 注册登录 | UI-01 | /auth/register;/auth/login | TC-AUTH-01—03 | AT-01 |
| FR-003 隔离 | 全局 | 所有资源 API | TC-SEC-01 | AT-01 |
| FR-005—008 库存 | UI-03/04 | /inventory | TC-INV-01/02 | AT-02 |
| FR-009 临期 | UI-06 | /inventory/expiring | TC-EXP-01—04 | AT-03 |
| FR-010 首页 | UI-02 | /dashboard/summary | 首页统计测试 | AT-02 |

FR-005 分类部分交付（D1）；FR-011/012/013/014/015/018 UI 延后 Sprint 2/3；FR-016 导入冻结；FR-017 无端点不做。03 §6 AI 验收项（107-111）标 Sprint 2 暂缓。

---

## 11. 实现顺序（批评员 sequencing，依赖有序）

- **Phase 0 基础设施 + 共享层冻结**（阻塞一切，先做，不并行页面）：types 全量修正 + auth 类型迁移；client 401 + NormalizedError.status；auth store user/fetchMe/logout；嵌套路由 + 守卫 + edit 路由 + catch-all；AppLayout 挂载 + zhCn + errorHandler；**冻结共享组件/composables/utils 契约（§4.6-4.8）**；tests/setup.ts + TZ。
- **Phase 1 垂直切片**（顺序）：1a UI-01 认证（验证守卫+401+store 端到端）→ 1b UI-03+UI-04 库存（最难写契约：expected_version/reason 方向/按值 diff/Decimal string/409 refetch/软归档 vs 耗尽，成为共享组件参考实现）。
- **Phase 2 铺页**（共享层冻结后可并行）：UI-06 临期、UI-02 首页（依赖 inventory 类型/组件 + appToday）；UI-10 偏好、UI-09 采购属 Sprint 2/3 不在本轮。
- **Phase 3 暂缓桩 + 验证**：AI 三桩改"Sprint 2 未开放"态（无 /ai/* 调用）；统一 AI 入口策略；404 页；人工真实后端集成走查 + 响应式浏览器验证；偏差登记同步。

**并行护栏**：Phase 0 共享契约冻结 + Phase 1 库存验证前，不启动 Phase 2 铺页（防 G3/G4/G5 冲突倍增）。

---

## 12. 决策点（A2 决定，2026-11-24，用户授权"你来决定"）

1. **名称长度**：创建按 03 §5 产品规则 **1~80**（trim 后）；编辑若载入名 >80 按后端上限 **200** 放行，避免阻塞既有数据。登记偏差 D3 待文档同步。理由：尊重产品规格于创建态，又不破坏真实数据。
2. **FR-010 首页跳转口径**：临期卡→`/expiry`；**过期卡→`/expiry` 过期分组**（目的地过期计数==expired_count）；**库存总数卡→`/inventory` 并加脚注/tooltip"库存列表含已耗尽条目，与统计口径不同"**。理由：后端无 qty>0 列表过滤参数，此为不改后端前提下最诚实且计数一致的方案。登记 D2。
3. **FR-005 分类**：前端做**静态选项（乳制品/蔬菜/蛋类/肉类）+ 诚实空态提示**"仅匹配已关联食材库的条目"；标记**部分交付，待 PO（psh）签字**。A2 先按此实现，不伪造 per-item 分类。登记 D1。
4. **状态管理**：**auth 等跨页共享态入 Pinia**；页面级服务端数据用 **composable（useAsyncState/usePagination）+ 本地 ref**，请求一律走 `src/api/` 封装。符合 §5.3"不在组件直接 fetch、共享状态放 Pinia"的意图；服务端数据非客户端共享态，不强塞 Pinia（避免方案 C 过度设计）。
5. **spec 位置**：保留 `docs/specs/`（A 组工作设计稿），评审后由 PO 同步 RTM/台账。原则已记入根 `CLAUDE.md`。