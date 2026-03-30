from __future__ import annotations

from collections.abc import AsyncGenerator
import os
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import logging

from soma_shared.db.metrics import DatabaseMetricsCollector, DatabaseMetricsSnapshot
from soma_shared.db.models.base import Base
from soma_shared.db.views import create_or_replace_views

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_metrics_collector: DatabaseMetricsCollector | None = None
logger = logging.getLogger(__name__)


def _read_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("invalid_float_env", extra={"name": name, "value": value})
        return default


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("invalid_int_env", extra={"name": name, "value": value})
        return default


def create_engine(
    dsn: Any,
    echo: bool,
    pool_size: int,
    max_overflow: int,
    *,
    enable_metrics: bool | None = None,
    slow_query_threshold_seconds: float | None = None,
    log_slow_queries: bool | None = None,
    max_slow_query_samples: int | None = None,
) -> AsyncEngine:
    global _metrics_collector
    if not dsn:
        raise RuntimeError("POSTGRES_DSN or RDS_SECRET_ID must be set")

    engine = create_async_engine(
        dsn,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
    )

    resolved_enable_metrics = (
        _read_bool_env("DB_METRICS_ENABLED", True)
        if enable_metrics is None
        else enable_metrics
    )
    if resolved_enable_metrics:
        _metrics_collector = DatabaseMetricsCollector(
            logger=logger,
            slow_query_threshold_seconds=(
                _read_float_env("DB_SLOW_QUERY_THRESHOLD_SECONDS", 0.5)
                if slow_query_threshold_seconds is None
                else slow_query_threshold_seconds
            ),
            log_slow_queries=(
                _read_bool_env("DB_LOG_SLOW_QUERIES", False)
                if log_slow_queries is None
                else log_slow_queries
            ),
            max_slow_query_samples=(
                _read_int_env("DB_SLOW_QUERY_SAMPLE_LIMIT", 20)
                if max_slow_query_samples is None
                else max_slow_query_samples
            ),
        )
        _metrics_collector.install(engine)
    else:
        _metrics_collector = None

    return engine


async def init_db(
    dsn: Any,
    echo: bool,
    pool_size: int,
    max_overflow: int,
    *,
    enable_metrics: bool | None = None,
    slow_query_threshold_seconds: float | None = None,
    log_slow_queries: bool | None = None,
    max_slow_query_samples: int | None = None,
) -> None:
    global _engine, _sessionmaker
    if _engine is None:
        _engine = create_engine(
            dsn=dsn,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            enable_metrics=enable_metrics,
            slow_query_threshold_seconds=slow_query_threshold_seconds,
            log_slow_queries=log_slow_queries,
            max_slow_query_samples=max_slow_query_samples,
        )
        _sessionmaker = async_sessionmaker(bind=_engine, expire_on_commit=False)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            if _engine.dialect.name == "postgresql":
                await create_or_replace_views(conn)
        logger.info("db_initialized")


async def close_db() -> None:
    global _engine, _metrics_collector
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _metrics_collector = None


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


def get_db_metrics_snapshot() -> DatabaseMetricsSnapshot | None:
    if _metrics_collector is None:
        return None
    return _metrics_collector.snapshot()


def get_current_db_request_metrics_snapshot() -> DatabaseMetricsSnapshot | None:
    if _metrics_collector is None:
        return None
    return _metrics_collector.current_request_snapshot()


def begin_db_request_metrics_scope() -> Any | None:
    if _metrics_collector is None:
        return None
    return _metrics_collector.begin_request_scope()


def end_db_request_metrics_scope(token: Any | None) -> None:
    if _metrics_collector is not None and token is not None:
        _metrics_collector.end_request_scope(token)


def reset_db_metrics() -> None:
    if _metrics_collector is not None:
        _metrics_collector.reset()
