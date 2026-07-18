"""New Build Week Ed25519 primitives; no P3 signer or verifier is reused."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .hashing import sha256_bytes


def public_key_bytes(public_key: Ed25519PublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def public_key_fingerprint(public_key: Ed25519PublicKey) -> str:
    return sha256_bytes(public_key_bytes(public_key))


def public_key_record(key_id: str, public_key: Ed25519PublicKey) -> dict[str, Any]:
    return {
        "key_id": key_id,
        "algorithm": "Ed25519",
        "public_key_encoding": "base64_raw",
        "public_key": base64.b64encode(public_key_bytes(public_key)).decode("ascii"),
        "fingerprint_sha256": public_key_fingerprint(public_key),
    }


def sign_bytes(private_key: Ed25519PrivateKey, payload: bytes) -> str:
    return base64.b64encode(private_key.sign(payload)).decode("ascii")


def generate_private_key_file(path: Path) -> Ed25519PrivateKey:
    """Generate a new local key with mode 0600 and refuse to overwrite."""

    path.parent.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(private_bytes)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return private_key


def load_private_key(path: Path) -> Ed25519PrivateKey:
    loaded = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(loaded, Ed25519PrivateKey):
        raise ValueError("private key is not Ed25519")
    return loaded
