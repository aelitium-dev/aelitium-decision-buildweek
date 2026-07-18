from __future__ import annotations

import json

import pytest

from aelitium_decision.demo import load_golden_manifest, run_demo_case
from aelitium_decision.paths import REPOSITORY_ROOT
from aelitium_decision.policy import PolicyEngine, load_policy_pack
from aelitium_decision.schema_validation import CanonicalSchemaError, validate_canonical


@pytest.mark.parametrize(
    ("case_name", "expected_state", "expected_blocking"),
    [
        ("T1", "READY_FOR_APPROVAL", []),
        (
            "T2",
            "NEEDS_MORE_EVIDENCE",
            ["R2_EU_DATA_RESIDENCY", "R4_CERTIFICATION"],
        ),
        ("T3", "HUMAN_REVIEW", []),
    ],
)
def test_golden_case_routes(case_name, expected_state, expected_blocking):
    result = run_demo_case(case_name)

    assert result["mode"] == "DEMO"
    assert result["assessment_valid"] is True
    assert result["policy_result_valid"] is True
    assert all(result["golden_checks"].values())
    assert result["policy_result"]["state"] == expected_state
    assert [
        item["control_id"] for item in result["policy_result"]["blocking_controls"]
    ] == expected_blocking


def test_t3_has_material_conflict():
    manifest = load_golden_manifest()
    path = REPOSITORY_ROOT / manifest["cases"]["T3"]["assessment_path"]
    assessment = json.loads(path.read_text(encoding="utf-8"))

    assert assessment["conflicts"]
    refs = assessment["conflicts"][0]["evidence_refs"]
    assert {ref["document_id"] for ref in refs} == {"F3", "F4"}


def test_model_recommendation_cannot_waive_blocking_controls():
    manifest = load_golden_manifest()
    case = manifest["cases"]["T2"]
    assessment = json.loads(
        (REPOSITORY_ROOT / case["assessment_path"]).read_text(encoding="utf-8")
    )
    assessment["recommendation"]["rationale"] = "The model recommends approval now."
    assessment["recommendation"]["conditions"] = []
    policy_pack = load_policy_pack(REPOSITORY_ROOT / manifest["policy_path"])

    result = PolicyEngine().evaluate(
        case_id=case["case_id"],
        assessment=assessment,
        policy_pack=policy_pack,
        evaluated_at=case["evaluated_at"],
    )

    assert result["state"] == "NEEDS_MORE_EVIDENCE"
    assert {item["control_id"] for item in result["blocking_controls"]} == {
        "R2_EU_DATA_RESIDENCY",
        "R4_CERTIFICATION",
    }
    assert "current written offer" not in result["suggested_request"]


def test_model_cannot_supply_policy_thresholds():
    manifest = load_golden_manifest()
    assessment_path = REPOSITORY_ROOT / manifest["cases"]["T2"]["assessment_path"]
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    assessment["confidence_floor"] = 0

    with pytest.raises(CanonicalSchemaError, match="confidence_floor"):
        validate_canonical(assessment, manifest["assessment_schema"])


def test_policy_pack_has_exactly_six_rules():
    manifest = load_golden_manifest()
    pack = load_policy_pack(REPOSITORY_ROOT / manifest["policy_path"])

    assert len(pack.rules) == 6
    assert pack.rules[0].expected_value == 15000
    assert pack.rules[-1].expected_value == 70


def test_demo_result_is_deterministic():
    assert run_demo_case("T2") == run_demo_case("T2")
