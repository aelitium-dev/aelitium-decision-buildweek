from __future__ import annotations

import json

from backend.scripts.live_smoke import build_live_artifact

from aelitium_decision.adapters.openai_assessment import AssessmentRun
from aelitium_decision.demo import load_golden_manifest
from aelitium_decision.hashing import hash_json
from aelitium_decision.paths import REPOSITORY_ROOT


def test_v3_live_artifact_builder_records_non_secret_call_provenance():
    manifest = load_golden_manifest()
    assessment_path = REPOSITORY_ROOT / manifest["cases"]["T1"]["assessment_path"]
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    assessment["model"] = "gpt-5.6"
    assessment["prompt_version"] = "vendor-assessment/v3.1"
    request_configuration = {
        "endpoint": "responses.create",
        "model": "gpt-5.6",
        "prompt_version": "vendor-assessment/v3.1",
        "store": False,
        "structured_outputs": {
            "type": "json_schema",
            "name": "model_assessment_v1",
            "strict": True,
        },
        "instructions_sha256": "1" * 64,
        "input_sha256": "2" * 64,
        "canonical_schema_sha256": "3" * 64,
        "transport_schema_sha256": "4" * 64,
    }
    run = AssessmentRun(
        assessment=assessment,
        provider_response_id="resp_test_live",
        provider_output_sha256="5" * 64,
        request_configuration=request_configuration,
        identifier_case_normalization_applied=False,
    )

    artifact = build_live_artifact(
        run=run,
        executed_at="2026-07-20T12:00:00Z",
    )

    assert artifact["artifact_version"] == "aelitium-live-assessment/v2"
    assert artifact["provider_response_id"] == "resp_test_live"
    assert artifact["provider_assessment_hash"] == hash_json(assessment)
    assert artifact["provider_sdk"]["package"] == "openai"
    assert artifact["provider_sdk"]["version"]
    assert artifact["request_configuration"] == request_configuration
    assert artifact["response_transport"] == {
        "provider_output_sha256": "5" * 64,
        "identifier_case_normalization_applied": False,
    }
    assert artifact["assessment_hash"] == hash_json(assessment)
    assert artifact["post_validation_transformations"] == []
    serialized = json.dumps(artifact).lower()
    assert "openai_api_key" not in serialized
    assert "authorization" not in serialized
