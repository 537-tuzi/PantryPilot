"""v1 路由汇总。

新增接口按业务域拆分到 endpoints/ 下的文件，并在此注册。
接口清单与文档/05 §6 保持一致。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    dashboard,
    health,
    inventory,
    meal_plans,
    shopping,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(inventory.router)
api_router.include_router(meal_plans.router)
api_router.include_router(shopping.router)
api_router.include_router(dashboard.router)
