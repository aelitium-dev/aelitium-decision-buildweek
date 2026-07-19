# Schemas

The five v1 JSON Schemas are:

- `DecisionCase`
- `ModelAssessment`
- `PolicyResult`
- `HumanApproval`
- `DecisionReceipt`

Objects reject additional properties. The GPT-5.6 assessment schema makes every property required to support strict Structured Outputs.

`PolicyResult.selected_approval_role` is singular by design. It is the one
authoritative role selected by deterministic routing, or `null` while approval
is blocked. `HumanApproval.conditions[].owner_role` records operational
ownership and does not grant approval authority.
