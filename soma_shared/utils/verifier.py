from __future__ import annotations

from typing import TypeVar, Any
import logging
import base64
import ipaddress
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from soma_shared.contracts.common.signatures import SignedEnvelope
from soma_shared.db.session import get_db_session
from soma_shared.db.exception_log import log_exception
from soma_shared.db.validator_log import log_validator_message
from soma_shared.db.miner_log import log_miner_message
from soma_shared.db.models.admin import Admin
from soma_shared.utils.signer import verify_nonce, verify_payload_model

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


def verify_ed25519_signature(message: bytes, signature_hex: str, public_key_hex: str) -> bool:
    """
    Verify Ed25519 signature using cryptography library.
    
    Args:
        message: Message bytes that were signed
        signature_hex: Signature in hex format
        public_key_hex: Public key in hex format
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Convert hex to bytes
        signature_bytes = bytes.fromhex(signature_hex)
        public_key_bytes = bytes.fromhex(public_key_hex)
        
        # Create public key object
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify signature
        public_key.verify(signature_bytes, message)
        return True
    except Exception as e:
        logger.debug(f"Ed25519 signature verification failed: {e}")
        return False


def verify_httpx_response(
    response: Any,
    model: type[T],
    *,
    expected_key: str | None = None,
    require_success: bool = True,
    verify_nonce_value: bool = False,
    verbose: bool = False,
) -> SignedEnvelope[T]:
    status_code = getattr(response, "status_code", None)
    if require_success and (status_code is None or status_code >= 400):
        raise ValueError(f"Unexpected status code: {status_code}")
    try:
        data = response.json()
    except Exception as exc:
        raise ValueError("Response is not valid JSON") from exc

    try:
        env_raw = SignedEnvelope[dict].model_validate(data)
    except ValidationError as exc:
        raise ValueError("Response is not a SignedEnvelope") from exc

    try:
        payload_obj = model.model_validate(env_raw.payload)
    except ValidationError as exc:
        raise ValueError(f"Response payload is invalid")

    if expected_key and env_raw.sig.signer_ss58 != expected_key:
        raise ValueError("Signer does not match expected key")

    if verify_nonce_value:
        ok, reason = verify_nonce(env_raw.sig.nonce)
        if not ok:
            raise ValueError(f"Invalid nonce: {reason}")

    ok = verify_payload_model(
        payload_obj,
        nonce=env_raw.sig.nonce,
        signature_b64=env_raw.sig.signature,
        signer_ss58_address=env_raw.sig.signer_ss58,
        verbose=verbose,
    )
    if not ok:
        raise ValueError("Invalid response signature")

    return SignedEnvelope[model](payload=payload_obj, sig=env_raw.sig)


def verify_request_dep(model: type[T], expected_key=None):
    async def _dependency(
        request: Request,
        env: SignedEnvelope[dict] = Depends(get_signed_envelope),
        db: AsyncSession = Depends(get_db_session),
        debug: bool = False,
    ) -> SignedEnvelope[T]:
        request_id = getattr(request.state, "request_id", None)
        try:
            payload_obj = model.model_validate(env.payload)
        except ValidationError as exc:
            logger.warning(
                "verify_request_payload_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "errors": exc.errors(),
                    "payload": env.payload,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from exc
        env_typed = SignedEnvelope[model](payload=payload_obj, sig=env.sig)
        return await verify_request(
            request=request,
            env=env_typed,
            expected_key=expected_key,
            db=db,
            debug=debug,
        )

    return _dependency


async def get_signed_envelope(
    env: SignedEnvelope[dict],
) -> SignedEnvelope[dict]:
    logging.info(f"Type of env: {type(env)} ")
    return env


def verify_miner_request_dep(model: type[T], expected_key=None):
    async def _dependency(
        request: Request,
        env: SignedEnvelope[dict],
        db: AsyncSession = Depends(get_db_session),
    ) -> SignedEnvelope[T]:
        request_id = getattr(request.state, "request_id", None)
        try:
            payload_obj = model.model_validate(env.payload)
        except ValidationError as exc:
            logger.warning(
                "verify_miner_request_payload_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "errors": exc.errors(),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from exc
        env_typed = SignedEnvelope[model](payload=payload_obj, sig=env.sig)
        return await verify_miner_request(
            request=request,
            env=env_typed,
            expected_key=expected_key,
            db=db,
        )

    return _dependency

def verify_request_dep_no_db(model: type[T], expected_key=None):
    async def _dependency(
        request: Request,
        env: SignedEnvelope[dict],
        debug: bool = False,
    ) -> SignedEnvelope[T]:
        request_id = getattr(request.state, "request_id", None)
        try:
            payload_obj = model.model_validate(env.payload)
        except ValidationError as exc:
            logger.warning(
                "verify_request_payload_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "errors": exc.errors(),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from exc
        env_typed = SignedEnvelope[model](payload=payload_obj, sig=env.sig)
        return await verify_request(
            request=request,
            env=env_typed,
            expected_key=expected_key,
            db=None,
            debug=debug
        )

    return _dependency

async def verify_hotkey_in_metagraph(
    request: Request,
    env: SignedEnvelope[T],     
    ) -> bool:
    metagraph_service = getattr(request.app.state, "metagraph_service", None)
    if metagraph_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metagraph service unavailable",
        )

    snapshot = metagraph_service.latest_snapshot
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metagraph not ready",
        )

    hotkeys = snapshot.get("hotkeys") or []
    signer_ss58 = env.sig.signer_ss58
    return signer_ss58 in hotkeys


def check_validator_stake(
    validator_ss58: str,
    metagraph_snapshot: dict[str, Any] | None,
    min_stake: float,
) -> tuple[bool, float | None, str]:
    """Check if validator has sufficient stake on the subnet."""
    if metagraph_snapshot is None:
        logger.warning(
            "check_validator_stake_snapshot_unavailable",
            extra={
                "validator_ss58": validator_ss58,
                "min_stake": min_stake,
            },
        )
        return False, None, "Metagraph snapshot unavailable"
    
    hotkeys = metagraph_snapshot.get("hotkeys", [])
    stakes = metagraph_snapshot.get("alpha_stake", [])
    
    if not hotkeys or not stakes:
        logger.warning(
            "check_validator_stake_data_incomplete",
            extra={
                "validator_ss58": validator_ss58,
                "hotkeys_count": len(hotkeys),
                "stakes_count": len(stakes),
                "min_stake": min_stake,
            },
        )
        return False, None, "Metagraph data incomplete"
    
    if len(hotkeys) != len(stakes):
        logger.error(
            "check_validator_stake_length_mismatch",
            extra={
                "validator_ss58": validator_ss58,
                "hotkeys_count": len(hotkeys),
                "stakes_count": len(stakes),
            },
        )
        return False, None, "Metagraph data inconsistent"
    
    try:
        uid = hotkeys.index(validator_ss58)
    except ValueError:
        logger.warning(
            "check_validator_stake_not_registered",
            extra={
                "validator_ss58": validator_ss58,
                "min_stake": min_stake,
            },
        )
        return False, None, "Validator hotkey not registered on subnet"
    
    try:
        current_stake = float(stakes[uid])
    except (IndexError, TypeError, ValueError) as e:
        logger.error(
            "check_validator_stake_retrieval_failed",
            extra={
                "validator_ss58": validator_ss58,
                "uid": uid,
                "error": str(e),
            },
        )
        return False, None, "Failed to retrieve stake"
    
    if current_stake < min_stake:
        logger.warning(
            "check_validator_stake_insufficient",
            extra={
                "validator_ss58": validator_ss58,
                "current_stake": current_stake,
                "min_stake": min_stake,
                "uid": uid,
            },
        )
        return (
            False,
            current_stake,
            f"Insufficient stake: {current_stake:.2f} α (minimum: {min_stake:.2f} α)",
        )
    
    logger.debug(
        "check_validator_stake_passed",
        extra={
            "validator_ss58": validator_ss58,
            "current_stake": current_stake,
            "min_stake": min_stake,
            "uid": uid,
        },
    )
    return True, current_stake, f"Sufficient stake: {current_stake:.2f} α"


def is_public_ip(ip_str: str) -> bool:
    """Check if an IP address is public (globally routable)."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_global
    except ValueError:
        return False


