# Backend

The D1 backend contains:

- `src/aelitium_decision/policy/` — generic deterministic engine and strict policy-pack models
- `policies/ai_vendor_approval.v1.json` — the domain-specific six-rule Vendor Approval Policy Pack
- `src/aelitium_decision/demo.py` and `cli.py` — no-key T1–T3 execution
- `src/aelitium_decision/api.py` — minimal FastAPI case and evaluation routes
- `src/aelitium_decision/persistence.py` and `sql/001_initial.sql` — SQLite boundary with versioned SQL
- `src/aelitium_decision/adapters/openai_assessment.py` — GPT-5.6 Responses API adapter
- `src/aelitium_decision/schema_validation.py` — authoritative Draft 2020-12 backend validation

The policy engine consumes thresholds and effects only from the versioned policy pack. Model output supplies observed facts and conflicts; it cannot replace routing, alter a threshold, or waive a blocking control.

Receipts, signing, human approval, and verification remain D2 work. No signing key is present in this repository.
