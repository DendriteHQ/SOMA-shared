from __future__ import annotations

from datetime import datetime


def require_tz(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(
            f"{field_name} must include timezone offset (e.g. 'Z' or '+00:00')"
        )
    return value
