"""Pre-computed DEMO runner; deliberately independent of API credentials."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .paths import FIXTURES_DIR, REPOSITORY_ROOT
from .policy import PolicyEngine, load_policy_pack
from .schema_validation import load_and_validate, validate_canonical


class DemoExpectationError(AssertionError):
    """Raised when deterministic output diverges from the checked-in golden case."""


@lru_cache(maxsize=1)
def load_golden_manifest() -> dict[str, Any]:
    path = FIXTURES_DIR / "demo" / "golden_cases.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_demo_case(case_name: str) -> dict[str, Any]:
    manifest = load_golden_manifest()
    try:
        case = manifest["cases"][case_name.upper()]
    except KeyError as exc:
        raise KeyError(f"unknown demo case: {case_name}") from exc

    assessment = load_and_validate(
        REPOSITORY_ROOT / case["assessment_path"], manifest["assessment_schema"]
    )
    policy_pack = load_policy_pack(REPOSITORY_ROOT / manifest["policy_path"])
    policy_result = PolicyEngine().evaluate(
        case_id=case["case_id"],
        assessment=assessment,
        policy_pack=policy_pack,
        evaluated_at=case["evaluated_at"],
    )
    validate_canonical(policy_result, manifest["policy_result_schema"])

    actual_blocking = [
        control["control_id"] for control in policy_result["blocking_controls"]
    ]
    checks = {
        "state": policy_result["state"] == case["expected_state"],
        "blocking_controls": actual_blocking == case["expected_blocking_controls"],
        "conflicts": len(assessment["conflicts"]) == case["expected_conflicts"],
        "assessment_hash": (
            policy_result["assessment_hash"] == case["expected_assessment_hash"]
        ),
    }
    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise DemoExpectationError(f"{case_name.upper()} golden checks failed: {failed}")

    return {
        "demo_case": case_name.upper(),
        "mode": "DEMO",
        "assessment_valid": True,
        "policy_result_valid": True,
        "golden_checks": checks,
        "policy_result": policy_result,
    }
