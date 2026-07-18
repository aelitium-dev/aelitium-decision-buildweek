# Policies

`ai_vendor_approval.v1.json` is the domain-specific Vendor Approval Policy Pack.
It contains the six thresholds, blocking flags, effects, roles, and routing
precedence used by the demo. The generic engine lives under
`backend/src/aelitium_decision/policy/` and contains no vendor-specific values.

Model assessments supply observed facts only. They cannot change a threshold,
replace routing precedence, or waive a blocking control.

The operator set implemented by the generic engine is a platform contract.
Policy packs are data: they may select and configure only existing operators,
and may never introduce executable code. Adding a new operator requires a
reviewed engine change and tests; editing a pack alone cannot expand execution.
