# PantryPilot 项目原则（每次会话必读）

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

面向独居青年与家庭的 Web 食材管理应用。Vue3 + TS + Element Plus + Pinia ｜ FastAPI + SQLAlchemy2 + PostgreSQL ｜ Nginx + Docker Compose。6 人团队 A/B/C 三组，30 天周期。

## 1. 最高原则（不可违背）
- **AI 只给建议，事实和库存变更由确定性程序与用户确认来完成。** 库存数量/到期日/扣减永远来自数据库，不来自模型。AI 草稿/膳食方案必须经 Schema 校验 → 业务规则校验 → **用户确认**才生效；模型阶段不写库。模型不可用时库存与临期照常工作。
- AI 生成内容前端必须显式标注"建议/草稿"，不得伪装成事实或已执行动作。

## 2. 契约权威与规划锚定
- **后端代码是契约权威**（`backend/app/schemas|endpoints|services`）。文档（05/03 等）滞后处以代码为准，并把偏差登记到 spec/台账，不擅自抹平。
- **任务范围严格锚定规划文档**：`10_工程管理台账.xlsx`（Backlog 的 Sprint 列与负责人列、需求追踪RTM、人员RACI）、`文档/01_项目立项书与项目管理计划.docx` §5/§6、`开发规范.md`、`README.md`。**从真实代码状态出发，不随意发挥、不超范围**；新增功能走变更评审。
- 台账内部矛盾（如 Sprint计划 row3 vs Backlog Sprint 列）以 Backlog+01+README 三源一致为准，登记待 PO 确认。台账"已完成"状态实指后端，须核实前端真实进度。

## 3. 前端强制规范（开发规范 §5.3）
- `<script setup lang="ts">`；组件 PascalCase，文件名与组件同名。
- **所有请求走 `src/api/` 封装，不在组件里直接 fetch**；共享状态放 Pinia。
- **每个页面必须实现四态：加载 / 空数据 / 错误 / 权限失效**（权限失效由全局 401 处理器统一 toast+redirect 满足）。
- 数量必须与单位同时展示；日期按**应用时区 Asia/Shanghai**（ADR-0001，非浏览器本地）；临期状态用服务端 `status`，前端不重算。
- 破坏性操作（删除、扣减）必须二次确认，确认框展示每项数量与单位。
- 分层：`api/`(按域 typed service) → `stores/`(Pinia) → `composables/` → `components/`(共享) → `views/`(薄页面)。

## 4. 契约总则（已逐字核验后端代码）
- 前缀 `/api/v1`；Bearer；错误信封 `{code, message, request_id, details?}` + 头 `X-Request-ID`。**Sprint 1 无代码填充 details，前端不依赖它分支**。
- **所有请求校验失败 → 400 `VALIDATION_ERROR`，无字段细节。Sprint 1 不存在 422。** → 前端客户端校验必须完整镜像后端规则。
- **按 code/status 分支，绝不按 message 文本**（401 有 3 种 message；后端 service message 是英文，需中文映射）。
- Decimal → **JSON 字符串**（固定 3 位小数 "1.500"；预算 2 位 "50.00"）。**提交也用字符串，绝不 parseFloat 往返**；展示去尾零，原始串保留。
- date "YYYY-MM-DD"；datetime ISO8601 带时区；UUID 小写连字符。
- Pydantic v2 响应始终输出全部字段 → 响应 TS 接口用**必填可空键**（`x: T|null`），`?` 仅用于请求体（PATCH 省略键=不变，null=清空）。
- JWT HS256 `{sub,exp}` 默认 60 分钟，`expires_in` 是**秒**。**无刷新端点、无服务端登出** → 登出仅客户端清 token，不宣称服务端失效。
- 库存 PATCH 必带 `expected_version`（乐观锁，409→refetch 保留输入不自动重发）；任何有效变更必带方向正确的 `reason`（add>0/consume<0/adjust）；编辑**按值 diff 省略未改键**；unit 创建后不可改。耗尽=PATCH quantity 0（条目保留）vs 删除=DELETE 软归档（隐藏、幂等）。
- `/inventory/expiring` 是**裸数组无分页**，含过期项、排除 archived+qty0。`/dashboard/summary` 只给计数（过滤 qty>0），与 `/inventory` 列表 total（不过滤 qty）口径不同（FR-010 跳转须修正）。
- 偏好 GET 404=首次设置态（非错误）；PUT 全量替换 upsert（首次也 200），**漏传列表=静默清空 → 永远六字段整表提交**。
- 采购 DELETE 是**硬删除非幂等**（vs 库存软归档幂等）；status 含 `cancelled`；勾选只改状态不自动入库/下单。
- confirm（Sprint 3）需头 `Idempotency-Key`(UUID) + 行级 `meal_plan_ingredient_id`（ADR-0002，05 §7 示例缺此字段是 P0 文档错误）。

