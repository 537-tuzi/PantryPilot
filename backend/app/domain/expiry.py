"""临期与过期规则。

纯规则层：不访问数据库，也不依赖 api / ai。
"""

from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from app.core.config import settings

InventoryStatus = Literal["normal", "expiring", "expired"]

# 临期窗口：到期日在“今天”到“今天 + 3 天”之间视为临期。
EXPIRING_WINDOW_DAYS = 3


def current_date() -> date:
    """Today in the configured application timezone."""
    return datetime.now(ZoneInfo(settings.app_timezone)).date()


def inventory_status(expiry_date: date | None, today: date) -> InventoryStatus:
    """Status is derived at read time and never persisted."""
    if expiry_date is None:
        return "normal"
    if expiry_date < today:
        return "expired"
    if expiry_date <= today + timedelta(days=EXPIRING_WINDOW_DAYS):
        return "expiring"
    return "normal"
