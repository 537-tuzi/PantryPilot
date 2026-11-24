# PantryPilot 项目原则（每次会话必读）

面向独居青年与小家庭的 Web 食材管理应用。Vue3 + TS + Element Plus + Pinia ｜ FastAPI + SQLAlchemy2 + PostgreSQL ｜ Nginx + Docker Compose。6 人团队 A/B/C 三组，30 天周期。

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
- **容器优先**：Docker 是唯一受支持后端运行环境（Python 3.11+）。统一入口 `bash scripts/dev.sh up|test|migrate|seed|logs|backup|restore`。前端热更新 `cd frontend && npm install && npm run dev`（:5200，/api 代理 :8000）。`SECRET_KEY` 占位符拒启动。
- 分支：每人只在 `dev/<名字>` 开发，每天 `git merge origin/main`；**禁止直接 push main**，全走 PR（Merge commit，CI 必绿）。当前 A2=dyl（dev/dyl），A1=psh(兼PO)。
- 目录归属：`frontend/src/**`、`frontend/tests/**` = A 组；`文档/**`、台账 = PO（评审后修订，同步 RTM）；`backend/alembic/**` = B 组；`deploy|scripts|.github` = C 组；`package.json|vite.config|tsconfig` 共享（加依赖 PR 说明）。
- 测试：作者写自己单测；C 组设计集成/E2E/AI 用例。**前端 CI（lint→typecheck→vitest→build）无后端无浏览器 → 所有 CI 测试 mock-based（mock service 层）**；真实后端验证走人工集成清单（demo 登录 `demo@example.com/demo12345`，登录非注册）。保留现有 8 个 format 测试绿。
- 安全：密钥（SECRET_KEY/LLM_API_KEY/DATABASE_URL）仅服务端，**不进前端产物/日志/截图/文档**；前端只用 `VITE_` 公开变量；不日志 token/密码；token 不进 URL。
- 项目末端门禁：Must 完成率 100%、P0 用例 100%、S1/S2 清零、核心闭环端到端、干净环境部署+持久化。**操作视频由 A 组负责**。

## 6. 当前真实进度（2026-11-24）
后端 Sprint 1 已实现并合入 main（20 个 API、12 表、2 迁移、93 test 函数）；**前端 10 视图全占位**（AppLayout 孤儿、无守卫、无 401、auth store 仅 token、types 漂移）；AI（Sprint 2）完全未实现（无 /ai/* 端点、seed 不创建 meal_plans/recipes）。
前端全程路线图与 Sprint 1 详设见 `docs/specs/2026-11-24-frontend-development-design.md`。

## 7. 沟通
始终用中文回复（技术标识符保持原文）。