## 5. 运行与协作
- **容器优先**：Docker 是唯一受支持后端运行环境（Python 3.11+，代码用 `datetime.UTC`/`StrEnum`）。统一入口 `bash scripts/dev.sh up|test|migrate|seed|logs|backup|restore`。前端热更新 `cd frontend && npm install && npm run dev`（:5200，/api 代理 :8000）。`SECRET_KEY` 占位符拒启动。
- **`docker` 报 permission denied 多半不是 Docker 坏了**：`install_docker.sh` 会把用户加进 `docker` 组，但**当前登录 shell 的组身份不会自动刷新**。判断：`getent group docker` 能看到用户名 = 组已加好、只是会话没刷新。处理：当前 shell 执行 `newgrp docker`（或注销后重新登录）；脚本里可用 `sg docker -c '...'` 临时切换。
- 分支：每人只在 `dev/<名字>` 开发，每天 `git merge origin/main`；**禁止直接 push main**，全走 PR（Merge commit，CI 必绿）。当前 A2=dyl（dev/dyl），A1=psh(兼PO)。
- 目录归属：`frontend/src/**`、`frontend/tests/**` = A 组；`文档/**`、台账 = PO（评审后修订，同步 RTM）；`backend/alembic/**` = B 组；`deploy|scripts|.github` = C 组；`package.json|vite.config|tsconfig` 共享（加依赖 PR 说明）。
- 测试：作者写自己单测；C 组设计集成/E2E/AI 用例。**前端 CI（lint→typecheck→vitest→build）无后端无浏览器 → 所有 CI 测试 mock-based（mock service 层）**；真实后端验证走人工集成清单（demo 登录 `demo@example.com/demo12345`，登录非注册）。保留现有 8 个 format 测试绿。
- 安全：密钥（SECRET_KEY/LLM_API_KEY/DATABASE_URL）仅服务端，**不进前端产物/日志/截图/文档**；前端只用 `VITE_` 公开变量；不日志 token/密码；token 不进 URL。
- 项目末端门禁：Must 完成率 100%、P0 用例 100%、S1/S2 清零、核心闭环端到端、干净环境部署+持久化。**操作视频由 A 组负责**。

## 6. 当前真实进度（2026-11-27 实测校准）
- 后端：Sprint 1 已实现并合入 main。实测 **22 个路由**（21 个在 `/api/v1` 下，含 `GET /inventory/categories`；+ 根路径 `GET /health`）、12 张表、2 个迁移（单一 head `20261121_0002`）、**94 个测试函数**。
- 前端：Sprint 1 五页（认证/首页/库存/表单/临期）+ Sprint 2 两页（偏好/采购）已实现并合入 main。`src/api/` 已是按域拆分（auth/users/inventory/dashboard/preferences/shopping），有 `composables/`（useAsyncState/usePagination/useUnsavedGuard/useConfirm/useMediaQuery）、`router/guards.ts`（含开放重定向净化）、`components/` 共享件（PageHeader/StatusTag/QuantityText/DecimalInput/FourState/ConfirmDialog）、`utils/appToday.ts`（Intl + Asia/Shanghai，非浏览器本地）。前端测试文件 21 个。
- AI（Sprint 2 后端）**完全未实现**：`backend/app/ai/` 仍只有 `contracts.py` 且**零业务代码导入**；无 `/ai/*` 端点；`config.py` 的 `llm_*` 四项无代码读取；seed 不创建 meal_plans/recipes。UI-05/07/08 保持诚实"Sprint 2 未开放"桩。**「AI 失败降级」目前只存在于文档，代码里没有** —— 因为根本没有 AI 调用可降级。
- 已知坑（必须遵守）：**el-form 组件的 @submit 修饰符 .prevent 在 fallthrough 时丢失且浏览器原生校验会静默阻止提交** → 所有表单加 `novalidate` + 处理器显式 `event?.preventDefault()`；el-input-number 的 `:step` 会进入原生 step 校验（step 必须与 min 对齐或 0.01/1，否则提交被静默拦截）。jsdom 下 el-form 字段不注册（validate 恒 true）→ 提交门禁用确定性手动守卫。
- 路线图与 Sprint 1 详设见 `docs/specs/2026-11-24-frontend-development-design.md`。

