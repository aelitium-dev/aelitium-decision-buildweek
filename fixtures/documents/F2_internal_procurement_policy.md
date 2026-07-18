# F2 — Caldera Works Europe Internal Procurement Policy

> FICTIONAL BUILD WEEK DEMO DOCUMENT — INTERNAL POLICY EXCERPT

| Field | Value |
|---|---|
| Policy ID | CW-PROC-07 |
| Version | 3.2 |
| Effective date | 2026-01-15 |
| Owner | Operations and Finance |
| Applies to | Software and hosted-service purchases |

## 1. Purpose

This policy establishes minimum evidence, approval, and contracting requirements for software purchases. It is designed to ensure that price, security, privacy, operational dependency, and contract risk are reviewed by the appropriate people before activation.

The requester and procurement reviewer must record the evidence used, unresolved questions, approval route, conditions, and final human decision. Automated assessments may support review but cannot approve a supplier.

## 2. Approval thresholds

Annual recurring cost is calculated before VAT and includes mandatory platform, support, and minimum-usage charges.

| Annual recurring cost | Required approval |
|---|---|
| Up to EUR 5,000 | Budget owner |
| EUR 5,001–15,000 | Budget owner and Operations |
| Above EUR 15,000 | Director approval in addition to Budget owner and Operations |

Splitting one purchase into multiple orders, altering a price field, or excluding mandatory fees to avoid a threshold is prohibited. The recorded annual price must match the vendor's current written offer.

Multi-year commitments are assessed using annual recurring cost for the approval threshold and total committed value for the risk summary.

## 3. Customer-data controls

Customer Data includes customer contact details, support conversations, account records, contract material, usage records, and any document from which a customer can be identified.

Before Customer Data is uploaded to a hosted service, the review record must contain all of the following:

1. written confirmation that Customer Data and its backups are stored and processed in the European Union or European Economic Area;
2. a Data Processing Addendum executed by both parties;
3. a current list of subprocessors and the applicable change-notification mechanism;
4. documented retention and deletion arrangements;
5. a named internal service owner.

If items 1 or 2 are missing, the case has a blocking control and cannot be approved. The API and user interface must enforce this rule; free-text justification cannot override it.

A material clause allowing transfers outside the EEA must be highlighted for human legal review even when the document has been executed.

## 4. Security evidence

The supplier must provide evidence appropriate to the service risk. A current SOC 2 Type II report, ISO/IEC 27001 certificate, or documented equivalent may satisfy the baseline assurance requirement.

Statements such as "in progress", "planned", or "expected" do not count as issued certification. When an issued report is not yet available, the reviewer must record missing evidence and request a dated written response from the supplier.

Conflicting answers across a proposal, questionnaire, security page, contract, or letter require human review. The conflict must remain visible even if a later document resolves the operational question.

## 5. AI-enabled services

For services that analyze company or customer documents using AI:

- the vendor must state whether Customer Data trains shared models;
- users must be told that model output requires human review;
- prohibited data categories must be documented;
- the reviewer must identify material model, subprocessor, and data-location dependencies;
- final approval remains with an authorized employee.

An AI-generated recommendation is evidence for consideration, not an approval and not proof that a vendor statement is true.

## 6. Conditional decisions

An authorized approver may approve with conditions when no blocking control remains. Conditions must be specific, assigned, and reviewable. Examples include renegotiating a non-blocking contract clause before renewal, limiting the initial user group, or completing a control review within 30 days.

Conditional approval cannot waive EU/EEA residency confirmation or an executed DPA where Customer Data is in scope.

## 7. Records and overrides

Every decision must record:

- documents reviewed and their versions;
- missing or conflicting evidence;
- policy rules evaluated and their versions;
- approver role and declared identity;
- decision, conditions, and timestamp;
- justification for any permitted override.

Where an override is permitted, justification is mandatory. Price routing, EU/EEA residency, executed-DPA requirements, and unresolved conflicts cannot be hidden or silently marked as passed.

Approved by: Demo Director, Caldera Works Europe S.A.S.  
Document status: Current fictional policy for Build Week evaluation.
