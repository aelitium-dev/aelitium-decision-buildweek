# Build Week Changelog

This log distinguishes work performed during OpenAI Build Week from the declared pre-existing allowlist.

## 2026-07-18

### Build Week work

- Performed a read-only repository and specification preflight.
- Identified and resolved the receipt-protocol ambiguity between deterministic content hashing and signed issuance metadata.
- Added an external trusted-keyring boundary to prevent receipt-controlled key substitution.
- Accepted ADR-001 with an explicit three-part receipt envelope and fail-closed verifier contract.
- Created machine-readable and human-readable pre-existing asset manifests.
- Created the standalone repository scaffold and initialized local Git on `main` without a remote or commit.
- Wrote fictional English fixtures F1–F5. F4 is a 34-page print fixture with the material subprocessor clause on page 23.
- Defined the five versioned JSON Schemas and validated them against Draft 2020-12.
- Defined the six deterministic vendor-approval rules and routing precedence.
- Vendored exactly the three allowlisted `aelitium-v3` assets and verified byte identity against their pinned source hashes.
- Added and passed a repeatable structural validation gate.

### D1 backend implementation

- Pinned only the seven approved direct backend dependencies: FastAPI, Uvicorn, Pydantic, jsonschema, cryptography, OpenAI, and pytest.
- Added pre-computed DEMO assessments for T1–T3 and a no-key CLI runner.
- Separated a generic deterministic Policy Engine from the six-rule Vendor Approval Policy Pack.
- Made policy thresholds, blocking flags, effects, roles, and routing precedence policy-pack inputs that model output cannot override.
- Added a versioned SQLite schema and minimal FastAPI case/evaluation surface.
- Added a GPT-5.6 Responses API adapter using `text.format` strict Structured Outputs with `store=false`.
- Added a derived API-call schema that preserves closed object shape and complete required fields while dropping compatibility-sensitive constraints and converting `const` to a typed one-value `enum`.
- Made full backend revalidation against `model_assessment.v1.schema.json` mandatory after every live adapter response and before every API policy evaluation. The canonical schema is authoritative.
- Added tests for deterministic routing, CLI execution, model/policy separation, schema derivation, canonical fail-closed behavior, SQLite persistence, and the ASGI API.
- Per D1 scope discipline, added no frontend, signing, receipt, verifier, deployment, retry framework, or live paid model run.

### Pre-existing work declared

- Pinned the `aelitium-v3` canonical JSON helper at commit `727afff1f26081a05d66d3634b58eb5bd3924a07` for a future verbatim vendor copy.
- Declared its Apache-2.0 `LICENSE` and `NOTICE` for retention.

### Explicitly not reused

- `aelitium-v3` P3 signer and receipt verifier
- Command Center source or components
- AELITIUM_OS source
- Historical workflows, sites, datasets, archives, and local service data

### D2 receipt verification gate

- Added `hashing.py` as the sole internal wrapper around the pinned canonicalization helper and migrated the Policy Engine and SQLite persistence away from direct vendor imports.
- Added strict JSON parsing that rejects duplicate keys, floats, non-finite numbers, non-string keys, and unsupported values before canonicalization.
- Added normalized Decision Content assembly, complete nested commitments, a detached Ed25519 signer, and an exact ADR-001 receipt envelope as new Build Week work.
- Added an external trusted keyring format; receipts contain `key_id` and signed fingerprint metadata but no public key.
- Generated a local mode-0600 DEMO private key under the Git-ignored runtime tree and committed only its public key and fingerprint.
- Added an offline fail-closed verifier with stable reasons and recomputation of assessment, policy result, policy pack, prompt, assessment schema, model request, timeline, content, fingerprint, and signature commitments.
- Made T4/T5 green, including the six required tamper classes plus the EUR 18,000 → EUR 14,000 narrative alteration.
- Did not reuse the `aelitium-v3` P3 signer or verifier, make a live OpenAI call, add UI, or push this D2 work.

### D2 clickable Decision Console

- Added a deterministic post-F5 DEMO workflow service and four focused FastAPI
  routes for case review, declared human approval, receipt issuance, and receipt
  verification.
- Kept receipt verification dependent on server-held external commitment
  materials and the external public keyring; no private-key bytes or path are
  returned by the API.
- Added the three spec §8 screens: case/evidence with clickable citations and
  the `UNKNOWN → PASS` diff, human approval with visible action boundaries, and
  receipt/verify with the EUR 18,000 → EUR 14,000 tamper interaction.
- Closed the approval-admission boundary: routing now selects one authoritative
  role, the server records one fingerprinted `HumanApproval`, and receipt
  creation accepts only `approval_id` before revalidating current decision
  bindings. Condition ownership remains separate from approval authority.
- Built the UI as new Build Week work. The historical Command Center remained a
  visual reference only; no component, markup, style, fixture, or media was
  copied.
- Pinned the approved frontend toolchain exactly: Next.js `15.5.20`, React and
  React DOM `19.2.7`, TypeScript `5.9.3`, Tailwind CSS and its PostCSS adapter
  `4.3.3`, PostCSS `8.5.19`, `@types/node` `24.13.3`, `@types/react` `19.2.17`,
  and `@types/react-dom` `19.2.3`.