## 7. 沟通
始终用中文回复（技术标识符保持原文）。

---

## 8. 后端架构：五个声明层，四个在用

声明的分层（`backend/app/__init__.py:3-6`、`开发规范.md:180`）：

```
api → services → domain / repositories → db      ＋  独立的 ai 层
```

**实际代码和声明不一致，这是最容易踩的坑：**

| 目录 | 声明 | 实际 |
|---|---|---|
| `app/domain/` | 领域规则（库存、日期、扣减校验） | **空壳**。只有 `__init__.py`（`__all__ = []`），零导入方。领域规则实际是 **`app/services/` 模块顶部的自由函数** |
| `app/ai/` | Provider / Prompt / Parser / Validator | **只有 `contracts.py`**（5 个 Pydantic 模型 + 1 个 StrEnum），**零业务代码导入** |
| `app/repositories/` | 数据访问 | 纯 SQL，无业务逻辑（唯一例外见下） |

**领域规则的真实位置**（新增规则先看这里，而不是去建 `domain/` 包）：

| 规则 | 位置 |
|---|---|
| 「今天」（按 `APP_TIMEZONE`） | `app/services/inventory_service.py:26-28` `current_date()` |
| 临期状态派生 | `app/services/inventory_service.py:31-39` `inventory_status()` |
| 临期窗口常量 | `app/services/inventory_service.py:23` `EXPIRING_WINDOW_DAYS = 3` |
| 幂等请求哈希 | `app/services/meal_plan_service.py:47-62` `compute_request_hash()` |
| `source_type` 推导 | `app/services/meal_plan_service.py:65-72` `plan_source_type()`（服务端推导，客户端不得传） |
| 采购清单去重键 | `app/services/shopping_service.py:32-36` `_item_key()` |

> 要新增真正的领域层，先与仓库负责人确认走哪条路：**填 `app/domain/`**（规范要求它不依赖 api/ai），还是**沿用 `services/` 里的自由函数约定**。两者当前互相矛盾，别自己混着来。

### 请求流

```
FastAPI 路由 (app/api/v1/endpoints/*.py)     —— 薄：取 current_user.id、映射状态码、传 Pydantic payload
  └─ CurrentUser = Annotated[User, Depends(get_current_user)]   (app/api/dependencies.py:32)
  └─ Depends(get_db) → request-scoped Session
  └─ Service().method(db, current_user.id, payload)
       └─ Repository().<query>(db, user_id, ...)   —— 所有查询必须带 user_id
            └─ ORM models
```

- 路由**从不**直接碰 repository、从不写 SQL、从不算业务值。
- **service 构造时接受可选 repository 参数**（`def __init__(self, inventory: InventoryRepository | None = None)`），这是测试注入 fake 的接缝 —— 照此写新 service。
- 新增业务域 = `endpoints/<domain>.py` 新文件 + 在 `app/api/v1/router.py` 加一行 `include_router`。

### 用户隔离（FR-003）

两道防线：

1. **Repository 层**：每条查询都带 `user_id`。唯一两个例外是「公共菜谱行 `user_id IS NULL`」和「经已鉴权父行间接限定」——后者在文档里也需注明。
2. **跨实体检查**：子行经父行到达时，父行的 WHERE 带 `user_id`，不匹配返回 **404 而非 403**（不泄露存在性）。

请求体里**永远不能出现 `user_id`** 作为权限依据。

