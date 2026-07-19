"""Deterministic, no-key model workflow used by the clickable Build Week demo.

The module assembles the post-F5 case from checked-in fixtures, runs the generic
Policy Engine with the Vendor Approval Policy Pack, records a declared human
approval, and issues or verifies ADR-001 receipts. Model assessment data is
pre-computed; only receipt signing uses a local, Git-ignored Ed25519 private key.
"""

from __future__ import annotations

import copy
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .approval import (
    ApprovalAuthorizationError,
    permitted_decisions,
    validate_authoritative_approval,
    validate_policy_receipt_eligibility,
)
from .demo import load_golden_manifest
from .hashing import hash_json
from .keyring import TrustedKeyring, load_trusted_keyring
from .paths import FIXTURES_DIR, POLICIES_DIR, REPOSITORY_ROOT
from .policy import PolicyEngine, load_policy_pack
from .receipt import (
    ReceiptMaterials,
    build_decision_content,
    issue_receipt,
    normalize_assessment,
    normalize_policy_result,
)
from .schema_validation import CanonicalSchemaError, load_schema, validate_canonical
from .signing import load_private_key, public_key_fingerprint
from .verification import VerificationResult, verify_receipt


DEMO_KEY_ID = "buildweek-demo-2026"
DEMO_PRIVATE_KEY_PATH = REPOSITORY_ROOT / "runtime" / "keys" / f"{DEMO_KEY_ID}.key"
DEMO_KEYRING_PATH = REPOSITORY_ROOT / "config" / "trusted-keyring.demo.json"
DEMO_ASSESSMENT_SOURCE = "precomputed_fixture"
DEMO_DERIVATION_VERSION = "demo-fixture-derivation/v1"
DEMO_DERIVATION_DESCRIPTION = (
    "Deterministically derive the post-F5 DEMO assessment from the checked-in "
    "T2 assessment fixture and the fixed F5 evidence changes in demo_workflow.py."
)
LIVE_ARTIFACT_PATH = "fixtures/live/gpt-5.6-t2-assessment.json"
DEMO_BASE_ASSESSMENT_PATH = "fixtures/demo/T2_assessment.json"
TRUST_LIMITATIONS = [
    "source_document_authenticity",
    "factual_truth",
    "assessment_correctness",
    "decision_correctness",
    "decision_fairness",
    "legal_validity",
    "identity_authentication",
    "trusted_time",
]


class DemoConfigurationError(RuntimeError):
    """Raised when local signing material is unavailable or does not match trust."""


@dataclass(frozen=True)
class IssuedDemoReceipt:
    receipt: dict[str, Any]
    materials: ReceiptMaterials
    keyring: TrustedKeyring


@dataclass(frozen=True)
class RecordedDemoApproval:
    """Server-held approval plus immutable decision-input fingerprints."""

    approval: dict[str, Any]
    approval_hash: str
    case_hash: str
    assessment_hash: str
    policy_result_hash: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def _post_f5_assessment() -> dict[str, Any]:
    manifest = load_golden_manifest()
    assessment = _load_json(
        REPOSITORY_ROOT / manifest["cases"]["T2"]["assessment_path"]
    )
    assessment["model"] = "demo-precomputed"
    assessment["prompt_version"] = DEMO_DERIVATION_VERSION
    assessment["case_summary"] = (
        "F1–F5 satisfy the blocking residency, DPA, and assurance controls; "
        "director approval and human conflict review remain required."
    )
    facts = {fact["fact_key"]: fact for fact in assessment["facts"]}

    residency = facts["privacy.eu_eea_only_residency_confirmed"]
    residency["statement"] = "F5 confirms EU or EEA-only residency for the tenant."
    residency["value"] = {
        "value_type": "boolean",
        "string_value": None,
        "integer_value": None,
        "boolean_value": True,
    }
    residency["evidence_refs"] = [
        {
            "document_id": "F5",
            "locator": "section 1",
            "quoted_text": (
                "Customer Content, backups, and core processing will remain in "
                "the European Union or European Economic Area."
            ),
            "reference_level": "validated_reference",
        }
    ]

    assurance = facts["security.assurance_report_issued"]
    assurance["statement"] = "F5 confirms the fictional assurance report was issued."
    assurance["value"] = {
        "value_type": "boolean",
        "string_value": None,
        "integer_value": None,
        "boolean_value": True,
    }
    assurance["evidence_refs"] = [
        {
            "document_id": "F5",
            "locator": "section 2",
            "quoted_text": "The report was issued on 2026-07-15.",
            "reference_level": "validated_reference",
        }
    ]

    assessment["missing_evidence"] = []
    assessment["risks"] = [
        {
            "risk_id": "risk-contract-conflict",
            "category": "contract",
            "summary": (
                "The questionnaire and executed DPA conflict on subprocessor notice."
            ),
            "severity": "high",
            "likelihood": "likely",
            "evidence_refs": copy.deepcopy(assessment["conflicts"][0]["evidence_refs"]),
        }
    ]
    assessment["options"] = [
        {
            "option_id": "option-conditional-approval",
            "label": "Conditional director approval",
            "description": "Approve with an explicit contract-remediation condition.",
            "benefits": ["Blocking evidence controls are satisfied."],
            "risks": ["Subprocessor notice language remains unresolved."],
            "preconditions": [
                "Director reviews the conflict and records a condition."
            ],
        }
    ]
    assessment["recommendation"] = {
        "option_id": "option-conditional-approval",
        "rationale": (
            "Evidence gates pass, but price and contractual conflict require human "
            "authority."
        ),
        "conditions": ["Renegotiate the subprocessor clause before renewal."],
    }
    assessment["confidence"] = 93
    assessment["requires_human_review"] = True
    validate_canonical(assessment, "model_assessment.v1.schema.json")
    return assessment


