# Fixtures

All demo fixtures are fictional, written in English, and contain no real personal or customer data.

- F1 — vendor commercial proposal
- F2 — internal procurement policy excerpt
- F3 — completed but incomplete security questionnaire
- F4 — long executed DPA with the material subprocessor clause on page 23
- F5 — later vendor assurance letter

`demo/` contains the three pre-computed ModelAssessment fixtures, their golden manifest, and two short evidence variants used to isolate the T1 low-risk and T3 conflict routes.

The golden manifest maps the two synthetic document IDs to their source files.
Automated evidence-integrity tests also resolve F1–F5 by both document ID and
filename and require every assessment `quoted_text` value to be a literal source
substring.

Fixture hashes used by cases and receipts will be computed from the exact UTF-8 file bytes.

F4 has 34 explicitly numbered print pages and 33 page breaks. The material no-prior-notice clause is in section 9.6 on page 23, and the fictional execution record is on page 34. See `FIXTURE_ASSUMPTIONS.md` for the interpretation that preserves the executed-DPA hard gate.
