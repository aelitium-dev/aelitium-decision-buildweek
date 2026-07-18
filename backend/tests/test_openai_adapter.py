from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from aelitium_decision.adapters.openai_assessment import (
    OpenAIAssessmentAdapter,
    derive_openai_response_schema,
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
    assessment = _t1_assessment()
    assessment["model"] = "gpt-5.6"
    client = FakeClient(json.dumps(assessment))
    adapter = OpenAIAssessmentAdapter(client=client)

    result = adapter.assess(case_context="fictional evidence")

    assert result == assessment
    call = client.responses.calls[0]
    assert call["model"] == "gpt-5.6"
    assert call["store"] is False
    assert call["text"]["format"]["type"] == "json_schema"
    assert call["text"]["format"]["strict"] is True


def test_canonical_schema_rejects_value_relaxed_for_api_transport():
    assessment = _t1_assessment()
    assessment["model"] = "gpt-5.6"
    assessment["case_summary"] = ""
    client = FakeClient(json.dumps(assessment))
    adapter = OpenAIAssessmentAdapter(client=client)

    with pytest.raises(CanonicalSchemaError, match="case_summary"):
        adapter.assess(case_context="fictional evidence")
