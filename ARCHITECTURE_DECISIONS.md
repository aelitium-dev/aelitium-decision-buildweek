# Architecture Decisions

## ADR-001 — Build Week boundary, provenance, and Decision Receipt protocol

- Status: Accepted
- Date: 2026-07-18
- Decision owner: Catarina Pereira
- Implementation session: primary Codex Build Week session
- Governing specification: session-supplied `SPEC_BUILDWEEK_2026-07-18.md`
- Governing specification SHA-256: `03f4fe1921862f0741bce3913fbc64a642db5724d71487a42cb8485a5afeb560`

### Context

The Build Week application must be a new, independently testable product while declaring every reused asset. The pre-existing `aelitium-v3` repository has a useful canonical JSON helper, but its P3 receipt representation does not express the required separation between deterministic decision content, signed receipt metadata, and the detached signature.

This ADR records the approved refinement of specification sections 8, 10, and 11. Where this ADR and those sections differ, this ADR governs the implementation.

### Decisions

1. The product is built in this new standalone repository. Existing repositories are read-only sources or references.
2. The MVP is one vertical workflow: documents → structured GPT-5.6 assessment → deterministic policy → human decision → Decision Receipt → offline verification → tamper result `INVALID`.
3. GPT-5.6 performs interpretation and proposes an assessment. Deterministic code validates and routes. A human remains the decision authority.
4. The backend is the only canonicalization, hashing, signing, and verification authority. Browser calculations are never authoritative.
5. Decision content is canonicalized with the pinned `aelitium-v3` canonical JSON contract, hashed with SHA-256, and bound into a separately canonicalized signed payload.
6. Ed25519 signs only the canonical `signed_receipt_payload`. The Base64 signature is detached and is not part of the signed payload.
7. Verification resolves a public key from an external trusted keyring. A receipt cannot introduce or authorize its own verification key.
8. Only the three assets enumerated in `PREEXISTING_ASSETS.json` may be copied. In particular, the P3 signer and verifier are not reused.
9. The Command Center is visual reference only. No source, markup, styles, components, fixtures, or media may be copied from it unless the D2 midday checkpoint first updates both provenance manifests.
10. Verification claims only supported-version/schema checks, content integrity, and Ed25519 validity under a separately trusted public key. It does not establish source-document authenticity, truth, correctness, fairness, decision quality, legal validity, or independently trusted time.

### Repository and implementation boundary

- New project license: MIT.
- Vendored `aelitium-v3` material retains Apache-2.0 `LICENSE` and `NOTICE` files.
- No imports from the absolute local `aelitium-v3` checkout.
- All current and future application modules import canonicalization and hashing
  only through `aelitium_decision.hashing`; that boundary is the sole module
  permitted to import the vendored helper directly.
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
| `model_execution` | `execution_mode`, `assessment_source`, `runtime_model_call`, `provider`, `model`, complete effective `model_config`, `prompt_version`, `prompt_hash`, `assessment_schema_version`, `assessment_schema_hash`, `model_request_hash` |
| `model_assessment` | The complete schema-valid `ModelAssessment` object |
| Assessment commitment | `assessment_hash` recomputed from the canonical `model_assessment` |
| `policy` | `policy_version`, `policy_rules_hash`, complete `policy_result`, and recomputed `policy_result_hash` |
| `human_approval` | The complete schema-valid `HumanApproval`, including declared approver identity/role, decision, conditions, justification, and decision timestamp |
| `timeline` | `event_count` and final `head_hash` of the case event chain |

Approval routing selects one authoritative approval role. Control or condition
ownership does not create an additional approval requirement. A receipt commits
to exactly one server-recorded `HumanApproval`; receipt issuance resolves it by
`approval_id` and revalidates its current case, assessment, policy-result,
decision, selected role, conditions, and admission fingerprint before signing.

Assessment provenance is part of signed decision content. `DEMO` requires
`assessment_source=precomputed_fixture` and `runtime_model_call=false`; its
`model_config` is empty, and `model_request_hash` commits to an explicit
`no_model_request` fixture-input record. It never records LIVE transport options
such as Structured Outputs or `store`. `LIVE` requires
`assessment_source=gpt_generated_live` and `runtime_model_call=true`, preserving
GPT-5.6 as the model-backed assessment path. The shared `model_request_hash`
field therefore commits either to the actual LIVE request record or to DEMO's
explicit no-call record; it never implies that DEMO invoked a model.

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
   The assessment-input record must also agree with the signed execution mode,
   source, and runtime-call flag; otherwise verification fails closed.
6. Resolve `key_id` in an external trusted keyring; never use a receipt-supplied key.
7. Recompute the trusted public key fingerprint and require an exact match with the signed fingerprint.
8. Canonicalize `signed_receipt_payload`, decode exactly one 64-byte Ed25519 signature, and verify it with the trusted public key.
9. Return `VALID` only if every check succeeds; otherwise return `INVALID` with a stable machine-readable reason.

### DEMO key bootstrap and public sample

Local DEMO issuance and public sample verification use separate lifecycle
boundaries. A clone creates a random local Ed25519 private key with exact mode
`0600` and a matching ignored runtime keyring. Bootstrap never overwrites
material: an existing pair is validated, a secure private-key-only state may
derive its public keyring, and a keyring-only, malformed, insecurely
permissioned, or mismatched state fails closed.

The checked-in sample contains only a receipt envelope, its external
verification materials, and a separately selected public keyring. Its private
key is neither versioned nor needed. Offline verification reads no signing
material and never accepts a receipt-supplied public key. A valid result proves
only the integrity and signature properties in this ADR, not truth,
authenticity, correctness, fairness, compliance, or legal validity.

### Decision Timeline API contract

The interactive DEMO keeps an append-only `decision-timeline/v1` event chain.
Each closed event records `event_type`, exact recorded `state`, UTC application
timestamp, actor/origin and execution mode, typed object references, sequence,
`previous_event_hash`, and `event_hash`. Its deterministic ID is derived from
sequence and type. The event hash is canonical SHA-256 over every event field
except `event_hash` itself, including the preceding hash.

Backend validation recomputes every link and rejects extra fields, invalid
chronology, case drift, missing/duplicate references, incompatible state or
origin, broken workflow ordering, count drift, and head drift. The frontend
validates the closed response shape, order, timestamp syntax, case and hash-link
continuity before rendering; backend recomputation remains authoritative.

A receipt can commit only the Timeline that precedes it. Interactive receipt
content therefore records the validated head through
`HUMAN_APPROVAL_RECORDED`; `RECEIPT_ISSUED` and `RECEIPT_VERIFIED` extend the API
chain afterwards and are not claimed to be protected by that earlier receipt.
The DEMO history before runtime interaction is reconstructed from validated
repository fixtures, timestamps are not trusted time, and the runtime chain is
in-memory rather than durable audit storage.

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
