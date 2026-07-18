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
  only after a successful GPT-5.6 response. The script has been prepared but not
  executed, so no live-model result is claimed.
