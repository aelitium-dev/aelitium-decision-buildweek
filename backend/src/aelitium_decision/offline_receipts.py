"""Portable sample issuance and offline receipt-file verification.

Verification consumes three independent inputs: a receipt envelope, the
external materials committed by that envelope, and an externally selected
public keyring.  It never loads a private key and never trusts key material
embedded in a receipt.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .demo_keys import (
    DEMO_KEYRING_PATH,
    DEMO_PRIVATE_KEY_PATH,
    PUBLIC_SAMPLE_KEYRING_PATH,
)
from .demo_workflow import (
    DemoConfigurationError,
    build_demo_snapshot,
    create_demo_approval,
    issue_demo_receipt,
    record_demo_approval,
)
from .hashing import CanonicalizationError, parse_json_strict, validate_json_value
from .keyring import KeyringError, load_trusted_keyring
from .paths import FIXTURES_DIR, REPOSITORY_ROOT
from .receipt import ReceiptMaterials
from .verification import VerificationResult, verify_receipt


MATERIALS_VERSION = "aelitium-receipt-materials/v1"
PUBLIC_SAMPLE_DIR = FIXTURES_DIR / "sample_receipt"
PUBLIC_SAMPLE_RECEIPT_PATH = PUBLIC_SAMPLE_DIR / "decision-receipt.json"
PUBLIC_SAMPLE_MATERIALS_PATH = PUBLIC_SAMPLE_DIR / "verification-materials.json"
LOCAL_SAMPLE_DIR = REPOSITORY_ROOT / "runtime" / "sample_receipt"
LOCAL_SAMPLE_RECEIPT_PATH = LOCAL_SAMPLE_DIR / "decision-receipt.json"
LOCAL_SAMPLE_MATERIALS_PATH = LOCAL_SAMPLE_DIR / "verification-materials.json"


class OfflineReceiptError(RuntimeError):
    """Stable, fail-closed file or material error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SampleIssuanceResult:
    receipt_path: Path
    materials_path: Path
    receipt_id: str
    content_hash: str
    public_key_fingerprint_sha256: str

    def as_dict(self) -> dict[str, str]:
        return {
            "status": "ISSUED",
            "receipt_path": str(self.receipt_path),
            "materials_path": str(self.materials_path),
            "receipt_id": self.receipt_id,
            "content_hash": self.content_hash,
            "public_key_fingerprint_sha256": self.public_key_fingerprint_sha256,
        }


def materials_to_payload(materials: ReceiptMaterials) -> dict[str, Any]:
    payload = {
        "materials_version": MATERIALS_VERSION,
        "policy_pack": materials.policy_pack,
        "prompt_text": materials.prompt_text,
        "assessment_schema": materials.assessment_schema,
        "model_request": materials.model_request,
        "timeline_events": materials.timeline_events,
    }
    validate_json_value(payload)
    return payload


