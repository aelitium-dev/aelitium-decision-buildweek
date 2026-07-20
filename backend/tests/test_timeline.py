from __future__ import annotations

import copy

import pytest

from aelitium_decision.demo_workflow import build_demo_snapshot
from aelitium_decision.receipt import ReceiptBuildError, build_timeline_commitment
from aelitium_decision.timeline import (
    ZERO_HASH,
    DecisionTimelineLog,
    TimelineContractError,
    build_demo_timeline,
    origin,
    reference,
    validate_timeline_payload,
)


def _initial_timeline():
    return build_demo_timeline(build_demo_snapshot())


def _append_runtime_events(log: DecisionTimelineLog) -> None:
    log.append(
        event_type="HUMAN_APPROVAL_RECORDED",
        state="APPROVE_WITH_CONDITIONS",
        occurred_at="2026-07-20T10:00:00Z",
        origin=origin("declared_human", "demo-director-01", "DEMO"),
        summary="Authoritative director approval recorded.",
        references=[
            reference("approval", "approval-demo-test", "a" * 64),
            reference("policy_result", "policy-result-post-f5", "b" * 64),
            reference("role", "director", None),
        ],
    )
    log.append(
        event_type="RECEIPT_ISSUED",
        state="ISSUED",
        occurred_at="2026-07-20T10:00:01Z",
        origin=origin(
            "receipt_builder", "aelitium-ed25519-receipt-builder", "DEMO"
        ),
        summary="Decision Receipt issued.",
        references=[
            reference("receipt", "rec-demo-test", "c" * 64),
            reference("approval", "approval-demo-test", "a" * 64),
        ],
    )
    log.append(
        event_type="RECEIPT_VERIFIED",
        state="VALID",
        occurred_at="2026-07-20T10:00:02Z",
        origin=origin(
            "integrity_verifier", "aelitium-local-integrity-verifier", "DEMO"
        ),
        summary="Receipt verification returned VALID: VERIFIED.",
        references=[
            reference("receipt", "rec-demo-test", "c" * 64),
            reference("verification_result", "VERIFIED", None),
        ],
    )


def test_initial_demo_timeline_is_complete_ordered_and_source_accurate():
    timeline = _initial_timeline().snapshot()

    assert timeline["event_count"] == 9
    assert [event["event_type"] for event in timeline["events"]] == [
        "CASE_CREATED",
        "EVIDENCE_INGESTED",
        "ASSESSMENT_RECORDED",
        "POLICY_EVALUATED",
        "ROUTING_DECIDED",
        "EVIDENCE_INGESTED",
        "ASSESSMENT_RECORDED",
        "POLICY_EVALUATED",
        "ROUTING_DECIDED",
    ]
    assert [event["sequence"] for event in timeline["events"]] == list(
        range(1, 10)
    )
    assert timeline["events"][0]["previous_event_hash"] == ZERO_HASH
    assert timeline["head_hash"] == timeline["events"][-1]["event_hash"]
    assert timeline["events"][3]["state"] == "NEEDS_MORE_EVIDENCE"
    assert timeline["events"][8]["state"] == "HUMAN_APPROVAL_REQUIRED"
    assert all(
        event["origin"]["execution_mode"] == "DEMO"
        for event in timeline["events"]
    )
    assessment_events = [
        event
        for event in timeline["events"]
        if event["event_type"] == "ASSESSMENT_RECORDED"
    ]
    assert all(
        event["origin"]["origin_type"] == "precomputed_assessment"
        for event in assessment_events
    )
    assert all("no model call" in event["summary"] for event in assessment_events)
    initial_document_ids = {
        item["reference_id"]
        for item in timeline["events"][1]["references"]
    }
    assert initial_document_ids == {"F1", "F2", "F3", "F4"}
    assert timeline["events"][5]["references"][0]["reference_id"] == "F5"


def test_initial_demo_timeline_is_deterministic():
    first = _initial_timeline().snapshot()
    second = _initial_timeline().snapshot()

    assert first == second
    assert first["head_hash"] == (
        "730d944d16330773e63381c922f036010cfb5eaaa6fa7de03ffddbee0caffd5d"
    )


def test_runtime_events_extend_the_chain_without_changing_prior_events():
    log = _initial_timeline()
    before = log.snapshot()

    _append_runtime_events(log)
    after = log.snapshot()

    assert after["events"][:9] == before["events"]
    assert after["event_count"] == 12
    assert [event["event_type"] for event in after["events"][-3:]] == [
        "HUMAN_APPROVAL_RECORDED",
        "RECEIPT_ISSUED",
        "RECEIPT_VERIFIED",
    ]
    assert after["events"][-1]["state"] == "VALID"
    assert after["head_hash"] != before["head_hash"]


def test_receipt_commitment_uses_the_validated_timeline_head():
    log = _initial_timeline()
    log.append(
        event_type="HUMAN_APPROVAL_RECORDED",
        state="APPROVE_WITH_CONDITIONS",
        occurred_at="2026-07-20T10:00:00Z",
        origin=origin("declared_human", "demo-director-01", "DEMO"),
        summary="Authoritative director approval recorded.",
        references=[
            reference("approval", "approval-demo-test", "a" * 64),
            reference("policy_result", "policy-result-post-f5", "b" * 64),
            reference("role", "director", None),
        ],
    )
    timeline = log.snapshot()

    assert build_timeline_commitment(log.receipt_events()) == {
        "event_count": 10,
        "head_hash": timeline["head_hash"],
    }


