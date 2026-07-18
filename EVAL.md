# Evaluation Plan

Results below come from the checked-in deterministic golden fixtures and local D1 test runs. They do not measure live-model quality.

## Golden cases

| Case | Scenario | Expected result | Status |
|---|---|---|---|
| T1 | Sufficient evidence, low-risk variant | `READY_FOR_APPROVAL` | Passed in DEMO CLI |
| T2 | F1–F4, critical evidence missing | `NEEDS_MORE_EVIDENCE` with non-empty `blocking_controls` | Passed in DEMO CLI |
| T3 | Contradiction between documents | Non-empty `conflicts` and `HUMAN_REVIEW` | Passed in DEMO CLI |
| T4 | Complete conditional approval | Receipt verifies as `VALID` | Passed locally |
| T5 | Any committed or signed field altered | Receipt verifies as `INVALID` | Passed locally |

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

## D2 receipt execution record

- T4 produced a schema-valid three-part receipt and returned `VALID / VERIFIED` with an external trusted keyring and independently supplied commitment materials.
- Identical decision content produced one stable `content_hash` across three runs.
- Changing only `receipt_id` and `issued_at` retained the same `content_hash` but produced a different valid signature.
- T5 returned `INVALID` for 7/7 scoped receipt alterations: content, content plus replaced hash, `issued_at`, signing fingerprint, signature bytes, added field, and the narrative price change EUR 18,000 → EUR 14,000.
- External policy, prompt, assessment schema, model request, and timeline materials were each altered independently; all 5/5 commitment checks returned `INVALID` with stable reasons.
- The complete backend suite passed 41 tests at this gate; the independent scaffold/provenance/key-material validator also passed.
- These are deterministic tests over the documented fixtures, not a generalized security, correctness, or legal-validity claim.

## LIVE smoke status

The environment-only GPT-5.6 smoke command is prepared but has not been run.
There is no checked-in live assessment artifact and no live-model quality claim
at this checkpoint. After explicit approval and a successful call, this section
will record the model, execution time, canonical assessment hash, resulting
policy route, and artifact path.

## D2 UI integration record

- The no-key API flow passed through the ASGI boundary: load the post-F5 case,
  record a declared conditional approval, issue a receipt, verify it as
  `VALID / VERIFIED`, change the committed price from EUR 18,000 to EUR 14,000,
  and verify the altered receipt as `INVALID / ASSESSMENT_HASH_MISMATCH`.
- The same receipt path passed once with the local ignored DEMO private key and
  committed external public keyring; no key value or private-key path was output.
- The complete backend suite passed 42 tests after UI API integration.
- Frontend TypeScript checking and the optimized Next.js production build passed.
- The pinned frontend dependency tree reports zero known npm vulnerabilities.
- Localhost socket binding is prohibited by the Codex sandbox (`EPERM`), so this
  checkpoint does not claim an in-sandbox browser session. Both attempted server
  processes shut down, and no orphan Uvicorn or Next process remained.
