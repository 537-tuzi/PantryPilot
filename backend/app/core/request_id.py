"""请求上下文：request_id 贯穿日志与错误响应（NFR-008）。"""

from contextvars import ContextVar
from uuid import uuid4

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str | None = None) -> str:
    """设置当前请求的 request_id，返回最终值。"""
    rid = value or uuid4().hex
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    """返回当前请求的 request_id。"""
    return _request_id.get()
