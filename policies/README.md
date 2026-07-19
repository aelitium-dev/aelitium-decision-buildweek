# Policies

`ai_vendor_approval.v1.json` is the domain-specific Vendor Approval Policy Pack.
It contains the six thresholds, blocking flags, effects, and routing precedence
used by the demo. Each route selects at most one authoritative approval role.
The generic engine lives under
`backend/src/aelitium_decision/policy/` and contains no vendor-specific values.

Approval routing selects one authoritative approval role. Control or condition
ownership does not create an additional approval requirement. In the post-F5
route, `director` is the authoritative approver; `operations_reviewer` owns the
recorded remediation condition but is not a second approver.

Model assessments supply observed facts only. They cannot change a threshold,
replace routing precedence, or waive a blocking control.

The operator set implemented by the generic engine is a platform contract.
Policy packs are data: they may select and configure only existing operators,
and may never introduce executable code. Adding a new operator requires a
reviewed engine change and tests; editing a pack alone cannot expand execution.
