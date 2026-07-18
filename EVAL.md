# Evaluation Plan

Results below come from the checked-in deterministic golden fixtures and local D1 test runs. They do not measure live-model quality.

## Golden cases

| Case | Scenario | Expected result | Status |
|---|---|---|---|
| T1 | Sufficient evidence, low-risk variant | `READY_FOR_APPROVAL` | Passed in DEMO CLI |
| T2 | F1–F4, critical evidence missing | `NEEDS_MORE_EVIDENCE` with non-empty `blocking_controls` | Passed in DEMO CLI |
| T3 | Contradiction between documents | Non-empty `conflicts` and `HUMAN_REVIEW` | Passed in DEMO CLI |
| T4 | Complete conditional approval | Receipt verifies as `VALID` | Not run |
| T5 | Any committed or signed field altered | Receipt verifies as `INVALID` | Not run |

## Metrics

- Strict schema-valid assessment rate
- Missing-evidence detection on the golden set
- Deterministic policy-routing accuracy on the golden set
- Tamper detection across at least five distinct altered fields
- Deterministic `content_hash` across three runs with identical decision content
- Stable `content_hash` across distinct receipt `issued_at` values
- Signed-metadata tamper detection

## Reporting discipline

Metrics describe only the small, documented golden set. They are not generalized performance, safety, compliance, or market claims.

## D1 execution record

- T1–T3 executed both through the Python service boundary and real CLI subprocesses.
- All three assessments passed the canonical `ModelAssessment` schema.
- All three policy results passed the canonical `PolicyResult` schema.
- Route assertions passed for 3/3 golden cases; this is a fixture result, not a generalized accuracy claim.
- The full D1 backend suite passed 17 tests before the final review gate.
- No OpenAI API key or live model call was used for these results.
