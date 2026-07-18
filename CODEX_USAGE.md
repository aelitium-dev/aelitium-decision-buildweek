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

## Submission reminder

Before submission, replace the pending `/feedback` entry with the Session ID produced for this primary development thread and cite concrete examples of where Codex accelerated implementation and testing.