def verify_validator_stake_dep(
    min_validator_stake: float = 10000.0,
    debug: bool = False,
):
    """Factory returning FastAPI dependency that verifies validator stake."""

    async def _verify_validator_stake(
        request: Request,
        env: SignedEnvelope = Depends(get_signed_envelope),
    ) -> None:

        if debug:
            return

        validator_ss58 = env.sig.signer_ss58

        metagraph_service = getattr(request.app.state, "metagraph_service", None)
        snapshot = (
            metagraph_service.latest_snapshot
            if metagraph_service
            else None
        )

        is_valid, current_stake, reason = check_validator_stake(
            validator_ss58=validator_ss58,
            metagraph_snapshot=snapshot,
            min_stake=min_validator_stake,
        )

        if not is_valid:
            logger.warning(
                "verify_validator_stake_failed",
                extra={
                    "validator_ss58": validator_ss58,
                    "current_stake": current_stake,
                    "min_stake": min_validator_stake,
                    "reason": reason,
                    "endpoint": request.url.path,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=reason,
            )

    return _verify_validator_stake


async def verify_request(
    request: Request,
    env: SignedEnvelope[T],
    expected_key=None,
    debug=False,
    db: AsyncSession | None = Depends(get_db_session),
) -> SignedEnvelope[T]:
    
    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "verify_request_start",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "signer_ss58": env.sig.signer_ss58,
            "expected_key": expected_key,
        },
    )
    if db is not None:
        validators = getattr(request.app.state, "registered_validators", None)
        is_validator = (
            isinstance(validators, dict)
            and env.sig.signer_ss58 in validators
        )
        if not is_validator and request.url.path.startswith("/validator"):
            is_validator = True
        await log_validator_message(
            db,
            direction="request",
            endpoint=request.url.path,
            method=request.method,
            signature=env.sig.signature,
            nonce=env.sig.nonce,
            signer_ss58=env.sig.signer_ss58,
            is_validator=is_validator,
            request_id=request_id,
            payload=env.payload.model_dump(mode="json"),
        )
    try:
        nonce = env.sig.nonce
        ok, reason = verify_nonce(nonce)
        if not ok:
            logger.warning(
                "verify_request_nonce_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "reason": reason,
                    "nonce": nonce,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid nonce: {reason}",
            )

        # Two verification modes:
        # - expected_key=None: Accept any validator/miner in metagraph (API endpoints)
        # - expected_key=ss58: Accept only that specific key (client scripts verify platform)
        if not expected_key:
            # Accept any metagraph participant
            # Skip metagraph verification in debug mode
            if not debug:
                if not await verify_hotkey_in_metagraph(request, env):
                    logger.warning(
                        "verify_request_hotkey_not_in_metagraph",
                        extra={
                            "request_id": request_id,
                            "endpoint": request.url.path,
                            "signer_ss58": env.sig.signer_ss58,
                        },
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Hotkey not registered in metagraph",
                    )
        else:
            # Accept only the specific expected key
            signer_ss58 = env.sig.signer_ss58
            if signer_ss58 != expected_key:
                logger.warning(
                    "verify_request_expected_key_mismatch",
                    extra={
                        "request_id": request_id,
                        "endpoint": request.url.path,
                        "signer_ss58": signer_ss58,
                        "expected_key": expected_key,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Hotkey does not match expected key",
                )
        signer_ss58 = env.sig.signer_ss58
        signature_b64 = env.sig.signature
        payload = env.payload

        ok = verify_payload_model(
            payload,
            nonce=nonce,
            signature_b64=signature_b64,
            signer_ss58_address=signer_ss58,
        )
        if not ok:
            logger.warning(
                "verify_request_signature_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "signer_ss58": signer_ss58,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not valid signature",
            )
    except HTTPException as exc:
        logger.info(
            "verify_request_http_error",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
        )
        if db is not None:
            await log_validator_message(
                db,
                direction="response",
                endpoint=request.url.path,
                method=request.method,
                signature=None,
                nonce=None,
                request_id=request_id,
                payload={"detail": exc.detail},
                status_code=exc.status_code,
            )
        raise
    except Exception as e:
        logger.exception(
            "verify_request_unexpected_error",
            extra={"request_id": request_id, "endpoint": request.url.path},
        )
        if db is not None:
            await log_exception(
                db,
                request_id=request_id,
                endpoint=request.url.path,
                exc=e,
                context={
                    "expected_key": expected_key,
                    "signer_ss58": env.sig.signer_ss58,
                    "signature": env.sig.signature,
                    "nonce": env.sig.nonce,
                    "payload": env.payload.model_dump(mode="json"),
                },
            )
            await log_validator_message(
                db,
                direction="response",
                endpoint=request.url.path,
                method=request.method,
                signature=None,
                nonce=None,
                request_id=request_id,
                payload={"detail": "Internal Server Error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e

    return env

async def verify_miner_request(
    request: Request,
    env: SignedEnvelope[T],
    expected_key=None,
    db: AsyncSession | None = Depends(get_db_session),
) -> SignedEnvelope[T]:
    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "verify_miner_request_start",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "signer_ss58": env.sig.signer_ss58,
            "expected_key": expected_key,
        },
    )
    if db is not None:
        await log_miner_message(
            db,
            direction="request",
            endpoint=request.url.path,
            method=request.method,
            signature=env.sig.signature,
            nonce=env.sig.nonce,
            signer_ss58=env.sig.signer_ss58,
            request_id=request_id,
            payload=env.payload.model_dump(mode="json"),
        )
    try:
        nonce = env.sig.nonce
        ok, reason = verify_nonce(nonce)
        if not ok:
            logger.warning(
                "verify_miner_request_nonce_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "reason": reason,
                    "nonce": nonce,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid nonce: {reason}",
            )

        if expected_key:
            signer_ss58 = env.sig.signer_ss58
            if signer_ss58 != expected_key:
                logger.warning(
                    "verify_miner_request_expected_key_mismatch",
                    extra={
                        "request_id": request_id,
                        "endpoint": request.url.path,
                        "signer_ss58": signer_ss58,
                        "expected_key": expected_key,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Hotkey does not match expected key",
                )

        signer_ss58 = env.sig.signer_ss58
        signature_b64 = env.sig.signature
        payload = env.payload

        ok = verify_payload_model(
            payload,
            nonce=nonce,
            signature_b64=signature_b64,
            signer_ss58_address=signer_ss58,
        )
        if not ok:
            logger.warning(
                "verify_miner_request_signature_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "signer_ss58": signer_ss58,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not valid signature",
            )
    except HTTPException as exc:
        logger.info(
            "verify_miner_request_http_error",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
        )
        if db is not None:
            await log_miner_message(
                db,
                direction="response",
                endpoint=request.url.path,
                method=request.method,
                signature=None,
                nonce=None,
                request_id=request_id,
                payload={"detail": exc.detail},
                status_code=exc.status_code,
            )
        raise
    except Exception as e:
        logger.exception(
            "verify_miner_request_unexpected_error",
            extra={"request_id": request_id, "endpoint": request.url.path},
        )
        if db is not None:
            await log_exception(
                db,
                request_id=request_id,
                endpoint=request.url.path,
                exc=e,
                context={
                    "expected_key": expected_key,
                    "signer_ss58": env.sig.signer_ss58,
                    "signature": env.sig.signature,
                    "nonce": env.sig.nonce,
                    "payload": env.payload.model_dump(mode="json"),
                },
            )
            await log_miner_message(
                db,
                direction="response",
                endpoint=request.url.path,
                method=request.method,
                signature=None,
                nonce=None,
                request_id=request_id,
                payload={"detail": "Internal Server Error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e

    return env


async def verify_request_no_db(
    request: Request,
    env: SignedEnvelope[T],
    expected_key=None,
    debug=False,
) -> SignedEnvelope[T]:
    return await verify_request(
        request=request,
        env=env,
        expected_key=expected_key,
        db=None,
        debug=debug,
    )


def verify_admin_request_dep(model: type[T]):
    """
    Dependency for admin endpoints that verifies signature against public key from admin table.
    """
    async def _dependency(
        request: Request,
        env: SignedEnvelope[dict],
        db: AsyncSession = Depends(get_db_session),
    ) -> SignedEnvelope[T]:
        request_id = getattr(request.state, "request_id", None)
        
        # Parse payload
        try:
            payload_obj = model.model_validate(env.payload)
        except ValidationError as exc:
            logger.warning(
                "verify_admin_request_payload_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "errors": exc.errors(),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from exc
        
        env_typed = SignedEnvelope[model](payload=payload_obj, sig=env.sig)

        await log_validator_message(
            db,
            direction="request",
            endpoint=request.url.path,
            method=request.method,
            signature=env.sig.signature,
            nonce=env.sig.nonce,
            signer_ss58=env.sig.signer_ss58,
            is_validator=False,
            request_id=request_id,
            payload=payload_obj.model_dump(mode="json"),
        )
        
        # Verify nonce
        nonce = env.sig.nonce
        ok, reason = verify_nonce(nonce)
        if not ok:
            logger.warning(
                "verify_admin_request_nonce_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "reason": reason,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid nonce: {reason}",
            )
        
        # Get admin public key from database
        from sqlalchemy import select
        result = await db.execute(select(Admin).limit(1))
        admin = result.scalars().first()
        
        if not admin:
            logger.error(
                "verify_admin_request_no_admin_found",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No admin key configured",
            )
        
        # Verify signature against admin public key
        signer_ss58 = env.sig.signer_ss58
        if signer_ss58 != admin.public_key:
            logger.warning(
                "verify_admin_request_key_mismatch",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "signer_ss58": signer_ss58,
                    "expected_key": admin.public_key,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin key does not match",
            )
        
        # Verify signature using Ed25519 instead of bittensor signing
        # Message is: nonce + payload_json
        import json
        payload_json = json.dumps(payload_obj.model_dump(mode="json"), separators=(',', ':'), sort_keys=True)
        message = f"{nonce}{payload_json}".encode('utf-8')
        
        # signature is in hex format (stored in env.sig.signature field)
        signature_hex = env.sig.signature
        public_key_hex = admin.public_key
        
        ok = verify_ed25519_signature(message, signature_hex, public_key_hex)
        if not ok:
            logger.warning(
                "verify_admin_request_signature_invalid",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "signer_ss58": signer_ss58,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )
        
        logger.info(
            "verify_admin_request_success",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "signer_ss58": signer_ss58,
            },
        )
        
        return env_typed
    
    return _dependency
