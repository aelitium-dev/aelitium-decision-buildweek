# Policies

`ai_vendor_approval.v1.json` is the domain-specific Vendor Approval Policy Pack.
It contains the six thresholds, blocking flags, effects, roles, and routing
precedence used by the demo. The generic engine lives under
`backend/src/aelitium_decision/policy/` and contains no vendor-specific values.

Model assessments supply observed facts only. They cannot change a threshold,
replace routing precedence, or waive a blocking control.
