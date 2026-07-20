from __future__ import annotations

import copy
import json
import stat

import pytest

from aelitium_decision.cli import main
from aelitium_decision.demo_keys import (
    DEMO_KEY_ID,
    PUBLIC_SAMPLE_KEYRING_PATH,
    DemoKeyBootstrapError,
    bootstrap_demo_keypair,
)
from aelitium_decision.keyring import load_trusted_keyring
from aelitium_decision.offline_receipts import (
    PUBLIC_SAMPLE_MATERIALS_PATH,
    PUBLIC_SAMPLE_RECEIPT_PATH,
    OfflineReceiptError,
    issue_sample_receipt_files,
    verify_receipt_files,
)
from aelitium_decision.signing import generate_private_key_file


def test_bootstrap_creates_ignored_style_keypair_and_is_idempotent(tmp_path):
    private_path = tmp_path / "runtime" / "demo.key"
    keyring_path = tmp_path / "runtime" / "keyring.json"

    created = bootstrap_demo_keypair(
        private_key_path=private_path, keyring_path=keyring_path
    )

    assert created.status == "KEYPAIR_CREATED"
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o600
    private_bytes = private_path.read_bytes()
    public_bytes = keyring_path.read_bytes()
    assert b"PRIVATE KEY" in private_bytes
    assert b"PRIVATE KEY" not in public_bytes
    trusted = load_trusted_keyring(keyring_path).resolve(DEMO_KEY_ID)
    assert trusted is not None
    assert trusted.fingerprint_sha256 == created.fingerprint_sha256

    ready = bootstrap_demo_keypair(
        private_key_path=private_path, keyring_path=keyring_path
    )

    assert ready.status == "READY"
    assert private_path.read_bytes() == private_bytes
    assert keyring_path.read_bytes() == public_bytes


def test_bootstrap_can_prepare_public_keyring_from_existing_secure_private_key(
    tmp_path,
):
    private_path = tmp_path / "demo.key"
    keyring_path = tmp_path / "keyring.json"
    generate_private_key_file(private_path)

    result = bootstrap_demo_keypair(
        private_key_path=private_path, keyring_path=keyring_path
    )

    assert result.status == "PUBLIC_KEYRING_CREATED"
    assert load_trusted_keyring(keyring_path).resolve(DEMO_KEY_ID) is not None


def test_bootstrap_fails_closed_when_private_key_is_missing(tmp_path):
    keyring_path = tmp_path / "keyring.json"
    keyring_path.write_text("{}", encoding="utf-8")

    with pytest.raises(DemoKeyBootstrapError) as caught:
        bootstrap_demo_keypair(
            private_key_path=tmp_path / "missing.key", keyring_path=keyring_path
        )

    assert caught.value.code == "PRIVATE_KEY_MISSING"


def test_bootstrap_fails_closed_for_invalid_private_key(tmp_path):
    private_path = tmp_path / "invalid.key"
    private_path.write_text("not a private key", encoding="utf-8")
    private_path.chmod(0o600)

    with pytest.raises(DemoKeyBootstrapError) as caught:
        bootstrap_demo_keypair(
            private_key_path=private_path, keyring_path=tmp_path / "keyring.json"
        )

    assert caught.value.code == "PRIVATE_KEY_INVALID"


def test_bootstrap_fails_closed_for_insecure_private_key_permissions(tmp_path):
    private_path = tmp_path / "demo.key"
    generate_private_key_file(private_path)
    private_path.chmod(0o644)

    with pytest.raises(DemoKeyBootstrapError) as caught:
        bootstrap_demo_keypair(
            private_key_path=private_path, keyring_path=tmp_path / "keyring.json"
        )

    assert caught.value.code == "PRIVATE_KEY_PERMISSIONS"


def test_bootstrap_fails_closed_for_mismatched_keyring(tmp_path):
    first_private = tmp_path / "first.key"
    first_keyring = tmp_path / "first-keyring.json"
    bootstrap_demo_keypair(
        private_key_path=first_private, keyring_path=first_keyring
    )
    second_private = tmp_path / "second.key"
    generate_private_key_file(second_private)

    with pytest.raises(DemoKeyBootstrapError) as caught:
        bootstrap_demo_keypair(
            private_key_path=second_private, keyring_path=first_keyring
        )

    assert caught.value.code == "KEYPAIR_MISMATCH"


def test_local_sample_issue_then_verify_needs_no_private_key(tmp_path):
    private_path = tmp_path / "demo.key"
    keyring_path = tmp_path / "keyring.json"
    receipt_path = tmp_path / "receipt.json"
    materials_path = tmp_path / "materials.json"
    bootstrap_demo_keypair(
        private_key_path=private_path, keyring_path=keyring_path
    )

    issued = issue_sample_receipt_files(
        private_key_path=private_path,
        keyring_path=keyring_path,
        receipt_path=receipt_path,
        materials_path=materials_path,
    )
    private_path.unlink()

    first = verify_receipt_files(
        receipt_path=receipt_path,
        materials_path=materials_path,
        keyring_path=keyring_path,
    )
    second = verify_receipt_files(
        receipt_path=receipt_path,
        materials_path=materials_path,
        keyring_path=keyring_path,
    )
    assert first.as_dict() == {"status": "VALID", "reason": "VERIFIED"}
    assert second == first
    assert issued.receipt_id == "rec-demo-sample-2026"


