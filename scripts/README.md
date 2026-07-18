# Scripts

Run the scaffold gate without installing project packages:

```bash
python3 scripts/validate_scaffold.py
```

The script verifies allowlisted bytes against their pinned sources, F1–F5 hashes, five schema structures, the 34-page F4 layout and page-23 clause, and the absence of committed private-key material. JSON Schema meta-validation runs when `jsonschema` is already available and is otherwise reported as skipped.
