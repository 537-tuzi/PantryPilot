import logging
import re
from contextvars import ContextVar

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")

_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)\b(authorization\s*:\s*bearer)\s+[^\s,;]+"),
    re.compile(r"(?i)\b(password|secret|token)\s*[=:]\s*[^\s,;]+"),
    re.compile(r"(?i)postgresql(?:\+[^:]+)?://[^\s@]+@"),
)


def redact_sensitive_text(value: str) -> str:
    authorization_pattern, key_value_pattern, database_url_pattern = _SENSITIVE_PATTERNS
    redacted = authorization_pattern.sub(r"\1 [REDACTED]", value)
    redacted = key_value_pattern.sub(r"\1=[REDACTED]", redacted)
    redacted = database_url_pattern.sub("postgresql://[REDACTED]@", redacted)
    return redacted


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        if record.args:
            record.msg = redact_sensitive_text(record.getMessage())
            record.args = ()
        elif isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s request_id=%(request_id)s %(name)s %(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())
