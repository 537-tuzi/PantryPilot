# Changelog

本文件记录 PantryPilot 各版本的变更。格式参考 Keep a Changelog。

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