def _decision_case() -> dict[str, Any]:
    manifest = _load_json(FIXTURES_DIR / "manifest.json")
    documents = [
        {
            "document_id": document["document_id"],
            "document_type": document["document_type"],
            "filename": document["filename"],
            "media_type": "text/markdown",
            "sha256": document["sha256"],
            "version": document["version"],
            "added_at": "2026-07-18T12:00:00Z",
        }
        for document in manifest["documents"]
    ]
    case = {
        "schema_version": "decision-case/v1",
        "case_id": "case-novamind-conditional-approval",
        "decision_domain": "ai_vendor_approval",
        "title": "NovaMind AI vendor approval",
        "case_version": 2,
        "state": "HUMAN_APPROVAL_REQUIRED",
        "documents": documents,
        "created_at": "2026-07-18T10:00:00Z",
        "updated_at": "2026-07-19T11:00:00Z",
    }
    validate_canonical(case, "decision_case.v1.schema.json")
    return case


def _evaluate(
    *, case_id: str, assessment: dict[str, Any], evaluated_at: str
) -> dict[str, Any]:
    result = PolicyEngine().evaluate(
        case_id=case_id,
        assessment=assessment,
        policy_pack=load_policy_pack(POLICIES_DIR / "ai_vendor_approval.v1.json"),
        evaluated_at=evaluated_at,
    )
    validate_canonical(result, "policy_result.v1.schema.json")
    return result


