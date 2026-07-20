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
- Original accepted assessment hash from the LIVE response:
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

### Post-validation literal evidence repair

- A later evidence-integrity audit found 19 `quoted_text` fields in the LIVE
  assessment that combined source fragments or paraphrased them. Structure and
  canonical schema validity alone did not establish literal quotation accuracy.
- The checked-in artifact now declares
  `literal-evidence-repair/v1`. Its scope is limited to replacing `quoted_text`
  with exact source substrings and splitting combined evidence references. No
  new OpenAI call was made and the original accepted assessment hash above is
  retained as the transformation input hash.
- The literal-repair output assessment hash is
  `1db3baa0d9e5d60706e426c77e33ca221924f6dd12409c6ee46e0eec4785892a`.
  The transformation record contains both hashes and the original failure count.
- Automated evidence-integrity tests resolve every `document_id` to a
  repository source and require each `quoted_text` value to be an exact raw
  substring. The policy route and its documented prompt-v2 fact-key limitation
  remain unchanged.

### Fictional vendor rename transformation

- A public exact-match screening on 2026-07-20 found no obvious AI/SaaS vendor
  collision for the synthetic replacement name `Nerythica AI Ltd.`. This was a
  practical fixture-name check, not trade-mark or company-name clearance.
- The existing LIVE assessment was not regenerated during the rename. Its
  transformation chain declares `fictional-vendor-rename/v1`, limited to the
  fictional vendor and product names, with the literal-repair hash above as its
  input.
- The current canonical assessment hash is
  `3b5863bb233c433c935a6dce7f670c0c2df4ee54751784116bdc24809d58f3c2`.
  No finding, risk, recommendation, policy fact, or route was changed by the
  rename. A later final LIVE run may replace this derived artifact explicitly.

### Prompt v3 attempt — canonical category rejection

- An externally invoked GPT-5.6 request used `vendor-assessment/v3`. The response
  reached the transport boundary, but canonical validation rejected five
  `risks[].category` values containing spaces: `security assurance`,
  `contract and subprocessor management`, `international transfers`,
  `ai governance`, and `approval governance`.
- The rejected response did not replace the checked-in artifact and did not
  reach policy evaluation. No model-quality, fact-key mapping, or routing result
  is claimed for this attempt.
- The executed v3 instructions hash was
  `aabace7f503893faa98bd0a1fc837d5c5fad9f65e58e0d153ad03fdca19a5c7d`.
- The prompt lists the four exact policy-pack fact keys for annual price,
  EU/EEA-only residency, DPA execution, and issued assurance. It includes no
  thresholds, permits free-form keys for other facts, and does not authorize
  semantic alias mapping or policy overrides.
- Tests require that this prompt catalog exactly matches the four fact-driven
  rules in `policies/ai_vendor_approval.v1.json`. The identifier boundary still
  leaves every `fact_key` unchanged.
- The corrected prompt is versioned separately as `vendor-assessment/v3.1`; it
  explicitly requires every risk category to match
  `^[a-z][a-z0-9_]{1,63}$` and gives lowercase `snake_case` examples. There is
  no category normalizer: invalid model output must still fail canonical
  validation.
- The prepared LIVE artifact writer will record the provider response ID when
  available, OpenAI SDK version, effective request settings, and SHA-256 hashes
  of the instructions, input, canonical schema, transport schema, and provider
  structured output text. It does not record the API key.
- This failed v3 attempt left the checked-in artifact and
  `test_live_artifact.py` on prompt v2. The successful v3.1 replacement is
  recorded in the following section.

### Prompt v3.1 — canonical LIVE artifact accepted

- Execution: `2026-07-20T11:44:42Z`, externally invoked with GPT-5.6, prompt
  `vendor-assessment/v3.1`, OpenAI Python SDK `2.46.0`, `store=false`, and strict
  Structured Outputs.
- Result: `LIVE_SMOKE_OK`. The response passed the transport boundary and full
  canonical `ModelAssessment` validation before artifact creation. Identifier
  casing normalization was not applied.
- Provider assessment hash:
  `5f4c37d53a6573c060527db3d46994a53dc76455b54420f6eb9f0a50badc9789`.
  The artifact records a provider response ID plus hashes for instructions,
  input, canonical schema, transport schema, and provider output text. The raw
  provider text is not stored, so its text hash is a recorded commitment rather
  than a repository-recomputable check.
- Evidence integrity found one non-literal quote caused only by the heading
  prefix `Data Subjects:`. A declared `literal-evidence-repair/v1`
  transformation removed that prefix; the exact source wording is otherwise
  unchanged. Current assessment hash:
  `b59cdb611035cb900d35d871c08046a74bf7938b88294df5b9ca48907feff8a3`.
- Each controlled fact key occurs exactly once with observed values: annual
  price `18000`, EU/EEA-only residency `false`, DPA executed by both parties
  `true`, and issued assurance report `false`.
- Actual Vendor Approval Policy Pack route: `NEEDS_MORE_EVIDENCE`. R1 fails at
  EUR 18,000 and requires director routing; R2 fails and blocks; R3 passes; R4
  fails and blocks; R5 requires human review for the documented conflict; R6
  passes at confidence 97. Because blockers take routing precedence, no approval
  role is selected yet.
- This result demonstrates one fixture run, not generalized extraction quality,
  truth, compliance, fairness, correctness, or legal validity.

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

## B7 Decision Timeline validation

- The deterministic initial DEMO chain contains nine ordered events: case
  creation; F1–F4 ingestion; pre-F5 assessment, policy and routing; F5 ingestion;
  and post-F5 assessment, policy and routing. Independent builds return the
  same event payloads and head hash.
- An ASGI workflow test records the authoritative approval, issues a receipt,
  verifies the original as `VALID`, and verifies the EUR 18,000 → EUR 14,000
  alteration as `INVALID`. The API Timeline grows from 9 to 13 events in that
  exact operation order.
- The issued receipt commits event 10 (`HUMAN_APPROVAL_RECORDED`). Events 11–13
  are the receipt issuance and two verifier results; they extend the API chain
  and are deliberately outside the earlier receipt commitment.
- Negative tests reject backward timestamps, incompatible origins, incomplete
  references, modified event data, non-contiguous sequence, cross-case events,
  count/head drift, mixed legacy/versioned receipt material, and a server-held
  event changed after append.
- The Timeline tests establish behavior for this fixed DEMO workflow. They do
  not establish trusted time, durable audit storage, source truth, decision
  correctness, fairness, compliance, or legal validity.
