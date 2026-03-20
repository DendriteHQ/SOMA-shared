from __future__ import annotations

from soma_shared.db.metrics import DatabaseMetricsSnapshot
from soma_shared.db.models.request import Request


def apply_db_metrics_snapshot_to_request(
    request_entry: Request,
    snapshot: DatabaseMetricsSnapshot | None,
) -> None:
    if snapshot is None:
        return

    request_entry.db_query_count = snapshot.total_queries
    request_entry.db_error_count = snapshot.total_errors
    request_entry.db_total_duration_ms = snapshot.total_duration_ms
    request_entry.db_max_duration_ms = snapshot.max_duration_ms
    request_entry.db_slow_query_count = snapshot.slow_query_count
    request_entry.db_pool_connect_count = snapshot.pool_connect_count
    request_entry.db_pool_checkout_count = snapshot.pool_checkout_count
    request_entry.db_pool_checkin_count = snapshot.pool_checkin_count
    request_entry.db_operation_counts = snapshot.operation_counts

    if snapshot.slowest_query is not None:
        request_entry.db_slowest_query_ms = snapshot.slowest_query.duration_ms
        request_entry.db_slowest_query_operation = snapshot.slowest_query.operation
        request_entry.db_slowest_query_preview = snapshot.slowest_query.statement_preview