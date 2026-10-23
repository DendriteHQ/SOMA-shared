from __future__ import annotations

import json
from collections.abc import Collection, Iterable, Mapping
from typing import Any

from pydantic import BaseModel

# Pydantic error keys that echo the submitted values.
_VALUE_ECHOING_ERROR_KEYS = frozenset({"input", "ctx"})


def omit_fields(payload: Mapping[str, Any], fields: Collection[str]) -> dict[str, Any]:
    """Replace the given top-level fields with a size marker so their content is not stored."""
    redacted = dict(payload)
    for field in fields:
        if field not in redacted:
            continue
        size = len(json.dumps(redacted[field], default=str).encode("utf-8"))
        redacted[field] = f"<omitted: {size} bytes>"
    return redacted


def log_omit_fields_of(model: BaseModel | type[BaseModel]) -> frozenset[str]:
    return frozenset(getattr(model, "log_omit_fields", ()))


def loggable_payload(payload: BaseModel) -> dict[str, Any]:
    """JSON dump of a contract model without the fields it marks as not loggable."""
    return omit_fields(payload.model_dump(mode="json"), log_omit_fields_of(payload))


def loggable_raw_payload(payload: Any, model: type[BaseModel]) -> Any:
    """A payload that failed validation against ``model``, without the fields it marks."""
    if isinstance(payload, Mapping):
        return omit_fields(payload, log_omit_fields_of(model))
    return payload


def loggable_validation_errors(errors: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validation errors without the submitted values (a missing field echoes the whole payload)."""
    return [
        {key: value for key, value in error.items() if key not in _VALUE_ECHOING_ERROR_KEYS}
        for error in errors
    ]
