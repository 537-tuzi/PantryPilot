# Sprint 1 前端人工集成清单（真实后端，非 CI）

> CI frontend job 无后端无浏览器，所有 CI 测试 mock-based。本清单在容器优先环境对真实后端验证。
> 前置：`bash scripts/dev.sh up && bash scripts/dev.sh migrate && bash scripts/dev.sh seed`；前端 `cd frontend && npm install && npm run dev`（:5200，/api 代理 :8000）。

## 演示账户
- **登录** `demo@example.com / demo12345`（seed.py:46-48）。注意：demo12345 无大写，**只能登录不能注册**（注册强度需大小写+数字）。

## 核心走查
- [ ] 注册新账户（用户名/邮箱/密码含大小写数字）→ 自动登录跳首页；重复注册显示统一"用户名或邮箱已被注册"（不指明哪个）。
- [ ] 登录错误密码 → "邮箱或密码错误"（不泄露账号是否存在）。
- [ ] 首页统计卡（库存/临期/过期）与统计日期；临期卡排除过期项；开始规划禁用 + Sprint 2 提示。
- [ ] 库存新增（名称≤80、数量>0≤3 位小数、单位）→ 列表出现；到期<购买弹确认。
- [ ] 库存编辑：仅改数量提交带 expected_version + reason；单位禁用；未改字段不发送。
- [ ] 耗尽（一键耗尽→0）条目保留；删除（归档）条目隐藏，二次确认文案区分。
- [ ] **409 双标签竞态**：两个标签页同时编辑/耗尽同一食材 → 后提交者 refetch 提示"已被修改"，不自动重发、不重复扣减。
- [ ] 临期页：服务端顺序（过期在前）、状态取服务端、剩余天数按应用时区；午夜边界（seed 用容器时区 vs API Asia/Shanghai，信任 API）。
- [ ] 偏好/采购/AI 页：Sprint 1 偏好/采购属后续 Sprint，AI 三桩显示"Sprint 2 开放"，无 /ai/* 调用。
- [ ] **401 过期**：等待 60 分钟或构造过期 token → 业务调用触发全局清 token + "登录已过期" + 跳登录保留 redirect；登录页 401 不触发全局跳转。
- [ ] 退出登录 → 清 token 跳登录；受保护路由重定向登录带 redirect。
- [ ] 深链刷新（/inventory 直接刷新）nginx try_files → index.html 正常。

## 响应式（NFR-009，浏览器验证）
- [ ] 375px（手机）：侧栏横向导航、库存/临期卡片态、表单单列、无横向滚动。
- [ ] 768px（平板）/ 1280px（桌面）：侧栏导航、表格态布局正常。

## 门禁
- [ ] `npm run lint && npm run typecheck && npx vitest run && npm run build` 全绿。
- [ ] 无密钥进前端产物；不日志 token/密码。

## 已知限制（披露）
- FR-005 分类筛选 demo 数据必空（seed 不写 ingredient_id，无 catalog 端点）——部分交付待 PO 签字。
- 名称长度创建 80（文档03）/编辑容忍 200（后端）。
- 无服务端登出/刷新；token localStorage 存储。
- Element Plus 全量注册 bundle 偏大（Sprint 1 后可选 tree-shaking）。