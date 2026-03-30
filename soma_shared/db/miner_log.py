from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from soma_shared.db.models.miner import Miner
from soma_shared.db.models.request import Request
from soma_shared.db.models.signed_request import SignedRequest
from soma_shared.db.request_metrics import apply_db_metrics_snapshot_to_request
from soma_shared.db.session import get_current_db_request_metrics_snapshot

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
    payload_value: Any
    if isinstance(payload, (dict, list)):
        payload_value = payload
    else:
        payload_value = {"raw": str(payload)}
    created_at = datetime.now(timezone.utc)
    external_request_id = request_id or uuid.uuid4().hex
    method_value = (method or "").strip() or "UNKNOWN"
    metrics_snapshot = get_current_db_request_metrics_snapshot()
    try:
        request_entry = None
        result = await session.execute(
            select(Request).where(Request.external_request_id == external_request_id)
        )
        request_entry = result.scalars().first()

        if direction == "request":
            if request_entry is None:
                request_entry = Request(
                    external_request_id=external_request_id,
                    endpoint=endpoint,
                    method=method_value,
                    created_at=created_at,
                    payload=payload_value,
                    status_code=status_code,
                )
                session.add(request_entry)
            else:
                request_entry.endpoint = endpoint
                request_entry.method = method_value
                request_entry.created_at = created_at
                request_entry.payload = payload_value
                if status_code is not None:
                    request_entry.status_code = status_code
            apply_db_metrics_snapshot_to_request(request_entry, metrics_snapshot)

            if signature and nonce and signer_ss58:
                if request_entry.id is None:
                    await session.flush()
                signed_entry = None
                result = await session.execute(
                    select(SignedRequest).where(
                        SignedRequest.request_fk == request_entry.id
                    )
                )
                signed_entry = result.scalars().first()
                signer_miner_fk = None
                miner_result = await session.execute(
                    select(Miner).where(Miner.ss58 == signer_ss58)
                )
                miner = miner_result.scalars().first()
                if miner is not None:
                    signer_miner_fk = miner.id

                if signed_entry is None:
                    signed_entry = SignedRequest(
                        request_fk=request_entry.id,
                        signature=signature,
                        nonce=nonce,
                        signer_validator_fk=None,
                        signer_miner_fk=signer_miner_fk,
                        signer_ss58=signer_ss58,
                    )
                    session.add(signed_entry)
                else:
                    signed_entry.signature = signature
                    signed_entry.nonce = nonce
                    signed_entry.signer_validator_fk = None
                    signed_entry.signer_miner_fk = signer_miner_fk
                    signed_entry.signer_ss58 = signer_ss58
        else:
            if request_entry is None:
                request_entry = Request(
                    external_request_id=external_request_id,
                    endpoint=endpoint,
                    method=method_value,
                    created_at=created_at,
                    payload=payload_value,
                    status_code=status_code,
                )
                apply_db_metrics_snapshot_to_request(request_entry, metrics_snapshot)
                session.add(request_entry)
            else:
                if status_code is not None:
                    request_entry.status_code = status_code
                apply_db_metrics_snapshot_to_request(request_entry, metrics_snapshot)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("miner_log_write_failed")
