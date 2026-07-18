from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import pytest

from aelitium_decision.adapters.openai_assessment import (
    DEFAULT_PROMPT_VERSION,
    AssessmentGenerationError,
    OpenAIAssessmentAdapter,
    derive_openai_response_schema,
    normalize_transport_identifiers,
)
from aelitium_decision.demo import load_golden_manifest
from aelitium_decision.paths import REPOSITORY_ROOT
from aelitium_decision.schema_validation import CanonicalSchemaError, load_schema


class FakeResponses:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output_text)


class FakeClient:
    def __init__(self, output_text: str) -> None:
        self.responses = FakeResponses(output_text)


def _t1_assessment():
    manifest = load_golden_manifest()
    path = REPOSITORY_ROOT / manifest["cases"]["T1"]["assessment_path"]
    return json.loads(path.read_text(encoding="utf-8"))


def _t2_assessment():
    manifest = load_golden_manifest()
    path = REPOSITORY_ROOT / manifest["cases"]["T2"]["assessment_path"]
    return json.loads(path.read_text(encoding="utf-8"))


def _with_live_metadata(assessment):
    assessment["model"] = "gpt-5.6"
    assessment["prompt_version"] = DEFAULT_PROMPT_VERSION
    return assessment


def _uppercase_transport_ids(assessment):
    fields = (
        ("facts", "fact_id"),
        ("conflicts", "conflict_id"),
        ("missing_evidence", "item_id"),
        ("risks", "risk_id"),
        ("options", "option_id"),
    )
    for collection, field in fields:
        for item in assessment[collection]:
            item[field] = item[field].upper()
    assessment["recommendation"]["option_id"] = assessment["recommendation"][
        "option_id"
    ].upper()
    return assessment


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def test_api_schema_is_derived_and_simplified():
    canonical = load_schema("model_assessment.v1.schema.json")
    derived = derive_openai_response_schema(canonical)
    keys = set(_walk_keys(derived))

    assert derived["additionalProperties"] is False
    assert derived["required"] == canonical["required"]
    assert derived["properties"]["schema_version"]["enum"] == [
        "model-assessment/v1"
    ]
    assert derived["properties"]["schema_version"]["type"] == "string"
    assert derived["$defs"]["conflict"]["properties"]["severity"]["type"] == "string"
    assert "const" not in keys
    assert "pattern" not in keys
    assert "format" not in keys
    assert "minLength" not in keys
    assert "maxItems" not in keys


def test_adapter_uses_responses_strict_schema_and_store_false():
    assessment = _with_live_metadata(_t1_assessment())
    client = FakeClient(json.dumps(assessment))
    adapter = OpenAIAssessmentAdapter(client=client)

    result = adapter.assess(case_context="fictional evidence")

    assert result == assessment
    call = client.responses.calls[0]
    assert call["model"] == "gpt-5.6"
    assert call["store"] is False
    assert call["text"]["format"]["type"] == "json_schema"
    assert call["text"]["format"]["strict"] is True
    assert "fact_id 'fact-001'" in call["instructions"]
    assert "conflict_id 'conflict-001'" in call["instructions"]
    assert "item_id 'missing-001'" in call["instructions"]
    assert "risk_id 'risk-001'" in call["instructions"]
    assert "option_id 'option-001'" in call["instructions"]
    assert "control_hint is one control-token" in call["instructions"]
    assert "'R2_EU_DATA_RESIDENCY'" in call["instructions"]
    assert DEFAULT_PROMPT_VERSION == "vendor-assessment/v2"


def test_canonical_schema_rejects_value_relaxed_for_api_transport():
    assessment = _with_live_metadata(_t1_assessment())
    assessment["case_summary"] = ""
    client = FakeClient(json.dumps(assessment))
    adapter = OpenAIAssessmentAdapter(client=client)

    with pytest.raises(CanonicalSchemaError, match="case_summary"):
        adapter.assess(case_context="fictional evidence")


def test_safe_transport_id_casing_is_normalized_before_canonical_validation():
    assessment = _with_live_metadata(_t2_assessment())
    original_control_hints = [
        item["control_hint"] for item in assessment["missing_evidence"]
    ]
    transported = _uppercase_transport_ids(copy.deepcopy(assessment))
    client = FakeClient(json.dumps(transported))

    result = OpenAIAssessmentAdapter(client=client).assess(
        case_context="fictional evidence"
    )

    for collection, field, prefix in (
        ("facts", "fact_id", "fact-"),
        ("conflicts", "conflict_id", "conflict-"),
        ("missing_evidence", "item_id", "missing-"),
        ("risks", "risk_id", "risk-"),
        ("options", "option_id", "option-"),
    ):
        assert all(item[field].startswith(prefix) for item in result[collection])
    assert result["recommendation"]["option_id"] == result["options"][0]["option_id"]
    assert [item["control_hint"] for item in result["missing_evidence"]] == (
        original_control_hints
    )
    assert result["facts"][0]["statement"] == assessment["facts"][0]["statement"]
    assert transported["facts"][0]["fact_id"].startswith("FACT-")


@pytest.mark.parametrize("unsafe_id", ["001", "fact_001", "risk-001", "fact-01!"])
def test_unsafe_transport_id_is_rejected_instead_of_invented(unsafe_id):
    assessment = _with_live_metadata(_t1_assessment())
    assessment["facts"][0]["fact_id"] = unsafe_id

    with pytest.raises(AssessmentGenerationError, match="cannot be safely normalized"):
        normalize_transport_identifiers(assessment)


def test_case_folding_collision_is_rejected():
    assessment = _with_live_metadata(_t1_assessment())
    duplicate = copy.deepcopy(assessment["facts"][0])
    duplicate["fact_id"] = assessment["facts"][0]["fact_id"].upper()
    assessment["facts"].append(duplicate)

    with pytest.raises(AssessmentGenerationError, match="ID collision"):
        normalize_transport_identifiers(assessment)


def test_recommendation_must_reference_an_existing_normalized_option():
    assessment = _with_live_metadata(_t1_assessment())
    assessment["recommendation"]["option_id"] = "OPTION-NOT-PRESENT"

    with pytest.raises(AssessmentGenerationError, match="does not reference"):
        normalize_transport_identifiers(assessment)


def test_control_hint_prose_is_not_normalized_and_fails_canonical_validation():
    assessment = _with_live_metadata(_t2_assessment())
    prose = "F2 section 3, customer-data control 1; F4 section 12.4"
    assessment["missing_evidence"][0]["control_hint"] = prose
    normalized = normalize_transport_identifiers(assessment)
    assert normalized["missing_evidence"][0]["control_hint"] == prose

    client = FakeClient(json.dumps(assessment))
    with pytest.raises(CanonicalSchemaError, match="control_hint"):
        OpenAIAssessmentAdapter(client=client).assess(
            case_context="fictional evidence"
        )
