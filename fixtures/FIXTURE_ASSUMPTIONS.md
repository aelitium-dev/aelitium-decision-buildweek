# Fixture Assumptions

All organizations, people, identifiers, reports, signatures, and events in F1–F5 are fictional. The documents are demonstration inputs, not legal, security, procurement, or certification advice.

## DPA execution interpretation

The governing specification calls F4 a “proposed DPA” while the hard policy rule requires an executed DPA before approval. To preserve both the non-overridable control and the approved demo sequence, F4 is the vendor-proposed form that the fictional parties subsequently executed for this evaluation. Its execution page is complete, while the substantive subprocessor and transfer clause remains a human-review risk.

This means:

- F1–F4 still produce `NEEDS_MORE_EVIDENCE` because EU-only residency confirmation and issued certification evidence are missing.
- F5 supplies those two missing items.
- The executed DPA satisfies the hard presence/execution control.
- The conflict between F3's claimed 30-day notice and F4's no-prior-notice clause remains visible and forces human review.
- The EUR 18,000 annual price independently requires director approval.

No policy rule is weakened to make the demo pass.

## Golden-case evidence sources

T1 and T3 intentionally isolate policy behavior and therefore cite two short,
fictional deterministic records outside the F1–F5 dossier:

- `T1-LOW-RISK` resolves to `fixtures/demo/T1_low_risk_evidence.md`.
- `T3-AMENDMENT` resolves to `fixtures/demo/T3_price_amendment.md`.

Their mappings are explicit in `fixtures/demo/golden_cases.v1.json`. Every
`quoted_text` field in DEMO and LIVE assessment artifacts must be an exact raw
substring of its mapped UTF-8 source; summaries belong in the surrounding
finding fields, not inside quotation marks.
