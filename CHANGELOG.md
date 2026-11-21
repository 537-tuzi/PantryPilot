# Changelog

本文件记录 PantryPilot 各版本的变更。格式参考 Keep a Changelog。

## [1.2.1] - 2026-11-21

### 配置与文档按实际运行状态校准

- `.env.example`：补齐 compose 实际读取的 `POSTGRES_*` / 端口变量，填好 `TEST_DATABASE_URL`（pantrypilot_test），
  并说明 `TEST_MAINTENANCE_DATABASE_URL` 留空时相关并发测试自动跳过。
- `文档/08` 环境变量表：与 `app/core/config.py` 的 Settings 字段及 compose 变量逐项对齐（8 项 → 17 项）。
- `文档/05` API 清单：与运行中的 OpenAPI 逐条对齐，16 个端点标注「已实现 / 待实现（Sprint 2）」。
- `文档/04` 模块划分：补「实现位置」列，指向实际 endpoint / service / repository / model 文件。
- `文档/07`：补充可执行用例位置（`backend/tests/`）与当前 100 用例全通过的事实。
- 台账：Backlog 状态按实现情况更新、Sprint 进度更新、新登记两个实跑发现的 S1 缺陷、
  R-04/R-06/R-09 状态更新为已缓解。

## [1.2.0] - 2026-11-21

### 统一：容器成为后端唯一受支持的运行环境

通读当前后端实现后确认：团队已把基线定为 **Python 3.11+**（`datetime.UTC`）、`python:3.11-slim` 镜像、
CI 同版本，且测试夹具强制 `TEST_DATABASE_URL` 指向 `pantrypilot_test`、迁移必须先行。
而 Ubuntu 22.04 自带 3.10、jammy 仅有 3.11.0**rc1**（实测装过并卸载，不适合做开发基线），
因此**宿主机 Python 版本不该再是任何人的阻塞项**。据此统一：

- 新增 `scripts/dev.sh`：所有后端操作的唯一入口（up / down / ps / logs / migrate / test-db / test / seed / backup / restore / check / shell / openapi），全部在容器内完成。
- `deploy/docker-compose.yml` 新增 `backend-test` 服务（带开发依赖的镜像 + 源码挂载），容器内跑 pytest 不用重装依赖。
- `backend/Dockerfile` 增加 `INSTALL_DEV` 构建参数，一份 Dockerfile 同时服务运行与测试。
- `scripts/bootstrap.sh` 改为容器优先：Docker 可用即走容器路径；仅当无 Docker 且宿主机 Python ≥ 3.11 时退回 venv 方式。
- `scripts/check_env.sh` 改为容器优先：宿主机 Python < 3.11 记 WARN 而非 FAIL；新增 compose 配置校验、后端容器与健康检查项。
- `开发规范.md` 第 10 节、`团队上手步骤.txt`、`README.md` 全部改写为容器优先流程。

### 修复

- `scripts/seed.py`：三处 INSERT 缺主键 `id`。模型的 UUID 主键是 Python 侧 `default=uuid4`、数据库无默认值，
  裸 SQL 插入必然报 `null value in column "id" ... violates not-null constraint`。已由 Python 生成 id 传入，
  实测演示账号可登录、错密码 401、库存状态正确。
- `docs/test-database-setup.md`：修正步骤顺序（授权脚本按表级权限授权，**必须先迁移出业务表**，
  原顺序会报 `relation "users" does not exist`），并接入 `scripts/dev.sh test-db`。

## [1.1.2] - 2026-11-21

### 修复
- **合并团队 main 后实测发现并修复**：前端 `stores/auth.ts` 登录提交 `username`，而后端 `LoginRequest` 要求 `email`，登录与注册必然失败。已改为登录传 `email`、注册传 `username + email + password`，并与 `文档/05` §10 契约同步（实测：注册返回 token、错误凭据 401、无 token 401、携带 token 可访问受保护接口）。
- `文档/05` §10 认证契约按**已实现代码**重新校准：登录改用 email、有效期改为 `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`（默认 60 分钟）、密码 Argon2id、令牌载荷 `{sub, exp}`。
- 新增 `backend/requirements-dev.txt`（pytest/pytest-cov/ruff/mypy）：此前文档只让成员装 `requirements.txt`，导致新克隆环境里 `pytest` 缺失、自检脚本与测试无法运行；bootstrap、CI、三份说明文档已统一改为同时安装。
- `backend/Dockerfile` 复制 `requirements-dev.txt`，使容器内可临时执行测试（此前镜像内无该文件）。
- `scripts/bootstrap.sh` 补 `ok()` 函数定义（此前报 `ok: 未找到命令`），并在无 docker 组权限时给出可读提示而非直接中断。
- `scripts/check_env.sh` 增加 Python 版本门禁（< 3.11 判 FAIL，因后端使用 `datetime.UTC`）、pytest 缺失检测、`--fast` 模式。

