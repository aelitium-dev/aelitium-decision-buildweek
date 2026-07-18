"""Offline, deterministic, fail-closed ADR-001 Decision Receipt verifier."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any, Literal

from cryptography.exceptions import InvalidSignature

from .hashing import (
    CanonicalizationError,
    canonical_bytes,
    hash_json,
    parse_json_strict,
    sha256_text,
    validate_json_value,
)
from .keyring import TrustedKeyring
from .receipt import (
    CANONICALIZATION,
    CONTENT_SCHEMA_VERSION,
    RECEIPT_VERSION,
    ReceiptBuildError,
    ReceiptMaterials,
    build_timeline_commitment,
    normalize_assessment,
    normalize_decision_content,
    normalize_policy_result,
)
from .schema_validation import CanonicalSchemaError, validate_canonical
from .signing import public_key_fingerprint


@dataclass(frozen=True)
class VerificationResult:
    status: Literal["VALID", "INVALID"]
    reason: str

    @property
    def valid(self) -> bool:
        return self.status == "VALID"

    def as_dict(self) -> dict[str, str]:
        return {"status": self.status, "reason": self.reason}


def _invalid(reason: str) -> VerificationResult:
    return VerificationResult("INVALID", reason)


def verify_receipt(
    receipt_input: dict[str, Any] | str | bytes,
    *,
    keyring: TrustedKeyring,
    materials: ReceiptMaterials,
) -> VerificationResult:
    try:
        if isinstance(receipt_input, (str, bytes)):
            receipt = parse_json_strict(receipt_input)
        else:
            validate_json_value(receipt_input)
            receipt = receipt_input
        if not isinstance(receipt, dict):
            return _invalid("JSON_ROOT_INVALID")
    except CanonicalizationError:
        return _invalid("JSON_INVALID")

    try:
        validate_canonical(receipt, "decision_receipt.v1.schema.json")
    except CanonicalSchemaError:
        return _invalid("SCHEMA_INVALID")

    payload = receipt["signed_receipt_payload"]
    metadata = payload["signing_metadata"]
    if (
        payload["receipt_version"] != RECEIPT_VERSION
        or payload["content_schema_version"] != CONTENT_SCHEMA_VERSION
        or payload["content_hash_algorithm"] != "sha256"
        or metadata["signature_algorithm"] != "Ed25519"
        or metadata["signature_encoding"] != "base64"
        or metadata["payload_canonicalization"] != CANONICALIZATION
    ):
        return _invalid("UNSUPPORTED_RECEIPT_CONTRACT")

    content = receipt["decision_content"]
    if normalize_decision_content(content) != content:
        return _invalid("CONTENT_NOT_NORMALIZED")

    assessment = content["model_assessment"]
    if hash_json(normalize_assessment(assessment)) != content["assessment_hash"]:
        return _invalid("ASSESSMENT_HASH_MISMATCH")
    policy = content["policy"]
    policy_result = policy["policy_result"]
    if hash_json(normalize_policy_result(policy_result)) != policy["policy_result_hash"]:
        return _invalid("POLICY_RESULT_HASH_MISMATCH")
    approval = content["human_approval"]
    if approval["policy_result_hash"] != policy["policy_result_hash"]:
        return _invalid("APPROVAL_POLICY_HASH_MISMATCH")
    if (
        policy_result["case_id"] != content["case"]["case_id"]
        or approval["case_id"] != content["case"]["case_id"]
        or policy_result["policy_version"] != policy["policy_version"]
        or assessment["model"] != content["model_execution"]["model"]
        or assessment["prompt_version"]
        != content["model_execution"]["prompt_version"]
    ):
        return _invalid("CROSS_REFERENCE_MISMATCH")

    try:
        if hash_json(materials.policy_pack) != policy["policy_rules_hash"]:
            return _invalid("POLICY_RULES_HASH_MISMATCH")
        execution = content["model_execution"]
        if sha256_text(materials.prompt_text) != execution["prompt_hash"]:
            return _invalid("PROMPT_HASH_MISMATCH")
        if hash_json(materials.assessment_schema) != execution["assessment_schema_hash"]:
            return _invalid("ASSESSMENT_SCHEMA_HASH_MISMATCH")
        if hash_json(materials.model_request) != execution["model_request_hash"]:
            return _invalid("MODEL_REQUEST_HASH_MISMATCH")
        if build_timeline_commitment(materials.timeline_events) != content["timeline"]:
            return _invalid("TIMELINE_HEAD_MISMATCH")
    except (CanonicalizationError, ReceiptBuildError):
        return _invalid("VERIFICATION_MATERIALS_INVALID")
    if hash_json(content) != payload["content_hash"]:
        return _invalid("CONTENT_HASH_MISMATCH")

    trusted_key = keyring.resolve(metadata["key_id"])
    if trusted_key is None:
        return _invalid("UNKNOWN_KEY_ID")
    fingerprint = public_key_fingerprint(trusted_key.public_key)
    if (
        fingerprint != trusted_key.fingerprint_sha256
        or fingerprint != metadata["public_key_fingerprint_sha256"]
    ):
        return _invalid("KEY_FINGERPRINT_MISMATCH")
    try:
        signature = base64.b64decode(receipt["signature"], validate=True)
    except (binascii.Error, ValueError):
        return _invalid("SIGNATURE_ENCODING_INVALID")
    if len(signature) != 64:
        return _invalid("SIGNATURE_LENGTH_INVALID")
    try:
        trusted_key.public_key.verify(signature, canonical_bytes(payload))
    except InvalidSignature:
        return _invalid("SIGNATURE_INVALID")
    return VerificationResult("VALID", "VERIFIED")
