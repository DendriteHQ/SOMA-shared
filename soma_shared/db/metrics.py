from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import logging
import threading
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import ExceptionContext
from sqlalchemy.ext.asyncio import AsyncEngine

QUERY_START_KEY = "_soma_query_start_ns"
DEFAULT_SLOW_QUERY_THRESHOLD_SECONDS = 0.5
DEFAULT_SLOW_QUERY_SAMPLE_LIMIT = 20
STATEMENT_PREVIEW_LIMIT = 240


@dataclass(frozen=True)
class SlowQuerySample:
    operation: str
    duration_ms: float
    rowcount: int | None
    statement_preview: str


@dataclass(frozen=True)
class DatabaseMetricsSnapshot:
    enabled: bool
    started_at: float
    collected_at: float
    total_queries: int
    total_errors: int
    total_duration_ms: float
    avg_duration_ms: float
    max_duration_ms: float
    slow_query_count: int
    slow_query_threshold_ms: float
    pool_connect_count: int
    pool_checkout_count: int
    pool_checkin_count: int
    operation_counts: dict[str, int]
    slow_queries: list[SlowQuerySample]


class DatabaseMetricsCollector:
    def __init__(
        self,
        *,
        logger: logging.Logger | None = None,
        slow_query_threshold_seconds: float = DEFAULT_SLOW_QUERY_THRESHOLD_SECONDS,
        log_slow_queries: bool = False,
        max_slow_query_samples: int = DEFAULT_SLOW_QUERY_SAMPLE_LIMIT,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._slow_query_threshold_seconds = max(0.0, slow_query_threshold_seconds)
        self._log_slow_queries = log_slow_queries
        self._slow_queries: deque[SlowQuerySample] = deque(
            maxlen=max(0, max_slow_query_samples)
        )
        self._lock = threading.Lock()
        self._installed = False
        self.reset()

    def install(self, engine: AsyncEngine) -> None:
        if self._installed:
            return

        sync_engine = engine.sync_engine

        @event.listens_for(sync_engine, "before_cursor_execute")
        def _before_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            del cursor, statement, parameters, context, executemany
            start_stack = conn.info.setdefault(QUERY_START_KEY, [])
            start_stack.append(time.perf_counter_ns())

        @event.listens_for(sync_engine, "after_cursor_execute")
        def _after_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            del parameters, context, executemany
            duration_ms = self._consume_duration_ms(conn)
            if duration_ms is None:
                return
            rowcount = getattr(cursor, "rowcount", None)
            self._record_query(
                statement=statement,
                duration_ms=duration_ms,
                rowcount=rowcount,
            )

        @event.listens_for(sync_engine, "handle_error")
        def _handle_error(exception_context: ExceptionContext) -> None:
            connection = exception_context.connection
            duration_ms = self._consume_duration_ms(connection)
            statement = exception_context.statement or ""
            self._record_error(statement=statement, duration_ms=duration_ms)

        @event.listens_for(sync_engine, "connect")
        def _connect(dbapi_connection: Any, connection_record: Any) -> None:
            del dbapi_connection, connection_record
            with self._lock:
                self._pool_connect_count += 1

        @event.listens_for(sync_engine, "checkout")
        def _checkout(
            dbapi_connection: Any,
            connection_record: Any,
            connection_proxy: Any,
        ) -> None:
            del dbapi_connection, connection_record, connection_proxy
            with self._lock:
                self._pool_checkout_count += 1

        @event.listens_for(sync_engine, "checkin")
        def _checkin(dbapi_connection: Any, connection_record: Any) -> None:
            del dbapi_connection, connection_record
            with self._lock:
                self._pool_checkin_count += 1

        self._installed = True

    def snapshot(self) -> DatabaseMetricsSnapshot:
        with self._lock:
            avg_duration_ms = (
                self._total_duration_ms / self._total_queries
                if self._total_queries
                else 0.0
            )
            return DatabaseMetricsSnapshot(
                enabled=True,
                started_at=self._started_at,
                collected_at=time.time(),
                total_queries=self._total_queries,
                total_errors=self._total_errors,
                total_duration_ms=self._total_duration_ms,
                avg_duration_ms=avg_duration_ms,
                max_duration_ms=self._max_duration_ms,
                slow_query_count=self._slow_query_count,
                slow_query_threshold_ms=self._slow_query_threshold_seconds * 1000.0,
                pool_connect_count=self._pool_connect_count,
                pool_checkout_count=self._pool_checkout_count,
                pool_checkin_count=self._pool_checkin_count,
                operation_counts=dict(self._operation_counts),
                slow_queries=list(self._slow_queries),
            )

    def reset(self) -> None:
        with self._lock:
            self._started_at = time.time()
            self._total_queries = 0
            self._total_errors = 0
            self._total_duration_ms = 0.0
            self._max_duration_ms = 0.0
            self._slow_query_count = 0
            self._pool_connect_count = 0
            self._pool_checkout_count = 0
            self._pool_checkin_count = 0
            self._operation_counts: Counter[str] = Counter()
            self._slow_queries.clear()

    def _consume_duration_ms(self, connection: Any) -> float | None:
        if connection is None:
            return None
        start_stack = connection.info.get(QUERY_START_KEY)
        if not start_stack:
            return None
        start_ns = start_stack.pop()
        return (time.perf_counter_ns() - start_ns) / 1_000_000.0

    def _record_query(
        self,
        *,
        statement: str,
        duration_ms: float,
        rowcount: int | None,
    ) -> None:
        operation = _classify_statement(statement)
        is_slow_query = duration_ms >= self._slow_query_threshold_seconds * 1000.0
        slow_query_sample = None

        if is_slow_query:
            slow_query_sample = SlowQuerySample(
                operation=operation,
                duration_ms=duration_ms,
                rowcount=rowcount if rowcount is not None and rowcount >= 0 else None,
                statement_preview=_truncate_statement(statement),
            )

        with self._lock:
            self._total_queries += 1
            self._total_duration_ms += duration_ms
            self._max_duration_ms = max(self._max_duration_ms, duration_ms)
            self._operation_counts[operation] += 1
            if is_slow_query:
                self._slow_query_count += 1
                if self._slow_queries.maxlen:
                    self._slow_queries.append(slow_query_sample)

        if is_slow_query and self._log_slow_queries:
            self._logger.warning(
                "db_slow_query",
                extra={
                    "duration_ms": round(duration_ms, 3),
                    "operation": operation,
                    "rowcount": rowcount,
                    "statement": _truncate_statement(statement),
                },
            )

    def _record_error(self, *, statement: str, duration_ms: float | None) -> None:
        operation = _classify_statement(statement)
        with self._lock:
            self._total_queries += 1
            self._total_errors += 1
            self._operation_counts[operation] += 1
            self._operation_counts[f"{operation}_error"] += 1
            if duration_ms is not None:
                self._total_duration_ms += duration_ms
                self._max_duration_ms = max(self._max_duration_ms, duration_ms)


def _classify_statement(statement: str) -> str:
    if not statement:
        return "unknown"
    first_token = statement.lstrip().split(None, 1)[0].upper()
    if first_token in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
        return first_token.lower()
    if first_token in {"BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"}:
        return "transaction"
    return first_token.lower()


def _truncate_statement(statement: str) -> str:
    compact_statement = " ".join(statement.split())
    if len(compact_statement) <= STATEMENT_PREVIEW_LIMIT:
        return compact_statement
    return compact_statement[: STATEMENT_PREVIEW_LIMIT - 3] + "..."