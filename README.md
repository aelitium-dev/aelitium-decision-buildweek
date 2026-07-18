# AELITIUM — Verifiable Decision Workflows

Turn AI recommendations into evidence-backed, human-approved, and tamper-evident decision records.

> Build status: initial OpenAI Build Week scaffold, started 2026-07-18. The end-to-end application is not implemented yet.

## Build Week workflow

The MVP evaluates whether a fictional European company should adopt the fictional AI SaaS vendor NovaMind AI:

1. GPT-5.6 cross-references a commercial proposal, internal procurement policy, security questionnaire, and DPA.
2. Deterministic rules identify blocking evidence and approval routing.
3. A human approves, rejects, requests evidence, or approves with conditions.
4. A Decision Receipt binds the recorded evidence, assessment, policy result, and human decision.
5. An offline verifier detects changes to decision content or signed receipt metadata.

GPT-5.6 performs interpretation. Deterministic code validates and routes. A human retains decision authority.

## Trust boundary

`Tamper-evident ≠ truthful · Verifiable ≠ correct · Signed ≠ legally valid`

Receipt verification checks integrity and Ed25519 validity under a separately trusted key. It does not prove factual truth, decision quality, legal validity, or independently trusted time.

## Execution modes

- `DEMO`: mandatory pre-computed assessment; no OpenAI key required. This will be the first judging path.
- `LIVE`: server-side GPT-5.6 Responses API integration with strict Structured Outputs.

Neither mode is implemented at scaffold time.

## Planned architecture

```text
Next.js Decision Console
        ↓
FastAPI case and decision API
        ↓
SQLite
        ↓
GPT-5.6 structured assessment
        ↓
Deterministic policy engine
        ↓
Human approval gate
        ↓
Decision Receipt + offline verifier
```

## Repository map

- `backend/` — API, domain logic, persistence, receipt code, and tests
- `frontend/` — Decision Console
- `fixtures/` — fictional English-language demo documents and pre-computed assessments
- `schemas/` — the five versioned JSON Schemas
- `policies/` — deterministic, versioned policy rules
- `config/` — public trusted-keyring examples only
- `third_party/` — allowlisted pre-existing source and its original notices

## Provenance

This is a new Build Week application. The exact pre-existing allowlist is recorded in [`PREEXISTING_ASSETS.json`](PREEXISTING_ASSETS.json) and explained in [`PREEXISTING_ASSETS.md`](PREEXISTING_ASSETS.md). The foundational decisions and receipt protocol are in [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md).

The project is MIT licensed. The allowlisted `aelitium-v3` canonicalization helper remains Apache-2.0 licensed and retains its original license and notice under `third_party/aelitium-v3/`.

## Current setup and testing

No packages were installed during preflight or scaffold creation. The repository currently contains documentation, fixtures, five schemas, the versioned policy, a scaffold validator, and the allowlisted canonicalization source; the application backend and frontend are not implemented and no claim is made that they run.

The current structural gate uses the existing Python environment without installing project dependencies:

```bash
python3 scripts/validate_scaffold.py
```

Reproducible application setup and test commands will be added with the first executable backend and frontend slices.

## Build Week records

- [`BUILD_WEEK_CHANGELOG.md`](BUILD_WEEK_CHANGELOG.md)
- [`CODEX_USAGE.md`](CODEX_USAGE.md)
- [`EVAL.md`](EVAL.md)
- [`ROADMAP.md`](ROADMAP.md)
