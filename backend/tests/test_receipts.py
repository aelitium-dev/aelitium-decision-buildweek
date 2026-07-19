from __future__ import annotations

import base64
import copy
import json
from dataclasses import dataclass, replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from aelitium_decision.approval import ApprovalAuthorizationError
from aelitium_decision.demo import load_golden_manifest
from aelitium_decision.hashing import canonical_json, hash_json
from aelitium_decision.keyring import TrustedKeyring
from aelitium_decision.paths import FIXTURES_DIR, POLICIES_DIR
from aelitium_decision.policy import PolicyEngine, load_policy_pack
from aelitium_decision.receipt import (
    ReceiptMaterials,
    build_decision_content,
    issue_receipt,
    normalize_policy_result,
)
from aelitium_decision.schema_validation import (
    CanonicalSchemaError,
    load_schema,
    validate_canonical,
)
from aelitium_decision.signing import public_key_record
from aelitium_decision.verification import VerificationResult, verify_receipt


@dataclass
class ReceiptBundle:
    receipt: dict
    content: dict
    materials: ReceiptMaterials
    keyring: TrustedKeyring
    private_key: Ed25519PrivateKey
    case: dict
    assessment: dict
    policy_result: dict
    approval: dict


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _t4_assessment():
    manifest = load_golden_manifest()
    assessment = _load_json(
        manifest_path(manifest["cases"]["T2"]["assessment_path"])
    )
    assessment["case_summary"] = (
        "F1–F5 satisfy the blocking residency, DPA, and assurance controls; "
        "director approval and human conflict review remain required."
    )
    assessment["prompt_version"] = "demo-fixture-derivation/v1"
    facts = {fact["fact_key"]: fact for fact in assessment["facts"]}
    residency = facts["privacy.eu_eea_only_residency_confirmed"]
    residency["statement"] = "F5 confirms EU or EEA-only residency for the tenant."
    residency["value"]["value_type"] = "boolean"
    residency["value"]["boolean_value"] = True
    residency["evidence_refs"] = [
        {
            "document_id": "F5",
            "locator": "section 1",
            "quoted_text": "Customer Content, backups, and core processing will remain in the European Union or European Economic Area.",
            "reference_level": "validated_reference",
        }
    ]
    assurance = facts["security.assurance_report_issued"]
    assurance["statement"] = "F5 confirms the fictional assurance report was issued."
    assurance["value"]["boolean_value"] = True
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
            "summary": "The questionnaire and executed DPA conflict on subprocessor notice.",
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
            "preconditions": ["Director reviews the conflict and records a condition."],
        }
    ]
    assessment["recommendation"] = {
        "option_id": "option-conditional-approval",
        "rationale": "Evidence gates pass, but price and contractual conflict require human authority.",
        "conditions": ["Renegotiate the subprocessor clause before renewal."],
    }
    assessment["confidence"] = 93
    assessment["requires_human_review"] = True
    validate_canonical(assessment, "model_assessment.v1.schema.json")
    return assessment


def manifest_path(relative_path):
    from aelitium_decision.paths import REPOSITORY_ROOT

    return REPOSITORY_ROOT / relative_path


