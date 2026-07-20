"""Validated, append-only Decision Timeline for the DEMO workflow.

Events record actual repository-fixture, policy, human, receipt, and verifier
transitions.  Every event commits its complete validated payload, sequence, and
previous event hash.  The application timestamp is explicit but is not a
trusted-time assertion.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .hashing import CanonicalizationError, hash_json


TIMELINE_VERSION = "decision-timeline/v1"
EVENT_VERSION = "decision-timeline-event/v1"
ZERO_HASH = "0" * 64
TIMELINE_LIMITATIONS = [
    "application_timestamps_are_not_trusted_time",
    "demo_history_is_reconstructed_from_validated_repository_fixtures",
    "receipt_commitment_ends_before_receipt_issuance",
    "runtime_timeline_is_in_memory_and_resets_with_the_demo_server",
]

EventType = Literal[
    "CASE_CREATED",
    "EVIDENCE_INGESTED",
    "ASSESSMENT_RECORDED",
    "POLICY_EVALUATED",
    "ROUTING_DECIDED",
    "HUMAN_APPROVAL_RECORDED",
    "RECEIPT_ISSUED",
    "RECEIPT_VERIFIED",
]
OriginType = Literal[
    "repository_fixture",
    "precomputed_assessment",
    "openai_live_assessment",
    "deterministic_policy_engine",
    "declared_human",
    "receipt_builder",
    "integrity_verifier",
]
ReferenceType = Literal[
    "case",
    "document",
    "assessment",
    "policy_result",
    "control",
    "role",
    "approval",
    "receipt",
    "verification_result",
]


class TimelineContractError(RuntimeError):
    """Stable fail-closed timeline error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TimelineOrigin(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    origin_type: OriginType
    actor_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]{1,127}$")
    execution_mode: Literal["DEMO", "LIVE"]


class TimelineReference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    reference_type: ReferenceType
    reference_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}$")
    commitment_sha256: str | None = Field(
        pattern=r"^[0-9a-f]{64}$"
    )


class TimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["decision-timeline-event/v1"]
    event_id: str = Field(pattern=r"^event-[0-9]{4}-[a-z][a-z0-9-]{2,63}$")
    case_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
    sequence: int = Field(ge=1)
    event_type: EventType
    state: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,63}$")
    occurred_at: str = Field(
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    )
    origin: TimelineOrigin
    summary: str = Field(min_length=1, max_length=500)
    references: list[TimelineReference] = Field(min_length=1, max_length=64)
    previous_event_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    event_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class DecisionTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    timeline_version: Literal["decision-timeline/v1"]
    case_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
    event_count: int = Field(ge=1)
    head_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    events: list[TimelineEvent] = Field(min_length=1, max_length=512)
    limitations: list[str] = Field(min_length=1, max_length=16)


_VALID_STATES: dict[str, set[str] | None] = {
    "CASE_CREATED": {"DRAFT"},
    "EVIDENCE_INGESTED": {"EVIDENCE_INGESTED", "EVIDENCE_UPDATED"},
    "ASSESSMENT_RECORDED": {"ASSESSMENT_RECORDED"},
    "POLICY_EVALUATED": {
        "READY_FOR_APPROVAL",
        "NEEDS_MORE_EVIDENCE",
        "HUMAN_REVIEW",
        "HUMAN_APPROVAL_REQUIRED",
    },
    "ROUTING_DECIDED": {
        "READY_FOR_APPROVAL",
        "NEEDS_MORE_EVIDENCE",
        "HUMAN_REVIEW",
        "HUMAN_APPROVAL_REQUIRED",
    },
    "HUMAN_APPROVAL_RECORDED": {
        "APPROVE",
        "APPROVE_WITH_CONDITIONS",
        "REJECT",
        "REQUEST_EVIDENCE",
    },
    "RECEIPT_ISSUED": {"ISSUED"},
    "RECEIPT_VERIFIED": {"VALID", "INVALID"},
}
_VALID_ORIGINS: dict[str, set[str]] = {
    "CASE_CREATED": {"repository_fixture"},
    "EVIDENCE_INGESTED": {"repository_fixture"},
    "ASSESSMENT_RECORDED": {
        "precomputed_assessment",
        "openai_live_assessment",
    },
    "POLICY_EVALUATED": {"deterministic_policy_engine"},
    "ROUTING_DECIDED": {"deterministic_policy_engine"},
    "HUMAN_APPROVAL_RECORDED": {"declared_human"},
    "RECEIPT_ISSUED": {"receipt_builder"},
    "RECEIPT_VERIFIED": {"integrity_verifier"},
}
_REQUIRED_REFERENCES: dict[str, set[str]] = {
    "CASE_CREATED": {"case"},
    "EVIDENCE_INGESTED": {"document"},
    "ASSESSMENT_RECORDED": {"assessment"},
    "POLICY_EVALUATED": {"policy_result"},
    "ROUTING_DECIDED": {"policy_result"},
    "HUMAN_APPROVAL_RECORDED": {"approval", "policy_result", "role"},
    "RECEIPT_ISSUED": {"receipt", "approval"},
    "RECEIPT_VERIFIED": {"receipt", "verification_result"},
}
_REQUIRED_COMMITMENTS: dict[str, set[str]] = {
    "CASE_CREATED": {"case"},
    "EVIDENCE_INGESTED": {"document"},
    "ASSESSMENT_RECORDED": {"assessment"},
    "POLICY_EVALUATED": {"policy_result"},
    "ROUTING_DECIDED": {"policy_result"},
    "HUMAN_APPROVAL_RECORDED": {"approval", "policy_result"},
    "RECEIPT_ISSUED": {"receipt", "approval"},
    "RECEIPT_VERIFIED": set(),
}


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=UTC
        )
    except ValueError as exc:
        raise TimelineContractError(
            "TIMELINE_TIMESTAMP_INVALID", "timeline timestamp is not valid UTC"
        ) from exc
    return parsed


