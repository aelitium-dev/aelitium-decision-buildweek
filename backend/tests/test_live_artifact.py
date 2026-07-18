from __future__ import annotations

import json

from aelitium_decision.hashing import hash_json
from aelitium_decision.paths import REPOSITORY_ROOT
from aelitium_decision.policy import PolicyEngine, load_policy_pack
from aelitium_decision.schema_validation import validate_canonical


LIVE_ARTIFACT_PATH = (
    REPOSITORY_ROOT / "fixtures/live/gpt-5.6-t2-assessment.json"
)
POLICY_PATH = REPOSITORY_ROOT / "policies/ai_vendor_approval.v1.json"


def test_checked_in_live_artifact_is_canonical_and_routes_fail_closed():
    artifact = json.loads(LIVE_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assessment = artifact["assessment"]

    assert artifact["artifact_version"] == "aelitium-live-assessment/v1"
    assert artifact["execution_mode"] == "LIVE"
    assert artifact["model"] == "gpt-5.6"
    assert artifact["prompt_version"] == "vendor-assessment/v2"
    assert assessment["model"] == artifact["model"]
    assert assessment["prompt_version"] == artifact["prompt_version"]
    validate_canonical(assessment, "model_assessment.v1.schema.json")
    assert hash_json(assessment) == artifact["assessment_hash"]

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
