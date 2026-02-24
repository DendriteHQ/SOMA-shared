from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock


@dataclass(frozen=True)
class NonceCacheConfig:
    ttl: timedelta = timedelta(minutes=2)
    max_items: int = 100_000  # safety cap


class NonceCache:
    def __init__(self, cfg: NonceCacheConfig | None = None) -> None:
        self._cfg = cfg or NonceCacheConfig()
        self._lock = Lock()
        self._store: dict[str, datetime] = {}  # nonce -> expires_at (UTC)

    def add_once(self, nonce: str, *, now: datetime | None = None) -> bool:
        now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        expires_at = now_utc + self._cfg.ttl

        with self._lock:
            self._cleanup_locked(now_utc)

            if nonce in self._store:
                return False  # replay

            if len(self._store) >= self._cfg.max_items:
                self._cleanup_locked(now_utc)
                if len(self._store) >= self._cfg.max_items:
                    for n, _exp in sorted(self._store.items(), key=lambda kv: kv[1])[
                        : len(self._store) - self._cfg.max_items + 1
                    ]:
                        self._store.pop(n, None)

            self._store[nonce] = expires_at
            return True

    def _cleanup_locked(self, now_utc: datetime) -> None:
        expired = [n for n, exp in self._store.items() if exp <= now_utc]
        for n in expired:
            self._store.pop(n, None)
