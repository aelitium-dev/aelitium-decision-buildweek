# Configuration

Only public configuration examples belong here. Private signing keys must never be committed.

Receipt verification resolves `key_id` from an external trusted keyring and confirms that the trusted raw Ed25519 public key has the fingerprint signed into the receipt payload.

`trusted-keyring.demo.json` contains only the public trust record for the local
Build Week demo key. Its matching private key is generated locally at
`runtime/keys/buildweek-demo-2026.key`, has mode `0600`, is Git-ignored, and must
never be copied into the repository or a receipt. A fresh clone must generate a
new keypair and update its own trusted public-key configuration deliberately.
