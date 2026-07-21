# Codex Usage

## Primary Build Week session

- Started: 2026-07-18
- Scope: specification → scaffold → backend → frontend → integration → tests
- `/feedback` Session ID: `019f75ba-0204-75e1-aadd-529c29934a84`
- Session discipline: all core implementation stays in this primary thread; secondary sessions are limited to audit or review

## Work performed with Codex

### Preflight

Codex inspected the local project inventory without modifying it, confirmed that the destination repository did not exist, identified the missing specification file, and stopped for explicit approval.

### Architecture

Codex identified that the earlier P3 receipt signed a representation with an empty signature field rather than modelling an explicit signed payload. The approved ADR separates `decision_content`, `signed_receipt_payload`, and the detached `signature`, and adds an external trusted-keyring boundary.

### Scaffold

Codex created ADR-001, exact provenance manifests, the Build Week documentation scaffold, fixtures, and versioned schemas. The following entries record concrete backend, policy, receipt, test, and UI work.

### D1 backend

Codex implemented DEMO mode before the live adapter, split the generic Policy Engine from the Vendor Approval Policy Pack, and exercised T1–T3 through real CLI subprocesses. It also derived a conservative Structured Outputs transport schema while keeping canonical backend validation authoritative, then built the minimal FastAPI/SQLite slice and its tests without adding packages outside the approved allowlist.

### D2 receipt gate

Codex introduced a single internal hashing boundary, implemented the new ADR-001 signer/verifier rather than inheriting P3 behavior, and iterated against a deterministic tamper matrix. The resulting tests distinguish top-level content mismatch, nested commitment mismatch, signed-metadata changes, key-fingerprint mismatch, signature failure, duplicate JSON keys, and schema additions without claiming that verification proves truth or legal validity.

### Integration and final audit gates

Codex implemented and tested the Decision Console, approval authorization, DEMO/LIVE provenance separation, literal-evidence gates, portable provenance validation, secure key bootstrap and offline sample, and the validated Decision Timeline. Repository changes proceeded through explicit human approval gates; LIVE GPT-5.6 calls were executed externally by the human operator, and repository publication remained subject to explicit human approval.
