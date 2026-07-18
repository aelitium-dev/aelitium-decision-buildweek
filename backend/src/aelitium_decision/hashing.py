"""Single internal boundary for canonical JSON and SHA-256 commitments.

Only this module may import the allowlisted vendor implementation. Application
code depends on this Build Week boundary, which also rejects duplicate keys,
floats, non-finite values, non-string object keys, and unsupported Python values
before delegating canonical JSON serialization to the pinned implementation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .vendor.aelitium_v3.canonical import (
    canonical_json as _vendor_canonical_json,
    canonicalize_and_hash as _vendor_canonicalize_and_hash,
)


class CanonicalizationError(ValueError):
    """Raised when a value is outside the ADR-001 canonical JSON contract."""


class DuplicateKeyError(CanonicalizationError):
    """Raised when strict JSON parsing encounters a duplicate object key."""


def validate_json_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise CanonicalizationError(f"{path}: JSON numbers must be integers")
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"{path}: object key must be a string")
            validate_json_value(item, f"{path}.{key}")
        return
    raise CanonicalizationError(f"{path}: unsupported value type {type(value).__name__}")


def canonical_json(value: Any) -> str:
    validate_json_value(value)
    return _vendor_canonical_json(value)


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def canonicalize_and_hash(value: Any) -> tuple[str, str]:
    validate_json_value(value)
    return _vendor_canonicalize_and_hash(value)


def hash_json(value: Any) -> str:
    return canonicalize_and_hash(value)[1]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def parse_json_strict(raw: str | bytes) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyError(f"duplicate object key: {key}")
            result[key] = value
        return result

    def reject_float(value: str) -> Any:
        raise CanonicalizationError(f"JSON numbers must be integers: {value}")

    def reject_constant(value: str) -> Any:
        raise CanonicalizationError(f"non-finite JSON number is prohibited: {value}")

    try:
        parsed = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise CanonicalizationError(f"invalid JSON: {exc.msg}") from exc
    validate_json_value(parsed)
    return parsed
