"""Fail-closed authority checks for the single recorded human approval.

Approval routing selects one authoritative approval role. Control or condition
ownership does not create an additional approval requirement.
"""

from __future__ import annotations

from typing import Any


RECEIPT_ELIGIBLE_STATES = {
    "HUMAN_REVIEW",
    "READY_FOR_APPROVAL",
    "HUMAN_APPROVAL_REQUIRED",
}
ALL_DECISIONS = {
    "approve",
    "approve_with_conditions",
    "reject",
    "request_evidence",
}
NON_APPROVAL_DECISIONS = {"reject", "request_evidence"}


class ApprovalAuthorizationError(ValueError):
    """A stable fail-closed rejection at approval admission or receipt issuance."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def conditions_required_for_approval(policy_result: dict[str, Any]) -> bool:
    """Return whether an affirmative decision must carry explicit conditions."""

    return any(
        rule["result"] == "FAIL" and rule["effect"] == "REQUIRE_HUMAN_REVIEW"
        for rule in policy_result["rules_evaluated"]
    )


def permitted_decisions(policy_result: dict[str, Any]) -> set[str]:
    """Derive the human action boundary from deterministic policy output."""

    if (
        policy_result["state"] not in RECEIPT_ELIGIBLE_STATES
        or policy_result["blocking_controls"]
    ):
        return set()
    if conditions_required_for_approval(policy_result):
        return {"approve_with_conditions", *NON_APPROVAL_DECISIONS}
    return set(ALL_DECISIONS)


def validate_policy_receipt_eligibility(policy_result: dict[str, Any]) -> None:
    """Reject policy states that cannot authorize a final decision receipt."""

    if policy_result["blocking_controls"]:
        raise ApprovalAuthorizationError(
            "POLICY_BLOCKING_CONTROLS",
            "receipt issuance is prohibited while blocking controls remain",
        )
    if policy_result["state"] not in RECEIPT_ELIGIBLE_STATES:
        raise ApprovalAuthorizationError(
            "POLICY_STATE_NOT_RECEIPT_ELIGIBLE",
            f"policy state {policy_result['state']} does not permit receipt issuance",
        )
    if policy_result["selected_approval_role"] is None:
        raise ApprovalAuthorizationError(
            "APPROVAL_ROLE_UNAVAILABLE",
            "receipt-eligible policy state has no selected approval role",
        )


def validate_authoritative_approval(
    *,
    policy_result: dict[str, Any],
    policy_result_hash: str,
    approval: dict[str, Any],
) -> None:
    """Validate one authoritative HumanApproval against its current policy route."""

    validate_policy_receipt_eligibility(policy_result)

    if approval["case_id"] != policy_result["case_id"]:
        raise ApprovalAuthorizationError(
            "APPROVAL_CASE_MISMATCH",
            "approval and policy result belong to different decision cases",
        )
    if approval["policy_result_hash"] != policy_result_hash:
        raise ApprovalAuthorizationError(
            "APPROVAL_STALE",
            "approval is not bound to the current policy result",
        )

    selected_role = policy_result["selected_approval_role"]
    if approval["approver"]["role"] != selected_role:
        raise ApprovalAuthorizationError(
            "APPROVER_ROLE_NOT_AUTHORIZED",
            f"receipt issuance requires the selected approval role {selected_role}",
        )
    if approval["override"]:
        raise ApprovalAuthorizationError(
            "APPROVAL_OVERRIDE_NOT_PERMITTED",
            "the MVP receipt boundary does not permit control overrides",
        )

    decision = approval["decision"]
    if conditions_required_for_approval(policy_result) and decision in {
        "approve",
        "approve_with_conditions",
    }:
        if decision != "approve_with_conditions" or not approval["conditions"]:
            raise ApprovalAuthorizationError(
                "APPROVAL_CONDITIONS_REQUIRED",
                "the current policy result requires conditional approval",
            )
    if decision not in permitted_decisions(policy_result):
        raise ApprovalAuthorizationError(
            "APPROVAL_DECISION_NOT_PERMITTED",
            f"decision {decision} is not permitted by the current policy result",
        )
