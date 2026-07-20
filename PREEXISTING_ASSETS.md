# Pre-existing Assets

This repository is a new OpenAI Build Week implementation started on 2026-07-18. Unless a component is explicitly listed below, it is classified as Build Week work.

The authoritative machine-readable record is [`PREEXISTING_ASSETS.json`](PREEXISTING_ASSETS.json). Every reused component records its source repository, source commit, source path, destination path, modification status, and classification.

The manifest contains no workstation checkout path. Standalone validation uses
the pinned source hashes and the vendored destination files, so a fresh clone of
this repository does not require `aelitium-v3` to be present alongside it.

## Approved allowlist

All approved source material comes from `git@github.com:aelitium-dev/aelitium-v3.git` at commit `727afff1f26081a05d66d3634b58eb5bd3924a07`.

| Component | Source path | Destination path | Modification status | Classification |
|---|---|---|---|---|
| Canonical JSON helper | `engine/canonical.py` | `backend/src/aelitium_decision/vendor/aelitium_v3/canonical.py` | Verbatim frozen copy; wrappers only outside `vendor/` | Pre-existing |
| Apache-2.0 license | `LICENSE` | `third_party/aelitium-v3/LICENSE` | Verbatim | Pre-existing |
| Attribution notice | `NOTICE` | `third_party/aelitium-v3/NOTICE` | Verbatim | Pre-existing |

## Not copied

- The `aelitium-v3` P3 signer and receipt verifier are not reused. ADR-001 requires a new explicit receipt envelope, detached Ed25519 signature, public-key-only verifier, and external trusted keyring.
- The Command Center is visual reference only. No component, markup, style, fixture, or media is copied.
- AELITIUM_OS is architecture reference only. No source file is copied.
- The applied-ai-portfolio, aelitium-site, evidence logger, offline verifier, n8n data, historical clones, bundles, archives, and quarantine directories are not reused.

## Build Week work

The following are new Build Week work: five domain schemas, fixtures F1–F5, GPT-5.6 Responses API adapter, strict-output validation, policy engine, human approval gate, receipt envelope, Ed25519 signer, trusted-keyring verifier, event timeline, FastAPI application, SQLite persistence, Next.js interface, DEMO mode, evaluation set, tests, and product documentation.

## UI checkpoint

At D2 midday, UI progress may be reviewed. If copying a specific historical UI component becomes necessary, both this document and `PREEXISTING_ASSETS.json` must be updated before the copy occurs. The new record must identify the exact source and destination paths and preserve its pre-existing classification.

## Licenses

The new project is MIT licensed. The vendored `aelitium-v3` files remain subject to Apache-2.0, with the original `LICENSE` and `NOTICE` retained under `third_party/aelitium-v3/`.

## Portable verification

Run the complete standalone gate from a fresh clone:

```bash
python3 scripts/validate_scaffold.py
```

This validates the allowlist metadata, rejects machine-local absolute paths,
and requires each vendored destination to match its pinned SHA-256. It does not
contact the network or require an upstream checkout.

If an `aelitium-v3` Git checkout is available, a reviewer can additionally
verify the source blobs stored at the pinned commit:

```bash
python3 scripts/validate_scaffold.py --upstream-checkout ../aelitium-v3
```

The strengthened check reads `commit:path` blobs from Git. It does not trust the
checkout's current branch or uncommitted working-tree bytes.
