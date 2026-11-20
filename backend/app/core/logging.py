"""日志配置。

要求：记录 request_id、耗时、状态与错误类别；不记录密码、令牌与密钥（NFR-008）。
"""

import logging
import re
import sys

from app.core.request_id import get_request_id

LOG_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"

_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)\b(authorization\s*:\s*bearer)\s+[^\s,;]+"),
    re.compile(r"(?i)\b(password|secret|token)\s*[=:]\s*[^\s,;]+"),
    re.compile(r"(?i)postgresql(?:\+[^:]+)?://[^\s@]+@"),
)


def redact_sensitive_text(value: str) -> str:
    """脱敏密码、令牌与数据库连接串中的凭据。"""
    authorization_pattern, key_value_pattern, database_url_pattern = _SENSITIVE_PATTERNS
    redacted = authorization_pattern.sub(r"\1 [REDACTED]", value)
    redacted = key_value_pattern.sub(r"\1=[REDACTED]", redacted)
    redacted = database_url_pattern.sub("postgresql://[REDACTED]@", redacted)
    return redacted


class RequestIdFilter(logging.Filter):
    """把 request_id 注入日志记录，并对消息脱敏。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        if record.args:
            record.msg = redact_sensitive_text(record.getMessage())
            record.args = ()
        elif isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        return True


def configure_logging(level: str | None = None) -> None:
    """配置根日志处理器。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level or "INFO")