- Overrode Next.js's older nested PostCSS with the already approved `8.5.19`;
  the resulting npm audit reports zero known vulnerabilities.
- Added a manual LIVE smoke script that reads `OPENAI_API_KEY` only from the
  process environment, redacts it from errors, and writes an assessment artifact
  only after a successful GPT-5.6 response. At the UI checkpoint the script had
  been prepared but not yet executed.

### LIVE smoke iteration 1 — fail-closed transport boundary

- Ran the T2-style F1–F4 smoke externally. GPT-5.6 returned a structurally valid
  transport object, but authoritative canonical validation rejected 34
  identifier-format violations and 7 prose-valued `control_hint` violations.
- Wrote no artifact and did not pass the rejected assessment to the Policy
  Engine. The failure is retained in `EVAL.md` as defense-in-depth evidence, not
  as a successful live result or model-quality claim.
- Bumped the live adapter prompt from `vendor-assessment/v1` to
  `vendor-assessment/v2` and added explicit lowercase ID examples plus the
  single-token `control_hint` contract.
- Added a deterministic pre-validation identifier casing boundary (implemented
  internally by `normalize_transport_identifiers`) that only lowercases tokens
  already carrying the correct case-insensitive prefix and grammar. It operates
  on a copy and rejects missing IDs, unsafe repairs, case-folding collisions,
  and recommendation references that do not resolve to an option.
- Explicitly excluded `control_hint`, findings, evidence, free text, fact keys,
  and all other semantic content from normalization. Those remain subject to
  fail-closed canonical validation.

### LIVE smoke iteration 2 — canonical GPT-5.6 artifact

- Re-ran the T2-style F1–F4 smoke externally with GPT-5.6 and prompt
  `vendor-assessment/v2`. It passed the transport boundary and authoritative
  canonical validation and wrote
  `fixtures/live/gpt-5.6-t2-assessment.json` without persisting or logging the
  API key.
- Recorded execution time `2026-07-18T19:48:39Z` and canonical assessment hash
  `55fe5993c5ec2aeb466052c61ed97e15dc60e3777b4d6469d55fb3a7203e4ca4`.
- Added a test that revalidates the checked-in live assessment and hash before
  evaluating it with the unchanged Vendor Approval Policy Pack. The resulting
  route is `NEEDS_MORE_EVIDENCE`.
- Kept the policy-fact limitation visible: prompt v2 did not supply the pack's
  exact `fact_key` catalog, so the four fact-driven controls failed closed on
  missing keys. No semantic aliases or inferred mappings were introduced, and
  this run is not presented as fact-to-policy mapping accuracy evidence.
- The complete backend suite passed 51 tests with the live-artifact check.

### D2 visual-test runtime repair

- Diagnosed the first browser launch failure as mixed Next.js output: production
  `page.js` and `chunks/833.js` were followed by development rewrites of the
  Webpack runtime and React Client Manifest in the same `.next` directory.
- Kept the approved Next.js 15 toolchain and added no package. Configured
  `.next-dev` for development and retained `.next` for production, preventing
  subsequent build/dev manifest collisions without deleting user data.

### B2 DEMO provenance correction

- Replaced misleading DEMO model-call metadata with signed assessment
  provenance: `execution_mode=DEMO`, `assessment_source=precomputed_fixture`,
  and `runtime_model_call=false`.
- Removed `store=false` and `structured_outputs=true` from DEMO receipt content;
  its model configuration is empty and its input commitment explicitly records
  `no_model_request` plus the checked-in base fixture and deterministic
  derivation version.
- Constrained those DEMO semantics in the receipt schema and made the verifier
  reject external assessment-input material whose mode, source, or runtime-call
  flag contradicts the signed provenance.
- Kept LIVE separate and model-backed: the checked-in artifact records provider
  `openai`, model `gpt-5.6`, `assessment_source=gpt_generated_live`, and
  `runtime_model_call=true`.
- Added machine-readable API/UI provenance for fictional source fixtures,
  human-entered approval fields, and AELITIUM-generated policy results, hashes,
  signature, receipt, and verification result. Trust wording now explicitly
  excludes original-document authenticity, correctness, fairness, and legal
  validity.
- Added a frontend runtime contract check so a stale pre-B2 API response produces
  an explicit backend-restart message instead of dereferencing missing
  provenance metadata.

### B3 literal evidence integrity

- Audited every `quoted_text` reference in the three DEMO assessments, the LIVE
  artifact, and the generated post-F5 assessment. Found 18 non-literal DEMO
  fields, 19 non-literal LIVE fields, and 2 non-literal generated fields.
- Replaced paraphrases and combined fragments with exact UTF-8 source
  substrings. Where one claim depended on multiple passages, split it into
  separate evidence references rather than manufacturing a composite quote.
- Added two small fictional source records for the isolated T1 and T3 golden
  inputs, and declared their `document_id` mappings in the golden manifest.
- Preserved the LIVE call's original accepted assessment hash and declared a
  scoped `literal-evidence-repair/v1` transformation with the current hash. No
  new OpenAI call was made; the assessment findings and policy route were not
  changed by the quotation repair.
- Added a repository-wide assessment evidence test that resolves each source
  path and requires every `quoted_text` to occur literally in the named file,
  including the assessment generated for the post-F5 clickable DEMO.
