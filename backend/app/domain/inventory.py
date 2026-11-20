"""库存数量调整规则。

纯规则层：只做方向校验，不负责持久化与事务。
"""

from decimal import Decimal


def reason_direction_error(reason: str, delta: Decimal) -> str | None:
    """Return a validation message when the reason contradicts the delta direction."""
    if reason == "add" and delta <= 0:
        return "reason 'add' requires a positive quantity delta"
    if reason == "consume" and delta >= 0:
        return "reason 'consume' requires a negative quantity delta"
    return None
