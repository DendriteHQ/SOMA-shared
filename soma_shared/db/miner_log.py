from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from soma_shared.db.models.request import Request

logger = logging.getLogger(__name__)


async def log_miner_message(
    session: AsyncSession,
    *,
    direction: str,
    endpoint: str,
    method: str | None = None,
    signature: str | None,
    nonce: str | None,
    signer_ss58: str | None = None,
    request_id: str | None = None,
    payload: Any,
    status_code: int | None = None,
) -> None:
    if isinstance(payload, (dict, list)):
        payload_value: Any = payload
    else:
        payload_value = {"raw": str(payload)}

    now = datetime.now(timezone.utc)
    external_request_id = request_id or uuid.uuid4().hex
    method_value = (method or "").strip() or "UNKNOWN"

    try:
        if direction == "request" and signature and nonce and signer_ss58:
            # Single round-trip: upsert requests, resolve miner FK by ss58,
            # upsert signed_requests — all in one CTE.
            await session.execute(
                text("""
                    WITH req AS (
                        INSERT INTO requests
                            (external_request_id, endpoint, method, created_at, payload, status_code)
                        VALUES
                            (:eid, :endpoint, :method, :created_at, CAST(:payload AS jsonb), :status_code)
                        ON CONFLICT (external_request_id) DO UPDATE SET
                            endpoint    = EXCLUDED.endpoint,
                            method      = EXCLUDED.method,
                            payload     = EXCLUDED.payload,
                            status_code = EXCLUDED.status_code
                        RETURNING id
                    )
                    INSERT INTO signed_requests
                        (request_fk, signature, nonce, signer_ss58,
                         signer_validator_fk, signer_miner_fk, created_at)
                    SELECT
                        req.id,
                        :signature,
                        :nonce,
                        :signer_ss58,
                        NULL,
                        (SELECT id FROM miners WHERE ss58 = :signer_ss58),
                        :created_at
                    FROM req
                    ON CONFLICT (request_fk) DO UPDATE SET
                        signature       = EXCLUDED.signature,
                        nonce           = EXCLUDED.nonce,
                        signer_ss58     = EXCLUDED.signer_ss58,
                        signer_miner_fk = EXCLUDED.signer_miner_fk
                """),
                {
                    "eid": external_request_id,
                    "endpoint": endpoint,
                    "method": method_value,
                    "created_at": now,
                    "payload": json.dumps(payload_value),
                    "status_code": status_code,
                    "signature": signature,
                    "nonce": nonce,
                    "signer_ss58": signer_ss58,
                },
            )
        else:
            stmt = pg_insert(Request).values(
                external_request_id=external_request_id,
                endpoint=endpoint,
                method=method_value,
                created_at=now,
                payload=payload_value,
                status_code=status_code,
            )
            if direction == "request":
                set_ = {
                    "endpoint": stmt.excluded.endpoint,
                    "method": stmt.excluded.method,
                    "payload": stmt.excluded.payload,
                    "status_code": stmt.excluded.status_code,
                }
            else:
                # response — preserve original request data, only update status_code
                set_ = {"status_code": stmt.excluded.status_code}
            await session.execute(
                stmt.on_conflict_do_update(index_elements=["external_request_id"], set_=set_)
            )

        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("miner_log_write_failed")

