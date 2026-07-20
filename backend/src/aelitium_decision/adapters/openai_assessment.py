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

Before canonical validation, ``normalize_transport_identifiers`` may lowercase
only identifier tokens that already match their required prefix and grammar
case-insensitively (for example ``FACT-001`` → ``fact-001``). It works on a copy,
rejects missing/unsafe IDs and normalization collisions, and keeps recommendation
references consistent. It never changes evidence, findings, free text, fact keys,
or ``control_hint``; semantic contract failures remain canonical validation errors.

Prompt v3 also gives the model an exact-use vocabulary for the four fact keys
consumed by the Vendor Approval Policy Pack. That vocabulary affects extraction
instructions only: it contains no policy thresholds, free-form keys remain valid
for other facts, and the adapter never maps semantic aliases into policy keys.
The prompt also states format constraints that the Structured Outputs subset
cannot express, including the lowercase ``snake_case`` risk-category pattern.
The adapter never repairs risk categories; full canonical backend validation
remains authoritative.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from openai import OpenAI

from aelitium_decision.hashing import hash_json, sha256_text
from aelitium_decision.schema_validation import load_schema, validate_canonical


MODEL_ASSESSMENT_SCHEMA = "model_assessment.v1.schema.json"
DEFAULT_MODEL = "gpt-5.6"
DEFAULT_PROMPT_VERSION = "vendor-assessment/v3.1"

VENDOR_APPROVAL_FACT_KEY_CATALOG = (
    (
        "annual recurring price in EUR as an integer",
        "commercial.annual_price_eur",
    ),
    (
        "written EU/EEA-only residency confirmation for customer content, "
        "backups, and core processing as a boolean",
        "privacy.eu_eea_only_residency_confirmed",
    ),
    (
        "DPA execution by both parties as a boolean",
        "privacy.dpa_executed_by_both_parties",
    ),
    (
        "issued SOC 2 Type II or equivalent assurance report as a boolean",
        "security.assurance_report_issued",
    ),
)

_IDENTIFIER_COLLECTIONS = (
    ("facts", "fact_id", "fact"),
    ("conflicts", "conflict_id", "conflict"),
    ("missing_evidence", "item_id", "missing"),
    ("risks", "risk_id", "risk"),
    ("options", "option_id", "option"),
)

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


@dataclass(frozen=True)
class AssessmentRun:
    """Canonical assessment plus non-secret transport provenance for one call."""

    assessment: dict[str, Any]
    provider_response_id: str | None
    provider_output_sha256: str
    request_configuration: dict[str, Any]
    identifier_case_normalization_applied: bool


def build_assessment_instructions(*, model: str, prompt_version: str) -> str:
    """Build the versioned extraction prompt, including exact policy fact keys."""

    catalog = " ".join(
        f"- {concept}: '{fact_key}'."
        for concept, fact_key in VENDOR_APPROVAL_FACT_KEY_CATALOG
    )
    return (
        "Extract evidence-backed facts, conflicts, missing evidence, risks, "
        "and decision options. Do not make the final decision, alter policy "
        "thresholds, or waive controls. Use lowercase identifier tokens with "
        "these exact prefix forms: fact_id 'fact-001', conflict_id "
        "'conflict-001', missing_evidence item_id 'missing-001', risk_id "
        "'risk-001', and option_id 'option-001'. recommendation.option_id "
        "must exactly equal one option_id. control_hint is one control-token, "
        "never prose or a citation; for example 'R2_EU_DATA_RESIDENCY'. Put "
        "explanations in description, requested_evidence, or evidence_refs. "
        "Every risks[].category must be a lowercase snake_case token matching "
        "the exact pattern ^[a-z][a-z0-9_]{1,63}$; for example "
        "'security_assurance' or 'international_transfers'. Spaces, hyphens, "
        "uppercase letters, and prose are invalid in category. "
        "For the Vendor Approval Policy Pack, whenever supplied evidence "
        "addresses one of the following four concepts, emit exactly one fact "
        "using its listed fact_key and typed value; do not use a synonym or "
        f"alias for that concept. {catalog} "
        "A boolean is true only when the supplied evidence establishes the "
        "listed proposition; otherwise use false when the evidence establishes "
        "the contrary, or omit that catalog fact and report missing evidence "
        "when no value is established. Free-form fact_key values remain allowed "
        "for facts outside these four catalog concepts. Do not invent evidence "
        "or duplicate a catalog concept under another key. "
        f"Set model to {model!r} and prompt_version to {prompt_version!r}."
    )


