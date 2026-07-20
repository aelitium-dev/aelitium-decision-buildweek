# Public offline-verification sample

This directory contains public data only:

- `decision-receipt.json` — the signed three-part receipt envelope;
- `verification-materials.json` — external policy, derivation description,
  assessment schema, input record, and existing receipt event commitments.

The verifier must separately be given `config/trusted-keyring.demo.json`. It
does not trust a key from the receipt, and no private key is required or
included. From the repository root:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m aelitium_decision.cli receipt verify
```

Expected output is `VALID` / `VERIFIED`. The command performs no network access,
does not start FastAPI, and does not use OpenAI. It proves integrity and Ed25519
validity under the selected public key only; it does not prove that documents
are authentic, facts are true, or a decision is correct, fair, compliant, or
legally valid.