### 事务与写路径

**`session.commit()` 只允许出现在 `app/services/` 的方法里。** Repository 不 commit，路由不 commit。

库存写路径的固定形状（`app/services/inventory_service.py:46-80`）：

```
校验 → 建实体 → repo.add + db.flush()（拿到 id）
     → 写一条 inventory_transactions 流水
     → db.commit()      ← 唯一的事务边界
     → db.refresh()     ← 重载 created_at/updated_at 等服务端默认值
     → 转 response
```

**每一次数量变化都必须同时写一条流水**，不变量：`sum(delta_quantity) == 当前 quantity`。流水表是 append-only。应用账号对流水只有 SELECT/INSERT 是**设计约定**（ADR-0002 §影响），**仓库里目前没有应用账号的授权脚本**，落地部署时需要补。

### 乐观锁与并发

- `inventory_items.version`（Int，NOT NULL，**DB 层无默认值**，应用必须显式写 1）。
- 客户端 PATCH 必须回传 `expected_version`（`ge=1`，必填）。
- 更新用一条条件 UPDATE：`UPDATE ... SET version = expected_version + 1 WHERE id=? AND user_id=? AND version = expected_version`；`rowcount == 0` → **409 `STATE_CONFLICT`**。前端的 `version` 预检查只是快路径，**rowcount 才是权威判定**。
- 计划确认扣减走 `SELECT ... FOR UPDATE` 行锁；**多个批次按 `inventory_item_id` 升序依次加锁**（`sorted(totals, key=str)`）——这是防死锁约定，别改顺序。
- 删除库存是**软删除**（置 `archived_at`），**流水必须保留**；重复归档幂等且保留首次时间戳。采购清单则是**硬删除**。

### 幂等（`POST /api/v1/meal-plans/{id}/confirm`）

- `Idempotency-Key` 是**必填 header**，规范化为 UUID 字符串。
- `request_hash` = SHA-256(规范化 JSON)：items 按 `meal_plan_ingredient_id` 排序、数量 quantize 到 3 位小数、`sort_keys=True` → **与请求字段顺序无关**。
- `result_snapshot` 存**业务结果**（不含 `idempotent_replay` 之类易变字段）→ 重放返回**逐字节相同**的响应体。
- **幂等检查在状态检查之前**：成功后的重试拿到首次结果，而不是 409。
- 同 Key 不同内容 → **409**；不同 Key 确认已 confirmed 的计划 → **409**。
- 幂等键作用域是 `UNIQUE(user_id, idempotency_key)`（按用户，不全局）。
- 兜底：唯一约束冲突时 `IntegrityError` → rollback → 重读 → 重放。

### 临期状态：运行时计算，不落库

状态**永远在读取时计算**，从不写进数据库（ADR-0001）。

```
过期：expiry_date < 今天
临期：今天 <= expiry_date <= 今天 + 3
正常：expiry_date > 今天 + 3
```

- 「今天」= `current_date()` = `datetime.now(ZoneInfo(settings.app_timezone)).date()`，`app_timezone` 默认 `Asia/Shanghai`。
- **绝不要用 `date.today()` 或不带 `ZoneInfo` 的 `datetime.now()`**。用户表没有时区字段，MVP 全局统一时区（ADR-0001）。
- **时间戳一律 UTC**（`datetime.now(UTC)`），只有「日期」按用户时区解释。
- ⚠️ `EXPIRING_WINDOW_DAYS = 3` 在 service 里，但 repository 的 SQL 又**字面量写了一遍 3**（`app/repositories/inventory_repository.py:174,180`）。改窗口必须同时改两处。

### 错误处理

所有面向用户的失败一律抛 `app/core/errors.py` 里的 `AppError` 子类 —— **不要用 `HTTPException`，不要抛裸 `Exception`**。响应体固定：

```json
{"code": "...", "message": "...", "request_id": "..."}
```

