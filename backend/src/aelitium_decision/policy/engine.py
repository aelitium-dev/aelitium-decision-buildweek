"""Generic deterministic policy engine; domain controls live in policy packs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from aelitium_decision.hashing import canonicalize_and_hash

from .pack import PolicyPack, PolicyRule, RoutingRule


Scalar = str | int | bool | None


class PolicyEvaluationError(ValueError):
    """Raised when assessment facts cannot be evaluated safely."""


@dataclass(frozen=True)
class OperatorOutcome:
    passed: bool
    observed_value: Scalar


def _typed_value(value: dict[str, Any]) -> Scalar:
    value_type = value["value_type"]
    fields = {
        "string": "string_value",
        "integer": "integer_value",
        "boolean": "boolean_value",
    }
    if value_type == "unknown":
        if any(value[name] is not None for name in fields.values()):
            raise PolicyEvaluationError("unknown typed value must not carry a scalar")
        return None

    selected = fields[value_type]
    if value[selected] is None:
        raise PolicyEvaluationError(f"{value_type} typed value is null")
    if any(value[name] is not None for name in fields.values() if name != selected):
        raise PolicyEvaluationError("typed value carries more than one scalar")
    return value[selected]


def _fact_index(assessment: dict[str, Any]) -> dict[str, Scalar]:
    result: dict[str, Scalar] = {}
    for fact in assessment["facts"]:
        fact_key = fact["fact_key"]
        if fact_key in result:
            raise PolicyEvaluationError(f"duplicate fact_key: {fact_key}")
        result[fact_key] = _typed_value(fact["value"])
    return result


def _missing(rule: PolicyRule) -> OperatorOutcome:
    return OperatorOutcome(rule.missing_fact_result == "PASS", None)


def _fact_integer_at_most(
    rule: PolicyRule, assessment: dict[str, Any], facts: dict[str, Scalar]
) -> OperatorOutcome:
    observed = facts.get(rule.fact_key)
    if observed is None:
        return _missing(rule)
    if isinstance(observed, bool) or not isinstance(observed, int):
        raise PolicyEvaluationError(f"{rule.fact_key} must be an integer")
    if isinstance(rule.expected_value, bool) or not isinstance(rule.expected_value, int):
        raise PolicyEvaluationError(f"{rule.control_id} expected_value must be an integer")
    return OperatorOutcome(observed <= rule.expected_value, observed)


def _fact_boolean_equals(
    rule: PolicyRule, assessment: dict[str, Any], facts: dict[str, Scalar]
) -> OperatorOutcome:
    observed = facts.get(rule.fact_key)
    if observed is None:
        return _missing(rule)
    if not isinstance(observed, bool) or not isinstance(rule.expected_value, bool):
        raise PolicyEvaluationError(f"{rule.fact_key} and expected_value must be booleans")
    return OperatorOutcome(observed == rule.expected_value, observed)


def _assessment_conflicts_count_equals(
    rule: PolicyRule, assessment: dict[str, Any], facts: dict[str, Scalar]
) -> OperatorOutcome:
    observed = len(assessment["conflicts"])
    if isinstance(rule.expected_value, bool) or not isinstance(rule.expected_value, int):
        raise PolicyEvaluationError(f"{rule.control_id} expected_value must be an integer")
    return OperatorOutcome(observed == rule.expected_value, observed)


def _assessment_confidence_at_least(
    rule: PolicyRule, assessment: dict[str, Any], facts: dict[str, Scalar]
) -> OperatorOutcome:
    observed = assessment["confidence"]
    if isinstance(observed, bool) or not isinstance(observed, int):
        raise PolicyEvaluationError("assessment confidence must be an integer")
    if isinstance(rule.expected_value, bool) or not isinstance(rule.expected_value, int):
        raise PolicyEvaluationError(f"{rule.control_id} expected_value must be an integer")
    return OperatorOutcome(observed >= rule.expected_value, observed)


Operator = Callable[[PolicyRule, dict[str, Any], dict[str, Scalar]], OperatorOutcome]

OPERATORS: dict[str, Operator] = {
    "fact_integer_at_most": _fact_integer_at_most,
    "fact_boolean_equals": _fact_boolean_equals,
    "assessment_conflicts_count_equals": _assessment_conflicts_count_equals,
    "assessment_confidence_at_least": _assessment_confidence_at_least,
}


class PolicyEngine:
    """Evaluate an assessment without allowing model-controlled policy inputs."""

    def evaluate(
        self,
        *,
        case_id: str,
        assessment: dict[str, Any],
        policy_pack: PolicyPack,
        evaluated_at: str,
    ) -> dict[str, Any]:
        facts = _fact_index(assessment)
        evaluations: list[dict[str, Any]] = []
        failed: list[PolicyRule] = []

        for rule in policy_pack.rules:
            outcome = OPERATORS[rule.operator](rule, assessment, facts)
            if not outcome.passed:
                failed.append(rule)
            evaluations.append(
                {
                    "control_id": rule.control_id,
                    "version": rule.version,
                    "description": rule.description,
                    "result": "PASS" if outcome.passed else "FAIL",
                    "observed_value": outcome.observed_value,
                    "expected_value": rule.expected_value,
                    "fact_keys": [rule.fact_key],
                    "effect": "NONE" if outcome.passed else rule.failure_effect,
                }
            )

        blocking_rules = [rule for rule in failed if rule.blocking]
        evidence_failures = [
            rule
            for rule in failed
            if rule.failure_effect != "REQUIRE_DIRECTOR_APPROVAL"
        ]
        conditions = {
            "blocking_controls_not_empty": bool(blocking_rules),
            "director_approval_required": any(
                rule.failure_effect == "REQUIRE_DIRECTOR_APPROVAL" for rule in failed
            ),
            "human_review_required": any(
                rule.failure_effect == "REQUIRE_HUMAN_REVIEW" for rule in failed
            ),
            "otherwise": True,
        }
        route = self._route(policy_pack, conditions)
        _, assessment_hash = canonicalize_and_hash(assessment)

        return {
            "schema_version": "policy-result/v1",
            "case_id": case_id,
            "policy_version": policy_pack.policy_version,
            "assessment_hash": assessment_hash,
            "state": route.state,
            "rules_evaluated": evaluations,
            "blocking_controls": [
                {
                    "control_id": rule.control_id,
                    "description": rule.description,
                    "missing_evidence": [rule.missing_evidence],
                    "suggested_request": rule.suggested_request,
                }
                for rule in blocking_rules
            ],
            "missing_evidence": [
                {
                    "item_id": f"missing-{rule.control_id.lower().replace('_', '-')}",
                    "description": rule.missing_evidence,
                    "required_by_controls": [rule.control_id],
                }
                for rule in evidence_failures
                if rule.missing_evidence
            ],
            "suggested_request": " ".join(
                dict.fromkeys(rule.suggested_request for rule in evidence_failures)
            ),
            "selected_approval_role": route.selected_approval_role,
            "routing_reasons": [
                f"{rule.control_id} failed: {rule.failure_effect}" for rule in failed
            ],
            "evaluated_at": evaluated_at,
        }

    @staticmethod
    def _route(
        policy_pack: PolicyPack, conditions: dict[str, bool]
    ) -> RoutingRule:
        for route in sorted(policy_pack.routing_precedence, key=lambda item: item.priority):
            if conditions[route.condition]:
                return route
        raise PolicyEvaluationError("policy pack has no matching routing rule")
