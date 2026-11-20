from dataclasses import dataclass


@dataclass
class AppError(Exception):
    """Expected application error represented through the documented error envelope."""

    status_code: int
    code: str
    message: str