- `details` 只在异常显式携带时才出现（Sprint 1 无代码填充）。
- **字段级校验错误不会回传给客户端** —— 统一转成 400 `VALIDATION_ERROR`（刻意为之：避免回显含密码的请求体）。
- `request_id` 由 `X-Request-ID` 请求头透传或 `uuid4().hex` 生成，同时进响应体和 `X-Request-ID` 响应头；日志里由 `RequestIdFilter` 自动带上。
- 已定义但**尚未被使用**的 AI 错误类：`AIOutputInvalidError`(422)、`RateLimitedError`(429)、`AIProviderError`(502)、`AITimeoutError`(504) —— AI 层落地时直接用它们。

---

## 9. 常用命令

### 后端测试

标准路径（容器内，无需宿主机 Python）：

```bash
bash scripts/dev.sh test                                   # 全量
```

**跑单个文件或单个用例**（容器内，`backend-test` 服务已挂载源码，改代码无需重建镜像）：

```bash
docker compose -f deploy/docker-compose.yml --profile test run --rm -T \
  backend-test python -m pytest tests/api/test_inventory.py -o addopts=

docker compose -f deploy/docker-compose.yml --profile test run --rm -T \
  backend-test python -m pytest tests/api/test_inventory.py::test_inventory_is_isolated_between_users -o addopts=
```

> ⚠️ **直连 compose 跑测试时，2 个并发用例会因连不上维护账号而失败**（不是代码问题）：
> 根目录 `.env` 里的 `TEST_MAINTENANCE_DATABASE_URL` 写的是 `localhost:5432`，而容器内的 `localhost`
> 不是 db 服务 → `connection refused`。**只有 `scripts/dev.sh test` 会把这个主机名改写成 `db:5432`**
> （`dev.sh` 的 `maintenance_url_in_container()`）。要直连 compose 跑并发用例，自己补上：
>
> ```bash
> docker compose -f deploy/docker-compose.yml --profile test run --rm -T \
>   -e TEST_MAINTENANCE_DATABASE_URL=postgresql+psycopg://<user>:<pass>@db:5432/pantrypilot_test \
>   backend-test python -m pytest tests/api/test_meal_plan_confirm.py -o addopts=
> ```
>
> 其余用例不受影响（`conftest.py` 只对维护账号这一条 URL 做连库动作）。

本地跑（需要 3.11+ 虚拟环境）：`cd backend && python -m pytest tests/api/test_inventory.py::test_name -q`

> **测试的三个硬前提**（缺一个就整轮 import 失败，不是跳过）：
> 1. `TEST_DATABASE_URL` 必须指向库名恰为 **`pantrypilot_test`** 的库，且**已执行过 `alembic upgrade head`** —— 夹具不建表。
> 2. `SECRET_KEY` 必须是非占位符 —— `app/core/config.py:79` 在 import 期就实例化 settings。
> 3. 需要一个可连的 PostgreSQL（即使只跑 `test_health.py`，因为 `client` 夹具依赖 `db_session`）。
>
> `tests/conftest.py:60-61` 的库名守卫会**硬失败**（`RuntimeError`，非 skip），确保测试永远打不到开发库。
> 需要真实并发（两条独立连接、真实行锁）的 2 个测试依赖 `TEST_MAINTENANCE_DATABASE_URL`；未配置时**自动 skip**。

### 后端检查（CI 同款）

```bash
cd backend
ruff check app tests            # lint
ruff format --check app tests   # 格式
alembic upgrade head            # 迁移
```

### 前端

```bash
cd frontend
npm install && npm run dev      # http://localhost:5200（/api 代理 :8000）
npm run lint / typecheck / test / build
npm run test -- tests/format.spec.ts   # 单个测试文件
```

> Vitest 的 `include` 是 `tests/**/*.spec.ts` —— **放在 `src/` 里的 spec 会被静默忽略**。

### 迁移

迁移文件命名 `<YYYYMMDD>_<NNNN>_<slug>.py`，放 `backend/alembic/versions/`。当前只有一个 head（`20261121_0002` → `20261120_0001`）。**只有 B 组能写迁移**；迁移与模型改动必须在同一个 PR 内；禁止手改已合并的迁移。

---

## 10. 已知问题与陷阱（均为 2026-11-21~27 在真实环境实测）

**已修（本次工作区提交）**

