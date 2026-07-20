# AELITIUM — Verifiable Decision Workflows

Turn AI recommendations into evidence-backed, human-approved, and tamper-evident decision records.

> Build status: the D1 backend, D2 receipt core, and clickable UI screens 1–3 are implemented. DEMO T1–T5 are green without an OpenAI key; a canonical GPT-5.6 LIVE smoke artifact is recorded with its evaluation limits.

## Build Week workflow

The MVP evaluates whether a fictional European company should adopt the fictional AI SaaS vendor Nerythica AI:

1. In LIVE mode, GPT-5.6 cross-references a commercial proposal, internal procurement policy, security questionnaire, and DPA. DEMO instead uses checked-in precomputed fixtures and makes no model call.
2. Deterministic rules identify blocking evidence and approval routing.
3. A human approves, rejects, requests evidence, or approves with conditions.
4. A Decision Receipt binds the recorded evidence, assessment, policy result, and human decision.
5. An offline verifier detects changes to decision content or signed receipt metadata.

GPT-5.6 performs interpretation. Deterministic code validates and routes. A human retains decision authority.

## Trust boundary

`Tamper-evident ≠ truthful · Verifiable ≠ correct · Signed ≠ legally valid`

Receipt verification checks integrity and Ed25519 validity under a separately trusted key. It does not prove source-document authenticity, factual truth, assessment or decision correctness, fairness, legal validity, identity, or independently trusted time.

## Execution modes

- `DEMO`: implemented with precomputed assessment fixtures and a deterministic post-F5 derivation. It makes no runtime model call and needs no OpenAI key. Its clickable approval → receipt → verify → tamper path is independent of the LIVE artifact.
- `LIVE`: GPT-5.6 Responses API adapter implemented with strict Structured Outputs. The checked-in v3.1 T2-style execution passed canonical validation and contains each controlled policy fact exactly once. It declares one later literal evidence-quote repair, preserving both the provider assessment hash and current assessment hash; its actual policy route is recorded in `EVAL.md`.

The fictional source documents are Build Week work checked into `fixtures/documents/`; they are not authenticated external originals. Human-entered approval data is limited to the declared name, condition text, and justification. AELITIUM generates the deterministic policy result, canonical hashes, local Ed25519 signature, receipt, and verification result. Those generated outputs bind what was recorded; they do not validate the underlying documents or decision claims.

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
- `config/` — public trusted-keyring examples only; never private keys
- `third_party/` — allowlisted pre-existing source and its original notices

## Provenance

This is a new Build Week application. The exact pre-existing allowlist is recorded in [`PREEXISTING_ASSETS.json`](PREEXISTING_ASSETS.json) and explained in [`PREEXISTING_ASSETS.md`](PREEXISTING_ASSETS.md). The foundational decisions and receipt protocol are in [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md).

The project is MIT licensed. The allowlisted `aelitium-v3` canonicalization helper remains Apache-2.0 licensed and retains its original license and notice under `third_party/aelitium-v3/`.

Provenance validation is standalone: the machine-readable manifest contains no
local checkout path, and `python3 scripts/validate_scaffold.py` verifies the
vendored files from their pinned SHA-256 values. A reviewer may optionally add
`--upstream-checkout ../aelitium-v3` to compare the same paths with blobs stored
at the pinned upstream commit; no network call is required.

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

Bootstrap the local DEMO signing key before starting the API or issuing a new
receipt. This command is safe to rerun: it creates a random Ed25519 private key
with mode `0600` and its matching public keyring under Git-ignored `runtime/`,
or validates the pair already there. It never overwrites either file.

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli keys bootstrap
```

Then start the API locally:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m uvicorn aelitium_decision.api:app --host 127.0.0.1 --port 8000
```

SQLite defaults to the ignored `runtime/aelitium.db`; override it with
`AELITIUM_DB_PATH`. The generic API surface remains intentionally small: health,
create/read case, deterministic evaluation, and latest policy result. The
`/v1/demo/*` routes expose the fixed Build Week scenario to the Decision Console.

### Offline receipt sample

