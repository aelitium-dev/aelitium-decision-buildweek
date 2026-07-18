# Architecture Decisions

## ADR-001 — Build Week boundary, provenance, and Decision Receipt protocol

- Status: Accepted
- Date: 2026-07-18
- Decision owner: Catarina Pereira
- Implementation session: primary Codex Build Week session
- Governing specification: `/home/catarina-aelitium/SPEC_BUILDWEEK_2026-07-18.md`
- Governing specification SHA-256: `03f4fe1921862f0741bce3913fbc64a642db5724d71487a42cb8485a5afeb560`

### Context

The Build Week application must be a new, independently testable product while declaring every reused asset. The pre-existing `aelitium-v3` repository has a useful canonical JSON helper, but its P3 receipt representation does not express the required separation between deterministic decision content, signed receipt metadata, and the detached signature.

This ADR records the approved refinement of specification sections 8, 10, and 11. Where this ADR and those sections differ, this ADR governs the implementation.

### Decisions

1. The product is built in a new standalone repository at `/home/catarina-aelitium/aelitium-decision-buildweek`. Existing repositories are read-only sources or references.
2. The MVP is one vertical workflow: documents → structured GPT-5.6 assessment → deterministic policy → human decision → Decision Receipt → offline verification → tamper result `INVALID`.
3. GPT-5.6 performs interpretation and proposes an assessment. Deterministic code validates and routes. A human remains the decision authority.
4. The backend is the only canonicalization, hashing, signing, and verification authority. Browser calculations are never authoritative.
5. Decision content is canonicalized with the pinned `aelitium-v3` canonical JSON contract, hashed with SHA-256, and bound into a separately canonicalized signed payload.
6. Ed25519 signs only the canonical `signed_receipt_payload`. The Base64 signature is detached and is not part of the signed payload.
7. Verification resolves a public key from an external trusted keyring. A receipt cannot introduce or authorize its own verification key.
8. Only the three assets enumerated in `PREEXISTING_ASSETS.json` may be copied. In particular, the P3 signer and verifier are not reused.
9. The Command Center is visual reference only. No source, markup, styles, components, fixtures, or media may be copied from it unless the D2 midday checkpoint first updates both provenance manifests.
10. Verification claims only supported-version/schema checks, content integrity, and Ed25519 validity under a separately trusted public key. It does not establish truth, correctness, decision quality, legal validity, or independently trusted time.

### Repository and implementation boundary

- New project license: MIT.
- Vendored `aelitium-v3` material retains Apache-2.0 `LICENSE` and `NOTICE` files.
- No imports from the absolute local `aelitium-v3` checkout.
- No Git submodule, history merge, runtime P3 service call, or packaging work on `aelitium-v3`.
- No existing repository is edited to support this application.
- Private signing keys are never committed. The verifier needs only a trusted public keyring.
- DEMO mode with a pre-computed assessment is mandatory and must exercise approval, receipt creation, verification, and tampering without an OpenAI key.

### Decision Receipt envelope

The receipt has exactly three top-level members. Additional top-level members are invalid.

```json
{
  "decision_content": {},
  "signed_receipt_payload": {
    "receipt_version": "aelitium-decision-receipt/v1",
    "receipt_id": "rec-...",
    "content_schema_version": "aelitium-decision-content/v1",
    "content_hash_algorithm": "sha256",
    "content_hash": "<64 lowercase hexadecimal characters>",
    "issued_at": "<RFC 3339 UTC timestamp>",
    "signing_metadata": {
      "signature_algorithm": "Ed25519",
      "signature_encoding": "base64",
      "key_id": "<trusted-key identifier>",
      "public_key_fingerprint_sha256": "<64 lowercase hexadecimal characters>",
      "payload_canonicalization": "json_sorted_keys_no_whitespace_utf8"
    }
  },
  "signature": "<base64-encoded 64-byte Ed25519 signature>"
}
```

No public key is embedded in the receipt. `key_id` identifies a key in the verifier's external trusted keyring; the verifier independently computes that key's fingerprint and compares it with the signed fingerprint.

### Exact `decision_content` commitment

`content_hash` commits to the complete `decision_content` object below. Receipt issuance metadata, specifically `receipt_id`, `issued_at`, and `signing_metadata`, is excluded from `decision_content` and protected by the signature instead.