1. ~~`dev.sh` 的 `cmd_test_db` 先授权后迁移~~ → **已修**：全新测试库上 `GRANT ... ON TABLE users` 报 `relation "users" does not exist`，psql 未开 `ON_ERROR_STOP` → **脚本仍打印「[OK] 维护账号已配置」**（静默撒谎），角色最终 0 条表权限 → 首次 `dev.sh test` 得 **2 failed, 98 passed**（`InsufficientPrivilege`）。改为 建库 → 迁移 → 授权 + `ON_ERROR_STOP=1`。修后全新库单次即 **100 passed**。
2. ~~`dev.sh check` 永远退出 2~~ → **已修**：`cmd_check` 用 `"${@:-}"`，无参数时传入**一个空字符串**，`check_env.sh` 落进「未知参数」→ 退出 2，**自检根本不会跑**。改用 `"$@"`。
3. ~~备份失败留下 0 字节文件，恢复会拿它清空数据库~~ → **已修**：shell 的 `>` 先建文件，`pg_dump` 失败也留下 0 字节「备份」；`cmd_restore` 不校验就 `DROP SCHEMA public CASCADE`，空文件喂 `psql` 退出码 0，脚本报「恢复完成」；而推荐的 `curl /health` **不查库**，清空了照样 ok。改为先写 `.partial`、失败即删；恢复前校验「非空 + 含 `CREATE TABLE`」，否则拒绝执行。
4. ~~`seed.py` 写入的库存没有流水~~ → **已修**：每次入库同步写一条 `inventory_transactions`（`reason='add'`、`source_type='manual'`），实测 `sum(delta_quantity) == quantity` 对每个条目成立。
5. ~~`seed.py` 用 `date.today()` 与应用的「今天」差一天~~ → **已修**：改用 `settings.app_timezone`。容器系统时区是 **UTC**，临期判定按 **Asia/Shanghai**，原实现每天有 8 小时会算错日期。
6. ~~`bootstrap.sh` 吞掉 `SECRET_KEY` 生成失败~~ → **已修**：原 `python3 ... || true` 失败也被吞掉却照样打印成功。现回读校验，仍是占位符就 die。
7. ~~nginx 启动时解析上游，后端换 IP 后前端持续 502~~ → **已修**：实测后端 `.5`→`.6` 后 nginx 仍打旧 IP（`upstream: "http://172.18.0.3:8000"`），前端 502 而后端直连 200。现改为 `resolver 127.0.0.11 valid=10s ipv6=off;` + `set $backend http://backend:8000; proxy_pass $backend$request_uri;`。⚠️ 变量形式的 `proxy_pass` **不会自动带原始 URI**，必须显式拼 `$request_uri`。

**仍未修（需团队决策）**

