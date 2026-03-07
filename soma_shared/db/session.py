from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import logging

from soma_shared.db.models.base import Base
from soma_shared.db.views import create_or_replace_views

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
logger = logging.getLogger(__name__)


def create_engine(dsn:Any, echo:bool, pool_size:int, max_overflow:int) -> AsyncEngine:
    if not dsn:
        raise RuntimeError("POSTGRES_DSN or RDS_SECRET_ID must be set")
    return create_async_engine(
        dsn,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
    )


async def init_db(dsn:Any, echo:bool, pool_size:int, max_overflow:int) -> None:
    global _engine, _sessionmaker
    if _engine is None:
        _engine = create_engine(
            dsn=dsn,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        _sessionmaker = async_sessionmaker(bind=_engine, expire_on_commit=False)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            if _engine.dialect.name == "postgresql":
                await create_or_replace_views(conn)
        logger.info("db_initialized")


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def clear_db() -> None:
    if _engine is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    try:
        async with _engine.begin() as conn:
            if _engine.dialect.name == "postgresql":
                preparer = _engine.dialect.identifier_preparer
                for table in reversed(Base.metadata.sorted_tables):
                    if table.schema:
                        table_name = (
                            f"{preparer.quote_schema(table.schema)}."
                            f"{preparer.quote(table.name)}"
                        )
                    else:
                        table_name = preparer.quote(table.name)
                    await conn.execute(
                        text(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    )
            else:
                await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            if _engine.dialect.name == "postgresql":
                await create_or_replace_views(conn)
        logger.info("db_cleared")
    except Exception:
        logger.exception("db_clear_failed")
        raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if _sessionmaker is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    async with _sessionmaker() as session:
        yield session


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    return _engine
