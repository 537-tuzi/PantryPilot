# ADR-0001: MVP 阶段使用全局时区 APP_TIMEZONE

- 状态：已采纳
- 日期：2026-11-20
- 范围：库存临期与过期判定

## 背景

库存的临期/过期状态需要按"今天"计算。需求写的是"按用户时区当前日期计算"，
但 `users` 与 `user_preferences` 表都没有时区字段，文档也未定义配置项。

## 决策

1. MVP 阶段所有用户统一使用 `APP_TIMEZONE` 配置，默认 `Asia/Shanghai`。
2. 通过 Python `zoneinfo` 解析，不依赖服务器系统时区，也不混用 UTC 日期。
3. 不新增数据库字段，不新增 Alembic 迁移。
4. 判定规则：
   - 过期：`expiry_date < 今天`
   - 临期：`今天 <= expiry_date <= 今天 + 3`
   - 正常：`expiry_date > 今天 + 3`
5. 状态在读取时计算，不写入数据库。

## 后果

- 优点：行为确定，跨部署环境一致，实现简单。
- 限制：**MVP 暂不支持用户独立时区**；海外用户按上海时间判定临期。
- 后续：若需多时区，在 `user_preferences` 增加 `timezone` 字段并新增迁移，
  同时把 `current_date()` 改为优先读取用户时区、回退到 `APP_TIMEZONE`。
