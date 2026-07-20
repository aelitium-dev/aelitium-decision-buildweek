from __future__ import annotations

import importlib.metadata
import json
import re

from backend.scripts.live_smoke import build_t2_context

from aelitium_decision.adapters.openai_assessment import (
    DEFAULT_MODEL,
    DEFAULT_PROMPT_VERSION,
    VENDOR_APPROVAL_FACT_KEY_CATALOG,
    build_assessment_instructions,
    derive_openai_response_schema,
)
from aelitium_decision.demo_workflow import build_demo_snapshot
from aelitium_decision.hashing import hash_json, sha256_text
from aelitium_decision.paths import REPOSITORY_ROOT
from aelitium_decision.policy import PolicyEngine, load_policy_pack
from aelitium_decision.schema_validation import load_schema, validate_canonical


LIVE_ARTIFACT_PATH = (
    REPOSITORY_ROOT / "fixtures/live/gpt-5.6-t2-assessment.json"
)
POLICY_PATH = REPOSITORY_ROOT / "policies/ai_vendor_approval.v1.json"
LIVE_PROVIDER_ASSESSMENT_HASH = (
    "5f4c37d53a6573c060527db3d46994a53dc76455b54420f6eb9f0a50badc9789"
)
LIVE_CURRENT_ASSESSMENT_HASH = (
    "b59cdb611035cb900d35d871c08046a74bf7938b88294df5b9ca48907feff8a3"
)


def test_checked_in_live_artifact_is_canonical_and_has_recomputable_provenance():
    artifact = json.loads(LIVE_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assessment = artifact["assessment"]

    assert artifact["artifact_version"] == "aelitium-live-assessment/v2"
    assert artifact["execution_mode"] == "LIVE"
    assert artifact["assessment_source"] == "gpt_generated_live"
    assert artifact["runtime_model_call"] is True
    assert artifact["provider"] == "openai"
    assert artifact["model"] == DEFAULT_MODEL == "gpt-5.6"
    assert artifact["prompt_version"] == DEFAULT_PROMPT_VERSION == (
        "vendor-assessment/v3.1"
    )
    assert assessment["model"] == artifact["model"]
    assert assessment["prompt_version"] == artifact["prompt_version"]
    validate_canonical(assessment, "model_assessment.v1.schema.json")
    assert hash_json(assessment) == artifact["assessment_hash"]
    assert artifact["assessment_hash"] == LIVE_CURRENT_ASSESSMENT_HASH
    assert artifact["provider_assessment_hash"] == LIVE_PROVIDER_ASSESSMENT_HASH
    assert artifact["post_validation_transformations"] == [
        {
            "transformation_version": "literal-evidence-repair/v1",
            "scope": "quoted_text exact-source repair only",
            "input_assessment_hash": LIVE_PROVIDER_ASSESSMENT_HASH,
            "output_assessment_hash": LIVE_CURRENT_ASSESSMENT_HASH,
            "original_non_literal_quote_fields": 1,
        }
    ]
    assert re.fullmatch(r"resp_[A-Za-z0-9]+", artifact["provider_response_id"])
    assert artifact["provider_sdk"] == {
        "package": "openai",
        "version": importlib.metadata.version("openai"),
    }
    request = artifact["request_configuration"]
    canonical_schema = load_schema("model_assessment.v1.schema.json")
    assert request == {
        "canonical_schema_sha256": hash_json(canonical_schema),
        "endpoint": "responses.create",
        "input_sha256": sha256_text(build_t2_context()),
        "instructions_sha256": sha256_text(
            build_assessment_instructions(
                model=DEFAULT_MODEL,
                prompt_version=DEFAULT_PROMPT_VERSION,
            )
        ),
        "model": DEFAULT_MODEL,
        "prompt_version": DEFAULT_PROMPT_VERSION,
        "store": False,
        "structured_outputs": {
            "name": "model_assessment_v1",
            "strict": True,
            "type": "json_schema",
        },
        "transport_schema_sha256": hash_json(
            derive_openai_response_schema(canonical_schema)
        ),
    }
    assert artifact["response_transport"][
        "identifier_case_normalization_applied"
    ] is False
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        artifact["response_transport"]["provider_output_sha256"],
    )
    serialized = json.dumps(artifact)
    assert re.search(r"\bsk-[A-Za-z0-9_-]{20,}\b", serialized) is None
    private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
    assert private_key_marker not in serialized
    assert "OPENAI_API_KEY" not in serialized
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


def test_live_controlled_facts_drive_the_actual_policy_route():
    artifact = json.loads(LIVE_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assessment = artifact["assessment"]
    facts_by_key = {fact["fact_key"]: fact for fact in assessment["facts"]}
    catalog_keys = [key for _, key in VENDOR_APPROVAL_FACT_KEY_CATALOG]

    assert all(
        sum(fact["fact_key"] == key for fact in assessment["facts"]) == 1
        for key in catalog_keys
    )
    assert facts_by_key["commercial.annual_price_eur"]["value"] == {
        "boolean_value": None,
        "integer_value": 18000,
        "string_value": None,
        "value_type": "integer",
    }
    assert facts_by_key["privacy.eu_eea_only_residency_confirmed"]["value"][
        "boolean_value"
    ] is False
    assert facts_by_key["privacy.dpa_executed_by_both_parties"]["value"][
        "boolean_value"
    ] is True
    assert facts_by_key["security.assurance_report_issued"]["value"][
        "boolean_value"
    ] is False

    result = PolicyEngine().evaluate(
        case_id="case-live-smoke-t2",
        assessment=assessment,
        policy_pack=load_policy_pack(POLICY_PATH),
        evaluated_at=artifact["executed_at"],
    )
    validate_canonical(result, "policy_result.v1.schema.json")

    assert result["state"] == "NEEDS_MORE_EVIDENCE"
    assert result["selected_approval_role"] is None
    assert [
        control["control_id"] for control in result["blocking_controls"]
    ] == [
        "R2_EU_DATA_RESIDENCY",
        "R4_CERTIFICATION",
    ]
    fact_rule_results = result["rules_evaluated"][:4]
    assert [rule["result"] for rule in fact_rule_results] == [
        "FAIL",
        "FAIL",
        "PASS",
        "FAIL",
    ]
    assert [rule["observed_value"] for rule in fact_rule_results] == [
        18000,
        False,
        True,
        False,
    ]


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
