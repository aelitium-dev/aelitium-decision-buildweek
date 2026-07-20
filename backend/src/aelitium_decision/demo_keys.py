"""Safe local DEMO signing-key bootstrap.

The private Ed25519 key and its matching runtime keyring are local runtime
state.  This module never overwrites either file, never prints key bytes, and
never derives trust from a receipt.  The checked-in sample keyring is a
separate public trust anchor used only to verify the checked-in sample receipt.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .keyring import load_trusted_keyring
from .paths import REPOSITORY_ROOT
from .signing import (
    generate_private_key_file,
    load_private_key,
    public_key_fingerprint,
    public_key_record,
)


DEMO_KEY_ID = "buildweek-demo-2026"
DEMO_PRIVATE_KEY_PATH = REPOSITORY_ROOT / "runtime" / "keys" / f"{DEMO_KEY_ID}.key"
DEMO_KEYRING_PATH = (
    REPOSITORY_ROOT / "runtime" / "keys" / "trusted-keyring.local.json"
)
PUBLIC_SAMPLE_KEYRING_PATH = (
    REPOSITORY_ROOT / "config" / "trusted-keyring.demo.json"
)


class DemoKeyBootstrapError(RuntimeError):
    """Stable, non-secret bootstrap failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DemoKeyBootstrapResult:
    status: str
    key_id: str
    fingerprint_sha256: str
    private_key_path: Path
    keyring_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "key_id": self.key_id,
            "fingerprint_sha256": self.fingerprint_sha256,
            "private_key_path": str(self.private_key_path),
            "keyring_path": str(self.keyring_path),
        }


def _keyring_payload(
    key_id: str, public_key: Ed25519PublicKey
) -> dict[str, Any]:
    return {
        "keyring_version": "aelitium-trusted-keyring/v1",
        "keys": [public_key_record(key_id, public_key)],
    }


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    """Write public JSON once; refuse existing files and symlink targets."""

    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _load_secure_private_key(path: Path):
    if path.is_symlink():
        raise DemoKeyBootstrapError(
            "PRIVATE_KEY_SYMLINK", "the DEMO private key must not be a symlink"
        )
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        raise DemoKeyBootstrapError(
            "PRIVATE_KEY_UNAVAILABLE", "the DEMO private key is unavailable"
        ) from exc
    if mode != 0o600:
        raise DemoKeyBootstrapError(
            "PRIVATE_KEY_PERMISSIONS",
            "the DEMO private key must have permissions 0600",
        )
    try:
        return load_private_key(path)
    except (OSError, ValueError, TypeError) as exc:
        raise DemoKeyBootstrapError(
            "PRIVATE_KEY_INVALID", "the DEMO private key is not a valid Ed25519 key"
        ) from exc


def _validate_pair(
    *, private_key_path: Path, keyring_path: Path, key_id: str
) -> str:
    private_key = _load_secure_private_key(private_key_path)
    if keyring_path.is_symlink():
        raise DemoKeyBootstrapError(
            "KEYRING_SYMLINK", "the DEMO runtime keyring must not be a symlink"
        )
    try:
        keyring = load_trusted_keyring(keyring_path)
    except (OSError, ValueError) as exc:
        raise DemoKeyBootstrapError(
            "KEYRING_INVALID", "the DEMO runtime keyring is unavailable or invalid"
        ) from exc
    trusted_key = keyring.resolve(key_id)
    fingerprint = public_key_fingerprint(private_key.public_key())
    if trusted_key is None or trusted_key.fingerprint_sha256 != fingerprint:
        raise DemoKeyBootstrapError(
            "KEYPAIR_MISMATCH",
            "the DEMO private key does not match the runtime keyring",
        )
    return fingerprint


def bootstrap_demo_keypair(
    *,
    private_key_path: Path = DEMO_PRIVATE_KEY_PATH,
    keyring_path: Path = DEMO_KEYRING_PATH,
    key_id: str = DEMO_KEY_ID,
) -> DemoKeyBootstrapResult:
    """Create or validate a local keypair without ever overwriting key material.

    If a valid private key already exists and the runtime keyring does not, only
    its public record is derived.  A keyring without its private key is treated
    as an unrecoverable partial state and fails closed.
    """

    private_exists = private_key_path.exists() or private_key_path.is_symlink()
    keyring_exists = keyring_path.exists() or keyring_path.is_symlink()

    if keyring_exists and not private_exists:
        raise DemoKeyBootstrapError(
            "PRIVATE_KEY_MISSING",
            "a runtime keyring exists but its DEMO private key is missing",
        )

    if private_exists and keyring_exists:
        fingerprint = _validate_pair(
            private_key_path=private_key_path,
            keyring_path=keyring_path,
            key_id=key_id,
        )
        return DemoKeyBootstrapResult(
            "READY", key_id, fingerprint, private_key_path, keyring_path
        )

    generated_private = False
    if private_exists:
        private_key = _load_secure_private_key(private_key_path)
        status = "PUBLIC_KEYRING_CREATED"
    else:
        try:
            private_key = generate_private_key_file(private_key_path)
        except (FileExistsError, OSError, ValueError) as exc:
            raise DemoKeyBootstrapError(
                "PRIVATE_KEY_CREATE_FAILED", "could not create the DEMO private key"
            ) from exc
        generated_private = True
        status = "KEYPAIR_CREATED"

    keyring_created = False
    try:
        _write_json_exclusive(
            keyring_path, _keyring_payload(key_id, private_key.public_key())
        )
        keyring_created = True
        fingerprint = _validate_pair(
            private_key_path=private_key_path,
            keyring_path=keyring_path,
            key_id=key_id,
        )
    except Exception:
        if keyring_created:
            keyring_path.unlink(missing_ok=True)
        if generated_private:
            private_key_path.unlink(missing_ok=True)
        raise

    return DemoKeyBootstrapResult(
        status, key_id, fingerprint, private_key_path, keyring_path
    )
