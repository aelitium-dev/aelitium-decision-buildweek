# Scripts

Run the scaffold gate without installing project packages:

```bash
python3 scripts/validate_scaffold.py
```

The standalone command needs only this repository. It verifies portable
allowlist metadata and vendored bytes against pinned SHA-256 values, F1–F5
hashes, five schema structures, the 34-page F4 layout and page-23 clause, and the
absence of committed private-key material. JSON Schema meta-validation runs
when `jsonschema` is already available and is otherwise reported as skipped.

An optional local upstream checkout enables a stronger source-blob check without
network access:

```bash
python3 scripts/validate_scaffold.py --upstream-checkout ../aelitium-v3
```

This reads the allowlisted paths directly from the pinned Git commit. The
current upstream branch and working tree are not trusted inputs.
