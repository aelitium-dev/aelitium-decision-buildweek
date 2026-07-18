"""GPT-5.6 Responses API adapter with an explicit two-schema boundary.

The canonical ``model_assessment.v1.schema.json`` is the authoritative backend
contract. ``derive_openai_response_schema`` produces a transport-only Structured
Outputs variant: it preserves object shape, complete ``required`` arrays,
``additionalProperties: false``, types, enums, references, and array items while
removing compatibility-sensitive validation keywords such as patterns, formats,
and length/item/number bounds. ``const`` is represented as a typed single-value
``enum`` in that API variant.

Every parsed response is revalidated against the full canonical schema. A value
accepted by the API-call schema but rejected by the canonical schema fails closed;
the model cannot relax backend constraints, policy thresholds, or blocking rules.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Protocol

from openai import OpenAI

from aelitium_decision.schema_validation import load_schema, validate_canonical


MODEL_ASSESSMENT_SCHEMA = "model_assessment.v1.schema.json"
DEFAULT_MODEL = "gpt-5.6"
DEFAULT_PROMPT_VERSION = "vendor-assessment/v1"

_REMOVED_API_KEYWORDS = {
    "$schema",
    "$id",
    "title",
    "description",
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "minimum",
    "maximum",
    "multipleOf",
    "minItems",
    "maxItems",
    "uniqueItems",
}


class ResponsesClient(Protocol):
    class ResponsesResource(Protocol):
        def create(self, **kwargs: Any) -> Any: ...

    responses: ResponsesResource


class AssessmentGenerationError(RuntimeError):
    """Raised when the live adapter cannot return a canonical assessment."""


def derive_openai_response_schema(canonical_schema: dict[str, Any]) -> dict[str, Any]:
    """Derive the strict API-call subset without weakening backend validation."""

    def simplify(value: Any, *, names_are_data: bool = False) -> Any:
        if isinstance(value, list):
            return [simplify(item) for item in value]
        if not isinstance(value, dict):
            return copy.deepcopy(value)

        if names_are_data:
            return {key: simplify(item) for key, item in value.items()}

        result: dict[str, Any] = {}
        for key, item in value.items():
            if key in _REMOVED_API_KEYWORDS:
                continue
            if key == "const":
                result["enum"] = [copy.deepcopy(item)]
                if "type" not in value:
                    result["type"] = _json_type(item)
                continue
            result[key] = simplify(item, names_are_data=key in {"properties", "$defs"})
        if "enum" in result and "type" not in result:
            enum_types = list(dict.fromkeys(_json_type(item) for item in result["enum"]))
            result["type"] = enum_types[0] if len(enum_types) == 1 else enum_types
        return result

    derived = simplify(canonical_schema)
    _assert_closed_required_objects(derived)
    return derived


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(f"unsupported const value: {type(value).__name__}")


def _assert_closed_required_objects(schema: Any, location: str = "$") -> None:
    if isinstance(schema, list):
        for index, item in enumerate(schema):
            _assert_closed_required_objects(item, f"{location}[{index}]")
        return
    if not isinstance(schema, dict):
        return

    properties = schema.get("properties")
    if properties is not None:
        if schema.get("additionalProperties") is not False:
            raise ValueError(f"{location} must set additionalProperties to false")
        if set(schema.get("required", [])) != set(properties):
            raise ValueError(f"{location} must require every property")

    for key, value in schema.items():
        _assert_closed_required_objects(value, f"{location}.{key}")


class OpenAIAssessmentAdapter:
    """Generate an assessment with GPT-5.6 and revalidate it canonically."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: ResponsesClient | None = None,
        model: str = DEFAULT_MODEL,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ) -> None:
        self._client: ResponsesClient = client or OpenAI(api_key=api_key)
        self.model = model
        self.prompt_version = prompt_version
        self._canonical_schema = load_schema(MODEL_ASSESSMENT_SCHEMA)
        self._api_schema = derive_openai_response_schema(self._canonical_schema)

    def assess(self, *, case_context: str) -> dict[str, Any]:
        response = self._client.responses.create(
            model=self.model,
            instructions=(
                "Extract evidence-backed facts, conflicts, missing evidence, risks, "
                "and decision options. Do not make the final decision, alter policy "
                f"thresholds, or waive controls. Set model to {self.model!r} and "
                f"prompt_version to {self.prompt_version!r}."
            ),
            input=case_context,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "model_assessment_v1",
                    "strict": True,
                    "schema": self._api_schema,
                }
            },
            store=False,
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise AssessmentGenerationError("Responses API returned no structured text")

        try:
            assessment = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise AssessmentGenerationError("Responses API returned invalid JSON") from exc

        validate_canonical(assessment, MODEL_ASSESSMENT_SCHEMA)
        if assessment["model"] != self.model:
            raise AssessmentGenerationError("assessment model metadata does not match request")
        if assessment["prompt_version"] != self.prompt_version:
            raise AssessmentGenerationError(
                "assessment prompt_version metadata does not match request"
            )
        return assessment