def _decision_case():
    manifest = _load_json(FIXTURES_DIR / "manifest.json")
    documents = []
    for document in manifest["documents"]:
        documents.append(
            {
                "document_id": document["document_id"],
                "document_type": document["document_type"],
                "filename": document["filename"],
                "media_type": "text/markdown",
                "sha256": document["sha256"],
                "version": document["version"],
                "added_at": "2026-07-18T12:00:00Z",
            }
        )
    case = {
        "schema_version": "decision-case/v1",
        "case_id": "case-t4-conditional-approval",
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


def _receipt_bundle() -> ReceiptBundle:
    case = _decision_case()
    assessment = _t4_assessment()
    policy_path = POLICIES_DIR / "ai_vendor_approval.v1.json"
    policy_pack_model = load_policy_pack(policy_path)
    policy_pack = _load_json(policy_path)
    policy_result = PolicyEngine().evaluate(
        case_id=case["case_id"],
        assessment=assessment,
        policy_pack=policy_pack_model,
        evaluated_at="2026-07-19T11:05:00Z",
    )
    validate_canonical(policy_result, "policy_result.v1.schema.json")
    assert policy_result["state"] == "HUMAN_APPROVAL_REQUIRED"
    assert policy_result["selected_approval_role"] == "director"
    assert policy_result["blocking_controls"] == []
    policy_result_hash = hash_json(normalize_policy_result(policy_result))
    approval = {
        "schema_version": "human-approval/v1",
        "approval_id": "approval-t4-director",
        "case_id": case["case_id"],
        "policy_result_hash": policy_result_hash,
        "approver": {
            "declared_id": "demo-director-01",
            "display_name": "Mara Ellison",
            "role": "director",
            "identity_assurance": "declared_only",
        },
        "decision": "approve_with_conditions",
        "conditions": [
            {
                "condition_id": "condition-renegotiate-subprocessors",
                "text": "Renegotiate the subprocessor clause before renewal.",
                "owner_role": "operations_reviewer",
                "due_event": "before contract renewal",
            }
        ],
        "requested_evidence": [],
        "justification": "Blocking evidence is complete; contractual conflict remains an explicit condition.",
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
        "decided_at": "2026-07-19T11:15:00Z",
    }
    validate_canonical(approval, "human_approval.v1.schema.json")
    prompt_text = (
        "Deterministically derive the post-F5 DEMO assessment from the checked-in "
        "T2 assessment fixture and fixed F5 evidence changes."
    )
    model_request = {
        "record_type": "no_model_request",
        "case_id": case["case_id"],
        "document_hashes": [document["sha256"] for document in case["documents"]],
        "execution_mode": "DEMO",
        "assessment_source": "precomputed_fixture",
        "runtime_model_call": False,
        "base_artifact_path": "fixtures/demo/T2_assessment.json",
        "derivation_version": "demo-fixture-derivation/v1",
        "schema_version": "model-assessment/v1",
    }
    timeline_events = [
        {"event_type": "case_created", "occurred_at": case["created_at"]},
        {"event_type": "documents_added", "occurred_at": "2026-07-18T12:00:00Z"},
        {"event_type": "assessment_recorded", "occurred_at": "2026-07-19T11:04:00Z"},
        {"event_type": "policy_evaluated", "occurred_at": policy_result["evaluated_at"]},
        {"event_type": "human_approved", "occurred_at": approval["decided_at"]},
    ]
    materials = ReceiptMaterials(
        policy_pack=policy_pack,
        prompt_text=prompt_text,
        assessment_schema=load_schema("model_assessment.v1.schema.json"),
        model_request=model_request,
        timeline_events=timeline_events,
    )
    content = build_decision_content(
        case=case,
        execution_mode="DEMO",
        assessment_source="precomputed_fixture",
        runtime_model_call=False,
        provider="repository-fixture",
        model="demo-precomputed",
        model_config=[],
        prompt_version="demo-fixture-derivation/v1",
        model_assessment=assessment,
        policy_result=policy_result,
        human_approval=approval,
        materials=materials,
    )
    private_key = Ed25519PrivateKey.generate()
    key_id = "buildweek-test-key"
    keyring = TrustedKeyring.from_payload(
        {
            "keyring_version": "aelitium-trusted-keyring/v1",
            "keys": [public_key_record(key_id, private_key.public_key())],
        }
    )
    receipt = issue_receipt(
        decision_content=content,
        receipt_id="rec-t4-demo-001",
        issued_at="2026-07-19T11:16:00Z",
        key_id=key_id,
        private_key=private_key,
    )
    return ReceiptBundle(
        receipt,
        content,
        materials,
        keyring,
        private_key,
        case,
        assessment,
        policy_result,
        approval,
    )


def test_t4_complete_approval_receipt_is_valid():
    bundle = _receipt_bundle()

    result = verify_receipt(
        bundle.receipt, keyring=bundle.keyring, materials=bundle.materials
    )

    assert result == VerificationResult("VALID", "VERIFIED")


def test_demo_receipt_commits_precomputed_fixture_provenance_without_model_call():
    bundle = _receipt_bundle()

    assert bundle.content["model_execution"] == {
        "execution_mode": "DEMO",
        "assessment_source": "precomputed_fixture",
        "runtime_model_call": False,
        "provider": "repository-fixture",
        "model": "demo-precomputed",
        "model_config": [],
        "prompt_version": "demo-fixture-derivation/v1",
        "prompt_hash": bundle.content["model_execution"]["prompt_hash"],
        "assessment_schema_version": "model-assessment/v1",
        "assessment_schema_hash": bundle.content["model_execution"][
            "assessment_schema_hash"
        ],
        "model_request_hash": bundle.content["model_execution"][
            "model_request_hash"
        ],
    }
    assert bundle.materials.model_request["record_type"] == "no_model_request"
    assert bundle.materials.model_request["runtime_model_call"] is False
    assert bundle.materials.model_request["assessment_source"] == (
        "precomputed_fixture"
    )
    parameter_names = {
        parameter["name"]
        for parameter in bundle.content["model_execution"]["model_config"]
    }
    assert not parameter_names & {"store", "structured_outputs"}


def test_receipt_schema_rejects_demo_claiming_a_runtime_model_call():
    bundle = _receipt_bundle()
    contradictory = copy.deepcopy(bundle.receipt)
    contradictory["decision_content"]["model_execution"][
        "runtime_model_call"
    ] = True

    with pytest.raises(CanonicalSchemaError, match="runtime_model_call"):
        validate_canonical(contradictory, "decision_receipt.v1.schema.json")


def test_verifier_rejects_external_assessment_input_with_false_provenance():
    bundle = _receipt_bundle()
    false_input = {
        **bundle.materials.model_request,
        "record_type": "model_request",
        "runtime_model_call": True,
    }
    inconsistent_content = copy.deepcopy(bundle.content)
    inconsistent_content["model_execution"]["model_request_hash"] = hash_json(
        false_input
    )
    receipt = issue_receipt(
        decision_content=inconsistent_content,
        receipt_id="rec-false-provenance-001",
        issued_at="2026-07-19T11:20:00Z",
        key_id="buildweek-test-key",
        private_key=bundle.private_key,
    )

    result = verify_receipt(
        receipt,
        keyring=bundle.keyring,
        materials=replace(bundle.materials, model_request=false_input),
    )

    assert result == VerificationResult(
        "INVALID", "ASSESSMENT_INPUT_PROVENANCE_MISMATCH"
    )


def test_content_hash_is_deterministic_and_excludes_receipt_issued_at():
    bundle = _receipt_bundle()
    hashes = [hash_json(bundle.content) for _ in range(3)]
    second = issue_receipt(
        decision_content=bundle.content,
        receipt_id="rec-t4-demo-002",
        issued_at="2026-07-19T11:17:00Z",
        key_id="buildweek-test-key",
        private_key=bundle.private_key,
    )

    assert len(set(hashes)) == 1
    assert (
        bundle.receipt["signed_receipt_payload"]["content_hash"]
        == second["signed_receipt_payload"]["content_hash"]
    )
    assert bundle.receipt["signature"] != second["signature"]
    assert verify_receipt(
        second, keyring=bundle.keyring, materials=bundle.materials
    ).valid


def _content_change(receipt):
    receipt["decision_content"]["case"]["case_version"] += 1


def _content_and_hash_change(receipt):
    _content_change(receipt)
    receipt["signed_receipt_payload"]["content_hash"] = hash_json(
        receipt["decision_content"]
    )


def _issued_at_change(receipt):
    receipt["signed_receipt_payload"]["issued_at"] = "2026-07-19T11:18:00Z"


def _signing_metadata_change(receipt):
    fingerprint = receipt["signed_receipt_payload"]["signing_metadata"][
        "public_key_fingerprint_sha256"
    ]
    receipt["signed_receipt_payload"]["signing_metadata"][
        "public_key_fingerprint_sha256"
    ] = ("0" if fingerprint[0] != "0" else "1") + fingerprint[1:]


def _signature_corruption(receipt):
    signature = bytearray(base64.b64decode(receipt["signature"]))
    signature[0] ^= 1
    receipt["signature"] = base64.b64encode(signature).decode("ascii")


def _added_field(receipt):
    receipt["unexpected"] = True


def _price_change(receipt):
    facts = receipt["decision_content"]["model_assessment"]["facts"]
    price = next(fact for fact in facts if fact["fact_key"] == "commercial.annual_price_eur")
    price["value"]["integer_value"] = 14000


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (_content_change, "CONTENT_HASH_MISMATCH"),
        (_content_and_hash_change, "SIGNATURE_INVALID"),
        (_issued_at_change, "SIGNATURE_INVALID"),
        (_signing_metadata_change, "KEY_FINGERPRINT_MISMATCH"),
        (_signature_corruption, "SIGNATURE_INVALID"),
        (_added_field, "SCHEMA_INVALID"),
        (_price_change, "ASSESSMENT_HASH_MISMATCH"),
    ],
)
def test_t5_tamper_matrix_is_invalid(mutator, reason):
    bundle = _receipt_bundle()
    tampered = copy.deepcopy(bundle.receipt)
    mutator(tampered)

    result = verify_receipt(tampered, keyring=bundle.keyring, materials=bundle.materials)

    assert result.status == "INVALID"
    assert result.reason == reason


