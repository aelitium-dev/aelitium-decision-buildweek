"""Run one T2-style GPT-5.6 smoke assessment and save a reviewable artifact.

The script reads ``OPENAI_API_KEY`` from the process environment only. It does
not load dotenv files, echo request headers, print the key, or persist it. The
adapter performs strict Structured Outputs transport validation followed by
mandatory validation against the full canonical backend schema.

This is intentionally a manual, paid-network gate. Do not invoke it from tests.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from importlib.metadata import version

from aelitium_decision.adapters.openai_assessment import (
    DEFAULT_MODEL,
    DEFAULT_PROMPT_VERSION,
    AssessmentRun,
    OpenAIAssessmentAdapter,
)
from aelitium_decision.hashing import hash_json
from aelitium_decision.paths import FIXTURES_DIR


SOURCE_DOCUMENTS = (
    "F1_vendor_commercial_proposal.md",
    "F2_internal_procurement_policy.md",
    "F3_security_questionnaire.md",
    "F4_executed_data_processing_addendum.md",
)
ARTIFACT_PATH = FIXTURES_DIR / "live" / "gpt-5.6-t2-assessment.json"


def build_t2_context() -> str:
    sections = [
        "Fictional AI vendor approval case. Assess all supplied F1–F4 evidence. "
        "F5 has not been supplied. Treat missing written evidence as missing; "
        "do not infer it and do not make the final decision."
    ]
    document_dir = FIXTURES_DIR / "documents"
    for filename in SOURCE_DOCUMENTS:
        content = (document_dir / filename).read_text(encoding="utf-8")
        sections.append(f"\n--- {filename} ---\n{content}")
    return "\n".join(sections)


def build_live_artifact(*, run: AssessmentRun, executed_at: str) -> dict:
    """Build a non-secret provenance record after canonical validation succeeds."""

    return {
        "artifact_version": "aelitium-live-assessment/v2",
        "assessment_source": "gpt_generated_live",
        "execution_mode": "LIVE",
        "runtime_model_call": True,
        "scenario": "T2-style F1–F4 missing-evidence case",
        "executed_at": executed_at,
        "model": run.request_configuration["model"],
        "provider": "openai",
        "provider_response_id": run.provider_response_id,
        "provider_sdk": {
            "package": "openai",
            "version": version("openai"),
        },
        "provider_assessment_hash": hash_json(run.assessment),
        "prompt_version": run.request_configuration["prompt_version"],
        "request_configuration": run.request_configuration,
        "response_transport": {
            "provider_output_sha256": run.provider_output_sha256,
            "identifier_case_normalization_applied": (
                run.identifier_case_normalization_applied
            ),
        },
        "post_validation_transformations": [],
        "source_documents": {
            "origin": "build_week_repository_fixtures",
            "classification": "fictional_build_week_work",
            "repository_paths": [
                f"fixtures/documents/{filename}" for filename in SOURCE_DOCUMENTS
            ],
            "authenticity_verified": False,
        },
        "assessment_hash": hash_json(run.assessment),
        "assessment": run.assessment,
    }


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("LIVE_SMOKE_NOT_RUN: OPENAI_API_KEY is not set", file=sys.stderr)
        return 2

    try:
        run = OpenAIAssessmentAdapter(api_key=api_key).assess_with_provenance(
            case_context=build_t2_context()
        )
    except Exception as exc:  # report API/schema failure without leaking the key
        safe_message = str(exc).replace(api_key, "[REDACTED]")
        print(
            f"LIVE_SMOKE_FAILED: {type(exc).__name__}: {safe_message}",
            file=sys.stderr,
        )
        return 1

    artifact = build_live_artifact(
        run=run,
        executed_at=datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    )
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "LIVE_SMOKE_OK "
        f"model={DEFAULT_MODEL} prompt_version={DEFAULT_PROMPT_VERSION} "
        f"assessment_hash={artifact['assessment_hash']} "
        f"artifact={ARTIFACT_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
