"""健康检查。

部署手册（文档/08 §3）使用根路径 /health 做存活探测；
文档/05 §6 同时要求 /api/v1/health。
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="健康检查")
def health() -> HealthResponse:
    """返回服务状态。"""
    from app.core.config import settings

    return HealthResponse(status="ok", version="1.1.0", environment=settings.app_env)