@lru_cache(maxsize=1)
def _static_snapshot() -> dict[str, Any]:
    case = _decision_case()
    manifest = load_golden_manifest()
    before_assessment = _load_json(
        REPOSITORY_ROOT / manifest["cases"]["T2"]["assessment_path"]
    )
    after_assessment = _post_f5_assessment()
    before_result = _evaluate(
        case_id=case["case_id"],
        assessment=before_assessment,
        evaluated_at="2026-07-19T10:55:00Z",
    )
    after_result = _evaluate(
        case_id=case["case_id"],
        assessment=after_assessment,
        evaluated_at="2026-07-19T11:05:00Z",
    )
    if before_result["state"] != "NEEDS_MORE_EVIDENCE":
        raise ValueError("DEMO pre-F5 route is not NEEDS_MORE_EVIDENCE")
    if after_result["state"] != "HUMAN_APPROVAL_REQUIRED":
        raise ValueError("DEMO post-F5 route is not HUMAN_APPROVAL_REQUIRED")
    if after_result["blocking_controls"]:
        raise ValueError("DEMO post-F5 route unexpectedly has blocking controls")
    if after_result["selected_approval_role"] != "director":
        raise ValueError("DEMO post-F5 route did not select director authority")

    policy_pack = _load_json(POLICIES_DIR / "ai_vendor_approval.v1.json")
    allowed_decisions = permitted_decisions(after_result)
    return {
        "mode": "DEMO",
        "company": "Caldera Works Europe S.A.S. (fictional)",
        "vendor": "NovaMind AI Ltd. (fictional)",
        "case": case,
        "assessment": after_assessment,
        "policy_result": after_result,
        "before_f5": {
            "assessment": before_assessment,
            "policy_result": before_result,
        },
        "evidence_diff": [
            {
                "label": "EU data residency",
                "fact_key": "privacy.eu_eea_only_residency_confirmed",
                "before": "UNKNOWN",
                "after": "PASS",
                "evidence_ref": "F5 · section 1",
            },
            {
                "label": "Issued assurance report",
                "fact_key": "security.assurance_report_issued",
                "before": "NOT ISSUED",
                "after": "PASS",
                "evidence_ref": "F5 · section 2",
            },
        ],
        "policy": {
            "policy_version": policy_pack["policy_version"],
            "rules": policy_pack["rules"],
        },
        "actions": {
            "allowed": [
                decision
                for decision in (
                    "approve",
                    "approve_with_conditions",
                    "reject",
                    "request_evidence",
                )
                if decision in allowed_decisions
            ],
            "prohibited": ["approve_without_condition", "waive_blocking_control"],
        },
        "provenance": {
            "source_documents": {
                "origin": "build_week_repository_fixtures",
                "classification": "fictional_build_week_work",
                "repository_paths": [
                    f"fixtures/documents/{document['filename']}"
                    for document in case["documents"]
                ],
                "authenticity_verified": False,
            },
            "demo_assessment": {
                "execution_mode": "DEMO",
                "assessment_source": DEMO_ASSESSMENT_SOURCE,
                "base_artifact_path": DEMO_BASE_ASSESSMENT_PATH,
                "derivation_version": DEMO_DERIVATION_VERSION,
                "runtime_model_call": False,
                "used_for_current_demo": True,
            },
            "live_assessment": {
                "execution_mode": "LIVE",
                "assessment_source": "gpt_generated_live",
                "provider": "openai",
                "model": "gpt-5.6",
                "prompt_version": "vendor-assessment/v2",
                "artifact_path": LIVE_ARTIFACT_PATH,
                "runtime_model_call": True,
                "used_for_current_demo": False,
            },
            "human_approval": {
                "source": "human_entered_at_runtime",
                "human_entered_fields": [
                    "approver.display_name",
                    "conditions[0].text",
                    "justification",
                ],
                "identity_assurance": "declared_only",
            },
            "aelitium_outputs": {
                "source": "aelitium_generated",
                "artifacts": [
                    "policy_result",
                    "canonical_hashes",
                    "signature",
                    "decision_receipt",
                    "verification_result",
                ],
            },
            "limitations": TRUST_LIMITATIONS,
        },
        "trust_notice": (
            "Verification establishes integrity and signature validity under a "
            "separately trusted key. It does not prove source-document authenticity, "
            "truth, correctness, fairness, legal validity, identity authentication, "
            "or trusted time."
        ),
    }


def build_demo_snapshot() -> dict[str, Any]:
    """Return an isolated copy so API or UI callers cannot mutate cached fixtures."""

    return copy.deepcopy(_static_snapshot())


def _current_decision_hashes(
    snapshot: dict[str, Any],
) -> tuple[str, str, str]:
    try:
        case = snapshot["case"]
        assessment = snapshot["assessment"]
        policy_result = snapshot["policy_result"]
        validate_canonical(case, "decision_case.v1.schema.json")
        validate_canonical(assessment, "model_assessment.v1.schema.json")
        validate_canonical(policy_result, "policy_result.v1.schema.json")
    except (CanonicalSchemaError, KeyError, TypeError) as exc:
        raise ApprovalAuthorizationError(
            "CURRENT_DECISION_INVALID",
            "current server-held decision inputs are invalid",
        ) from exc

    if policy_result["case_id"] != case["case_id"]:
        raise ApprovalAuthorizationError(
            "CURRENT_POLICY_CASE_MISMATCH",
            "current policy result does not belong to the current decision case",
        )
    assessment_hash = hash_json(normalize_assessment(assessment))
    if policy_result["assessment_hash"] != assessment_hash:
        raise ApprovalAuthorizationError(
            "CURRENT_ASSESSMENT_MISMATCH",
            "current assessment does not match the current policy result",
        )
    return (
        hash_json(case),
        assessment_hash,
        hash_json(normalize_policy_result(policy_result)),
    )


