# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目一句话

PantryPilot（食刻管家）—— 面向独居青年与小家庭的 Web 食材库存管理。核心信条写在 `README.md`：

> **AI 只给建议，事实和库存变更由确定性程序与用户确认来完成。**

任何改动都不能破坏这条边界：库存数量、到期日期、扣减结果永远来自数据库，不来自模型；模型输出必须经 Schema 校验 + 业务规则校验 + 用户确认后才生效。

技术栈：Vue 3 + TS + Element Plus ｜ FastAPI + SQLAlchemy 2.x + PostgreSQL 16 ｜ Nginx + Docker Compose ｜ OpenAI 兼容模型 API。

---

## 1. 环境：容器是唯一受支持的后端运行环境

后端基线是 **Python 3.11+**（代码里用了 `datetime.UTC`，3.11 才引入），而 Ubuntu 22.04 自带 3.10。**宿主机 Python 版本不是阻塞项，但也不是可选项** —— 3.10 的解释器连 `import app.main` 都会失败。

```bash
sudo bash scripts/install_docker.sh && newgrp docker   # 一次性
bash scripts/bootstrap.sh                              # 写 .env + 生成随机 SECRET_KEY + 构建镜像 + 起服务 + 迁移开发库与测试库
bash scripts/check_env.sh                              # 环境自检，期望 FAIL 0（--fast 跳过前端检查，约 15s）
```

> **「permission denied while trying to connect to the docker API」多半不是 Docker 没装好。**
> `scripts/install_docker.sh` 会把用户加进 `docker` 组，但**当前登录 shell 的组身份不会自动刷新**。
> 判断方法：`getent group docker` 能看到用户名 → 组已加成功，只是会话没刷新。
> 处理：在当前 shell 执行 `newgrp docker`（或注销后重新登录）；脚本里可用 `sg docker -c 'docker ...'` 临时切换。
> `check_env.sh` 会把它报成 `docker ... 可用` 之外的失败，`dev.sh` 的 `require_docker()` 会提示「执行 newgrp docker 或注销后重新登录」。

- `.env` 在**仓库根目录**（不在 `backend/` 下）。`SECRET_KEY` 保留占位符 `change-me-to-a-long-random-string` 或留空 → 服务**拒绝启动**（`app/core/config.py:51-57`）。`app/core/config.py` 会同时读根目录 `.env` 与 `backend/.env`，后者优先，真实环境变量永远最高优先。
- 密钥只进服务端环境变量。`.env` / `LLM_API_KEY` / 备份文件一律不提交（`.gitignore` 已覆盖）。

## 2. 常用命令

### 统一入口 `scripts/dev.sh`（所有后端操作走这里）

| 命令 | 作用 |
|---|---|
| `bash scripts/dev.sh up` | 构建镜像并启动 db/backend/frontend，轮询 `pg_isready` 后自动迁移开发库 |
| `bash scripts/dev.sh down` | 停止（`--volumes` 连数据卷一起删） |
| `bash scripts/dev.sh restart` | 重启服务 |
| `bash scripts/dev.sh ps` / `logs [服务名]` | 状态 / 日志 |
| `bash scripts/dev.sh migrate` | 对**开发库**执行 `alembic upgrade head` |
| `bash scripts/dev.sh test-db` | 准备测试库：建库 → 授权维护账号 → 迁移测试库 |
| `bash scripts/dev.sh test` | 先 `test-db`，再在 `backend-test` 容器内跑 pytest |
| `bash scripts/dev.sh seed` | 写入演示数据（`demo` / `demo12345`） |
| `bash scripts/dev.sh backup` / `restore <文件>` | 备份 / 恢复开发库 |
| `bash scripts/dev.sh shell` | 进入后端容器 |
| `bash scripts/dev.sh check [--fast]` | 等价于 `check_env.sh` |
| `bash scripts/dev.sh openapi` | 打印 `/docs`、`/openapi.json`、`/health` 地址 |

