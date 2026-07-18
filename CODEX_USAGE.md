# Codex Usage

## Primary Build Week session

- Started: 2026-07-18
- Scope: specification → scaffold → backend → frontend → integration → tests
- `/feedback` Session ID: pending; record the exact value before submission
- Session discipline: all core implementation stays in this primary thread; secondary sessions are limited to audit or review

## Work performed with Codex

### Preflight

Codex inspected the local project inventory without modifying it, confirmed that the destination repository did not exist, identified the missing specification file, and stopped for explicit approval.

### Architecture

Codex identified that the earlier P3 receipt signed a representation with an empty signature field rather than modelling an explicit signed payload. The approved ADR separates `decision_content`, `signed_receipt_payload`, and the detached `signature`, and adds an external trusted-keyring boundary.

### Scaffold

Codex created ADR-001, exact provenance manifests, the Build Week documentation scaffold, fixtures, and versioned schemas. Subsequent entries will record concrete backend, policy, receipt, test, and UI work.

### D1 backend

Codex implemented DEMO mode before the live adapter, split the generic Policy Engine from the Vendor Approval Policy Pack, and exercised T1–T3 through real CLI subprocesses. It also derived a conservative Structured Outputs transport schema while keeping canonical backend validation authoritative, then built the minimal FastAPI/SQLite slice and its tests without adding packages outside the approved allowlist.

## Submission reminder

Before submission, replace the pending `/feedback` entry with the Session ID produced for this primary development thread and cite concrete examples of where Codex accelerated implementation and testing.
