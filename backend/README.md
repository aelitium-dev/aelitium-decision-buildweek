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

Receipt construction, signing, and verification are implemented as a core
library and tested through T4/T5. The clickable DEMO API adds case, approval,
receipt, and verification routes without requiring an OpenAI key. No private
signing key is present in Git; the locally generated demo key is an ignored
runtime file and is never returned by the API.
