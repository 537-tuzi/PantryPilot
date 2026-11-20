# PantryPilot（食刻管家）

> 面向独居青年与小家庭的 Web 食材管理应用。以家庭食材库存为**事实数据**，以 AI 的自然语言理解与膳食方案生成为**辅助能力**，帮助用户管理库存、关注临期食材、规划餐食并减少重复采购。

版本：1.1.0　　基线日期：2026-11-20　　团队：6 人（A / B / C 三组各 2 人）

## 项目定位

一句话：**AI 只给建议，事实和库存变更由确定性程序与用户确认来完成。**

- 库存数量、到期日期、扣减结果永远来自数据库，不来自模型。
- AI 生成的录入草稿与膳食方案必须经 Schema 校验、业务规则校验，并经用户确认后才生效。
- 模型不可用时，库存与临期功能照常工作。

## 功能范围

| 级别 | 内容 |
|---|---|
| Must | 注册/登录/退出、用户数据隔离、饮食偏好、库存批次 CRUD、临期计算、首页概览、AI 自然语言录入、AI 膳食规划与校验、计划确认与事务扣减、AI 失败降级 |
| Should | 采购清单 |
| Could | 菜谱收藏 |
| 本期不做 | 图片识别/OCR/小票/条码、家庭多人共享与复杂权限、小程序与原生 App、电商价格与下单支付、医疗营养诊断、微服务/K8s/多智能体/模型微调 |

## 技术栈

Vue 3 + TypeScript + Element Plus ｜ FastAPI + SQLAlchemy 2.x + PostgreSQL ｜ Nginx + Docker Compose ｜ OpenAI 兼容模型 API（Provider Adapter 隔离）

## 目录结构

```
PantryPilot/
├── backend/          FastAPI 后端（api / services / domain / repositories / ai）
├── frontend/         Vue 3 前端（views / components / stores / api）
├── deploy/           docker-compose、nginx
├── scripts/          初始化、种子数据、备份恢复
├── .github/          CI 工作流
├── 文档/             01~09 工程文档（需求、设计、测试、部署、验收）
├── 产品原型/         可点击低保真 HTML 原型
├── 架构图/           draw.io 多页架构与流程图
├── 10_工程管理台账.xlsx  Backlog / Sprint / RTM / 风险 / 缺陷 / ADR / 测试用例
└── 开发规范.md       分支、目录归属、代码与提交流程规范
```

目录与小组的归属关系见 [`开发规范.md`](开发规范.md) 第 3 节。

## 分支模型

```
main            受保护分支，始终可运行、可部署
dev/psh         A1 前端/产品协调
dev/dyl         A2 前端/产品协调
dev/{其他四人}   B 组（后端/数据）2 人、C 组（AI/质量工程）2 人
```

- 不直接 push `main`，全部走 Pull Request，至少 1 人 Review，CI 必须通过。
- 每人只在自己的 `dev/<名字>` 分支开发，每天 `git merge origin/main` 同步。
- 上手步骤见 [`开发规范.md`](开发规范.md) 第 10 节。

## 快速开始

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

一键启动（含 PostgreSQL）：

```bash
cp .env.example .env
# 必须先把 SECRET_KEY 换成强随机值，否则服务拒绝启动
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml exec backend alembic upgrade head
curl http://localhost/health
```

运行后端测试前需配置独立的 `TEST_DATABASE_URL`，说明见
[`docs/test-database-setup.md`](docs/test-database-setup.md)。

## 文档索引

| 文档 | 用途 |
|---|---|
| `文档/01_项目立项书与项目管理计划.docx` | 立项、范围、计划、分工、质量门禁 |
| `文档/02_用户调研方案与软件需求规格说明书.docx` | 调研方案与桌面研究、用户故事、FR/NFR、业务规则 |
| `文档/03_产品原型说明与交互规格.docx` | 信息架构、页面清单、交互与字段校验 |
| `文档/04_软件总体设计说明书.docx` | 架构分层、模块划分、关键流程、ADR |
| `文档/05_数据库详细设计与API接口规范.docx` | 数据表、约束索引、事务、API 清单与错误码 |
| `文档/06_AI技术设计与评测方案.docx` | AI 边界、输出契约、护栏、评测集 |
| `文档/07_软件测试计划与测试用例.docx` | 测试层级、用例、缺陷分级与退出准则 |
| `文档/08_部署运维与开源交付手册.docx` | 部署、备份恢复、故障处理、开源规范 |
| `文档/09_项目验收方案与项目总结模板.docx` | 验收场景、交付物验收、总结模板 |
| `10_工程管理台账.xlsx` | 执行期唯一台账：Backlog、Sprint、RTM、风险、缺陷、ADR、用例 |
| `开发规范.md` | 分支、目录归属、代码规范、提交流程、DoD |

## 使用约束

- 数据库使用 **PostgreSQL**，不使用 SQLite。
- AI 输出必须经过 Schema 与业务规则校验；**录入与库存扣减必须用户确认**。
- 原型为静态演示数据，不连接真实 AI 与数据库。
- `文档/01~09` 与台账中的"待执行/待验收"状态，**只有真实发生后才能改为完成**。

## 当前状态

Sprint 3 进行中。已实现：邮箱注册/登录与 JWT、用户偏好、库存 CRUD/归档/临期/审计流水、
首页汇总、计划详情与确认扣减（幂等 + 行锁 + 乐观锁）、采购清单（状态机/软删除）与计划导入。
AI 自然语言录入与膳食规划尚未实现（C 组）；前端仍为原型骨架，部分页面待接入真实 API。
执行记录以 `10_工程管理台账.xlsx` 为准。