def create_demo_approval(
    *,
    snapshot: dict[str, Any],
    display_name: str,
    approver_role: str,
    justification: str,
    condition: str,
    decided_at: str | None = None,
) -> dict[str, Any]:
    policy_result = snapshot["policy_result"]
    _, _, policy_result_hash = _current_decision_hashes(snapshot)
    validate_policy_receipt_eligibility(policy_result)

    display_name = display_name.strip()
    approver_role = approver_role.strip()
    justification = justification.strip()
    condition = condition.strip()
    if not display_name or not approver_role or not justification or not condition:
        raise ValueError(
            "display name, approver role, justification, and condition are required"
        )

    approval = {
        "schema_version": "human-approval/v1",
        "approval_id": f"approval-demo-{secrets.token_hex(6)}",
        "case_id": snapshot["case"]["case_id"],
        "policy_result_hash": policy_result_hash,
        "approver": {
            "declared_id": "demo-director-01",
            "display_name": display_name,
            "role": approver_role,
            "identity_assurance": "declared_only",
        },
        "decision": "approve_with_conditions",
        "conditions": [
            {
                "condition_id": "condition-renegotiate-subprocessors",
                "text": condition,
                "owner_role": "operations_reviewer",
                "due_event": "before contract renewal",
            }
        ],
        "requested_evidence": [],
        "justification": justification,
        "override": False,
        "override_controls": [],
        "decision_evidence_refs": [
            {
                "document_id": "F4",
                "locator": "page 23, clause 9.6",
                "note": "Contractual conflict accepted only with remediation condition.",
            },
            {
                "document_id": "F5",
                "locator": "sections 1 and 2",
                "note": "Residency and issued-assurance evidence accepted.",
            },
        ],
        "decided_at": decided_at or _utc_now(),
    }
    validate_canonical(approval, "human_approval.v1.schema.json")
    validate_authoritative_approval(
        policy_result=policy_result,
        policy_result_hash=policy_result_hash,
        approval=approval,
    )
    return approval


def record_demo_approval(
    *, approval: dict[str, Any], snapshot: dict[str, Any]
) -> RecordedDemoApproval:
    """Bind a canonical approval to the current server-held decision inputs."""

    validate_canonical(approval, "human_approval.v1.schema.json")
    case_hash, assessment_hash, policy_result_hash = _current_decision_hashes(
        snapshot
    )
    validate_authoritative_approval(
        policy_result=snapshot["policy_result"],
        policy_result_hash=policy_result_hash,
        approval=approval,
    )
    stored = copy.deepcopy(approval)
    return RecordedDemoApproval(
        approval=stored,
        approval_hash=hash_json(stored),
        case_hash=case_hash,
        assessment_hash=assessment_hash,
        policy_result_hash=policy_result_hash,
    )


def _receipt_materials(
    *, case: dict[str, Any], policy_result: dict[str, Any], approval: dict[str, Any]
) -> ReceiptMaterials:
    policy_pack = _load_json(POLICIES_DIR / "ai_vendor_approval.v1.json")
    return ReceiptMaterials(
        policy_pack=policy_pack,
        prompt_text=DEMO_DERIVATION_DESCRIPTION,
        assessment_schema=load_schema("model_assessment.v1.schema.json"),
        model_request={
            "record_type": "no_model_request",
            "case_id": case["case_id"],
            "document_hashes": [document["sha256"] for document in case["documents"]],
            "execution_mode": "DEMO",
            "assessment_source": DEMO_ASSESSMENT_SOURCE,
            "runtime_model_call": False,
            "base_artifact_path": DEMO_BASE_ASSESSMENT_PATH,
            "derivation_version": DEMO_DERIVATION_VERSION,
            "schema_version": "model-assessment/v1",
        },
        timeline_events=[
            {"event_type": "case_created", "occurred_at": case["created_at"]},
            {
                "event_type": "documents_added",
                "occurred_at": "2026-07-18T12:00:00Z",
            },
            {
                "event_type": "evidence_added",
                "occurred_at": "2026-07-19T11:00:00Z",
                "document_id": "F5",
            },
            {
                "event_type": "assessment_recorded",
                "occurred_at": "2026-07-19T11:04:00Z",
            },
            {
                "event_type": "policy_evaluated",
                "occurred_at": policy_result["evaluated_at"],
            },
            {
                "event_type": "human_approved",
                "occurred_at": approval["decided_at"],
            },
        ],
    )


