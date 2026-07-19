"""ADR-001 Decision Receipt assembly and detached Ed25519 issuance."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .approval import validate_authoritative_approval
from .hashing import canonical_bytes, hash_json, sha256_text, validate_json_value
from .policy.pack import PolicyPack
from .schema_validation import validate_canonical
from .signing import public_key_fingerprint, sign_bytes


RECEIPT_VERSION = "aelitium-decision-receipt/v1"
CONTENT_SCHEMA_VERSION = "aelitium-decision-content/v1"
CANONICALIZATION = "json_sorted_keys_no_whitespace_utf8"


class ReceiptBuildError(ValueError):
    """Raised when effective decision inputs cannot form an ADR-001 receipt."""


@dataclass(frozen=True)
class ReceiptMaterials:
    """External materials required to build and independently verify commitments."""

    policy_pack: dict[str, Any]
    prompt_text: str
    assessment_schema: dict[str, Any]
    model_request: dict[str, Any]
    timeline_events: list[dict[str, Any]]


def _normalize_references(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_references(item) for item in value]
    if not isinstance(value, dict):
        return copy.deepcopy(value)

    result = {key: _normalize_references(item) for key, item in value.items()}
    for field in ("evidence_refs", "decision_evidence_refs"):
        refs = result.get(field)
        if isinstance(refs, list):
            result[field] = sorted(
                refs,
                key=lambda ref: (ref["document_id"], ref["locator"]),
            )
    return result


def normalize_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    return _normalize_references(assessment)


def normalize_policy_result(policy_result: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_references(policy_result)
    normalized["rules_evaluated"] = sorted(
        normalized["rules_evaluated"], key=lambda rule: rule["control_id"]
    )
    return normalized


def normalize_decision_content(content: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_references(content)
    normalized["case"]["documents"] = sorted(
        normalized["case"]["documents"],
        key=lambda document: (document["document_id"], document["version"]),
    )
    normalized["model_execution"]["model_config"] = sorted(
        normalized["model_execution"]["model_config"],
        key=lambda parameter: parameter["name"],
    )
    normalized["policy"]["policy_result"] = normalize_policy_result(
        normalized["policy"]["policy_result"]
    )
    return normalized


def build_timeline_commitment(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        raise ReceiptBuildError("timeline requires at least one event")
    head_hash = "0" * 64
    for sequence, event in enumerate(events, start=1):
        validate_json_value(event)
        head_hash = hash_json(
            {"event": event, "previous_hash": head_hash, "sequence": sequence}
        )
    return {"event_count": len(events), "head_hash": head_hash}


def _validate_model_config(parameters: list[dict[str, Any]]) -> None:
    names: set[str] = set()
    scalar_fields = {
        "string": "string_value",
        "integer": "integer_value",
        "boolean": "boolean_value",
    }
    required = {
        "name",
        "value_type",
        "string_value",
        "integer_value",
        "boolean_value",
    }
    for parameter in parameters:
        if set(parameter) != required:
            raise ReceiptBuildError("model_config parameter fields are invalid")
        if parameter["name"] in names:
            raise ReceiptBuildError("model_config parameter names must be unique")
        names.add(parameter["name"])
        value_type = parameter["value_type"]
        if value_type == "null":
            if any(parameter[field] is not None for field in scalar_fields.values()):
                raise ReceiptBuildError("null model parameter carries a scalar")
            continue
        selected = scalar_fields.get(value_type)
        if selected is None or parameter[selected] is None:
            raise ReceiptBuildError("model parameter type/value mismatch")
        if any(
            parameter[field] is not None
            for field in scalar_fields.values()
            if field != selected
        ):
            raise ReceiptBuildError("model parameter carries multiple scalars")


def build_decision_content(
    *,
    case: dict[str, Any],
    provider: str,
    model: str,
    model_config: list[dict[str, Any]],
    prompt_version: str,
    model_assessment: dict[str, Any],
    policy_result: dict[str, Any],
    human_approval: dict[str, Any],
    materials: ReceiptMaterials,
) -> dict[str, Any]:
    validate_canonical(case, "decision_case.v1.schema.json")
    validate_canonical(model_assessment, "model_assessment.v1.schema.json")
    validate_canonical(policy_result, "policy_result.v1.schema.json")
    validate_canonical(human_approval, "human_approval.v1.schema.json")
    validate_json_value(materials.policy_pack)
    validate_json_value(materials.assessment_schema)
    validate_json_value(materials.model_request)
    _validate_model_config(model_config)
    try:
        effective_policy = PolicyPack.model_validate(materials.policy_pack)
    except ValueError as exc:
        raise ReceiptBuildError("policy pack is invalid") from exc

    if policy_result["case_id"] != case["case_id"]:
        raise ReceiptBuildError("policy result case_id mismatch")
    if human_approval["case_id"] != case["case_id"]:
        raise ReceiptBuildError("human approval case_id mismatch")
    if policy_result["policy_version"] != effective_policy.policy_version:
        raise ReceiptBuildError("policy version mismatch")
    if model_assessment["model"] != model:
        raise ReceiptBuildError("model assessment metadata mismatch")
    if model_assessment["prompt_version"] != prompt_version:
        raise ReceiptBuildError("prompt version mismatch")
    normalized_assessment = normalize_assessment(model_assessment)
    assessment_hash = hash_json(normalized_assessment)
    if policy_result["assessment_hash"] != assessment_hash:
        raise ReceiptBuildError("model assessment and policy result hash mismatch")
    normalized_policy_result = normalize_policy_result(policy_result)
    policy_result_hash = hash_json(normalized_policy_result)
    validate_authoritative_approval(
        policy_result=normalized_policy_result,
        policy_result_hash=policy_result_hash,
        approval=human_approval,
    )

    case_commitment = {
        "case_id": case["case_id"],
        "decision_domain": case["decision_domain"],
        "case_version": case["case_version"],
        "created_at": case["created_at"],
        "documents": [
            {
                "document_id": document["document_id"],
                "document_type": document["document_type"],
                "filename": document["filename"],
                "sha256": document["sha256"],
                "version": document["version"],
            }
            for document in case["documents"]
        ],
    }
    model_execution = {
        "provider": provider,
        "model": model,
        "model_config": copy.deepcopy(model_config),
        "prompt_version": prompt_version,
        "prompt_hash": sha256_text(materials.prompt_text),
        "assessment_schema_version": "model-assessment/v1",
        "assessment_schema_hash": hash_json(materials.assessment_schema),
        "model_request_hash": hash_json(materials.model_request),
    }
    content = {
        "case": case_commitment,
        "model_execution": model_execution,
        "model_assessment": normalized_assessment,
        "assessment_hash": assessment_hash,
        "policy": {
            "policy_version": policy_result["policy_version"],
            "policy_rules_hash": hash_json(materials.policy_pack),
            "policy_result": normalized_policy_result,
            "policy_result_hash": policy_result_hash,
        },
        "human_approval": _normalize_references(human_approval),
        "timeline": build_timeline_commitment(materials.timeline_events),
    }
    return normalize_decision_content(content)


def issue_receipt(
    *,
    decision_content: dict[str, Any],
    receipt_id: str,
    issued_at: str,
    key_id: str,
    private_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    normalized_content = normalize_decision_content(decision_content)
    public_key = private_key.public_key()
    signed_payload = {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": receipt_id,
        "content_schema_version": CONTENT_SCHEMA_VERSION,
        "content_hash_algorithm": "sha256",
        "content_hash": hash_json(normalized_content),
        "issued_at": issued_at,
        "signing_metadata": {
            "signature_algorithm": "Ed25519",
            "signature_encoding": "base64",
            "key_id": key_id,
            "public_key_fingerprint_sha256": public_key_fingerprint(public_key),
            "payload_canonicalization": CANONICALIZATION,
        },
    }
    receipt = {
        "decision_content": normalized_content,
        "signed_receipt_payload": signed_payload,
        "signature": sign_bytes(private_key, canonical_bytes(signed_payload)),
    }
    validate_canonical(receipt, "decision_receipt.v1.schema.json")
    return receipt
