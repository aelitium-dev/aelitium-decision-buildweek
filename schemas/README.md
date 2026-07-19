# Schemas

The five v1 JSON Schemas are:

- `DecisionCase`
- `ModelAssessment`
- `PolicyResult`
- `HumanApproval`
- `DecisionReceipt`

Objects reject additional properties. `ModelAssessment` is shared by GPT-generated LIVE artifacts and deterministic precomputed DEMO fixtures. Every property is required so the LIVE transport variant can support strict Structured Outputs; the backend always validates the full canonical schema.

`DecisionReceipt.model_execution` records assessment provenance as signed
decision content. DEMO is constrained to `precomputed_fixture` with no runtime
model call; LIVE is constrained to `gpt_generated_live` with a runtime model
call. A DEMO receipt therefore cannot claim LIVE execution semantics while
remaining schema-valid.

`PolicyResult.selected_approval_role` is singular by design. It is the one
authoritative role selected by deterministic routing, or `null` while approval
is blocked. `HumanApproval.conditions[].owner_role` records operational
ownership and does not grant approval authority.