8. **应用连的是数据库超级用户**（`deploy/docker-compose.yml:33`）：实测 `current_user = pantry`、`is_superuser = True`。ADR-0002 的「应用账号对 `inventory_transactions` 只有 SELECT/INSERT」**没有任何数据库层强制**，仓库里也没有应用账号授权脚本 —— **追加式审计目前只靠应用代码自律**。需补 `pantrypilot_app` 最小权限账号。
9. **compose 的 `${POSTGRES_*}` 插值不读根目录 `.env`**：compose 的项目目录是 `deploy/`，它找 `deploy/.env`（不存在）→ 回落默认值。但 `dev.sh` 会 `set -a; . ./.env` 导出到 shell，而 **shell 环境变量在 compose 插值中优先级最高** → 所以 **`dev.sh` 路径生效、直连 `docker compose` 不生效**（`README.md` 的「底层等价命令」正是直连那条）。另外 `bootstrap.sh` 只在 `.env` **不存在**时才从 `.env.example` 复制，老 `.env` 永远补不上 `POSTGRES_*`/`*_PORT`。
10. **登录接口存在用户枚举时序侧信道**（`auth_service.py:46`）：实测未知邮箱 **~0ms**、已注册邮箱 **~76ms**（Argon2id 耗时），响应体与状态码完全一致，只能靠计时区分。注册接口还会**明文回显「邮箱已被占用」**；登录/注册**均无限流**。
11. **JWT 无吊销机制**（无 `token_version`/`jti`/logout/改密），泄露令牌 60 分钟内不可作废；`auth_service` 里也没有改密路径。
12. **`X-Request-ID` 完全由客户端控制且无字符/长度校验**；4xx 与认证失败**完全不落日志**；日志脱敏正则遗漏 `secret_key=`/`api_key=`/Basic 认证/Cookie。
13. `MealPlanRepository.list_ingredients()` 与 `RecipeRepository.get()` 的签名里**没有 `user_id`**，间接限定全靠调用方自觉 —— 落地 AI 接口时极易踩成跨用户读取。
14. `InventoryRepository` 的列表 ORDER BY 不是全序，同到期日的条目**分页会随无关编辑漂移**，导致条目被静默漏掉或重复。
15. `SELECT ... FOR UPDATE` **不会刷新已在 identity map 中的实体**（缺 `populate_existing()`），可能读到陈旧的 `quantity`/`version`。
16. **Vitest `include` 只覆盖 `tests/`**（`vite.config.ts:31`），**`src/` 下的 spec 被静默忽略** —— Vue 生态惯例是就近放，A 组很容易踩空，「修复缺陷必须补回归用例」会形同虚设。
17. `backend/tests/conftest.py:37-51` 的 `_unsafe_legacy_db_session()` 是**未被引用的死函数**，会 `create_all`/`drop_all` 业务 schema —— 恰好违反它自己上面三行的注释。可删。
18. `app/core/errors.py:58-60` 的 `ConflictError` 与 `:53-55` 的 `StateConflictError` 完全等价（都 409/`STATE_CONFLICT`），只有 `auth_service.py` 在用前者。留一个即可。
19. `app/models/enums.py` 的 4 个枚举**完全没人用**，schemas 各自用 `Literal[...]` 重新声明了一遍 —— 两套事实来源。
20. `app/domain/`、`tests/unit/`、`tests/ai/`、`backend/scripts/` 都是空目录；`backend/UNKNOWN.egg-info/` 是残留。**不要因为目录存在就以为有实现。**
21. `DashboardRepository` 直接调用兄弟仓库的静态方法 `InventoryRepository.status_conditions()`；`MealPlanService` 绕过 `InventoryService` 直接改数量，导致**写流水的规则散落在两处**。新增扣减路径时别再复制第三份。
22. `GET /api/v1/inventory/expiring` 实际返回**过期 + 临期**（按 `expiry_date <= today+3` 过滤，不是 `>= today`），路由名有误导性。
23. 已归档的库存即使带 `include_archived=true`，`GET /inventory/{id}` 仍返回 404（只有列表端点认这个参数）。
24. `tests/api/test_errors.py:16,33` 在**全局 app** 上注册路由且不清理，会泄漏到后续测试。
25. `scripts/dev.sh` 的 `backend-test` 镜像**永不重建**，改 `requirements-dev.txt` 后测试仍跑在旧依赖上（源码挂载了、依赖没有）。
26. 迁移 `20261121_0002` 未用 `op.f()`，`shopping_items` 的数量检查在库里叫 `ck_shopping_items_ck_shopping_items_quantity_positive`（前缀重复）。**功能正常**（实测能拒绝 `quantity=0`）、**autogenerate 也不报漂移**，但迁移里引用该约束必须用这个名字。要修正应在**新增迁移**里改名（`backend/alembic/**` 归 B 组）。
27. `scripts/install_docker.sh` **覆盖式重写** `/etc/docker/daemon.json`，会清掉公司环境自带的 registry-mirror / insecure-registries。
28. `frontend/Dockerfile` 用 `npm install` 且 lockfile glob 可选（`package-lock.json*`），**镜像构建不可重现** —— CI 用的是 `npm ci`。
29. CI 里**从不构建 Docker 镜像**，也不校验 `docker compose config`（只有本地 `check_env.sh` 校验）。
30. `scripts/` **不在 CI 的 ruff 覆盖范围内**（CI 只跑 `ruff check app tests`，工作目录 `backend/`）—— `scripts/seed.py` 实测有 5 条 lint 报错（1×I001 导入排序 + 4×RUF100 多余 `noqa`），长期无人发现。注意 `noqa: E402` 是有意义的标注（导入必须放在 `_bootstrap_import_path()` 之后），修 RUF100 前先确认 E402 是否真的未启用。
31. **直连 compose 跑 pytest 时 2 个并发用例会假失败**：根 `.env` 的 `TEST_MAINTENANCE_DATABASE_URL` 写的是 `localhost:5432`，容器内 `localhost` 不是 db 服务 → `connection refused`。**只有 `scripts/dev.sh test` 会把主机名改写成 `db:5432`**。直连 compose 跑并发用例要自己补 `-e TEST_MAINTENANCE_DATABASE_URL=...@db:5432/...`。
32. `scripts/seed.py` 的幂等清理**范围刻意收窄**到「演示账户 + 本脚本那组（名称, 单位）」，演示账户上手工添加的条目不会被清掉。清理顺序必须**先流水后库存**（`inventory_transactions.inventory_item_id` 是 ON DELETE RESTRICT）。
33. `README.md` 的「当前状态」仍写「Sprint 1 尚未开工」，与台账/实际不符。**以 `10_工程管理台账.xlsx` 为准。**

