# Evaluation Plan

No evaluation results are claimed at scaffold time. Results will be recorded only from materialized test runs.

## Golden cases

| Case | Scenario | Expected result | Status |
|---|---|---|---|
| T1 | Sufficient evidence, low-risk variant | `READY_FOR_APPROVAL` | Not run |
| T2 | F1–F4, critical evidence missing | `NEEDS_MORE_EVIDENCE` with non-empty `blocking_controls` | Not run |
| T3 | Contradiction between documents | Non-empty `conflicts` and `HUMAN_REVIEW` | Not run |
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
