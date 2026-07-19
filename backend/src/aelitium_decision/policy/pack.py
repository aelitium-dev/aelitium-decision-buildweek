"""Strict, domain-neutral models for versioned policy packs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PolicyState = Literal[
    "NEEDS_MORE_EVIDENCE",
    "HUMAN_REVIEW",
    "READY_FOR_APPROVAL",
    "HUMAN_APPROVAL_REQUIRED",
]


class RoutingRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    priority: int = Field(ge=1)
    condition: Literal[
        "blocking_controls_not_empty",
        "director_approval_required",
        "human_review_required",
        "otherwise",
    ]
    state: PolicyState
    selected_approval_role: str | None = Field(
        pattern=r"^[a-z][a-z0-9_]{1,63}$"
    )


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    control_id: str
    version: str
    description: str
    operator: Literal[
        "fact_integer_at_most",
        "fact_boolean_equals",
        "assessment_conflicts_count_equals",
        "assessment_confidence_at_least",
    ]
    fact_key: str
    expected_value: Any
    missing_fact_result: Literal["PASS", "FAIL"]
    failure_effect: Literal[
        "BLOCK_APPROVAL",
        "REQUEST_EVIDENCE",
        "REQUIRE_HUMAN_REVIEW",
        "REQUIRE_DIRECTOR_APPROVAL",
    ]
    blocking: bool
    missing_evidence: str
    suggested_request: str


class PolicyPack(BaseModel):
    """A policy pack supplies thresholds and effects; assessments never do."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_schema_version: Literal["aelitium-policy/v1"]
    policy_version: str
    decision_domain: str
    description: str
    confidence_floor: int = Field(ge=0, le=100)
    routing_precedence: list[RoutingRule]
    rules: list[PolicyRule] = Field(min_length=1)


def load_policy_pack(path: Path) -> PolicyPack:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pack = PolicyPack.model_validate(payload)

    control_ids = [rule.control_id for rule in pack.rules]
    if len(control_ids) != len(set(control_ids)):
        raise ValueError("policy pack contains duplicate control_id values")

    priorities = [route.priority for route in pack.routing_precedence]
    if len(priorities) != len(set(priorities)):
        raise ValueError("policy pack contains duplicate routing priorities")

    for route in pack.routing_precedence:
        if route.state == "NEEDS_MORE_EVIDENCE":
            if route.selected_approval_role is not None:
                raise ValueError("blocked routes must not select an approval role")
        elif route.selected_approval_role is None:
            raise ValueError("receipt-eligible routes must select an approval role")

    return pack
