from __future__ import annotations

import hashlib
import json
import os
import base64
import logging
import os
import re
import secrets

from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from soma_shared.contracts.common.signatures import Signature
from .nonce_cache import NonceCache, NonceCacheConfig

_NONCE_RE = re.compile(r"^(?P<ts>\d{8}T\d{6}\d{6}Z)\.(?P<rnd>[0-9a-f]{32})$")

NONCE_TTL = timedelta(minutes=2)

#TODO current nonce cache is in-memory only (process-local), consider using redis or similar for shared cache
_nonce_cache = NonceCache(NonceCacheConfig(ttl=NONCE_TTL))
logger = logging.getLogger(__name__)


def _get_wallet_lib():
    try:
        import bittensor_wallet  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "bittensor_wallet unavailable; signing/verification disabled"
        ) from exc
    return bittensor_wallet


def get_wallet(wallet_name: str, wallet_hotkey: str | None = None, wallet_path: str | None = None):
    """Get wallet from parameters instead of settings."""
    if not wallet_name or wallet_name.strip() == "":
        logger.warning(
            "wallet_name_missing",
            extra={"wallet_name": wallet_name, "wallet_path": wallet_path},
        )
        raise RuntimeError("wallet_name must be provided to sign payloads")
    wallet_base = (
        os.path.expanduser(wallet_path)
        if wallet_path
        else os.path.expanduser("~/.bittensor/wallets")
    )
    if not os.path.exists(wallet_base):
        logger.warning(
            "wallet_base_missing",
            extra={"wallet_base": wallet_base},
        )
    else:
        wallet_dir = os.path.join(wallet_base, wallet_name)
        if not os.path.exists(wallet_dir):
            logger.warning(
                "wallet_dir_missing",
                extra={"wallet_dir": wallet_dir},
            )
    wallet_lib = _get_wallet_lib()
    wallet_kwargs = {"name": wallet_name}
    if wallet_hotkey:
        wallet_kwargs["hotkey"] = wallet_hotkey
    if wallet_path:
        wallet_kwargs["path"] = wallet_path
    wallet = wallet_lib.Wallet(**wallet_kwargs)
    return wallet


def get_wallet_from_settings():
    """Get wallet from environment variables (WALLET_NAME, WALLET_HOTKEY, WALLET_PATH)."""
    wallet_name = os.getenv("WALLET_NAME", "").strip()
    wallet_hotkey = os.getenv("WALLET_HOTKEY", "").strip() or None
    wallet_path = os.getenv("WALLET_PATH", "").strip() or None
    
    if not wallet_name:
        logger.warning(
            "wallet_name_missing",
            extra={"wallet_name": wallet_name, "wallet_path": wallet_path},
        )
        raise RuntimeError("WALLET_NAME must be set to sign payloads")
    
    return get_wallet(wallet_name, wallet_hotkey, wallet_path)


def _sign_message(payload_str: str, nonce: str, keypair) -> str:
    wrapped_message_str = f"payload:{payload_str}::nonce:{nonce}"
    message = wrapped_message_str.encode("utf-8")

    signature = keypair.sign(data=message)
    return base64.b64encode(bytes(signature)).decode("utf-8")


def _build_signature(payload_str: str, nonce: str, keypair) -> Signature:
    signature = _sign_message(payload_str, nonce, keypair)
    return Signature(
        signer_ss58=keypair.ss58_address,
        nonce=nonce,
        signature=signature,
    )


def generate_nonce() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    rnd = secrets.token_hex(16)  # 128-bit
    return f"{ts}.{rnd}"


