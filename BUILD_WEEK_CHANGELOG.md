# Build Week Changelog

This log distinguishes work performed during OpenAI Build Week from the declared pre-existing allowlist.

## 2026-07-18

### Build Week work

- Performed a read-only repository and specification preflight.
- Identified and resolved the receipt-protocol ambiguity between deterministic content hashing and signed issuance metadata.
- Added an external trusted-keyring boundary to prevent receipt-controlled key substitution.
- Accepted ADR-001 with an explicit three-part receipt envelope and fail-closed verifier contract.
- Created machine-readable and human-readable pre-existing asset manifests.
- Created the standalone repository scaffold and initialized local Git on `main` without a remote or commit.
- Wrote fictional English fixtures F1–F5. F4 is a 34-page print fixture with the material subprocessor clause on page 23.
- Defined the five versioned JSON Schemas and validated them against Draft 2020-12.
- Defined the six deterministic vendor-approval rules and routing precedence.
- Vendored exactly the three allowlisted `aelitium-v3` assets and verified byte identity against their pinned source hashes.
- Added and passed a repeatable structural validation gate.

### Pre-existing work declared

- Pinned the `aelitium-v3` canonical JSON helper at commit `727afff1f26081a05d66d3634b58eb5bd3924a07` for a future verbatim vendor copy.
- Declared its Apache-2.0 `LICENSE` and `NOTICE` for retention.

### Explicitly not reused

- `aelitium-v3` P3 signer and receipt verifier
- Command Center source or components
- AELITIUM_OS source
- Historical workflows, sites, datasets, archives, and local service data