def materials_from_payload(payload: Any) -> ReceiptMaterials:
    required = {
        "materials_version",
        "policy_pack",
        "prompt_text",
        "assessment_schema",
        "model_request",
        "timeline_events",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise OfflineReceiptError(
            "MATERIALS_INVALID", "verification-material root fields are invalid"
        )
    if payload["materials_version"] != MATERIALS_VERSION:
        raise OfflineReceiptError(
            "MATERIALS_VERSION_UNSUPPORTED",
            "verification-material version is unsupported",
        )
    if (
        not isinstance(payload["policy_pack"], dict)
        or not isinstance(payload["prompt_text"], str)
        or not isinstance(payload["assessment_schema"], dict)
        or not isinstance(payload["model_request"], dict)
        or not isinstance(payload["timeline_events"], list)
    ):
        raise OfflineReceiptError(
            "MATERIALS_INVALID", "verification-material field types are invalid"
        )
    try:
        validate_json_value(payload)
    except CanonicalizationError as exc:
        raise OfflineReceiptError(
            "MATERIALS_INVALID", "verification materials are not canonical JSON data"
        ) from exc
    return ReceiptMaterials(
        policy_pack=payload["policy_pack"],
        prompt_text=payload["prompt_text"],
        assessment_schema=payload["assessment_schema"],
        model_request=payload["model_request"],
        timeline_events=payload["timeline_events"],
    )


def load_receipt_materials(path: Path) -> ReceiptMaterials:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise OfflineReceiptError(
            "MATERIALS_UNAVAILABLE", "verification materials are unavailable"
        ) from exc
    try:
        payload = parse_json_strict(raw)
    except CanonicalizationError as exc:
        raise OfflineReceiptError(
            "MATERIALS_INVALID", "verification materials are invalid JSON"
        ) from exc
    return materials_from_payload(payload)


def verify_receipt_files(
    *, receipt_path: Path, materials_path: Path, keyring_path: Path
) -> VerificationResult:
    """Verify using public/external inputs only; no signing material is read."""

    try:
        receipt = receipt_path.read_bytes()
    except OSError as exc:
        raise OfflineReceiptError(
            "RECEIPT_UNAVAILABLE", "receipt envelope is unavailable"
        ) from exc
    materials = load_receipt_materials(materials_path)
    try:
        keyring = load_trusted_keyring(keyring_path)
    except OSError as exc:
        raise OfflineReceiptError(
            "KEYRING_UNAVAILABLE", "trusted public keyring is unavailable"
        ) from exc
    except (KeyringError, CanonicalizationError, ValueError) as exc:
        raise OfflineReceiptError(
            "KEYRING_INVALID", "trusted public keyring is invalid"
        ) from exc
    return verify_receipt(receipt, materials=materials, keyring=keyring)


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise


def issue_sample_receipt_files(
    *,
    private_key_path: Path = DEMO_PRIVATE_KEY_PATH,
    keyring_path: Path = DEMO_KEYRING_PATH,
    receipt_path: Path = LOCAL_SAMPLE_RECEIPT_PATH,
    materials_path: Path = LOCAL_SAMPLE_MATERIALS_PATH,
) -> SampleIssuanceResult:
    """Issue a fixed DEMO scenario with local signing material.

    Output files are public, but are written below ignored runtime storage by
    default. Existing files are never overwritten.
    """

    if receipt_path == materials_path:
        raise OfflineReceiptError(
            "OUTPUT_PATH_COLLISION", "receipt and materials paths must differ"
        )
    if receipt_path.exists() or receipt_path.is_symlink():
        raise OfflineReceiptError(
            "RECEIPT_OUTPUT_EXISTS", "receipt output already exists"
        )
    if materials_path.exists() or materials_path.is_symlink():
        raise OfflineReceiptError(
            "MATERIALS_OUTPUT_EXISTS", "verification-material output already exists"
        )

    snapshot = build_demo_snapshot()
    approval = create_demo_approval(
        snapshot=snapshot,
        display_name="Mara Ellison",
        approver_role="director",
        justification=(
            "Blocking evidence is complete; the contractual conflict remains "
            "an explicit condition."
        ),
        condition="Renegotiate the subprocessor clause before renewal.",
        decided_at="2026-07-19T11:15:00Z",
    )
    approval["approval_id"] = "approval-demo-sample-2026"
    recorded = record_demo_approval(approval=approval, snapshot=snapshot)
    try:
        issued = issue_demo_receipt(
            recorded_approval=recorded,
            snapshot=snapshot,
            private_key_path=private_key_path,
            keyring_path=keyring_path,
            receipt_id="rec-demo-sample-2026",
            issued_at="2026-07-19T11:16:00Z",
        )
    except DemoConfigurationError as exc:
        raise OfflineReceiptError(
            "SIGNING_MATERIAL_INVALID",
            "local DEMO signing material is unavailable, invalid, or mismatched",
        ) from exc

    receipt_created = False
    materials_created = False
    try:
        _write_json_exclusive(receipt_path, issued.receipt)
        receipt_created = True
        _write_json_exclusive(
            materials_path, materials_to_payload(issued.materials)
        )
        materials_created = True
    except (FileExistsError, OSError, ValueError) as exc:
        if receipt_created:
            receipt_path.unlink(missing_ok=True)
        if materials_created:
            materials_path.unlink(missing_ok=True)
        raise OfflineReceiptError(
            "SAMPLE_WRITE_FAILED", "sample receipt outputs could not be written"
        ) from exc

    payload = issued.receipt["signed_receipt_payload"]
    metadata = payload["signing_metadata"]
    return SampleIssuanceResult(
        receipt_path=receipt_path,
        materials_path=materials_path,
        receipt_id=payload["receipt_id"],
        content_hash=payload["content_hash"],
        public_key_fingerprint_sha256=metadata["public_key_fingerprint_sha256"],
    )


def verify_public_sample() -> VerificationResult:
    return verify_receipt_files(
        receipt_path=PUBLIC_SAMPLE_RECEIPT_PATH,
        materials_path=PUBLIC_SAMPLE_MATERIALS_PATH,
        keyring_path=PUBLIC_SAMPLE_KEYRING_PATH,
    )