### 变更
- 开发规范 / 团队上手步骤 / README 的 Python 基线由 3.10+ 更正为 **3.11+**，与 `pyproject.toml`、Dockerfile、CI 实际版本一致。
- `.env.example` 合并双方内容：保留团队的 `APP_TIMEZONE`、`JWT_*`、`TEST_*` 配置，并把 `DATABASE_URL` 改为 `localhost`（compose 容器内仍覆盖为 `db:5432`），使宿主机直跑与容器两种方式都可用。

## [1.1.1] - 2026-11-21

### 修复
- **新增 `.dockerignore` 与 `backend/.dockerignore`**：前端镜像构建上下文原本是仓库根目录，会把 226MB 的 `node_modules`、`.git` 以及 **`.env`（含密钥）** 一并发送给 Docker daemon；现已排除，镜像内确认无 `.env`。
- `.env.example` 的 `DATABASE_URL` 由容器名 `db` 改为 `localhost`（compose 容器内仍由 `docker-compose.yml` 覆盖为 `db:5432`），修复宿主机直跑后端连不上数据库。
- `nginx.conf` 补充 `/openapi.json` 代理，此前经 nginx 打开 `/docs` 无法加载接口列表。
- `backend/app/ai/contracts.py`：`storage_location` 由 `str` 改为 `StorageLocation` 枚举（冷藏/冷冻/常温/自定义），与 `文档/06` §4 契约一致。
- `scripts/check_env.sh` 新增 `--fast` 模式（跳过前端 lint/类型/测试，约 15 秒），并修正容器段在无 docker 组权限时静默无输出的问题。

### 变更
- CI 改用 `npm ci`（可重现安装），并新增 `ruff format --check` 检查，与规范中“格式化”要求对齐。
- `文档/05` 新增“10 认证与令牌契约（2026-11-20 冻结）”，冻结注册/登录请求响应结构、`access_token` 命名、JWT 载荷、有效期与鉴权方式，解除前端 `stores/auth.ts` 的字段猜测。
- `文档/08` 附录 A 追加 3 条部署验证结果（镜像内容检查、OpenAPI 代理、宿主机直连数据库）。
- `开发规范.md`、`团队上手步骤.txt`、`README.md` 按实际配置校正：分支保护审批人数为 0（作者可自批自合）、`python3 -m venv` 缺 ensurepip 的提示、`.env` 位于仓库根目录、目标目录布局与归属表。
- `README.md` 当前状态改为“准备阶段已完成，Sprint 1 尚未开工”，不再夸大为“处于 Sprint 1”。

### 新增
- `backend/tests/api/test_errors.py`：统一错误响应结构测试（400/409/404 + request_id），此前该全局异常处理路径无任何测试覆盖。

## [1.1.0] - 2026-11-20

### 变更
- 团队基线由 3 名开发人员调整为 **6 人**（A 前端/产品协调、B 后端/数据、C AI/质量工程，各 2 人），新增 PO 角色（psh，兼 A 组开发），不设专职 SM 与专职测试。
- 新增根目录 `开发规范.md`：分支模型、目录与小组归属、代码规范、接口与迁移规则、测试与 AI 规范、DoD 自检清单、新成员上手步骤。
- 新增 `.gitignore`：忽略依赖与构建产物、密钥、本地数据库、备份、测试产物、个人临时与分析记录文件、Office 临时文件。
- 仓库补齐工程骨架：`backend/`、`frontend/`、`deploy/`、`scripts/`、`.github/workflows/`、`.env.example`。
- `文档/02` 增加"桌面研究（二手资料）"小节，并更新待调研问题的确认状态。
- `文档/01` 人员分工与团队基线改为 6 人；`文档/04` ADR-001 理由同步更新；`文档/07` 测试职责；`文档/09` 交付物责任人。
- `10_工程管理台账.xlsx` 负责人列改为角色标签（A1/A2/B1/B2/C1/C2），风险登记册补充分值与应对，测试用例与 RTM 关联保持一致。

### 移除
- 从版本控制移除 Office 临时锁文件 `文档/~$项目立项书与项目管理计划.docx`。

## [1.0.0] - 2026-11-14

### 新增
- 项目立项书、用户调研方案与 SRS、产品原型说明与交互规格、总体设计、数据库与 API 规范、AI 技术设计与评测方案、测试计划与用例、部署运维与开源交付手册、验收方案与总结模板。
- 可点击低保真原型 `产品原型/index.html`。
- 架构与流程图 `架构图/PantryPilot_架构与流程图.drawio`。
- 工程管理台账 `10_工程管理台账.xlsx`。