**做得对、不要动**

- 幂等重放逐字节一致；幂等检查**刻意排在状态检查之前**；`source_type` 由服务端推导、客户端不得传；空 `ai_provider` 在任何写入前 400 拒绝；跨实体访问 404 而非 403；`commit()` 只出现在 `app/services/`；每次数量变化都写流水；批次按 id 升序加锁防死锁；校验错误不回显请求体；测试库名守卫硬失败。

---

## 11. 参考资料

| 文档 | 何时读 |
|---|---|
| `README.md` | 项目定位、功能范围、技术栈、快速开始 |
| `开发规范.md` | 分支模型、目录归属、代码规范、DoD 自检清单（**提交前必读第 9 节**） |
| `团队上手步骤.txt` | 新成员五步上手（面向人的版本） |
| `文档/04_软件总体设计说明书.docx` | 分层职责、模块划分、关键流程、ADR-001~005 |
| `文档/05_数据库详细设计与API接口规范.docx` | 表结构、约束索引、事务、**API 清单与错误码（§8）**、认证契约（§10，已冻结） |
| `文档/06_AI技术设计与评测方案.docx` | AI 边界、6 个组件、输出契约、护栏、**评测集 AI-001~AI-008** |
| `文档/07_软件测试计划与测试用例.docx` | 测试层级、`TC-*` 用例编号、缺陷分级与退出准则 |
| `文档/08_部署运维与开源交付手册.docx` | 环境变量表、备份恢复、故障处理、附录 A 部署验证记录 |
| `docs/adr/0001-app-timezone.md` | 临期判定为什么用全局时区、为什么运行时计算 |
| `docs/adr/0002-meal-plan-confirmation.md` | 幂等、批次汇总扣减、`source_type` 推导、单位不换算的全部决策 |
| `docs/test-database-setup.md` | 测试库与维护账号的准备顺序、最小权限 |
| `docs/specs/2026-11-24-frontend-development-design.md` | 前端 Sprint 1 详设与实现计划 |
| `10_工程管理台账.xlsx` | **执行期唯一事实源**：人员 RACI、Backlog、Sprint、RTM、风险、缺陷、ADR、测试用例 |
| `CHANGELOG.md` | 每次变更的实际内容（Keep a Changelog 格式） |
| `docs/reviews/2026-11-21-配置实测报告.md` | **在真实环境跑过每条配置路径**的记录，含复现命令 |
| `docs/reviews/2026-11-21-代码审查报告.md` | 多维度扫描 + 对抗式验证的审查结果，带 ✅已实测 / 🔍反方未推翻 / ⚠️待核实 三级标记 |
| `docs/reviews/2026-11-21-文档与台账一致性审查.md` | 文档与台账跟实际代码的逐条核对 |
| `docs/research/2026-11-21-竞品与最佳实践调研.md` | 竞品对比与领域最佳实践，附对照本仓的 P0/P1/P2 差距清单 |
| `docs/research/2026-11-21-AI层落地设计调研.md` | Sprint 2 AI 层落地设计（Provider Adapter / 菜谱检索与评测 / 注入防护与降级） |