常用地址：前端容器 `http://localhost/` ｜ 后端 `http://localhost:8000` ｜ 前端热更新 `http://localhost:5200`（`/api` 自动代理到后端）｜ Swagger `http://localhost/docs`。

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

本地跑（需要 3.11+ 虚拟环境）：

```bash
cd backend && python -m pytest tests/api/test_inventory.py::test_name -q
```

> **测试的三个硬前提**（缺一个就整轮 import 失败，不是跳过）：
> 1. `TEST_DATABASE_URL` 必须指向库名恰为 **`pantrypilot_test`** 的库，且**已执行过 `alembic upgrade head`** —— 夹具不建表。
> 2. `SECRET_KEY` 必须是非占位符 —— `app/core/config.py:79` 在 import 期就实例化 settings。
> 3. 需要一个可连的 PostgreSQL（即使只跑 `test_health.py`，因为 `client` 夹具依赖 `db_session`）。
>
> `tests/conftest.py:60-61` 的库名守卫会**硬失败**（`RuntimeError`，不是 skip），确保测试永远打不到开发库。

需要真实并发（两个独立连接、真实行锁）的 2 个测试依赖 `TEST_MAINTENANCE_DATABASE_URL`；未配置时**自动 skip**，不会用应用账号去删流水。

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
npm install && npm run dev      # http://localhost:5200
npm run lint                    # eslint
npm run typecheck               # vue-tsc --noEmit
npm run test                    # vitest run
npm run test -- tests/format.spec.ts   # 单个测试文件
npm run build                   # vue-tsc --noEmit && vite build
```

> Vitest 的 `include` 是 `tests/**/*.spec.ts` —— **放在 `src/` 里的 spec 会被静默忽略**。目前前端只有 `frontend/tests/format.spec.ts` 一个测试文件。

### 迁移

```bash
bash scripts/dev.sh migrate                     # 开发库
docker compose -f deploy/docker-compose.yml --profile test run --rm -T backend-test alembic upgrade head   # 测试库
```

迁移文件命名 `<YYYYMMDD>_<NNNN>_<slug>.py`，放 `backend/alembic/versions/`。当前只有一个 head（`20261121_0002` → `20261120_0001`）。**只有 B 组能写迁移**；迁移与模型改动必须在同一个 PR 内；禁止手改已合并的迁移。

---

## 3. 架构：五个声明层，四个在用

声明的分层（`app/__init__.py:3-6`、`开发规范.md:180`）：

```
api → services → domain / repositories → db      ＋  独立的 ai 层
```

**但实际代码和声明不一致，这是最容易踩的坑：**

| 目录 | 声明 | 实际 |
|---|---|---|
| `app/domain/` | 领域规则（库存、日期、扣减校验） | **空壳**。只有 `__init__.py`（`__all__ = []`），零导入方。领域规则实际是 **`app/services/` 模块顶部的自由函数** |
| `app/ai/` | Provider / Prompt / Parser / Validator | **只有 `contracts.py`**（Pydantic 输出契约）。没有 provider、没有 prompts 目录、没有 parser/validator，**`contracts.py` 也没有任何业务代码导入它** |
| `app/repositories/` | 数据访问 | 纯 SQL，无业务逻辑（唯一的例外见下） |

**领域规则的真实位置**（新增规则时先看这里，而不是去建 `domain/` 包）：

| 规则 | 位置 |
|---|---|
| 「今天」（按 `APP_TIMEZONE`） | `app/services/inventory_service.py:26-28` `current_date()` |
| 临期状态派生 | `app/services/inventory_service.py:31-39` `inventory_status()` |
| 临期窗口常量 | `app/services/inventory_service.py:23` `EXPIRING_WINDOW_DAYS = 3` |
| 幂等请求哈希 | `app/services/meal_plan_service.py:47-62` `compute_request_hash()` |
| `source_type` 推导 | `app/services/meal_plan_service.py:65-72` `plan_source_type()`（服务端推导，客户端不得传） |
| 采购清单去重键 | `app/services/shopping_service.py:32-36` `_item_key()` |

> 要新增真正的领域层，请与仓库负责人确认走哪条路：**填 `app/domain/`（规范要求它不依赖 api/ai）**，还是**沿用 `services/` 里的自由函数约定**。两者当前互相矛盾，别自己混着来。

### 请求流

```
FastAPI 路由 (app/api/v1/endpoints/*.py)     —— 薄：取 current_user.id、映射状态码、传 Pydantic payload
  └─ CurrentUser = Annotated[User, Depends(get_current_user)]   (app/api/dependencies.py:32)
  └─ Depends(get_db) → request-scoped Session
  └─ Service().method(db, current_user.id, payload)
       └─ Repository().<query>(db, user_id, ...)   —— 所有查询必须带 user_id
            └─ SQLAlchemy 模型
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

**每一次数量变化都必须同时写一条流水**，不变量：`sum(delta_quantity) == 当前 quantity`。流水表是 append-only。应用账号对流水只有 SELECT/INSERT 是**设计约定**（`docs/adr/0002` §影响、`docs/test-database-setup.md` 最小权限），**仓库里目前没有应用账号的授权脚本**，落地部署时需要补。

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
- ⚠️ `EXPIRING_WINDOW_DAYS = 3` 在 service 里，但 repository 的 SQL 又**字面量写了一遍 3**（`app/repositories/inventory_repository.py:174,180`）。改窗口必须同时改两处，否则 `?status=expiring` 过滤结果和逐行 `status` 字段会不一致。

### 错误处理

所有面向用户的失败一律抛 `app/core/errors.py` 里的 `AppError` 子类 —— **不要用 `HTTPException`，不要抛裸 `Exception`**。响应体固定：

```json
{"code": "...", "message": "...", "request_id": "..."}
```

- `details` 只在异常显式携带时才出现（目前没有 service 传 `details=`，实际永远不出现）。
- **字段级校验错误不会回传给客户端** —— `request_validation_error_handler` 统一转成 400 `VALIDATION_ERROR`（刻意为之：避免回显含密码的请求体）。
- `request_id` 由 `X-Request-ID` 请求头透传或 `uuid4().hex` 生成，同时进响应体和 `X-Request-ID` 响应头；日志里由 `RequestIdFilter` 自动带上（`core/logging.py`）。
- 已定义但**尚未被使用**的 AI 错误类：`AIOutputInvalidError`(422)、`RateLimitedError`(429)、`AIProviderError`(502)、`AITimeoutError`(504) —— AI 层落地时直接用它们。

---

## 4. AI 层：当前是空的

`app/ai/contracts.py` 只有 5 个 Pydantic 模型 + 1 个枚举：`IngredientDraft` / `RecipeIngredient` / `RecipeCandidate` / `MissingIngredient` / `MealPlan`，以及 `StorageLocation`（StrEnum）。**没有任何运行时 AI 代码**：

- 没有 `app/ai/provider.py`（规范要求所有模型调用经 Provider Adapter）。
- 没有 `app/ai/prompts/`（规范要求 prompt 带版本后缀并纳入 Git）。
- 没有 Output Parser / Business Validator / Context Builder / Evaluation Harness。
- **没有任何 `/ai/*` 端点** —— `router.py` 里没有注册 AI 路由。
- `config.py` 里的 `llm_base_url` / `llm_api_key` / `llm_model` / `llm_timeout_seconds` **没有任何代码读取**。

**因此「AI 失败降级」在代码里也不存在** —— 因为根本没有 AI 调用可降级。库存、临期、计划确认这些非 AI 路径本来就不依赖模型，所以「模型不可用时其余功能正常」天然成立。

**最大的功能缺口**：没有 HTTP 方式创建 `meal_plans` / `meal_plan_items` / `meal_plan_ingredients`。目前这些行只能由 `scripts/seed.py` 或直接写库产生。落地 AI 时这必须一起解决（AI 只负责生成**候选**，落库仍走用户确认）。

实现 AI 时必须遵守的顺序（`文档/06`）：

```
模型调用 → Output Parser（Schema 校验）→ Business Validator（过敏/禁忌、数量、单位、库存、状态）
        → 前端预览（库存不变）→ 用户确认 → 服务端事务写入
```

- 模型输出**不得**直接写库存、扣库存、宣称已下单。
- 用户输入一律视为不可信数据，与系统指令分离；限制输入长度、输出 token、调用频率与重试次数。
- 新增 AI 行为必须同步更新 `文档/06` 的评测集（`AI-001`~`AI-008`）。

---

## 5. 数据模型要点（12 张表）

| 表 | 关键点 |
|---|---|
| `users` | `username`/`email` 唯一；Argon2id 密码哈希；`is_active` 是唯一的「禁用开关」 |
| `user_preferences` | 过敏原/忌口/饮食偏好为 JSONB；**没有时区字段**（见 ADR-0001） |
| `ingredient_catalog` | `canonical_name` 唯一 + `lower(btrim(...))` 函数唯一索引 |
| `inventory_items` | `quantity` `NUMERIC(12,3)` 且 CHECK ≥ 0；`version` 乐观锁；`archived_at` 软删除 |
| `inventory_transactions` | append-only 流水；`reason` CHECK ∈ add/adjust/consume/meal_plan_deduction；`source_type` CHECK ∈ manual/ai/import；`operation_id` 指向一次操作 |
| `recipes` / `recipe_ingredients` | `recipes.user_id` **可空 = 公共菜谱**（用户隔离规则唯一的例外） |
| `meal_plans` | `status` CHECK ∈ draft/confirmed；**`ai_provider` NOT NULL**（确认时据此推导 `source_type`，空串会被 400 拒绝） |
| `meal_plan_items` / `meal_plan_ingredients` | 用料行绑定 `inventory_item_id`，记录 `required_quantity` / `actual_quantity` / `is_missing` |
| `shopping_items` | `quantity` CHECK > 0；`status` CHECK ∈ pending/purchased/cancelled |
| `meal_plan_confirmations` | `UNIQUE(user_id, idempotency_key)`；存 `request_hash` + `result_snapshot` |

- 命名规范（`app/db/base.py` 的 `NAMING_CONVENTION`）：`pk_` / `fk_` / `uq_` / `ck_` / `ix_` 前缀。**约束名由约定展开**（`ck_%(table_name)s_%(constraint_name)s`），模型里只写短名即可。现有两个例外：迁移 `20261121_0002` 未用 `op.f()`，导致 `shopping_items` 的数量检查在库里叫 **`ck_shopping_items_ck_shopping_items_quantity_positive`**（前缀重复，约束功能正常、autogenerate 也不报漂移，但迁移里引用它必须用这个名字）；`meal_plan_confirmations` 的唯一约束显式命名为 `user_idempotency_key`（无前缀）。
- **新增模型后必须在 `app/models/__init__.py` 里注册** —— Alembic 靠这个 import 才拿得到 metadata（`alembic/env.py:13`）。
- 数量/金额一律 `Decimal`（DB 为 `NUMERIC`），**禁止 `float`**。精度与 `NUMERIC(12,3)` 对齐（`QUANTUM = Decimal("0.001")`）。
- ⚠️ `app/models/enums.py` 里的 4 个枚举**完全没人用**，schemas 那边各自用 `Literal[...]` 重新声明了一遍 —— 两套事实来源，改动时注意同步。

---

## 6. 前端现状：10 个页面全是占位符

`src/views/*.vue` **每个都只有 13 行**，内容是 `PlaceholderView`，后端一个都没接。

- **`src/api/client.ts` 是唯一的请求出口**，但只有裸 axios 实例 —— **没有任何按资源拆分的封装**（`api/inventory.ts` 之类都还没有）。全仓目前只有两个真实请求：`stores/auth.ts` 里的 `POST /auth/login` 与 `POST /auth/register`。规范要求「所有请求走 `src/api/` 下的封装」，实现页面时需要先补这层。
- **没有路由守卫** —— 没有 `beforeEach`，没有 `requiresAuth` meta，未登录不会跳 `/login`。`src/layouts/AppLayout.vue`（带 6 项侧边栏）**是孤儿**，没有任何地方 import 它，`App.vue` 只渲染 `<RouterView/>`。
- **「加载 / 空数据 / 错误 / 权限失效」四态一条都没实现** —— 没有 `ElMessage`、没有 `v-loading`、没有 loading/error ref。`client.ts` 的响应拦截器保留了**响应体**里的 `code` / `message` / `request_id`，但**丢掉了 HTTP status 与响应头里的 `X-Request-ID`**，所以「权限失效」态目前无法从 HTTP 层触发。
- `stores/auth.ts` 没有 `logout()`（只有本地 `clear()`，不通知后端），没有用户态，没有 token 过期跟踪（`expires_in` 被丢弃）。
- 路由 `meta.pageId`（UI-01~UI-10）是路由与 `文档/03` 页面清单的唯一绑定；新增页面沿用这个约定。
- `src/utils/format.ts` 在**前端重算了一遍 3 天临期阈值**，而 `ExpiryView.vue` 的说明写着「状态由服务端计算，前端不自行判定」（FR-009）。两处要同步，或把客户端函数降级为纯展示。

---

## 7. 团队协作约定（摘自 `开发规范.md`，此处只列容易踩的）

- 分支：`main` 受保护，**禁止直接 push**；每人只在自己的 `dev/<名字>` 上开发；每天开工前 `git fetch origin && git merge origin/main`；PR 用 **Merge commit** 合并；审批人数为 0（可自批自合），但留了评论就必须回复或解决。
- 目录归属（**每个目录只有一个组**，冲突的主要来源）：
  - A 组：`frontend/src/**`、`frontend/tests/**`
  - B 组：`backend/app/{api,db,models,schemas,services,domain,repositories}/**`、`backend/alembic/**`（**只有 B 组能写迁移**）
  - C 组：`backend/app/ai/**`、`backend/tests/ai/**`、`deploy/**`、`scripts/**`、`.github/workflows/**`
  - 共享（改动必须 PR 且 CI 必绿）：`backend/app/main.py`、`backend/app/core/**`、`backend/requirements*.txt`、`frontend/package.json`、`frontend/vite.config.ts`、`deploy/docker-compose.yml`、`.env.example`
  - PO 独占：`文档/**`、`10_工程管理台账.xlsx`（二进制，同一时间只能一人编辑）
- 提交信息 `<type>(<scope>): <说明>`；`type` ∈ feat fix docs style refactor perf test build ci chore；`scope` ∈ auth inventory expiry dashboard ai mealplan shopping deploy frontend backend。禁止 `update`、`fix bug`、`修改` 这类无信息量说明。
- 大改动（>300 行或改契约）先开 issue 说明方案。
- 文档 `文档/01~09` 是**基线**，标注「待执行」的只有真实发生后才能改成完成；任何需求/接口变更都要同步 `10_工程管理台账.xlsx` 的 **RTM** 页。
- 不设专职测试：作者写自己的单测，C 组负责集成/E2E/AI 专项的用例设计与自动化，缺陷在台账「缺陷跟踪」页登记。**修复缺陷必须补一条回归用例。**

---

## 8. 已知问题与陷阱（动手前先知道）

**已在 2026-11-21 实测修复（工作区未提交）**

1. ~~`scripts/dev.sh` 的 `cmd_test_db` 先授权后迁移~~ → **已修**：改为 **建库 → 迁移 → 授权**，并给授权步骤加 `ON_ERROR_STOP=1`。原实现在全新测试库上 `GRANT ... ON TABLE users` 报 `relation "users" does not exist`，psql 未开 `ON_ERROR_STOP` → **脚本仍打印「[OK] 维护账号已配置」**（静默撒谎），角色最终 0 条表权限 → 首次 `dev.sh test` 得到 **2 failed, 98 passed**（`InsufficientPrivilege: permission denied for table meal_plan_ingredients`）。修后全新库单次执行即 **100 passed**。
2. ~~`scripts/seed.py` 重复执行会让库存翻倍~~ → **已修**：`seed.py` 现在先清理本次要写的同名批次（演示账户 + 同名同单位）再写入，重复执行结果稳定（实测 12 → 6 → 6）。**注意该脚本现在会 `DELETE`**，范围仅限演示账户由本脚本写入的批次；用户手工添加的条目不受影响。
3. ~~`scripts/seed.py` 写入的库存没有流水~~ → **已修**：每次入库同步写一条 `inventory_transactions`（`reason='add'`、`source_type='manual'`），实测 `sum(delta_quantity) == quantity` 对每个条目成立（不变量此前被演示数据破坏）。
4. ~~`scripts/seed.py` 用 `date.today()` 与应用的「今天」差一天~~ → **已修**：改用 `settings.app_timezone`（与 `current_date()` 同源）。容器系统时区是 **UTC**，而临期判定按 **Asia/Shanghai**，原实现每天有 8 小时会算错日期。
5. ~~`docs/test-database-setup.md` 自相矛盾~~ → **已修**：原文第 19 行写「建库 → 授权 → 迁移」，第 20–21 行却要求「必须先有业务表存在」。已统一为 建库 → 迁移 → 授权。
6. ~~`dev.sh check` 永远退出 2~~ → **已修**：`cmd_check` 用了 `"${@:-}"`，无参数时会传入**一个空字符串**，`check_env.sh` 落进「未知参数」分支 → 退出 2，**自检根本不会跑**。改用 `"$@"`。现 `dev.sh check` → PASS 17 / WARN 6 / FAIL 0。
7. ~~备份失败留下 0 字节文件，恢复会拿它清空数据库~~ → **已修**：shell 的 `>` 先建文件，`pg_dump` 失败也留下 0 字节「备份」；`cmd_restore` 不校验就 `DROP SCHEMA public CASCADE`，空文件喂 `psql` 退出码 0，脚本报「恢复完成」；而推荐的 `curl /health` **不查库**，清空了照样 ok。现改为先写 `.partial`、失败即删；恢复前校验「非空 + 含 `CREATE TABLE`」，否则拒绝执行。
8. ~~`bootstrap.sh` 吞掉 `SECRET_KEY` 生成失败~~ → **已修**：原 `python3 ... || true` 失败也被吞掉，却照样打印「已写入随机 SECRET_KEY」。现已回读校验，仍是占位符就 die。

**代码层面**

9. **应用连的是数据库超级用户**（`deploy/docker-compose.yml:33`）：实测 `current_user = pantry`、`is_superuser = True`。ADR-0002 写的「应用账号对 `inventory_transactions` 只有 SELECT/INSERT」**没有任何数据库层强制**，仓库里也没有应用账号授权脚本 —— 追加式审计目前**只靠应用代码自律**。落地部署前需补 `pantrypilot_app` 最小权限账号。
10. **compose 的 `${POSTGRES_*}` 插值不读根目录 `.env`**：compose 的项目目录是 `deploy/`，它找 `deploy/.env`（不存在）→ 回落默认值。但 `dev.sh` 会 `set -a; . ./.env` 把根 `.env` 导出到 shell，而 **shell 环境变量在 compose 插值中优先级最高** → 所以 **`dev.sh` 路径生效、直连 `docker compose` 不生效**。`README.md` 的「底层等价命令」正是直连那条。另外 `bootstrap.sh` 只在 `.env` **不存在**时才从 `.env.example` 复制，所以老 `.env` 永远补不上 `POSTGRES_*` / `*_PORT`。
11. `backend/tests/conftest.py:37-51` 有一个**未被引用的死函数** `_unsafe_legacy_db_session()`，它会 `create_all` / `drop_all` 业务 schema —— 恰好违反它自己上面三行的注释。可以删。
12. `app/core/errors.py:58-60` 的 `ConflictError` 与 `:53-55` 的 `StateConflictError` 完全等价（都 409 / `STATE_CONFLICT`），只有 `auth_service.py` 在用前者。留一个即可。
13. `app/domain/`、`app/ai/`（除 contracts）、`tests/unit/`、`tests/ai/`、`backend/scripts/` 都是空目录；`backend/UNKNOWN.egg-info/` 是 `pip install -e .` 之前的残留。**不要因为目录存在就以为有实现。**
14. `DashboardRepository` 直接调用兄弟仓库的静态方法 `InventoryRepository.status_conditions()`；`MealPlanService` 绕过 `InventoryService` 直接改数量，导致**写流水的规则散落在两处**（`inventory_service.py:147-171` 与 `meal_plan_service.py:253-267`）。新增扣减路径时注意别再复制第三份。
15. `GET /api/v1/inventory/expiring` 实际返回的是**过期 + 临期**（按 `expiry_date <= today+3` 过滤，不是 `>= today`），路由名有误导性。
16. 已归档的库存即使带 `include_archived=true`，`GET /inventory/{id}` 仍返回 404（只有列表端点认这个参数）。
17. `tests/api/test_errors.py:16,33` 在**全局 app** 上注册路由且不清理，会泄漏到后续测试。
18. **前端产物里根本没有 HTTP 层**：`stores/auth.ts` 没有任何模块 import 它，`api/client.ts` 只被 `stores/auth.ts` import → 整条链路被 tree-shaking 掉，实测构建产物中 `baseURL` 与 `pantrypilot.token` 出现 **0 次**。也就是说当前镜像里**登录流程不可达**。实现第一个真实页面时必须先把 store 接进视图，否则请求层不会进包。
19. **登录接口存在用户枚举时序侧信道**（`auth_service.py:46`）：实测未知邮箱 **~0ms**、已注册邮箱 **~76ms**（Argon2id 耗时），响应体与状态码完全一致，只能靠计时区分。注册接口还会**明文回显「邮箱已被占用」**。
20. **JWT 无吊销机制**（无 `token_version` / `jti` / logout / 改密），泄露令牌 60 分钟内不可作废；`auth_service` 里也没有改密路径。
21. **登录/注册无限流** —— 撞库与 DoS 无成本（Argon2id 每次 64MiB 内存）。
22. `MealPlanRepository.list_ingredients()` 与 `RecipeRepository.get()` 的签名里**没有 `user_id`**，间接限定全靠调用方自觉 —— 落地 AI 接口时极易踩成跨用户读取。
23. `InventoryRepository` 的列表 ORDER BY 不是全序，同到期日的条目**分页会随无关编辑漂移**，导致条目被静默漏掉或重复。
24. `SELECT ... FOR UPDATE` **不会刷新已在 identity map 中的实体**（缺 `populate_existing()`），可能读到陈旧的 `quantity`/`version`。
25. Vitest `include` 只覆盖 `tests/`，**`src/` 下的 spec 被静默忽略** —— Vue 生态惯例是就近放，A 组很容易踩空，「修复缺陷必须补回归用例」会形同虚设。
26. `X-Request-ID` 完全由客户端控制且无字符/长度校验；4xx 与认证失败**完全不落日志**；日志脱敏正则遗漏 `secret_key=` / `api_key=` / Basic 认证 / Cookie。
27. nginx 的 `proxy_pass http://backend:8000` **在启动时解析上游** —— 重建后端容器换 IP 后前端持续 502，必须手动 `restart frontend`。
28. `scripts/dev.sh` 的 `backend-test` 镜像**永不重建**，改 `requirements-dev.txt` 后测试仍跑在旧依赖上（源码挂载了、依赖没有）。
29. 迁移 `20261121_0002` 未用 `op.f()`，`shopping_items` 的数量检查在库里叫 `ck_shopping_items_ck_shopping_items_quantity_positive`（前缀重复）。**功能正常**（实测能拒绝 `quantity=0`）、**autogenerate 也不报漂移**（实测生成的 `upgrade()` 为空），但迁移里引用该约束必须用这个名字。要修正应在**新增迁移**里改名（不要改已合并的迁移），且 `backend/alembic/**` 归 B 组。
30. `scripts/install_docker.sh` **覆盖式重写** `/etc/docker/daemon.json`，会清掉公司环境自带的 registry-mirror / insecure-registries。

**文档层面**

31. `README.md:126-127` 仍写「Sprint 1 尚未开工」，但台账 Backlog 显示 Sprint 1 与 Sprint 3 的条目**均已完成**（FR-001~FR-010、FR-014~FR-016），后端 21 个路由（20 个在 `/api/v1` 下 + 根路径 `GET /health`）、93 个测试函数已实现。**以 `10_工程管理台账.xlsx` 为准。**
32. `frontend/Dockerfile:5-6` 用 `npm install` 且 lockfile glob 可选（`package-lock.json*`），**镜像构建不可重现** —— CI 用的是 `npm ci`。改成 `npm ci` 需要同步改 `COPY` 行为。
33. CI 里**从不构建 Docker 镜像**，也不校验 `docker compose config`（只有本地 `check_env.sh` 校验）。

---

## 9. 参考资料

| 文档 | 何时读 |
|---|---|
| `README.md` | 项目定位、功能范围、技术栈、快速开始 |
| `开发规范.md` | 分支模型、目录归属、代码规范、DoD 自检清单（**提交前必读第 9 节**） |
| `团队上手步骤.txt` | 新成员五步上手（面向人的版本） |
| `文档/04_软件总体设计说明书.docx` | 分层职责、模块划分、关键流程、ADR-001~005 |
| `文档/05_数据库详细设计与API接口规范.docx` | 表结构、约束索引、事务、**API 清单与错误码（§8）**、认证契约（§10，已冻结） |
| `文档/06_AI技术设计与评测方案.docx` | AI 边界、6 个组件、输出契约、护栏、**评测集 AI-001~AI-008** |
| `文档/07_软件测试计划与测试用例.docx` | 测试层级、`TC-*` 用例编号、缺陷分级与退出准则 |
| `文档/08_部署运维与开源交付手册.docx` | 环境变量表（17 项）、备份恢复、故障处理、附录 A 部署验证记录 |
| `docs/adr/0001-app-timezone.md` | 临期判定为什么用全局时区、为什么运行时计算 |
| `docs/adr/0002-meal-plan-confirmation.md` | 幂等、批次汇总扣减、`source_type` 推导、单位不换算的全部决策 |
| `docs/test-database-setup.md` | 测试库与维护账号的准备顺序、最小权限 |
| `10_工程管理台账.xlsx` | **执行期唯一事实源**：人员 RACI、Backlog、Sprint、RTM、风险、缺陷、ADR、测试用例 |
| `CHANGELOG.md` | 每次变更的实际内容（Keep a Changelog 格式） |
| `docs/reviews/2026-11-21-配置实测报告.md` | **在真实环境跑过每条配置路径**的记录：怎么起服务、跑测试、灌种子、备份恢复、构建镜像，含复现命令 |
| `docs/reviews/2026-11-21-代码审查报告.md` | 多维度扫描 + 对抗式验证的审查结果，**带 ✅已实测 / 🔍反方未推翻 / ⚠️待核实 三级标记**，附「做得对、不要改」清单 |
| `docs/reviews/2026-11-21-文档与台账一致性审查.md` | 文档与台账跟实际代码的逐条核对，含 CLAUDE.md 事实核对结果 |
| `docs/research/2026-11-21-竞品与最佳实践调研.md` | 竞品对比与领域最佳实践（批次/FEFO、单位规范化、HITL 风险分级、RAG vs 纯生成、幂等三态），以及对照本仓的 P0/P1/P2 差距清单 |