def _event_without_hash(event: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(event)
    payload.pop("event_hash", None)
    return payload


def _event_slug(event_type: str) -> str:
    return event_type.lower().replace("_", "-")


def _validate_event_semantics(
    event: dict[str, Any], prior_events: list[dict[str, Any]]
) -> None:
    event_type = event["event_type"]
    state = event["state"]
    allowed_states = _VALID_STATES[event_type]
    if allowed_states is not None and state not in allowed_states:
        raise TimelineContractError(
            "TIMELINE_STATE_INCONSISTENT",
            f"{event_type} cannot record state {state}",
        )
    if event["origin"]["origin_type"] not in _VALID_ORIGINS[event_type]:
        raise TimelineContractError(
            "TIMELINE_ORIGIN_INCONSISTENT",
            f"{event_type} has an incompatible origin",
        )
    reference_types = {
        reference["reference_type"] for reference in event["references"]
    }
    if not _REQUIRED_REFERENCES[event_type].issubset(reference_types):
        raise TimelineContractError(
            "TIMELINE_REFERENCES_INCOMPLETE",
            f"{event_type} is missing required references",
        )
    committed_reference_types = {
        reference["reference_type"]
        for reference in event["references"]
        if reference["commitment_sha256"] is not None
    }
    if not _REQUIRED_COMMITMENTS[event_type].issubset(
        committed_reference_types
    ):
        raise TimelineContractError(
            "TIMELINE_COMMITMENTS_INCOMPLETE",
            f"{event_type} is missing required object commitments",
        )
    reference_keys = [
        (reference["reference_type"], reference["reference_id"])
        for reference in event["references"]
    ]
    if len(reference_keys) != len(set(reference_keys)):
        raise TimelineContractError(
            "TIMELINE_REFERENCE_DUPLICATE",
            "timeline event references must be unique",
        )

    if event_type == "ROUTING_DECIDED":
        if (
            not prior_events
            or prior_events[-1]["event_type"] != "POLICY_EVALUATED"
            or prior_events[-1]["state"] != state
        ):
            raise TimelineContractError(
                "TIMELINE_ROUTING_INCONSISTENT",
                "routing must follow a matching policy evaluation",
            )
        if state == "HUMAN_APPROVAL_REQUIRED" and "role" not in reference_types:
            raise TimelineContractError(
                "TIMELINE_ROUTING_INCONSISTENT",
                "human approval routing must reference its selected role",
            )
        if state == "NEEDS_MORE_EVIDENCE" and "control" not in reference_types:
            raise TimelineContractError(
                "TIMELINE_ROUTING_INCONSISTENT",
                "evidence routing must reference its blocking controls",
            )
    if event_type == "HUMAN_APPROVAL_RECORDED":
        if not prior_events or prior_events[-1]["event_type"] != "ROUTING_DECIDED":
            raise TimelineContractError(
                "TIMELINE_APPROVAL_ORDER_INVALID",
                "human approval must follow deterministic routing",
            )
    if event_type == "RECEIPT_ISSUED":
        if (
            not prior_events
            or prior_events[-1]["event_type"] != "HUMAN_APPROVAL_RECORDED"
        ):
            raise TimelineContractError(
                "TIMELINE_RECEIPT_ORDER_INVALID",
                "receipt issuance must follow the recorded human approval",
            )
    if event_type == "RECEIPT_VERIFIED":
        receipt_ids = {
            reference["reference_id"]
            for reference in event["references"]
            if reference["reference_type"] == "receipt"
        }
        issued_ids = {
            reference["reference_id"]
            for prior in prior_events
            if prior["event_type"] == "RECEIPT_ISSUED"
            for reference in prior["references"]
            if reference["reference_type"] == "receipt"
        }
        if not receipt_ids.intersection(issued_ids):
            raise TimelineContractError(
                "TIMELINE_VERIFICATION_ORDER_INVALID",
                "verification must reference a receipt issued by this timeline",
            )


def validate_timeline_payload(payload: Any) -> dict[str, Any]:
    """Validate structure, chronology, semantics, and every hash link."""

    try:
        timeline = DecisionTimeline.model_validate(payload)
    except ValidationError as exc:
        raise TimelineContractError(
            "TIMELINE_SCHEMA_INVALID", "timeline does not satisfy its API contract"
        ) from exc
    normalized = timeline.model_dump(mode="json")
    events = normalized["events"]
    if normalized["event_count"] != len(events):
        raise TimelineContractError(
            "TIMELINE_COUNT_MISMATCH", "timeline event_count is inconsistent"
        )
    if normalized["limitations"] != TIMELINE_LIMITATIONS:
        raise TimelineContractError(
            "TIMELINE_LIMITATIONS_INVALID", "timeline limitations are inconsistent"
        )

    previous_hash = ZERO_HASH
    previous_time: datetime | None = None
    prior_events: list[dict[str, Any]] = []
    for sequence, event in enumerate(events, start=1):
        if event["case_id"] != normalized["case_id"]:
            raise TimelineContractError(
                "TIMELINE_CASE_MISMATCH", "timeline event belongs to another case"
            )
        if event["sequence"] != sequence:
            raise TimelineContractError(
                "TIMELINE_SEQUENCE_INVALID", "timeline sequence is not contiguous"
            )
        expected_id = f"event-{sequence:04d}-{_event_slug(event['event_type'])}"
        if event["event_id"] != expected_id:
            raise TimelineContractError(
                "TIMELINE_EVENT_ID_INVALID", "timeline event_id is not deterministic"
            )
        occurred_at = _parse_timestamp(event["occurred_at"])
        if previous_time is not None and occurred_at < previous_time:
            raise TimelineContractError(
                "TIMELINE_ORDER_INVALID", "timeline timestamps move backwards"
            )
        if event["previous_event_hash"] != previous_hash:
            raise TimelineContractError(
                "TIMELINE_PREVIOUS_HASH_MISMATCH",
                "timeline previous-event commitment is inconsistent",
            )
        expected_hash = hash_json(_event_without_hash(event))
        if event["event_hash"] != expected_hash:
            raise TimelineContractError(
                "TIMELINE_EVENT_HASH_MISMATCH",
                "timeline event commitment is inconsistent",
            )
        _validate_event_semantics(event, prior_events)
        prior_events.append(event)
        previous_hash = event["event_hash"]
        previous_time = occurred_at

    if normalized["head_hash"] != previous_hash:
        raise TimelineContractError(
            "TIMELINE_HEAD_MISMATCH", "timeline head_hash is inconsistent"
        )
    return normalized


class DecisionTimelineLog:
    """Append-only validated event chain for one case."""

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self._events: list[dict[str, Any]] = []

    def append(
        self,
        *,
        event_type: EventType,
        state: str,
        occurred_at: str,
        origin: dict[str, Any],
        summary: str,
        references: list[dict[str, Any]],
    ) -> dict[str, Any]:
        sequence = len(self._events) + 1
        event = {
            "schema_version": EVENT_VERSION,
            "event_id": f"event-{sequence:04d}-{_event_slug(event_type)}",
            "case_id": self.case_id,
            "sequence": sequence,
            "event_type": event_type,
            "state": state,
            "occurred_at": occurred_at,
            "origin": copy.deepcopy(origin),
            "summary": summary,
            "references": copy.deepcopy(references),
            "previous_event_hash": (
                self._events[-1]["event_hash"] if self._events else ZERO_HASH
            ),
        }
        try:
            event["event_hash"] = hash_json(event)
        except (CanonicalizationError, TypeError, ValueError) as exc:
            raise TimelineContractError(
                "TIMELINE_EVENT_INVALID",
                "timeline event is outside the canonical JSON contract",
            ) from exc
        candidate = self._payload([*self._events, event])
        normalized = validate_timeline_payload(candidate)
        stored = normalized["events"][-1]
        self._events.append(stored)
        return copy.deepcopy(stored)

    def _payload(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "timeline_version": TIMELINE_VERSION,
            "case_id": self.case_id,
            "event_count": len(events),
            "head_hash": events[-1]["event_hash"] if events else ZERO_HASH,
            "events": copy.deepcopy(events),
            "limitations": TIMELINE_LIMITATIONS,
        }

    def snapshot(self) -> dict[str, Any]:
        if not self._events:
            raise TimelineContractError(
                "TIMELINE_EMPTY", "decision timeline contains no events"
            )
        return validate_timeline_payload(self._payload(self._events))

    def receipt_events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self.snapshot()["events"])