def test_local_sample_issue_never_overwrites_existing_outputs(tmp_path):
    private_path = tmp_path / "demo.key"
    keyring_path = tmp_path / "keyring.json"
    receipt_path = tmp_path / "receipt.json"
    materials_path = tmp_path / "materials.json"
    bootstrap_demo_keypair(
        private_key_path=private_path, keyring_path=keyring_path
    )
    issue_sample_receipt_files(
        private_key_path=private_path,
        keyring_path=keyring_path,
        receipt_path=receipt_path,
        materials_path=materials_path,
    )
    original_receipt = receipt_path.read_bytes()
    original_materials = materials_path.read_bytes()

    with pytest.raises(OfflineReceiptError) as caught:
        issue_sample_receipt_files(
            private_key_path=private_path,
            keyring_path=keyring_path,
            receipt_path=receipt_path,
            materials_path=materials_path,
        )

    assert caught.value.code == "RECEIPT_OUTPUT_EXISTS"
    assert receipt_path.read_bytes() == original_receipt
    assert materials_path.read_bytes() == original_materials


def test_sample_issue_fails_closed_without_private_key(tmp_path):
    with pytest.raises(OfflineReceiptError) as caught:
        issue_sample_receipt_files(
            private_key_path=tmp_path / "missing.key",
            keyring_path=tmp_path / "missing-keyring.json",
            receipt_path=tmp_path / "receipt.json",
            materials_path=tmp_path / "materials.json",
        )

    assert caught.value.code == "SIGNING_MATERIAL_INVALID"
    assert not (tmp_path / "receipt.json").exists()
    assert not (tmp_path / "materials.json").exists()


def test_checked_in_public_sample_verifies_offline_and_deterministically():
    results = [
        verify_receipt_files(
            receipt_path=PUBLIC_SAMPLE_RECEIPT_PATH,
            materials_path=PUBLIC_SAMPLE_MATERIALS_PATH,
            keyring_path=PUBLIC_SAMPLE_KEYRING_PATH,
        )
        for _ in range(3)
    ]

    assert all(result.as_dict() == {"status": "VALID", "reason": "VERIFIED"} for result in results)
    receipt = json.loads(PUBLIC_SAMPLE_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt["signed_receipt_payload"]["content_hash"] == (
        "df00717b3c5aa68553596bb8bdac9c9d4f0efe8a72361c3870c94dff26aed0e2"
    )
    for path in (
        PUBLIC_SAMPLE_RECEIPT_PATH,
        PUBLIC_SAMPLE_MATERIALS_PATH,
        PUBLIC_SAMPLE_KEYRING_PATH,
    ):
        assert "PRIVATE KEY" not in path.read_text(encoding="utf-8")


def test_checked_in_sample_tamper_is_invalid(tmp_path):
    receipt = json.loads(PUBLIC_SAMPLE_RECEIPT_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(receipt)
    price = next(
        fact
        for fact in tampered["decision_content"]["model_assessment"]["facts"]
        if fact["fact_key"] == "commercial.annual_price_eur"
    )
    price["value"]["integer_value"] = 14000
    tampered_path = tmp_path / "tampered-receipt.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")

    result = verify_receipt_files(
        receipt_path=tampered_path,
        materials_path=PUBLIC_SAMPLE_MATERIALS_PATH,
        keyring_path=PUBLIC_SAMPLE_KEYRING_PATH,
    )

    assert result.as_dict() == {
        "status": "INVALID",
        "reason": "ASSESSMENT_HASH_MISMATCH",
    }


def test_offline_verify_fails_closed_when_external_materials_are_missing(tmp_path):
    with pytest.raises(OfflineReceiptError) as caught:
        verify_receipt_files(
            receipt_path=PUBLIC_SAMPLE_RECEIPT_PATH,
            materials_path=tmp_path / "missing-materials.json",
            keyring_path=PUBLIC_SAMPLE_KEYRING_PATH,
        )

    assert caught.value.code == "MATERIALS_UNAVAILABLE"


def test_offline_verify_fails_closed_when_trusted_keyring_is_missing(tmp_path):
    with pytest.raises(OfflineReceiptError) as caught:
        verify_receipt_files(
            receipt_path=PUBLIC_SAMPLE_RECEIPT_PATH,
            materials_path=PUBLIC_SAMPLE_MATERIALS_PATH,
            keyring_path=tmp_path / "missing-keyring.json",
        )

    assert caught.value.code == "KEYRING_UNAVAILABLE"


def test_public_sample_is_invalid_under_a_different_public_key(tmp_path):
    private_path = tmp_path / "other.key"
    keyring_path = tmp_path / "other-keyring.json"
    bootstrap_demo_keypair(
        private_key_path=private_path, keyring_path=keyring_path
    )

    result = verify_receipt_files(
        receipt_path=PUBLIC_SAMPLE_RECEIPT_PATH,
        materials_path=PUBLIC_SAMPLE_MATERIALS_PATH,
        keyring_path=keyring_path,
    )

    assert result.as_dict() == {
        "status": "INVALID",
        "reason": "KEY_FINGERPRINT_MISMATCH",
    }


def test_cli_bootstrap_and_public_sample_verify(tmp_path, capsys):
    private_path = tmp_path / "demo.key"
    keyring_path = tmp_path / "keyring.json"
    assert main(
        [
            "keys",
            "bootstrap",
            "--private-key",
            str(private_path),
            "--keyring",
            str(keyring_path),
        ]
    ) == 0
    bootstrap_output = json.loads(capsys.readouterr().out)
    assert bootstrap_output["status"] == "KEYPAIR_CREATED"
    assert "private_key" not in json.dumps(bootstrap_output).lower().replace(
        "private_key_path", ""
    )

    assert main(["receipt", "verify"]) == 0
    verification_output = json.loads(capsys.readouterr().out)
    assert verification_output == {"status": "VALID", "reason": "VERIFIED"}
