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

### Attempt 1 — canonical validation rejected the response

- Execution: external T2-style F1–F4 GPT-5.6 call through the Responses API.
- Transport result: the derived strict Structured Outputs schema accepted the
  response shape.
- Authoritative result: `LIVE_SMOKE_FAILED: CanonicalSchemaError`; the backend
  rejected the assessment before artifact creation or policy evaluation.
- Exact violation classes: 34 prefixed IDs used uppercase forms (14 `fact_id`,
  1 `conflict_id`, 7 missing-evidence `item_id`, 7 `risk_id`, 4 option
  `option_id`, and 1 recommendation `option_id`), while 7 `control_hint` values
  contained citation prose rather than a single identifier token.
- Representative failures: `FACT-001` did not match `fact-…`, `OPTION-001` did
  not match `option-…`, and `F2 section 3, customer-data control 1; F4 section
  12.4` did not satisfy the token-only `control_hint` contract.
- Security/result discipline: the key was redacted, no assessment artifact was
  written, and no successful live-model or policy-route claim is made.

Remediation for attempt 2 uses prompt `vendor-assessment/v2`. The prompt states
the ID and `control_hint` formats explicitly. A deterministic boundary may
lowercase only correctly prefixed, otherwise valid IDs; it cannot edit
`control_hint` or other semantic content. Canonical validation remains
authoritative.

### Attempt 2 — canonical live artifact accepted

- Execution: `2026-07-18T19:48:39Z`, externally invoked with model `gpt-5.6`
  and prompt `vendor-assessment/v2`.
- Result: `LIVE_SMOKE_OK`; the response passed the transport boundary and the
  complete canonical `ModelAssessment` schema before artifact creation.
- Artifact: `fixtures/live/gpt-5.6-t2-assessment.json`.
- Provenance: `assessment_source=gpt_generated_live`, provider `openai`,
  `runtime_model_call=true`. The artifact lists the four checked-in fictional
  source fixtures and explicitly records that their authenticity was not
  verified.
- Canonical assessment hash:
  `55fe5993c5ec2aeb466052c61ed97e15dc60e3777b4d6469d55fb3a7203e4ca4`.
- Vendor Approval Policy Pack result: `NEEDS_MORE_EVIDENCE`; blocking controls
  were `R2_EU_DATA_RESIDENCY`, `R3_DPA_SIGNED`, and `R4_CERTIFICATION`.
- Policy-fact boundary: prompt v2 did not provide the pack's exact `fact_key`
  catalog. The live response used semantically descriptive keys such as
  `annual_recurring_cost_eur` instead of `commercial.annual_price_eur`.
  Consequently, all four fact-driven rules observed a missing value and failed
  closed. The route is conservative, but it is not claimed as evidence of
  correct live fact-to-policy mapping; in particular, `R3_DPA_SIGNED` failed as
  missing even though the assessment narrative identifies the executed DPA.
- The checked-in artifact test revalidates the canonical schema and assessment
  hash, runs the unchanged policy pack, asserts the real route and blocking
  controls, and preserves the missing-fact limitation as an explicit assertion.
- The complete backend suite passed 51 tests with the live-artifact check.

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

The clickable path is a DEMO fixture execution, not a replay of the LIVE call.
Its post-F5 assessment is derived deterministically from a checked-in fixture,
records `runtime_model_call=false`, and is evaluated separately from the LIVE
artifact above.
