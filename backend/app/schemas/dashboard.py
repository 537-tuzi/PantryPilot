"""Read-only schemas for the FR-010 dashboard summary."""

from datetime import date

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    statistics_date: date
    inventory_count: int
    expiring_count: int
    expired_count: int