def _normalize_prefixed_identifier(
    value: Any, *, prefix: str, location: str
) -> str:
    """Lowercase one already well-formed identifier; never infer or repair it."""

    if not isinstance(value, str):
        raise AssessmentGenerationError(f"{location} is not a string identifier")
    pattern = rf"{re.escape(prefix)}-[A-Za-z0-9][A-Za-z0-9-]{{0,63}}"
    if re.fullmatch(pattern, value, flags=re.IGNORECASE) is None:
        raise AssessmentGenerationError(
            f"{location} cannot be safely normalized as a {prefix}- identifier"
        )
    return value.lower()


def normalize_transport_identifiers(assessment: Any) -> dict[str, Any]:
    """Mechanically normalize safe ID casing before canonical validation.

    The transport schema deliberately omits unsupported ``pattern`` constraints.
    This boundary handles casing only when the required prefix and token grammar
    are already present. It rejects ambiguous repairs and duplicate IDs created by
    case folding. ``control_hint`` is intentionally outside this transformation.
    """

    if not isinstance(assessment, dict):
        raise AssessmentGenerationError("assessment root must be a JSON object")
    normalized = copy.deepcopy(assessment)
    normalized_options: set[str] = set()

    for collection_name, id_field, prefix in _IDENTIFIER_COLLECTIONS:
        collection = normalized.get(collection_name)
        if not isinstance(collection, list):
            raise AssessmentGenerationError(
                f"{collection_name} must be an array before ID normalization"
            )
        seen: set[str] = set()
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                raise AssessmentGenerationError(
                    f"{collection_name}.{index} must be an object"
                )
            location = f"{collection_name}.{index}.{id_field}"
            identifier = _normalize_prefixed_identifier(
                item.get(id_field), prefix=prefix, location=location
            )
            if identifier in seen:
                raise AssessmentGenerationError(
                    f"{collection_name} contains an ID collision after normalization: "
                    f"{identifier}"
                )
            item[id_field] = identifier
            seen.add(identifier)
        if collection_name == "options":
            normalized_options = seen

    recommendation = normalized.get("recommendation")
    if not isinstance(recommendation, dict):
        raise AssessmentGenerationError(
            "recommendation must be an object before ID normalization"
        )
    recommendation_id = _normalize_prefixed_identifier(
        recommendation.get("option_id"),
        prefix="option",
        location="recommendation.option_id",
    )
    if recommendation_id not in normalized_options:
        raise AssessmentGenerationError(
            "recommendation.option_id does not reference a normalized option"
        )
    recommendation["option_id"] = recommendation_id
    return normalized


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
        """Return only the canonical assessment for existing application callers."""

        return self.assess_with_provenance(case_context=case_context).assessment

    def assess_with_provenance(self, *, case_context: str) -> AssessmentRun:
        """Return a canonical assessment and auditable, non-secret call metadata."""

        instructions = build_assessment_instructions(
            model=self.model,
            prompt_version=self.prompt_version,
        )
        format_configuration = {
            "type": "json_schema",
            "name": "model_assessment_v1",
            "strict": True,
            "schema": self._api_schema,
        }
        response = self._client.responses.create(
            model=self.model,
            instructions=instructions,
            input=case_context,
            text={"format": format_configuration},
            store=False,
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise AssessmentGenerationError("Responses API returned no structured text")

        try:
            transported_assessment = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise AssessmentGenerationError("Responses API returned invalid JSON") from exc

        assessment = normalize_transport_identifiers(transported_assessment)
        validate_canonical(assessment, MODEL_ASSESSMENT_SCHEMA)
        if assessment["model"] != self.model:
            raise AssessmentGenerationError("assessment model metadata does not match request")
        if assessment["prompt_version"] != self.prompt_version:
            raise AssessmentGenerationError(
                "assessment prompt_version metadata does not match request"
            )
        response_id = getattr(response, "id", None)
        if response_id is not None and not isinstance(response_id, str):
            raise AssessmentGenerationError("Responses API returned a non-string response ID")

        return AssessmentRun(
            assessment=assessment,
            provider_response_id=response_id,
            provider_output_sha256=sha256_text(output_text),
            request_configuration={
                "endpoint": "responses.create",
                "model": self.model,
                "prompt_version": self.prompt_version,
                "store": False,
                "structured_outputs": {
                    "type": format_configuration["type"],
                    "name": format_configuration["name"],
                    "strict": format_configuration["strict"],
                },
                "instructions_sha256": sha256_text(instructions),
                "input_sha256": sha256_text(case_context),
                "canonical_schema_sha256": hash_json(self._canonical_schema),
                "transport_schema_sha256": hash_json(self._api_schema),
            },
            identifier_case_normalization_applied=(
                transported_assessment != assessment
            ),
        )
