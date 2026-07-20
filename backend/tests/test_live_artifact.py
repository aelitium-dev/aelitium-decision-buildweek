from __future__ import annotations

import json

from aelitium_decision.hashing import hash_json
from aelitium_decision.demo_workflow import build_demo_snapshot
from aelitium_decision.paths import REPOSITORY_ROOT
from aelitium_decision.policy import PolicyEngine, load_policy_pack
from aelitium_decision.schema_validation import validate_canonical


LIVE_ARTIFACT_PATH = (
    REPOSITORY_ROOT / "fixtures/live/gpt-5.6-t2-assessment.json"
)
POLICY_PATH = REPOSITORY_ROOT / "policies/ai_vendor_approval.v1.json"
LIVE_INPUT_ASSESSMENT_HASH = (
    "55fe5993c5ec2aeb466052c61ed97e15dc60e3777b4d6469d55fb3a7203e4ca4"
)
LIVE_LITERAL_REPAIR_HASH = (
    "1db3baa0d9e5d60706e426c77e33ca221924f6dd12409c6ee46e0eec4785892a"
)
LIVE_CURRENT_ASSESSMENT_HASH = (
    "3b5863bb233c433c935a6dce7f670c0c2df4ee54751784116bdc24809d58f3c2"
)


def test_checked_in_live_artifact_is_canonical_and_routes_fail_closed():
    artifact = json.loads(LIVE_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assessment = artifact["assessment"]

    assert artifact["artifact_version"] == "aelitium-live-assessment/v1"
    assert artifact["execution_mode"] == "LIVE"
    assert artifact["assessment_source"] == "gpt_generated_live"
    assert artifact["runtime_model_call"] is True
    assert artifact["provider"] == "openai"
    assert artifact["model"] == "gpt-5.6"
    assert artifact["prompt_version"] == "vendor-assessment/v2"
    assert assessment["model"] == artifact["model"]
    assert assessment["prompt_version"] == artifact["prompt_version"]
    validate_canonical(assessment, "model_assessment.v1.schema.json")
    assert hash_json(assessment) == artifact["assessment_hash"]
    assert artifact["assessment_hash"] == LIVE_CURRENT_ASSESSMENT_HASH
    assert artifact["post_validation_transformations"] == [
        {
            "transformation_version": "literal-evidence-repair/v1",
            "scope": (
                "quoted_text exact-source repair and evidence-reference splitting only"
            ),
            "input_assessment_hash": LIVE_INPUT_ASSESSMENT_HASH,
            "output_assessment_hash": LIVE_LITERAL_REPAIR_HASH,
            "original_non_literal_quote_fields": 19,
        },
        {
            "transformation_version": "fictional-vendor-rename/v1",
            "scope": "fictional vendor and product names only",
            "input_assessment_hash": LIVE_LITERAL_REPAIR_HASH,
            "output_assessment_hash": LIVE_CURRENT_ASSESSMENT_HASH,
        }
    ]
    assert artifact["source_documents"] == {
        "origin": "build_week_repository_fixtures",
        "classification": "fictional_build_week_work",
        "repository_paths": [
            "fixtures/documents/F1_vendor_commercial_proposal.md",
            "fixtures/documents/F2_internal_procurement_policy.md",
            "fixtures/documents/F3_security_questionnaire.md",
            "fixtures/documents/F4_executed_data_processing_addendum.md",
        ],
        "authenticity_verified": False,
    }

    result = PolicyEngine().evaluate(
        case_id="live-smoke-t2",
        assessment=assessment,
        policy_pack=load_policy_pack(POLICY_PATH),
        evaluated_at=artifact["executed_at"],
    )

    assert result["state"] == "NEEDS_MORE_EVIDENCE"
    assert [
        control["control_id"] for control in result["blocking_controls"]
    ] == [
        "R2_EU_DATA_RESIDENCY",
        "R3_DPA_SIGNED",
        "R4_CERTIFICATION",
    ]

    # Prompt v2 did not supply the policy pack's exact fact-key catalog. The
    # engine therefore treats its four fact-driven controls as missing and
    # fails closed. Keep this visible so the route is never misreported as
    # evidence of fact-to-policy mapping accuracy.
    fact_rule_results = result["rules_evaluated"][:4]
    assert all(rule["result"] == "FAIL" for rule in fact_rule_results)
    assert all(rule["observed_value"] is None for rule in fact_rule_results)


def test_demo_snapshot_references_live_artifact_without_using_it():
    artifact = json.loads(LIVE_ARTIFACT_PATH.read_text(encoding="utf-8"))
    provenance = build_demo_snapshot()["provenance"]
    live = provenance["live_assessment"]

    assert live == {
        "execution_mode": artifact["execution_mode"],
        "assessment_source": artifact["assessment_source"],
        "provider": artifact["provider"],
        "model": artifact["model"],
        "prompt_version": artifact["prompt_version"],
        "artifact_path": "fixtures/live/gpt-5.6-t2-assessment.json",
        "runtime_model_call": artifact["runtime_model_call"],
        "post_validation_transformations": artifact[
            "post_validation_transformations"
        ],
        "used_for_current_demo": False,
    }
    assert provenance["demo_assessment"]["runtime_model_call"] is False
    assert provenance["demo_assessment"]["used_for_current_demo"] is True
