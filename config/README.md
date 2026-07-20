# Configuration

Only public configuration examples belong here. Private signing keys must never be committed.

Receipt verification resolves `key_id` from an external trusted keyring and confirms that the trusted raw Ed25519 public key has the fingerprint signed into the receipt payload.

`trusted-keyring.demo.json` contains only the public trust record selected for
the checked-in sample receipt. Its matching private key is not versioned and is
not required for sample verification.

Local receipt issuance uses a separate per-clone pair created by the documented
bootstrap command: the private key is
`runtime/keys/buildweek-demo-2026.key` with mode `0600`, and its derived public
keyring is `runtime/keys/trusted-keyring.local.json`. Both paths are Git-ignored.
The bootstrap never replaces the checked-in sample keyring, and the verifier
never trusts a key carried inside a receipt.
