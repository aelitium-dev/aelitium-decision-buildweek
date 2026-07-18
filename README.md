# AELITIUM — Verifiable Decision Workflows

Turn AI recommendations into evidence-backed, human-approved, and tamper-evident decision records.

> Build status: D1 backend and the first D2 receipt gate are implemented. DEMO T1–T5 are green without an OpenAI key; API wiring for approval/receipts and frontend work remain.

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

- `DEMO`: implemented with three pre-computed assessments; no OpenAI key required.
- `LIVE`: GPT-5.6 Responses API adapter implemented with strict Structured Outputs. No live call is required for the D1 test gate and no live result is claimed yet.

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

## Backend setup

Python 3.12 is used for the current build. The requirements file pins only the seven approved direct backend dependencies; package-manager-resolved transitives are not promoted to direct dependencies.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

Run the three no-key golden cases individually or together:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli demo T1
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli demo T2
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli demo T3
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli demo all
```

Run the backend tests and the independent scaffold/provenance gate:

```bash
backend/.venv/bin/python -m pytest backend/tests -q
python3 scripts/validate_scaffold.py
```

Start the API locally:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m uvicorn aelitium_decision.api:app --host 127.0.0.1 --port 8000
```

SQLite defaults to the ignored `runtime/aelitium.db`; override it with `AELITIUM_DB_PATH`. The D1 API surface is intentionally small: health, create/read case, deterministic evaluation, and latest policy result.

## Structured Outputs boundary

The live adapter derives a transport-only schema from the canonical `ModelAssessment` schema. It retains the closed object shape and complete required fields while relaxing compatibility-sensitive validation keywords. Every response is then revalidated against the full canonical schema in the backend. The canonical schema always wins.

## Decision Receipt core

The receipt implementation now has one internal canonicalization boundary, a new
Build Week Ed25519 signer, a three-part ADR-001 envelope, and an offline verifier.
Verification requires both an external public keyring and the external policy,
prompt, schema, model-request, and timeline materials whose hashes are committed
by the receipt. No public key is accepted from a receipt.

The local demo private key is ignored under `runtime/keys/`; only its public key
and SHA-256 fingerprint are present in `config/trusted-keyring.demo.json`.
Verification establishes integrity and signature validity under that separately
trusted key. It does not establish truth, correctness, decision quality, legal
validity, identity authentication, or independently trusted time.

## Build Week records

- [`BUILD_WEEK_CHANGELOG.md`](BUILD_WEEK_CHANGELOG.md)
- [`CODEX_USAGE.md`](CODEX_USAGE.md)
- [`EVAL.md`](EVAL.md)
- [`ROADMAP.md`](ROADMAP.md)
