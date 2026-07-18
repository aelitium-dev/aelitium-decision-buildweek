"""External trusted public-key registry for offline receipt verification."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .hashing import parse_json_strict
from .signing import public_key_fingerprint


KEY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


class KeyringError(ValueError):
    """Raised when a trusted keyring is malformed or internally inconsistent."""


@dataclass(frozen=True)
class TrustedKey:
    key_id: str
    public_key: Ed25519PublicKey
    fingerprint_sha256: str


@dataclass(frozen=True)
class TrustedKeyring:
    keys: dict[str, TrustedKey]

    def resolve(self, key_id: str) -> TrustedKey | None:
        return self.keys.get(key_id)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TrustedKeyring":
        if set(payload) != {"keyring_version", "keys"}:
            raise KeyringError("keyring root fields are invalid")
        if payload["keyring_version"] != "aelitium-trusted-keyring/v1":
            raise KeyringError("unsupported keyring version")
        records = payload["keys"]
        if not isinstance(records, list) or not records:
            raise KeyringError("keyring must contain at least one key")

        keys: dict[str, TrustedKey] = {}
        required = {
            "key_id",
            "algorithm",
            "public_key_encoding",
            "public_key",
            "fingerprint_sha256",
        }
        for record in records:
            if not isinstance(record, dict) or set(record) != required:
                raise KeyringError("key record fields are invalid")
            key_id = record["key_id"]
            if not isinstance(key_id, str) or KEY_ID_RE.fullmatch(key_id) is None:
                raise KeyringError("key_id is invalid")
            if key_id in keys:
                raise KeyringError(f"duplicate key_id: {key_id}")
            if record["algorithm"] != "Ed25519":
                raise KeyringError("unsupported key algorithm")
            if record["public_key_encoding"] != "base64_raw":
                raise KeyringError("unsupported public key encoding")
            if not isinstance(record["public_key"], str):
                raise KeyringError("public key must be a base64 string")
            if (
                not isinstance(record["fingerprint_sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", record["fingerprint_sha256"])
                is None
            ):
                raise KeyringError("public key fingerprint is invalid")
            try:
                raw_key = base64.b64decode(record["public_key"], validate=True)
            except (binascii.Error, TypeError, ValueError) as exc:
                raise KeyringError("public key is not valid base64") from exc
            if len(raw_key) != 32:
                raise KeyringError("Ed25519 public key must be 32 bytes")
            public_key = Ed25519PublicKey.from_public_bytes(raw_key)
            fingerprint = public_key_fingerprint(public_key)
            if record["fingerprint_sha256"] != fingerprint:
                raise KeyringError("public key fingerprint mismatch")
            keys[key_id] = TrustedKey(key_id, public_key, fingerprint)
        return cls(keys)


def load_trusted_keyring(path: Path) -> TrustedKeyring:
    payload = parse_json_strict(path.read_bytes())
    if not isinstance(payload, dict):
        raise KeyringError("keyring must be a JSON object")
    return TrustedKeyring.from_payload(payload)
