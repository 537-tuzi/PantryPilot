"""日志配置。

要求：记录 request_id、耗时、状态与错误类别；不记录密码、令牌与密钥（NFR-008）。
"""

import logging
import sys

from app.core.request_id import get_request_id

LOG_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"


class RequestIdFilter(logging.Filter):
    """把 request_id 注入日志记录。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_logging(level: str | None = None) -> None:
    """配置根日志处理器。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level or "INFO")
