from __future__ import annotations

import logging
import traceback
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from soma_shared.db.models.exception_log import ExceptionLog
from soma_shared.db.models.request import Request

logger = logging.getLogger(__name__)


async def log_exception(
    session: AsyncSession,
    *,
    request_id: str | None,
    endpoint: str | None,
    exc: Exception,
    context: dict[str, Any] | None = None,
) -> None:
    merged_context: dict[str, Any] | None = None
    if context:
        merged_context = dict(context)
    if endpoint:
        if merged_context is None:
            merged_context = {}
        merged_context["endpoint"] = endpoint
    request_fk = None
    if request_id:
        result = await session.execute(
            select(Request).where(Request.external_request_id == request_id)
        )
        request_row = result.scalars().first()
        if request_row is not None:
            request_fk = request_row.id
    entry = ExceptionLog(
        request_fk=request_fk,
        exception_type=exc.__class__.__name__,
        message=str(exc),
        traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        context=merged_context,
    )
    try:
        session.add(entry)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("exception_log_write_failed")