def _load_signing_material(
    *, private_key_path: Path, keyring_path: Path
) -> tuple[Ed25519PrivateKey, TrustedKeyring]:
    try:
        mode = private_key_path.stat().st_mode & 0o777
        if mode & 0o077:
            raise DemoConfigurationError("DEMO private key permissions must be 0600")
        private_key = load_private_key(private_key_path)
        keyring = load_trusted_keyring(keyring_path)
    except DemoConfigurationError:
        raise
    except (OSError, ValueError) as exc:
        raise DemoConfigurationError("DEMO signing material is unavailable or invalid") from exc

    trusted_key = keyring.resolve(DEMO_KEY_ID)
    fingerprint = public_key_fingerprint(private_key.public_key())
    if trusted_key is None or trusted_key.fingerprint_sha256 != fingerprint:
        raise DemoConfigurationError(
            "DEMO private key does not match the externally trusted keyring"
        )
    return private_key, keyring


def issue_demo_receipt(
    *,
    recorded_approval: RecordedDemoApproval,
    snapshot: dict[str, Any],
    private_key_path: Path = DEMO_PRIVATE_KEY_PATH,
    keyring_path: Path = DEMO_KEYRING_PATH,
    issued_at: str | None = None,
) -> IssuedDemoReceipt:
    try:
        current_approval_hash = hash_json(recorded_approval.approval)
    except (TypeError, ValueError) as exc:
        raise ApprovalAuthorizationError(
            "APPROVAL_RECORD_MODIFIED",
            "server-recorded approval changed after admission",
        ) from exc
    if current_approval_hash != recorded_approval.approval_hash:
        raise ApprovalAuthorizationError(
            "APPROVAL_RECORD_MODIFIED",
            "server-recorded approval changed after admission",
        )
    try:
        validate_canonical(recorded_approval.approval, "human_approval.v1.schema.json")
    except CanonicalSchemaError as exc:
        raise ApprovalAuthorizationError(
            "APPROVAL_RECORD_INVALID",
            "server-recorded approval no longer satisfies its canonical schema",
        ) from exc
    case = snapshot["case"]
    assessment = snapshot["assessment"]
    policy_result = snapshot["policy_result"]
    case_hash, assessment_hash, policy_result_hash = _current_decision_hashes(
        snapshot
    )
    validate_policy_receipt_eligibility(policy_result)

    approval = recorded_approval.approval
    if approval["case_id"] != case["case_id"]:
        raise ApprovalAuthorizationError(
            "APPROVAL_CASE_MISMATCH",
            "server-recorded approval belongs to another decision case",
        )
    if (
        recorded_approval.case_hash != case_hash
        or recorded_approval.assessment_hash != assessment_hash
        or recorded_approval.policy_result_hash != policy_result_hash
    ):
        raise ApprovalAuthorizationError(
            "APPROVAL_STALE",
            "server-recorded approval is not bound to the current decision inputs",
        )
    validate_authoritative_approval(
        policy_result=policy_result,
        policy_result_hash=policy_result_hash,
        approval=approval,
    )
    approval = copy.deepcopy(approval)
    materials = _receipt_materials(
        case=case, policy_result=policy_result, approval=approval
    )
    content = build_decision_content(
        case=case,
        execution_mode="DEMO",
        assessment_source=DEMO_ASSESSMENT_SOURCE,
        runtime_model_call=False,
        provider="repository-fixture",
        model="demo-precomputed",
        model_config=[],
        prompt_version=DEMO_DERIVATION_VERSION,
        model_assessment=assessment,
        policy_result=policy_result,
        human_approval=approval,
        materials=materials,
    )
    private_key, keyring = _load_signing_material(
        private_key_path=private_key_path, keyring_path=keyring_path
    )
    receipt = issue_receipt(
        decision_content=content,
        receipt_id=f"rec-demo-{secrets.token_hex(8)}",
        issued_at=issued_at or _utc_now(),
        key_id=DEMO_KEY_ID,
        private_key=private_key,
    )
    return IssuedDemoReceipt(receipt, materials, keyring)


def verify_demo_receipt(
    receipt: dict[str, Any],
    *,
    materials: ReceiptMaterials,
    keyring: TrustedKeyring,
) -> VerificationResult:
    return verify_receipt(receipt, materials=materials, keyring=keyring)