@pytest.mark.parametrize(
    ("materials_mutator", "reason"),
    [
        (
            lambda materials: replace(
                materials,
                policy_pack={**materials.policy_pack, "description": "tampered"},
            ),
            "POLICY_RULES_HASH_MISMATCH",
        ),
        (
            lambda materials: replace(materials, prompt_text=materials.prompt_text + "!"),
            "PROMPT_HASH_MISMATCH",
        ),
        (
            lambda materials: replace(
                materials,
                assessment_schema={**materials.assessment_schema, "$comment": "tampered"},
            ),
            "ASSESSMENT_SCHEMA_HASH_MISMATCH",
        ),
        (
            lambda materials: replace(
                materials,
                model_request={**materials.model_request, "mode": "LIVE"},
            ),
            "MODEL_REQUEST_HASH_MISMATCH",
        ),
        (
            lambda materials: replace(
                materials,
                timeline_events=materials.timeline_events
                + [{"event_type": "tampered", "occurred_at": "2026-07-19T11:20:00Z"}],
            ),
            "TIMELINE_HEAD_MISMATCH",
        ),
    ],
)
def test_external_commitment_materials_are_recomputed(materials_mutator, reason):
    bundle = _receipt_bundle()
    materials = materials_mutator(bundle.materials)

    result = verify_receipt(
        bundle.receipt, keyring=bundle.keyring, materials=materials
    )

    assert result == VerificationResult("INVALID", reason)