A fresh clone can verify the checked-in sample without bootstrapping a private
key, starting FastAPI, using a network connection, or setting an OpenAI key:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli receipt verify
```

Expected result:

```json
{
  "reason": "VERIFIED",
  "status": "VALID"
}
```

The command reads three separate public inputs: the receipt envelope at
`fixtures/sample_receipt/decision-receipt.json`, its committed external
materials at `fixtures/sample_receipt/verification-materials.json`, and the
trusted public keyring at `config/trusted-keyring.demo.json`. Verification never
loads a private key and never accepts a public key from the receipt.

To reproduce local issuance with the clone's newly bootstrapped key, run:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli sample issue
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli receipt verify \
  --receipt runtime/sample_receipt/decision-receipt.json \
  --materials runtime/sample_receipt/verification-materials.json \
  --keyring runtime/keys/trusted-keyring.local.json
```

Local sample outputs are ignored and are never overwritten. Delete or archive
them deliberately before issuing another local sample. Bootstrap
reproducibility means every clone can create and validate its own random local
keypair; it does not mean reproducing the private key used for the checked-in
public sample.

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. Next rewrites `/api/backend/*` to the local FastAPI
origin; set `AELITIUM_API_BASE_URL` before starting Next if the backend is elsewhere.

## Structured Outputs boundary

The live adapter derives a transport-only schema from the canonical `ModelAssessment` schema. It retains the closed object shape and complete required fields while relaxing compatibility-sensitive validation keywords. Every response is then revalidated against the full canonical schema in the backend. The canonical schema always wins.

The strict transport schema enforces the supported structural subset; canonical
backend validation enforces the complete contract. Before that final validation,
the adapter may lowercase only already well-formed, correctly prefixed identifier
tokens (`FACT-001` → `fact-001`). It rejects ambiguous repairs and collisions and
never normalizes findings, evidence, free text, fact keys, or `control_hint`.

The prompt-v3 line gives GPT-5.6 the four exact
`fact_key` names consumed by the Vendor Approval Policy Pack. It contains no
policy thresholds, permits free-form keys for other facts, and does not add a
semantic mapping layer: model output using an alias remains an alias and the
policy engine still fails closed on a missing controlled key. The first v3 call
was rejected canonically because five risk categories contained spaces. The
corrected `vendor-assessment/v3.1` prompt states the required lowercase
`snake_case` pattern explicitly and still performs no category normalization.
Its LIVE execution passed canonical validation; the four controlled facts now
drive the policy rules from observed values rather than missing-key fallbacks.

## Decision Receipt core

The receipt implementation now has one internal canonicalization boundary, a new
Build Week Ed25519 signer, a three-part ADR-001 envelope, and an offline verifier.
Verification requires both an external public keyring and the external policy,
prompt/derivation description, schema, assessment-input record, and timeline materials whose hashes are committed
by the receipt. No public key is accepted from a receipt.

The local demo private key and matching runtime keyring are ignored under
`runtime/keys/`. The checked-in `config/trusted-keyring.demo.json` contains only
the public trust record needed for the checked-in sample; its private key is not
versioned or needed for verification. Verification establishes integrity and
signature validity under the public key selected by the verifier. It does not
establish source-document authenticity, truth, assessment or decision
correctness, fairness, legal validity, identity authentication, or independently
trusted time.

## Manual LIVE smoke gate

After setting `OPENAI_API_KEY` in the invoking shell, one T2-style F1–F4 run can
be performed with:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python backend/scripts/live_smoke.py
```

The script never reads a key file, persists the key, or includes it in its own
output. It uses the strict Responses
API transport schema, applies the narrow identifier boundary described above,
revalidates against the canonical backend schema, and only then writes
`fixtures/live/gpt-5.6-t2-assessment.json`. The checked-in artifact records
`assessment_source=gpt_generated_live`, `runtime_model_call=true`, the OpenAI
provider response ID when available, the installed SDK version, and hashes of
the instructions, input, canonical schema, transport schema, and provider
output text. The output hash is a recorded commitment; the raw provider text is
not persisted, so that one hash is not independently recomputable from the
repository alone. The artifact preserves the provider assessment hash and
declares one scoped post-validation repair that removed a non-literal heading
prefix from a quoted source passage. No additional model call produced that
repair.

The historical v1/v2 attempts and their fail-closed boundaries remain documented
in `EVAL.md`. The current `vendor-assessment/v3.1` run maps all four controlled
facts and routes to `NEEDS_MORE_EVIDENCE` with R2 and R4 blocking; R3 passes from
the observed executed-DPA fact.

## Build Week records

- [`BUILD_WEEK_CHANGELOG.md`](BUILD_WEEK_CHANGELOG.md)
- [`CODEX_USAGE.md`](CODEX_USAGE.md)
- [`EVAL.md`](EVAL.md)
- [`ROADMAP.md`](ROADMAP.md)
