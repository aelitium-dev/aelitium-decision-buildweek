# Backend

The D1 backend contains:

- `src/aelitium_decision/policy/` — generic deterministic engine and strict policy-pack models
- `policies/ai_vendor_approval.v1.json` — the domain-specific six-rule Vendor Approval Policy Pack
- `src/aelitium_decision/demo.py` and `cli.py` — no-key T1–T3 execution
- `src/aelitium_decision/api.py` — generic case routes and focused DEMO UI routes
- `src/aelitium_decision/demo_workflow.py` — post-F5 approval/receipt workflow over checked-in fixtures
- `src/aelitium_decision/persistence.py` and `sql/001_initial.sql` — SQLite boundary with versioned SQL
- `src/aelitium_decision/adapters/openai_assessment.py` — GPT-5.6 Responses API adapter
- `src/aelitium_decision/schema_validation.py` — authoritative Draft 2020-12 backend validation
- `src/aelitium_decision/hashing.py` — sole internal wrapper around the allowlisted canonical JSON helper
- `src/aelitium_decision/receipt.py` and `signing.py` — normalized ADR-001 content assembly and detached Ed25519 issuance
- `src/aelitium_decision/keyring.py` and `verification.py` — external-keyring, offline, fail-closed verification

The policy engine consumes thresholds and effects only from the versioned policy pack. Model output supplies observed facts and conflicts; it cannot replace routing, alter a threshold, or waive a blocking control.

Approval routing selects one authoritative approval role. Control or condition
ownership does not create an additional approval requirement. The DEMO approval
route records that single approval in server state; receipt creation accepts only
its `approval_id` and fails closed if the record or its bound decision inputs no
longer match.

Receipt construction, signing, and verification are implemented as a core
library and tested through T4/T5. The clickable DEMO API adds case, approval,
receipt, and verification routes without requiring an OpenAI key. No private
signing key is present in Git; the locally generated demo key is an ignored
runtime file and is never returned by the API.

DEMO assessment provenance is `precomputed_fixture` with
`runtime_model_call=false`; its receipt commits an explicit no-model-request
input record and no LIVE transport settings. The separate checked-in LIVE
artifact records `gpt_generated_live`, provider `openai`, model `gpt-5.6`, and
`runtime_model_call=true`. API provenance also distinguishes fictional source
fixtures, human-entered approval fields, and AELITIUM-generated policy, hash,
signature, receipt, and verification outputs.

The adapter default and checked-in LIVE artifact use
`vendor-assessment/v3.1`. Its prompt lists the
four exact fact keys consumed by the Vendor Approval Policy Pack while retaining
free-form keys for unrelated facts; it does not expose thresholds or perform
semantic alias mapping. It also states the canonical lowercase `snake_case`
risk-category pattern; categories are never repaired after transport. The
successful LIVE artifact records the provider response ID, OpenAI SDK version,
and hashes
for the instructions, input, canonical schema, transport schema, and provider
output text. Its four controlled facts produce observed policy values and route
to `NEEDS_MORE_EVIDENCE` with R2 and R4 blocking. The preceding v3 attempt was
rejected canonically and created no artifact.