def test_append_rejects_a_timestamp_that_moves_backwards():
    log = _initial_timeline()

    with pytest.raises(TimelineContractError) as caught:
        log.append(
            event_type="HUMAN_APPROVAL_RECORDED",
            state="APPROVE_WITH_CONDITIONS",
            occurred_at="2026-07-18T09:00:00Z",
            origin=origin("declared_human", "demo-director-01", "DEMO"),
            summary="Out-of-order approval.",
            references=[
                reference("approval", "approval-demo-test", "a" * 64),
                reference("policy_result", "policy-result-post-f5", "b" * 64),
                reference("role", "director", None),
            ],
        )

    assert caught.value.code == "TIMELINE_ORDER_INVALID"
    assert log.snapshot()["event_count"] == 9


def test_append_rejects_an_origin_incompatible_with_the_event_type():
    log = _initial_timeline()

    with pytest.raises(TimelineContractError) as caught:
        log.append(
            event_type="HUMAN_APPROVAL_RECORDED",
            state="APPROVE_WITH_CONDITIONS",
            occurred_at="2026-07-20T10:00:00Z",
            origin=origin(
                "deterministic_policy_engine", "vendor-policy-v1", "DEMO"
            ),
            summary="Invalid origin.",
            references=[
                reference("approval", "approval-demo-test", "a" * 64),
                reference("policy_result", "policy-result-post-f5", "b" * 64),
                reference("role", "director", None),
            ],
        )

    assert caught.value.code == "TIMELINE_ORIGIN_INCONSISTENT"


def test_append_rejects_incomplete_event_references():
    log = _initial_timeline()

    with pytest.raises(TimelineContractError) as caught:
        log.append(
            event_type="HUMAN_APPROVAL_RECORDED",
            state="APPROVE_WITH_CONDITIONS",
            occurred_at="2026-07-20T10:00:00Z",
            origin=origin("declared_human", "demo-director-01", "DEMO"),
            summary="Missing policy and role references.",
            references=[
                reference("approval", "approval-demo-test", "a" * 64),
            ],
        )

    assert caught.value.code == "TIMELINE_REFERENCES_INCOMPLETE"


def test_append_rejects_missing_object_commitments():
    log = _initial_timeline()

    with pytest.raises(TimelineContractError) as caught:
        log.append(
            event_type="HUMAN_APPROVAL_RECORDED",
            state="APPROVE_WITH_CONDITIONS",
            occurred_at="2026-07-20T10:00:00Z",
            origin=origin("declared_human", "demo-director-01", "DEMO"),
            summary="Approval references have no commitments.",
            references=[
                reference("approval", "approval-demo-test", None),
                reference("policy_result", "policy-result-post-f5", None),
                reference("role", "director", None),
            ],
        )

    assert caught.value.code == "TIMELINE_COMMITMENTS_INCOMPLETE"


def test_append_wraps_noncanonical_event_data_in_a_stable_error():
    log = _initial_timeline()
    malformed_reference = reference("approval", "approval-demo-test", "a" * 64)
    malformed_reference["commitment_sha256"] = 1.5  # type: ignore[assignment]

    with pytest.raises(TimelineContractError) as caught:
        log.append(
            event_type="HUMAN_APPROVAL_RECORDED",
            state="APPROVE_WITH_CONDITIONS",
            occurred_at="2026-07-20T10:00:00Z",
            origin=origin("declared_human", "demo-director-01", "DEMO"),
            summary="Noncanonical reference value.",
            references=[
                malformed_reference,
                reference("policy_result", "policy-result-post-f5", "b" * 64),
                reference("role", "director", None),
            ],
        )

    assert caught.value.code == "TIMELINE_EVENT_INVALID"


def test_demo_timeline_rejects_inconsistent_assessment_policy_sources():
    snapshot = build_demo_snapshot()
    snapshot["before_f5"]["policy_result"]["assessment_hash"] = "f" * 64

    with pytest.raises(TimelineContractError) as caught:
        build_demo_timeline(snapshot)

    assert caught.value.code == "TIMELINE_SOURCE_INVALID"


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (
            lambda payload: payload["events"][0].update(
                {"summary": "Silently altered summary."}
            ),
            "TIMELINE_EVENT_HASH_MISMATCH",
        ),
        (
            lambda payload: payload["events"][1].update({"sequence": 8}),
            "TIMELINE_SEQUENCE_INVALID",
        ),
        (
            lambda payload: payload["events"][2].update(
                {"case_id": "case-another-decision"}
            ),
            "TIMELINE_CASE_MISMATCH",
        ),
        (
            lambda payload: payload.update({"event_count": 999}),
            "TIMELINE_COUNT_MISMATCH",
        ),
        (
            lambda payload: payload.update({"head_hash": "f" * 64}),
            "TIMELINE_HEAD_MISMATCH",
        ),
    ],
)
def test_timeline_validation_fails_closed_for_inconsistent_payloads(mutate, reason):
    payload = copy.deepcopy(_initial_timeline().snapshot())
    mutate(payload)

    with pytest.raises(TimelineContractError) as caught:
        validate_timeline_payload(payload)

    assert caught.value.code == reason


def test_receipt_builder_rejects_mixed_timeline_contracts():
    events = _initial_timeline().receipt_events()
    events.append({"event_type": "legacy_event"})

    with pytest.raises(ReceiptBuildError, match="mixes incompatible"):
        build_timeline_commitment(events)
