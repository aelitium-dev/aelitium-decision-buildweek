from __future__ import annotations

import copy

import pytest

from aelitium_decision.keyring import KeyringError, TrustedKeyring, load_trusted_keyring
from aelitium_decision.paths import REPOSITORY_ROOT


def test_demo_keyring_contains_only_a_valid_public_trust_record():
    path = REPOSITORY_ROOT / "config" / "trusted-keyring.demo.json"
    keyring = load_trusted_keyring(path)
    trusted = keyring.resolve("buildweek-demo-2026")

    assert trusted is not None
    assert trusted.fingerprint_sha256 == (
        "6fa378abbdbc64d19459e421a3a32575d32432529f093bdb855afe865ebe281e"
    )
    assert "PRIVATE" not in path.read_text(encoding="utf-8")


def test_keyring_rejects_a_malformed_public_record():
    payload = {
        "keyring_version": "aelitium-trusted-keyring/v1",
        "keys": [
            {
                "key_id": "demo-key",
                "algorithm": "Ed25519",
                "public_key_encoding": "base64_raw",
                "public_key": 123,
                "fingerprint_sha256": "0" * 64,
            }
        ],
    }

    with pytest.raises(KeyringError, match="base64 string"):
        TrustedKeyring.from_payload(copy.deepcopy(payload))