def test_duplicate_json_keys_fail_before_schema_or_signature_checks():
    bundle = _receipt_bundle()
    raw = canonical_json(bundle.receipt)
    duplicate = '{"signature":"duplicate",' + raw[1:]

    assert verify_receipt(
        duplicate, keyring=bundle.keyring, materials=bundle.materials
    ) == VerificationResult("INVALID", "JSON_INVALID")


def test_approval_with_blocking_controls_cannot_be_receipted():
    bundle = _receipt_bundle()
    blocked_result = copy.deepcopy(bundle.policy_result)
    blocked_result["blocking_controls"] = [
        {
            "control_id": "R2_EU_DATA_RESIDENCY",
            "description": "Residency evidence required.",
            "missing_evidence": ["EU-only confirmation"],
            "suggested_request": "Provide EU-only confirmation.",
        }
    ]
    blocked_result["state"] = "NEEDS_MORE_EVIDENCE"
    blocked_approval = copy.deepcopy(bundle.approval)
    blocked_approval["policy_result_hash"] = hash_json(
        normalize_policy_result(blocked_result)
    )

    with pytest.raises(
        ApprovalAuthorizationError, match="POLICY_BLOCKING_CONTROLS"
    ):
        build_decision_content(
            case=bundle.case,
            execution_mode="DEMO",
            assessment_source="precomputed_fixture",
            runtime_model_call=False,
            provider="repository-fixture",
            model="demo-precomputed",
            model_config=bundle.content["model_execution"]["model_config"],
            prompt_version="demo-fixture-derivation/v1",
            model_assessment=bundle.assessment,
            policy_result=blocked_result,
            human_approval=blocked_approval,
            materials=bundle.materials,
        )