def origin(
    origin_type: OriginType, actor_id: str, execution_mode: Literal["DEMO", "LIVE"]
) -> dict[str, str]:
    return {
        "origin_type": origin_type,
        "actor_id": actor_id,
        "execution_mode": execution_mode,
    }


def reference(
    reference_type: ReferenceType,
    reference_id: str,
    commitment_sha256: str | None,
) -> dict[str, str | None]:
    return {
        "reference_type": reference_type,
        "reference_id": reference_id,
        "commitment_sha256": commitment_sha256,
    }


def _policy_references(
    policy_result: dict[str, Any], label: str
) -> list[dict[str, str | None]]:
    references = [
        reference("policy_result", label, hash_json(policy_result))
    ]
    references.extend(
        reference("control", control["control_id"], None)
        for control in sorted(
            policy_result["blocking_controls"], key=lambda item: item["control_id"]
        )
    )
    selected_role = policy_result["selected_approval_role"]
    if selected_role is not None:
        references.append(reference("role", selected_role, None))
    return references


def build_demo_timeline(snapshot: dict[str, Any]) -> DecisionTimelineLog:
    """Derive the initial DEMO history from validated workflow objects."""

    try:
        case = snapshot["case"]
        before = snapshot["before_f5"]
        after_assessment = snapshot["assessment"]
        after_policy = snapshot["policy_result"]
        documents = sorted(case["documents"], key=lambda item: item["document_id"])
        initial_documents = [item for item in documents if item["document_id"] != "F5"]
        later_document = next(item for item in documents if item["document_id"] == "F5")
        before_assessment = before["assessment"]
        before_policy = before["policy_result"]
    except (KeyError, StopIteration, TypeError) as exc:
        raise TimelineContractError(
            "TIMELINE_SOURCE_INVALID", "DEMO workflow objects are incomplete"
        ) from exc
    if not initial_documents:
        raise TimelineContractError(
            "TIMELINE_SOURCE_INVALID", "DEMO has no initial evidence documents"
        )
    document_ids = [item["document_id"] for item in documents]
    if len(document_ids) != len(set(document_ids)) or document_ids.count("F5") != 1:
        raise TimelineContractError(
            "TIMELINE_SOURCE_INVALID", "DEMO evidence identifiers are inconsistent"
        )
    try:
        source_consistent = (
            before_policy["case_id"] == case["case_id"]
            and after_policy["case_id"] == case["case_id"]
            and before_policy["assessment_hash"] == hash_json(before_assessment)
            and after_policy["assessment_hash"] == hash_json(after_assessment)
        )
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise TimelineContractError(
            "TIMELINE_SOURCE_INVALID",
            "DEMO timeline sources are outside the canonical JSON contract",
        ) from exc
    if not source_consistent:
        raise TimelineContractError(
            "TIMELINE_SOURCE_INVALID",
            "DEMO assessments and policy results are not cross-consistent",
        )
    initial_times = {item["added_at"] for item in initial_documents}
    if len(initial_times) != 1:
        raise TimelineContractError(
            "TIMELINE_SOURCE_INVALID",
            "initial DEMO evidence does not form one ingestion batch",
        )

    log = DecisionTimelineLog(case["case_id"])
    log.append(
        event_type="CASE_CREATED",
        state="DRAFT",
        occurred_at=case["created_at"],
        origin=origin("repository_fixture", "aelitium-demo-loader", "DEMO"),
        summary=f"Decision case {case['case_id']} created from the DEMO fixture.",
        references=[
            reference(
                "case",
                case["case_id"],
                hash_json(
                    {
                        "case_id": case["case_id"],
                        "created_at": case["created_at"],
                        "decision_domain": case["decision_domain"],
                    }
                ),
            )
        ],
    )
    log.append(
        event_type="EVIDENCE_INGESTED",
        state="EVIDENCE_INGESTED",
        occurred_at=next(iter(initial_times)),
        origin=origin("repository_fixture", "aelitium-demo-loader", "DEMO"),
        summary=f"{len(initial_documents)} initial source documents ingested.",
        references=[
            reference("document", item["document_id"], item["sha256"])
            for item in initial_documents
        ],
    )
    log.append(
        event_type="ASSESSMENT_RECORDED",
        state="ASSESSMENT_RECORDED",
        occurred_at=before_policy["evaluated_at"],
        origin=origin(
            "precomputed_assessment", "demo-t2-precomputed-fixture", "DEMO"
        ),
        summary=(
            "Pre-F5 assessment recorded from the checked-in fixture; no model "
            "call executed."
        ),
        references=[
            reference(
                "assessment",
                "assessment-pre-f5",
                before_policy["assessment_hash"],
            )
        ],
    )
    log.append(
        event_type="POLICY_EVALUATED",
        state=before_policy["state"],
        occurred_at=before_policy["evaluated_at"],
        origin=origin(
            "deterministic_policy_engine", before_policy["policy_version"], "DEMO"
        ),
        summary=(
            f"Deterministic policy evaluation returned {before_policy['state']}."
        ),
        references=_policy_references(before_policy, "policy-result-pre-f5")[:1],
    )
    log.append(
        event_type="ROUTING_DECIDED",
        state=before_policy["state"],
        occurred_at=before_policy["evaluated_at"],
        origin=origin(
            "deterministic_policy_engine", before_policy["policy_version"], "DEMO"
        ),
        summary=(
            f"Routing retained {len(before_policy['blocking_controls'])} blocking "
            "controls and requested more evidence."
        ),
        references=_policy_references(before_policy, "policy-result-pre-f5"),
    )
    log.append(
        event_type="EVIDENCE_INGESTED",
        state="EVIDENCE_UPDATED",
        occurred_at=later_document["added_at"],
        origin=origin("repository_fixture", "aelitium-demo-loader", "DEMO"),
        summary="Later vendor assurance evidence F5 ingested.",
        references=[
            reference(
                "document",
                later_document["document_id"],
                later_document["sha256"],
            )
        ],
    )
    log.append(
        event_type="ASSESSMENT_RECORDED",
        state="ASSESSMENT_RECORDED",
        occurred_at=after_policy["evaluated_at"],
        origin=origin(
            "precomputed_assessment", "demo-fixture-derivation-v1", "DEMO"
        ),
        summary=(
            "Post-F5 assessment deterministically derived from checked-in DEMO "
            "fixtures; no model call executed."
        ),
        references=[
            reference(
                "assessment",
                "assessment-post-f5",
                after_policy["assessment_hash"],
            )
        ],
    )
    log.append(
        event_type="POLICY_EVALUATED",
        state=after_policy["state"],
        occurred_at=after_policy["evaluated_at"],
        origin=origin(
            "deterministic_policy_engine", after_policy["policy_version"], "DEMO"
        ),
        summary=(
            f"Deterministic policy evaluation returned {after_policy['state']}."
        ),
        references=_policy_references(after_policy, "policy-result-post-f5")[:1],
    )
    log.append(
        event_type="ROUTING_DECIDED",
        state=after_policy["state"],
        occurred_at=after_policy["evaluated_at"],
        origin=origin(
            "deterministic_policy_engine", after_policy["policy_version"], "DEMO"
        ),
        summary=(
            "Routing selected director as the single authoritative approver; "
            "no blocking controls remained."
        ),
        references=_policy_references(after_policy, "policy-result-post-f5"),
    )
    return log


def timeline_commitment_from_events(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    if not events:
        raise TimelineContractError(
            "TIMELINE_EMPTY", "receipt timeline contains no events"
        )
    payload = {
        "timeline_version": TIMELINE_VERSION,
        "case_id": events[0].get("case_id"),
        "event_count": len(events),
        "head_hash": events[-1].get("event_hash"),
        "events": copy.deepcopy(events),
        "limitations": TIMELINE_LIMITATIONS,
    }
    normalized = validate_timeline_payload(payload)
    return {
        "event_count": normalized["event_count"],
        "head_hash": normalized["head_hash"],
    }
