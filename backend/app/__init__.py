"""PantryPilot 后端应用包。

分层约定（见 文档/04 §3）：
    api -> services -> domain / repositories -> db
    ai 层只能被 services 调用，不得直接提交库存事务。
"""

__version__ = "1.1.0"
