"""API 层。

约束：Router 只做参数校验、鉴权与状态码映射，业务逻辑下沉到 services。
"""

from app.api.v1.router import api_router

__all__ = ["api_router"]