| Object | Committed fields |
|---|---|
| `case` | `case_id`, `decision_domain`, `case_version`, `created_at`, ordered `documents[]` |
| Each document | `document_id`, `document_type`, `filename`, `sha256`, `version` |
| `model_execution` | `provider`, `model`, complete effective `model_config`, `prompt_version`, `prompt_hash`, `assessment_schema_version`, `assessment_schema_hash`, `model_request_hash` |
| `model_assessment` | The complete schema-valid `ModelAssessment` object |
| Assessment commitment | `assessment_hash` recomputed from the canonical `model_assessment` |
| `policy` | `policy_version`, `policy_rules_hash`, complete `policy_result`, and recomputed `policy_result_hash` |
| `human_approval` | The complete schema-valid `HumanApproval`, including declared approver identity/role, decision, conditions, justification, and decision timestamp |
| `timeline` | `event_count` and final `head_hash` of the case event chain |

Document bodies are not embedded in a receipt; their committed SHA-256 hashes are. Collections with set semantics are normalized before hashing: documents by `(document_id, version)`, rule evaluations by `control_id`, and evidence references by `(document_id, locator)`. Arrays whose order is semantically authored, such as approval conditions, retain their supplied order.

All recorded timestamps other than receipt-level `issued_at` remain part of decision content when their containing schema requires them. Excluding `issued_at` therefore does not erase the case or approval chronology.

### Canonicalization and `content_hash`

Canonicalization identifier:

`json_sorted_keys_no_whitespace_utf8`

Its implemented contract is `json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` followed by UTF-8 encoding. Schema validation occurs before canonicalization. Duplicate object keys, non-finite numbers, and non-integer JSON numbers are rejected. Confidence is represented as an integer percentage from 0 through 100.

```text
content_bytes = UTF8(canonical_json(decision_content))
content_hash  = lowercase_hex(SHA256(content_bytes))
```

The hash has no `sha256:` prefix, preserving the chosen `aelitium-v3` representation.

### `signed_receipt_payload` and signature

`signed_receipt_payload` binds the content commitment to issuance and signing interpretation. A second issuance of unchanged decision content may retain the same `content_hash` while having a different `receipt_id`, `issued_at`, signing key, and signature.

```text
signed_payload_bytes = UTF8(canonical_json(signed_receipt_payload))
signature_bytes      = Ed25519.Sign(private_key, signed_payload_bytes)
signature            = Base64(signature_bytes)
```

The signature is not produced over formatted receipt JSON, `decision_content` directly, or the bare content hash.

### Fail-closed verification contract

Verification is offline and deterministic. It must:

1. Parse JSON without accepting duplicate keys.
2. Validate the exact receipt schema and reject additional or unsupported fields.
3. Reject unsupported receipt/content versions, algorithms, encodings, or canonicalization identifiers.
4. Canonicalize `decision_content`, recompute `content_hash`, and require an exact match with the signed value.
5. Recompute and validate every nested commitment: document hash shape, assessment hash, policy-result hash, ruleset hash reference, model-request hash reference, and timeline head shape.
6. Resolve `key_id` in an external trusted keyring; never use a receipt-supplied key.
7. Recompute the trusted public key fingerprint and require an exact match with the signed fingerprint.
8. Canonicalize `signed_receipt_payload`, decode exactly one 64-byte Ed25519 signature, and verify it with the trusted public key.
9. Return `VALID` only if every check succeeds; otherwise return `INVALID` with a stable machine-readable reason.

Consequences of alteration:

- Changing decision content without changing `content_hash` causes `CONTENT_HASH_MISMATCH`.
- Changing decision content and replacing `content_hash` invalidates the Ed25519 signature.
- Changing `issued_at`, a version, `key_id`, fingerprint, algorithm, or canonicalization invalidates the signature or fails the supported-value checks.
- Changing the detached signature fails decoding, length validation, or signature verification.
- Adding any field fails schema validation.

### Pre-existing asset decision

The authoritative machine-readable allowlist is `PREEXISTING_ASSETS.json`; `PREEXISTING_ASSETS.md` is its human-readable explanation. Everything not enumerated in the JSON allowlist is Build Week work or reference-only material that cannot be copied.

### Command Center checkpoint

At D2 midday, UI progress is reviewed. If the UI is behind, specific Command Center components may be proposed for copying. No copy occurs until both provenance manifests identify each exact source path, source repository/commit, destination, modification status, and pre-existing classification.

### Credits and live-mode consequence

The credit-request deadline has passed. This ADR makes no claim about the project's account balance or whether all account credits are exhausted. The owner verifies account status separately. DEMO mode remains mandatory regardless of live-mode availability.

### Consequences

- The protocol is more explicit than the prior P3 receipt and cannot silently drift into that representation.
- The same decision content can be identified consistently across separate receipt issuances.
- All mutable receipt metadata is either content-hashed or signed.
- External key trust is an explicit verifier input rather than an unsigned receipt assertion.
- The minimal allowlist maximizes Build Week provenance while retaining canonical compatibility.
- New signing, verification, schemas, workflows, policies, fixtures, API, UI, tests, and documentation are Build Week work.