def verify_nonce(
    nonce: str,
    *,
    allow_future_skew: timedelta = timedelta(seconds=30),
    now: datetime | None = None,
    cache: NonceCache | None = None,
) -> tuple[bool, str | None]:
    """
    Verifies:
      1) format
      2) timestamp freshness
      3) replay (nonce must not be seen before) using cache

    IMPORTANT: cache is in-memory by default (process-local).
    """
    max_age = NONCE_TTL
    m = _NONCE_RE.match(nonce)
    if not m:
        return False, "invalid_format"

    ts_str = m.group("ts")
    try:
        ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False, "invalid_timestamp"

    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    if ts > now_utc + allow_future_skew:
        return False, "timestamp_in_future"

    if now_utc - ts > max_age:
        return False, "nonce_expired"

    # replay protection
    cache_to_use = cache or _nonce_cache
    if not cache_to_use.add_once(nonce, now=now_utc):
        return False, "nonce_replay"

    return True, None


def _resolve_keypair(wallet=None, keypair=None):
    """Resolve keypair from wallet or keypair parameter."""
    if keypair is not None:
        return keypair
    if wallet is not None:
        return wallet.hotkey
    raise RuntimeError("Either wallet or keypair must be provided")


def sign_payload_str(
    payload_str: str,
    *,
    nonce: str,
    use_coldkey: bool = False,
    verbose: bool = False,
    wallet=None,
    keypair=None,
) -> Signature:
    keypair = _resolve_keypair(wallet, keypair)

    signature = _build_signature(payload_str, nonce, keypair)
    if verbose:
        payload_md5 = hashlib.md5(payload_str.encode("utf-8")).hexdigest()
        _write_signature_payload(payload_md5, payload_str)
        logger.info(
            "signature_payload",
            extra={
                "payload_md5": payload_md5,
                "signer_ss58": signature.signer_ss58,
            },
        )
    return signature


def _write_signature_payload(payload_md5: str, payload_str: str) -> None:
    base_dir = os.environ.get("SIGNATURE_PAYLOAD_DIR") or os.path.join(
        os.path.expanduser("~"), ".mcp_platform", "signature_payloads"
    )
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"{payload_md5}.json")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(payload_str)
    except OSError:
        logger.exception("signature_payload_write_failed", extra={"path": path})


def verify_str_signature(
    payload_str: str,
    *,
    nonce: str,
    signature_b64: str,
    signer_ss58_address: str,
) -> bool:
    wallet_lib = _get_wallet_lib()
    wrapped_message_str = f"payload:{payload_str}::nonce:{nonce}"
    message = wrapped_message_str.encode("utf-8")

    try:
        sig_bytes = base64.b64decode(signature_b64, validate=True)
    except Exception:
        return False

    kp = wallet_lib.Keypair(ss58_address=signer_ss58_address)

    try:
        return bool(kp.verify(data=message, signature=sig_bytes))
    except Exception:
        return False

def payload_to_canonical_str(payload: BaseModel) -> str:
    """
    Convert a Pydantic model to a deterministic JSON string suitable for signing.
    - Stable key ordering
    - No extra whitespace
    - JSON-safe values (datetimes -> ISO strings, etc.)
    """
    obj = payload.model_dump(mode="json")
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sign_payload_model(
    payload: BaseModel,
    *,
    nonce: str,
    use_coldkey: bool = False,
    verbose: bool = False,
    wallet=None,
    keypair=None,
) -> Signature:
    payload_str = payload_to_canonical_str(payload)
    return sign_payload_str(
        payload_str,
        nonce=nonce,
        use_coldkey=use_coldkey,
        verbose=verbose,
        wallet=wallet,
        keypair=keypair,
    )


def verify_payload_model(
    payload: BaseModel,
    *,
    nonce: str,
    signature_b64: str,
    signer_ss58_address: str,
    verbose: bool = False,
) -> bool:
    import hashlib
    payload_str = payload_to_canonical_str(payload)
    if verbose:
        with open("payload_debug.txt", "w", encoding="utf-8") as f:
            f.write(payload_str)
    logging.info(f"Verifying payload: {hashlib.md5(payload_str.encode("utf-8")).hexdigest()}")
    return verify_str_signature(
        payload_str,
        nonce=nonce,
        signature_b64=signature_b64,
        signer_ss58_address=signer_ss58_address,
    )
