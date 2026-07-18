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
