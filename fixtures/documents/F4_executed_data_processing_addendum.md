# F4 — Nerythica AI Data Processing Addendum

> FICTIONAL BUILD WEEK DEMO DOCUMENT — 34-PAGE PRINT FIXTURE — NOT LEGAL ADVICE

## Page 1 of 34 — Cover and document control

**DATA PROCESSING ADDENDUM**  
**Document reference:** NYA-DPA-EU-2026-04
**Form proposed by:** Nerythica AI Ltd.
**Executed for:** Caldera Works Europe S.A.S.  
**Effective date:** 2026-07-12  
**DPA version:** 4.3

This Data Processing Addendum (the **DPA**) forms part of the Master Subscription Agreement and enterprise order documentation between Caldera Works Europe S.A.S. (**Customer**, **Controller**) and Nerythica AI Ltd. (**Nerythica**, **Processor**) for the Nerythica Workspace Enterprise service.

This fixture is intentionally long. Material terms appear throughout the document and must be evaluated together with the commercial proposal, security questionnaire, internal procurement policy, and later written assurance. Page numbers are fixed for the Build Week demonstration so a cited passage can be located deterministically.

### Document status

- Vendor-proposed standard form: yes
- Executed by both fictional parties: yes; see page 34
- Customer-specific EU-only order-form commitment at execution: no
- Later supplemental assurance: see separate fixture F5
- Incorporated schedules: Annex I, Annex II, subprocessor schedule, and applicable transfer modules

No person, organization, address, signature, certificate, or service described in this document is real.

*NYA-DPA-EU-2026-04 · Page 1 of 34*

<div style="page-break-after: always;"></div>

## Page 2 of 34 — Table of contents

1. Purpose, scope, and precedence ........................................ 3  
2. Definitions .......................................................... 4  
3. Roles and documented instructions .................................... 5  
4. Compliance and cooperation ........................................... 6  
5. Confidentiality ...................................................... 7  
6. Security programme ................................................... 8  
6.1 Identity and access management ...................................... 9  
6.2 Encryption and key management ...................................... 10  
6.3 Testing and vulnerability management ............................... 11  
7. Incident management ................................................. 12  
7.1 Personal Data Breach notice ........................................ 13  
8. Data-subject requests ................................................ 14  
8.1 Impact assessments and consultation ................................ 15  
8.2 Records, evidence, and audits ....................................... 16  
8.3 Retention .......................................................... 17  
8.4 Return and deletion ................................................ 18  
8.5 Continuity and restoration ......................................... 19  
9. Subprocessor principles .............................................. 20  
9.1 Current subprocessor schedule ...................................... 21  
9.2 Due diligence and contractual flow-down ............................ 22  
9.6 Appointment, changes, and cross-border processing ................... 23  
10. Transfer mechanisms ................................................. 24  
10.1 Government-access requests ........................................ 25  
11. AI-specific processing .............................................. 26  
11.1 Telemetry and service improvement ................................. 27  
12. Data location and regional configuration ........................... 28  
13. Customer responsibilities .......................................... 29  
14. Liability, order of precedence, and changes ......................... 30  
15. Term and termination ................................................ 31  
Annex I — Processing details ............................................ 32  
Annex II — Technical and organizational measures ....................... 33  
Execution page .......................................................... 34

Headings are descriptive. The complete clause text, not the table of contents, governs interpretation.

*NYA-DPA-EU-2026-04 · Page 2 of 34*

<div style="page-break-after: always;"></div>

## Page 3 of 34 — 1. Purpose, scope, and precedence

### 1.1 Purpose

This DPA governs Nerythica's Processing of Personal Data on Customer's behalf in connection with the Service. It allocates responsibilities for confidentiality, security, assistance, retention, subprocessors, international transfers, and deletion.

### 1.2 Scope

This DPA applies when Customer or an authorized user submits Personal Data to the Service, or when Nerythica otherwise Processes Personal Data to provide, secure, support, or maintain the Service. It does not govern data for which Nerythica independently determines purposes and means and acts as a separate Controller, except where Applicable Data Protection Law requires additional terms.

### 1.3 Incorporated documents

The Agreement, order form, security schedule, and this DPA form one contract. The Annexes form part of this DPA. Online documentation does not override an executed customer-specific term unless the Agreement expressly says otherwise.

### 1.4 Precedence

For Personal Data Processing, this DPA prevails over inconsistent general terms. A customer-specific order-form data-location commitment prevails over the default location language in section 12. The Standard Contractual Clauses prevail to the extent required for a Restricted Transfer. Commercial pricing and user quantities remain governed by the order form.

### 1.5 No legal conclusion

Execution of this DPA records agreed processing instructions and safeguards. It does not by itself establish that either party complies with every law, that a Service configuration is suitable for every data category, or that Customer has completed its internal approval process.

*NYA-DPA-EU-2026-04 · Page 3 of 34*

<div style="page-break-after: always;"></div>

## Page 4 of 34 — 2. Definitions

**Affiliate** means an entity controlling, controlled by, or under common control with a party.

**Applicable Data Protection Law** means law applicable to the Processing under the Agreement, including the GDPR where relevant.

**Authorized User** means a person whom Customer permits to use the Service.

**Controller**, **Data Subject**, **Personal Data**, **Personal Data Breach**, **Processing**, and **Processor** have the meanings given by Applicable Data Protection Law.

**Customer Content** means information submitted to, stored in, or generated for Customer through the Service, excluding Nerythica's own account, billing, and aggregated service-administration data.

**Customer Data** means Customer Content that constitutes Personal Data.

**Documentation** means the then-current technical and user materials for the Service.

**EEA** means the European Economic Area.

**Restricted Transfer** means a transfer of Personal Data requiring a transfer mechanism under Applicable Data Protection Law.

**Security Incident** means unauthorized access to, acquisition of, alteration of, or loss of systems used to Process Customer Data. It excludes unsuccessful attempts that do not compromise Customer Data, such as blocked scans, pings, or failed authentication attempts.

**Service** means Nerythica Workspace Enterprise and the hosted features identified in the applicable order form.

**Standard Contractual Clauses** or **SCCs** means the European Commission standard clauses adopted by Implementing Decision (EU) 2021/914, as amended or replaced.

**Subprocessor** means a third party engaged by Nerythica to Process Customer Data on Customer's behalf. A network carrier acting only as a conduit is not a Subprocessor for this definition.

Terms such as “including” are illustrative and not limiting. Singular includes plural where the context permits.

*NYA-DPA-EU-2026-04 · Page 4 of 34*

<div style="page-break-after: always;"></div>

## Page 5 of 34 — 3. Roles and documented instructions

### 3.1 Roles

Customer is Controller and Nerythica is Processor for Customer Data. Where Customer acts as Processor for another Controller, Nerythica acts as Customer's Subprocessor and Customer represents that its instructions are authorized by the relevant Controller.

### 3.2 Instructions

Nerythica will Process Customer Data only on documented instructions from Customer, including to provide the Service, comply with configured settings, prevent abuse, maintain security, provide support, and perform obligations in the Agreement. The Agreement, authorized use of the Service, support requests, and lawful configuration changes constitute documented instructions.

### 3.3 Legally required Processing

If law requires Nerythica to Process Customer Data beyond Customer's instructions, Nerythica will inform Customer before Processing unless law prohibits notice on important public-interest grounds.

### 3.4 Unlawful instructions

Nerythica will inform Customer if it reasonably believes an instruction infringes Applicable Data Protection Law. Nerythica may suspend the affected Processing while the parties clarify the instruction, without deciding Customer's legal obligations for it.

### 3.5 Customer control

Customer determines which Authorized Users receive access, which documents they submit, what retention settings they select, and whether AI-assisted output is used in a business process. Nerythica does not become the decision maker merely by generating or organizing output.

### 3.6 Purpose limitation

Nerythica will not sell Customer Data or use it for targeted advertising. AI-specific restrictions, including model-training treatment, appear in section 11.

*NYA-DPA-EU-2026-04 · Page 5 of 34*

<div style="page-break-after: always;"></div>

## Page 6 of 34 — 4. Compliance and cooperation

### 4.1 Processor obligations

Nerythica will implement the measures described in this DPA, make available information reasonably necessary to demonstrate those measures, and cooperate with Customer as required for Customer's documented obligations relating to Customer Data.

### 4.2 Customer obligations

Customer is responsible for the lawfulness, accuracy, quality, and collection of Customer Data; required notices and consents; its instructions; and its Authorized Users. Customer will not direct Nerythica to Process prohibited data categories unless the parties have expressly agreed appropriate controls.

### 4.3 Requests for information

Cooperation is subject to reasonable scope, confidentiality, security, and effort controls. Nerythica may satisfy repeated or broad requests through current audit reports, certifications, security documentation, written responses, or a scoped meeting.

### 4.4 Regulatory cooperation

If a supervisory authority contacts Nerythica directly about Customer Data, Nerythica will notify Customer unless prohibited and will not represent Customer's position without authorization. Customer remains responsible for its regulatory communications.

### 4.5 Changes in law

The parties will discuss in good faith amendments reasonably necessary because of a binding change in Applicable Data Protection Law. Neither party is required to accept a change that materially expands the Service without corresponding commercial agreement.

### 4.6 Costs

Ordinary assistance included in Nerythica's standard compliance programme is included in subscription fees. Nerythica may charge reasonable pre-agreed fees for bespoke, repetitive, or unusually burdensome assistance not caused by its breach.

*NYA-DPA-EU-2026-04 · Page 6 of 34*

<div style="page-break-after: always;"></div>

## Page 7 of 34 — 5. Confidentiality

### 5.1 Personnel confidentiality

Nerythica ensures that personnel authorized to Process Customer Data are bound by statutory or contractual confidentiality obligations. Authorization is limited to people who require access for their role.

### 5.2 Access approval

Production access requires documented approval, role-based assignment, and authentication controls. Privileged access is reviewed periodically and removed when no longer required.

### 5.3 Support access

Support personnel may access Customer Data only when needed to resolve an authorized support case, investigate abuse or a Security Incident, or perform a documented instruction. Support access is logged where technically feasible and may involve personnel in approved support locations subject to section 12 and applicable transfer measures.

### 5.4 Confidentiality survives termination

Confidentiality duties survive termination for as long as the information remains confidential or Applicable Data Protection Law requires protection.

### 5.5 Disclosure controls

Nerythica will not disclose Customer Data to a third party except to an authorized Subprocessor, as instructed by Customer, or as legally required. Before a lawful disclosure where notice is permitted, Nerythica will provide available information so Customer can seek protective measures.

### 5.6 Training and awareness

Personnel with relevant access receive security and privacy awareness training at onboarding and periodically thereafter. Specialized teams receive additional role-based training.

These commitments do not replace Customer's responsibility to limit the documents and data categories submitted to the Service.

*NYA-DPA-EU-2026-04 · Page 7 of 34*

<div style="page-break-after: always;"></div>

## Page 8 of 34 — 6. Security programme

### 6.1 Programme

Nerythica maintains a written information-security programme designed to protect Customer Data against accidental or unlawful destruction, loss, alteration, unauthorized disclosure, and unauthorized access. Measures are proportionate to the Service, available technology, implementation cost, and risks to Data Subjects.

### 6.2 Governance

The programme assigns security responsibilities, includes management review, documents material risks, and tracks remediation. Policies address access, cryptography, change management, incident response, resilience, vendor risk, vulnerability management, and secure development.

### 6.3 Risk assessment

Nerythica periodically evaluates threats and control effectiveness. Material findings are assigned owners and target dates. Risk acceptance requires an authorized role.

### 6.4 Change management

Material production changes are reviewed, tested, approved, and logged according to risk. Emergency changes may use an accelerated process followed by retrospective review.

### 6.5 Secure development

Development environments are logically separated from production. Source changes use version control and review. Secrets must not be hard-coded in source. Dependency and code scanning are used according to risk.

### 6.6 Shared responsibility

Security depends on Customer configuration and Authorized User behavior as well as Nerythica controls. Customer is responsible for SSO configuration, account lifecycle, role assignment, appropriate source documents, endpoint security, and review of AI-assisted output.

Annex II summarizes controls and is not an exhaustive security architecture disclosure.

*NYA-DPA-EU-2026-04 · Page 8 of 34*

<div style="page-break-after: always;"></div>

## Page 9 of 34 — 6.1 Identity and access management

### 6.1.1 Workforce identity

Nerythica assigns unique workforce identities and prohibits shared privileged accounts except controlled emergency credentials. Multi-factor authentication is required for administrative access to production infrastructure.

### 6.1.2 Least privilege

Access is granted according to least privilege and job responsibility. Privileged roles require additional approval. Access is adjusted upon role change and disabled promptly after termination.

### 6.1.3 Reviews

Privileged production access is reviewed at least quarterly. Other sensitive access is reviewed according to system risk. Review records identify the reviewer, scope, findings, and remediation.

### 6.1.4 Authentication

Nerythica uses centrally managed authentication where feasible, password standards, session controls, and device-security requirements. Service accounts use managed credentials or workload identity where supported.

### 6.1.5 Customer identity

Enterprise Customer may configure SAML-based single sign-on. Customer controls user provisioning and deprovisioning unless a separate automated-provisioning feature is enabled.

### 6.1.6 Logging

Authentication and privileged administrative events are logged. Logs are protected against ordinary user modification and retained according to operational and security requirements.

### 6.1.7 Break-glass access

Emergency access is limited, monitored, and reviewed after use. Emergency access does not eliminate transfer or confidentiality obligations.

*NYA-DPA-EU-2026-04 · Page 9 of 34*

<div style="page-break-after: always;"></div>

## Page 10 of 34 — 6.2 Encryption and key management

### 6.2.1 Transit

Customer Data is encrypted in transit over public networks using TLS 1.2 or later where supported by the communicating system. Nerythica disables obsolete protocols according to its security baseline.

### 6.2.2 Storage

Production databases, object storage, and managed backups containing Customer Data use encryption at rest through cloud-provider or application controls. The stated control does not mean every transient memory buffer is separately encrypted.

### 6.2.3 Key management

Cryptographic keys are access-controlled, logically separated from protected data where feasible, and rotated according to key type, provider capability, and risk. Key-management activity is restricted to authorized roles.

### 6.2.4 Secrets

Application secrets are stored in managed secret systems or equivalent protected configuration. Source repositories must not contain live production secrets.

### 6.2.5 Customer-managed keys

Customer-managed encryption keys are not supported in the proposed Service configuration. This limitation is disclosed for review and is not changed by execution of this DPA.

### 6.2.6 Passwords and tokens

Passwords are stored using appropriate one-way derivation. Access tokens are scoped and expire according to their use. Long-lived credentials are avoided where workload identity is available.

Encryption reduces certain risks but does not establish that every access, purpose, or transfer is lawful or appropriate.

*NYA-DPA-EU-2026-04 · Page 10 of 34*

<div style="page-break-after: always;"></div>

## Page 11 of 34 — 6.3 Testing and vulnerability management

### 6.3.1 Scanning

Nerythica performs vulnerability scanning of relevant infrastructure, applications, containers, and dependencies on a risk-based schedule. Findings are prioritized by severity, exploitability, exposure, and compensating controls.

### 6.3.2 Remediation

Target remediation periods are defined internally. A target is not a warranty that every finding is fixed within the same period, but overdue material risks require documented treatment.

### 6.3.3 Penetration testing

An independent provider performs penetration testing at least annually against material Service surfaces. Nerythica tracks findings and may provide an executive summary subject to confidentiality.

### 6.3.4 Secure release

Material releases undergo automated or manual checks appropriate to risk. High-risk changes require peer review and testing before deployment, except documented emergency changes.

### 6.3.5 Customer testing

Customer may not perform intrusive testing without Nerythica's prior written authorization. A coordinated-testing request must identify scope, timing, source addresses, methods, and contacts. Nerythica may impose safety conditions.

### 6.3.6 Responsible disclosure

Nerythica maintains a channel for security reports and investigates credible submissions. Disclosure terms do not authorize access to other customers' data.

### 6.3.7 Assurance status

As of this DPA's effective date, the parties' questionnaire records Nerythica's SOC 2 Type II examination as in progress. This DPA does not convert an unfinished examination into an issued report.

*NYA-DPA-EU-2026-04 · Page 11 of 34*

<div style="page-break-after: always;"></div>

## Page 12 of 34 — 7. Incident management

### 7.1 Response plan

Nerythica maintains an incident-response plan defining preparation, identification, containment, investigation, recovery, communication, and lessons learned. Relevant personnel participate in exercises at least annually.

### 7.2 Triage

Suspected events are triaged according to severity and potential impact. Nerythica may preserve evidence, restrict access, isolate resources, rotate credentials, or suspend affected features during investigation.

### 7.3 Customer cooperation

Customer will provide information reasonably necessary to investigate an incident involving Customer accounts, including relevant user activity, configuration, endpoints, and support records.

### 7.4 Communications

Operational security communications use designated contacts. Customer must maintain current security and privacy contacts. Public statements referring to the other party require coordination unless law requires otherwise.

### 7.5 No admission

Incident notification, investigation, or assistance is not an admission of fault or liability. Each party retains its own legal analysis and notification obligations.

### 7.6 Evidence protection

Nerythica restricts access to incident evidence and retains it according to investigative, contractual, and legal needs. Sharing may be limited to protect other customers, personnel, systems, legal privilege, or active investigations.

### 7.7 Unsuccessful events

Routine blocked attacks, unsuccessful logins, scans, and events that do not compromise Customer Data are not Personal Data Breaches and do not individually trigger customer notice.

*NYA-DPA-EU-2026-04 · Page 12 of 34*

<div style="page-break-after: always;"></div>

## Page 13 of 34 — 7.1 Personal Data Breach notice

### 7.1.1 Notice

Nerythica will notify Customer without undue delay after confirming a Personal Data Breach affecting Customer Data. Notice will be sent to Customer's designated security or privacy contact.

### 7.1.2 Available information

As information becomes reasonably available, notice will describe:

- the nature of the Personal Data Breach;
- affected data categories and approximate scope, if known;
- likely consequences identified by Nerythica;
- containment and remediation measures taken or planned;
- a contact for follow-up.

Information may be provided in phases when complete details are unavailable at initial notice.

### 7.1.3 Customer responsibility

Customer determines whether it must notify a supervisory authority, Data Subject, customer, insurer, or other party. Nerythica will provide reasonable assistance but does not make Customer's legal notification decision.

### 7.1.4 Investigation updates

Nerythica will provide material updates and a summary after containment when reasonably appropriate. Detailed forensic material may be restricted to protect security, privilege, confidentiality, or other customers.

### 7.1.5 Contact accuracy

Delay caused solely by Customer's failure to maintain a working notice contact does not breach the timing obligation if Nerythica used the current contact in its records.

### 7.1.6 Mitigation

Both parties will take reasonable steps within their control to mitigate harm and prevent recurrence.

*NYA-DPA-EU-2026-04 · Page 13 of 34*

<div style="page-break-after: always;"></div>

## Page 14 of 34 — 8. Data-subject requests

### 8.1 Customer responsibility

Customer is responsible for responding to Data Subject requests concerning Customer Data. The Service may provide search, export, correction, restriction, or deletion features that Customer can use directly.

### 8.2 Processor assistance

Taking account of the nature of Processing, Nerythica will provide reasonable assistance through available Service functionality and, where necessary, scoped technical support.

### 8.3 Direct requests

If Nerythica receives a request from a Data Subject that identifies Customer, Nerythica will direct the requester to Customer where reasonably possible and notify Customer unless prohibited. Nerythica will not independently respond on Customer's behalf without authorization or legal obligation.

### 8.4 Verification

Customer is responsible for verifying requester identity and authority. Nerythica may require Customer authentication before acting on an instruction.

### 8.5 Limitations

Assistance is subject to rights of others, security, confidentiality, legal holds, backup architecture, and data that Nerythica cannot reasonably associate with the requester based on information supplied.

### 8.6 Timing

Customer should submit assistance requests promptly and include case identifiers, data scope, requested action, and deadline. Nerythica does not warrant completion by a deadline that was not reasonably communicated.

### 8.7 Costs

Standard self-service functionality is included. Unusually complex assistance may be charged only after the parties agree scope and fees, unless the need results from Nerythica's breach.

*NYA-DPA-EU-2026-04 · Page 14 of 34*

<div style="page-break-after: always;"></div>

## Page 15 of 34 — 8.1 Impact assessments and consultation

### 8.1.1 Assistance

Nerythica will provide information reasonably available about the Service to assist Customer with a data-protection impact assessment or prior consultation that Applicable Data Protection Law requires.

### 8.1.2 Available materials

Assistance may include this DPA, security documentation, data-flow descriptions, subprocessor information, retention details, assurance reports, and written answers. Nerythica is not required to disclose source code, penetration-test details, information about other customers, or privileged material.

### 8.1.3 Customer analysis

Customer determines whether an impact assessment is required and remains responsible for its content, risk acceptance, consultation, and final Processing decision.

### 8.1.4 AI-assisted features

Customer should consider the categories of documents submitted, affected people, consequences of inaccurate output, human review, access, retention, and whether a proposed use makes or materially supports a high-impact decision.

### 8.1.5 Changes

Nerythica may provide generally available notices of material Service or security changes. Customer is responsible for assessing whether a change affects its impact assessment.

### 8.1.6 No professional advice

Nerythica's materials describe the Service and do not constitute Customer-specific legal advice or regulatory approval. A technical control may reduce risk without resolving lawfulness or appropriateness.

### 8.1.7 Consultation support

If a supervisory authority requests Service-specific information, Nerythica will reasonably support Customer, subject to confidentiality and an agreed communication process.

*NYA-DPA-EU-2026-04 · Page 15 of 34*

<div style="page-break-after: always;"></div>

## Page 16 of 34 — 8.2 Records, evidence, and audits

### 8.2.1 Information

Nerythica will make available information reasonably necessary to demonstrate compliance with its Processor obligations under this DPA.

### 8.2.2 Assurance-first approach

Customer will first use current independent reports, certifications, summaries, questionnaires, and other documentation. If those materials do not reasonably address a material concern, Customer may request additional information.

### 8.2.3 Audit right

Where legally required and assurance materials remain insufficient, Customer may conduct one audit in a twelve-month period on at least 30 days' written notice. Additional audits may occur after a confirmed Personal Data Breach or binding authority request.

### 8.2.4 Audit conditions

Audits must occur during business hours, minimize disruption, follow security requirements, protect other customers, and use an independent auditor that is not Nerythica's competitor. Scope must relate to Customer Data and obligations under this DPA.

### 8.2.5 Findings

The parties will discuss substantiated material findings and reasonable remediation. Audit reports are Nerythica Confidential Information unless law requires disclosure.

### 8.2.6 Costs

Customer bears its audit costs. Nerythica bears ordinary cooperation costs, but may charge pre-agreed fees for excessive scope unless the audit identifies Nerythica's material breach.

### 8.2.7 No continuous access

This clause does not grant continuous monitoring, physical access to shared cloud facilities, or access to source code.

*NYA-DPA-EU-2026-04 · Page 16 of 34*

<div style="page-break-after: always;"></div>

## Page 17 of 34 — 8.3 Retention

### 8.3.1 Active term

Nerythica retains Customer Data during the Agreement term as necessary to provide the Service and according to Customer actions and configured retention settings.

### 8.3.2 Customer deletion

Authorized Users may delete supported content through the Service. Deletion from active systems follows the Service workflow and may not immediately remove copies from backups, security logs, or legal holds.

### 8.3.3 Logs

Security, access, and operational logs may be retained for periods appropriate to security, troubleshooting, fraud prevention, contractual evidence, and legal requirements. Logs are minimized where reasonably feasible.

### 8.3.4 Backups

Encrypted backups use rolling retention and ordinarily expire within 90 days after deletion from active systems. Restored backup data remains subject to deletion workflows before ordinary use.

### 8.3.5 Legal retention

Nerythica may retain limited data where law requires, provided it isolates the data from ordinary use and continues to protect it.

### 8.3.6 Aggregated information

Information irreversibly aggregated so that it no longer constitutes Personal Data is outside Customer Data retention instructions, subject to Applicable Data Protection Law.

### 8.3.7 Configuration

Customer must select and document appropriate retention settings. Default retention is not a conclusion that the period is appropriate for Customer's purpose.

*NYA-DPA-EU-2026-04 · Page 17 of 34*

<div style="page-break-after: always;"></div>

## Page 18 of 34 — 8.4 Return and deletion

### 8.4.1 Export

During the Agreement term and any stated retrieval period, Customer may export supported Customer Data using available Service functionality.

### 8.4.2 Termination

Following termination or expiration, Nerythica will make Customer Data available for export for 30 days unless the order form states otherwise. Customer is responsible for completing export within that period.

### 8.4.3 Active-system deletion

After the retrieval period, Nerythica will delete Customer Data from active production systems within 45 days, except where retention is legally required.

### 8.4.4 Backup expiry

Residual backup copies expire through ordinary rotation, normally within 90 additional days. Backup copies are protected and not restored except for continuity or security needs.

### 8.4.5 Certification

On written request, Nerythica will provide a statement that deletion workflows have been initiated or completed, subject to backup and legal-retention exceptions.

### 8.4.6 Return format

Export formats are those supported by the Service. Bespoke transformation or migration services require separate agreement.

### 8.4.7 Credentials and local copies

Customer must remove integrations, tokens, downloaded exports, and local copies under its control. Nerythica's deletion does not delete copies Customer or its users created outside the Service.

*NYA-DPA-EU-2026-04 · Page 18 of 34*

<div style="page-break-after: always;"></div>

## Page 19 of 34 — 8.5 Continuity and restoration

### 8.5.1 Programme

Nerythica maintains business-continuity and disaster-recovery procedures for material Service components. Procedures identify responsibilities, communication, backup, restoration, and dependency considerations.

### 8.5.2 Objectives

The proposed Service targets a recovery time objective of 12 hours for core functionality and a recovery point objective of 24 hours. Targets are planning objectives, not service-level guarantees unless the order form expressly states them.

### 8.5.3 Testing

Nerythica tests sample restoration at least quarterly and performs broader continuity exercises periodically. Material findings are tracked.

### 8.5.4 Dependencies

Recovery depends on cloud infrastructure, communications, identity services, model providers, and other Subprocessors. Nerythica evaluates material dependencies and maintains alternatives or recovery procedures according to risk.

### 8.5.5 Customer planning

Customer should maintain appropriate exports, contingency procedures, and human decision processes for interruption. The Service is not designed as the sole system of record for emergency, medical, safety-critical, or time-critical legal decisions.

### 8.5.6 Incident priority

During a major incident, Nerythica may prioritize containment and restoration over ordinary support requests or feature delivery.

### 8.5.7 Regional restoration

Restoration location follows the active customer-specific regional commitment, if any, subject to emergency measures permitted by law and contract. Default regional terms appear in section 12.

*NYA-DPA-EU-2026-04 · Page 19 of 34*

<div style="page-break-after: always;"></div>

## Page 20 of 34 — 9. Subprocessor principles

### 9.1 General authorization

Customer gives Nerythica general written authorization to engage Subprocessors subject to this section. Nerythica remains responsible for each Subprocessor's performance of data-protection obligations to the extent required by Applicable Data Protection Law.

### 9.2 Selection

Nerythica evaluates a prospective Subprocessor's security, privacy, service capability, location, and relevant assurance before authorizing Processing of Customer Data.

### 9.3 Contract

Nerythica imposes written data-protection obligations that provide protection appropriate to the Processing and materially consistent with applicable Processor obligations in this DPA.

### 9.4 Scope limitation

A Subprocessor receives access only for defined services and according to documented arrangements. Nerythica restricts access according to role and technical need where feasible.

### 9.5 List

Nerythica maintains a current subprocessor list in its customer trust portal. The list identifies entity name, service purpose, and primary Processing country or region. Customer is responsible for maintaining an active trust-portal subscription if it wishes to receive portal updates.

The following pages identify the schedule supplied at execution, due-diligence controls, change mechanism, objection process, and transfer provisions. A questionnaire answer or sales statement does not amend these clauses unless incorporated into an executed written amendment.

*NYA-DPA-EU-2026-04 · Page 20 of 34*

<div style="page-break-after: always;"></div>

## Page 21 of 34 — 9.1 Current subprocessor schedule

The following fictional entities are authorized as of the Effective Date:

| Subprocessor | Purpose | Primary processing locations |
|---|---|---|
| Nimbus Compute Europe GmbH | EU application hosting, databases, object storage | Germany, Ireland |
| Nimbus Compute Inc. | Global traffic protection and emergency infrastructure support | United States, global edge |
| Vector Forge Europe B.V. | Model inference routing for EU-configured tenants | Netherlands |
| Vector Forge Inc. | Model operations and overflow inference | United States |
| Signal Harbor Ltd. | Security monitoring and incident alerting | Ireland, United Kingdom |
| Support Loom Pte. Ltd. | Customer-support ticket platform | Singapore, Germany |
| Ledger Finch S.A. | Subscription billing metadata; no document content intended | France |
| Mail Arc Systems Inc. | Transactional email | United States |

The list distinguishes intended use but does not guarantee that every network packet, operational record, or exceptional support activity remains in the primary location. Customer-specific regional commitments modify eligible Processing only to the extent expressly stated.

Billing contact details and account administration may be processed separately from Customer Content. This schedule does not authorize a Subprocessor to use Customer Data for its own advertising or unrelated model training.

Customer acknowledges receipt of this schedule as of execution. Subsequent appointments and location changes are governed by the following clauses, including section 9.6 on page 23.

*NYA-DPA-EU-2026-04 · Page 21 of 34*

<div style="page-break-after: always;"></div>

## Page 22 of 34 — 9.2 Due diligence and contractual flow-down

### 9.2.1 Review

Before granting access to Customer Data, Nerythica assesses a Subprocessor using information proportionate to service and data risk. Review may consider assurance reports, security questionnaires, architecture, incident history, transfer locations, financial resilience, and contractual protections.

### 9.2.2 Approval

A designated Nerythica owner approves the engagement. Material unresolved risks require documented treatment or acceptance.

### 9.2.3 Terms

Subprocessor terms address confidentiality, security, restricted purpose, incident notice, deletion or return, assistance, and transfer mechanisms as applicable. Nerythica may use a provider's standard terms when they meet legal and risk requirements.

### 9.2.4 Monitoring

Nerythica periodically reviews material Subprocessors. Frequency depends on service criticality, access, location, and available assurance.

### 9.2.5 Incident coordination

Subprocessor incident notices are escalated through Nerythica's incident process. Nerythica remains Customer's contractual contact and may combine information from multiple parties during investigation.

### 9.2.6 Termination

Nerythica may suspend or replace a Subprocessor that no longer provides appropriate protection. Migration timing may reflect security, continuity, technical feasibility, and contractual obligations.

### 9.2.7 Evidence limits

Customer may request reasonable information about a material Subprocessor, subject to confidentiality and provider restrictions. Nerythica is not required to disclose another provider's confidential audit report directly if a summary reasonably addresses the request.

*NYA-DPA-EU-2026-04 · Page 22 of 34*

<div style="page-break-after: always;"></div>

## Page 23 of 34 — 9.6 Appointment, changes, and cross-border processing

### 9.6.1 Operational appointment right

Notwithstanding any questionnaire response, trust-portal practice, or other general statement, Customer authorizes Nerythica to appoint, replace, or change a Subprocessor when Nerythica reasonably considers the change necessary for security, availability, capacity, support, legal compliance, or Service development.

### 9.6.2 No prior-notice obligation

**Nerythica may authorize a new or replacement Subprocessor to Process Customer Data, and may permit that Processing to occur outside the EEA, without providing Customer prior notice, provided that Nerythica updates its online subprocessor list within a commercially reasonable period and implements a transfer mechanism where Applicable Data Protection Law requires one.** Customer is deemed to have accepted the appointment when the updated list is published.

### 9.6.3 Post-publication objection

Customer may object on reasonable data-protection grounds by written notice received within ten calendar days after publication of the updated list. The objection must identify the affected Processing and specific grounds.

### 9.6.4 Resolution

Nerythica may respond by providing additional safeguards, proposing a configuration that avoids the Subprocessor, delaying affected Processing where feasible, or offering termination of the affected feature. If the parties cannot resolve the objection within 30 days, Customer's sole remedy is to stop using or terminate the affected feature; fees already committed remain governed by the Agreement.

### 9.6.5 Emergency changes

Nerythica may make an immediate change without prior or simultaneous publication where delay would materially threaten security, continuity, or legal compliance. Nerythica will update the list after the emergency when reasonably practicable.

### 9.6.6 Conflict acknowledgement

This section does not promise the 30 days' advance notice stated in questionnaire response SUB-02. The executed DPA controls unless the parties sign a specific amendment.

*NYA-DPA-EU-2026-04 · Page 23 of 34*

<div style="page-break-after: always;"></div>

## Page 24 of 34 — 10. Transfer mechanisms

### 10.1 Restricted Transfers

Where Nerythica's Processing of Customer Data constitutes a Restricted Transfer, the parties will rely on an available lawful mechanism, including an adequacy decision or the SCCs as applicable.

### 10.2 SCC modules

For an EEA Controller-to-Processor transfer, Module Two applies. For an EEA Processor-to-Processor transfer, Module Three applies. Docking and other optional clauses apply only where stated in Annex I or required by the circumstances.

### 10.3 Supplemental measures

Nerythica evaluates technical, contractual, and organizational supplemental measures appropriate to the transfer, including encryption, access control, request review, transparency, and data minimization.

### 10.4 Transfer assessment

Each party will provide information reasonably necessary for the other's transfer assessment. Customer remains responsible for determining whether its instructions and use are lawful.

### 10.5 Alternative mechanism

If a relied-on mechanism becomes unavailable, the parties will cooperate to implement a valid alternative. Nerythica may suspend affected Processing if no lawful mechanism is reasonably available.

### 10.6 Precedence

The SCCs prevail over conflicting commercial terms to the extent of the conflict. This section does not itself create an EU-only residency commitment; residency restrictions require a customer-specific written term under section 12.

### 10.7 United Kingdom and Switzerland

Where relevant, the SCCs are adapted through the recognized UK addendum or Swiss modifications unless another lawful mechanism applies.

*NYA-DPA-EU-2026-04 · Page 24 of 34*

<div style="page-break-after: always;"></div>

## Page 25 of 34 — 10.1 Government-access requests

### 10.1.1 Review

Nerythica reviews a binding government request for Customer Data to determine validity, authority, scope, and whether challenge or narrowing is reasonably available.

### 10.1.2 Notice

Nerythica will notify Customer before disclosure unless legally prohibited. If prohibited, Nerythica may seek permission to notify where reasonably appropriate.

### 10.1.3 Minimization

Nerythica will disclose only data reasonably required by a valid request and will use available channels intended for lawful requests.

### 10.1.4 Challenge

Nerythica may challenge a request it reasonably believes is unlawful, overbroad, or inconsistent with applicable protections, taking account of legal advice and potential harm.

### 10.1.5 Transparency

Where legally permitted, Nerythica may publish aggregate transparency information. Aggregate reporting may omit categories where disclosure would create security or legal risk.

### 10.1.6 Emergency requests

Nerythica may respond to a good-faith emergency request involving imminent risk of death or serious physical harm where law permits, and will document the basis for the response.

### 10.1.7 Subprocessors

Nerythica contractually requires material Subprocessors to handle government requests according to applicable law and to notify Nerythica when permitted.

These measures reduce but cannot eliminate legal-access risk in every jurisdiction.

*NYA-DPA-EU-2026-04 · Page 25 of 34*

<div style="page-break-after: always;"></div>

## Page 26 of 34 — 11. AI-specific processing

### 11.1 Service purpose

The Service uses machine-learning models to analyze prompts and Customer Content, generate text, extract structured information, compare documents, and support customer-configured workflows.

### 11.2 No autonomous authority

Nerythica provides generated output for Customer review. The Service does not receive authority under this DPA to make final legal, employment, procurement, credit, medical, or similarly consequential decisions for Customer.

### 11.3 Shared-model training

Nerythica will not use Customer Content from an enterprise tenant to train a shared foundation model unless Customer gives separate express written authorization. Customer Content may be processed transiently by an authorized model Subprocessor to provide the requested output.

### 11.4 Quality and accuracy

Model output may be incomplete, inconsistent, or incorrect. Customer must use qualified human review appropriate to the use case. A citation generated by a model is not proof that the cited statement is true.

### 11.5 Safety and abuse

Nerythica may Process prompts, outputs, account signals, and limited Customer Content to detect abuse, investigate a Security Incident, enforce agreed restrictions, or comply with law, subject to access and retention controls.

### 11.6 Model changes

Nerythica may update models and routing to maintain or improve the Service. Material changes remain subject to the Agreement and applicable subprocessor terms; no fixed model version is promised unless the order form states one.

### 11.7 Prohibited categories

Customer will not submit special-category data or highly sensitive regulated records unless expressly approved with suitable controls.

*NYA-DPA-EU-2026-04 · Page 26 of 34*

<div style="page-break-after: always;"></div>

## Page 27 of 34 — 11.1 Telemetry and service improvement

### 11.1.1 Operational telemetry

Nerythica collects service telemetry such as request timing, error type, model route, token or processing-unit counts, feature use, security events, and system performance.

### 11.1.2 Content minimization

Telemetry is designed to avoid full Customer Content where feasible. Limited content fragments may appear in controlled diagnostic records when necessary to investigate a support case, abuse report, or failure.

### 11.1.3 Improvement

Nerythica may use aggregated or de-identified telemetry to improve reliability, capacity planning, interface design, abuse prevention, and operational models. It will not represent data as de-identified if re-identification remains reasonably likely.

### 11.1.4 Human access

Authorized personnel may inspect limited content for an approved support or security purpose. Access is subject to confidentiality and logging controls.

### 11.1.5 Feedback

Customer may submit feedback and may choose to include example output. Feedback does not authorize use of unrelated Customer Content for shared-model training.

### 11.1.6 Retention

Telemetry retention varies by category and purpose. Security logs may be retained longer than routine performance metrics. Customer-specific retention documentation is available through the trust process.

### 11.1.7 Controller data

Business contact, billing, and account-administration data may be processed by Nerythica as an independent Controller for contract administration, security, and legal obligations, as described in its privacy notice.

*NYA-DPA-EU-2026-04 · Page 27 of 34*

<div style="page-break-after: always;"></div>

## Page 28 of 34 — 12. Data location and regional configuration

### 12.1 Default architecture

The Service uses global cloud infrastructure and may Process Customer Data in the United States, European Union, and other locations where Nerythica or an authorized Subprocessor operates, subject to applicable transfer mechanisms.

### 12.2 Regional options

Enterprise tenants may be eligible for a regional configuration. A selectable interface option, sales statement, or questionnaire answer does not create a binding residency commitment unless the location is recorded in an executed order form or signed customer-specific assurance.

### 12.3 Backups and support

Unless a customer-specific term expressly includes them, a primary-region setting may not restrict all backups, telemetry, security logs, support access, email, or account-administration data.

### 12.4 Customer-specific precedence

A later signed written assurance may establish stricter location controls for an identified tenant and will prevail over this section to its stated scope. The parties must identify whether the assurance covers content, backups, inference, support access, telemetry, and subprocessors.

### 12.5 No commitment at execution

As of this DPA's Effective Date, the parties have not recorded an EU-only location commitment for the Caldera Works Europe tenant. The questionnaire describes US–EU configuration as available but does not identify a completed configuration or binding order-form term.

### 12.6 Transfers

Where Processing occurs outside the EEA, section 10 applies. Transfer safeguards do not make a non-EEA location an EU-only location.

### 12.7 Changes

Regional availability may change, but Nerythica will not knowingly reduce an executed customer-specific commitment without Customer agreement or a lawful emergency basis.

*NYA-DPA-EU-2026-04 · Page 28 of 34*

<div style="page-break-after: always;"></div>

## Page 29 of 34 — 13. Customer responsibilities

### 13.1 Lawful basis and transparency

Customer determines its lawful basis, provides required notices, and obtains required permissions for Customer Data and instructions.

### 13.2 Data minimization

Customer will limit Customer Data to what is appropriate for the approved use. It will not upload credentials, payment-card data, health records, government identifiers, or special-category data unless separately approved.

### 13.3 Account controls

Customer manages Authorized Users, roles, SSO, endpoints, integration credentials, and timely deprovisioning. Customer must protect administrator credentials and report suspected compromise.

### 13.4 Human review

Customer is responsible for appropriate human review of model output and for final business decisions. Customer will not represent generated output as verified fact merely because the Service produced a citation or confidence score.

### 13.5 Configuration verification

Customer must verify that required regional, retention, sharing, and feature settings are enabled before uploading Customer Data.

### 13.6 Requests and objections

Customer must monitor designated contacts and, where it relies on trust-portal updates, maintain the applicable subscription. Failure to review an update does not expand the contract's notice obligation.

### 13.7 Incident cooperation

Customer will preserve relevant logs and provide timely information when its account, users, integration, or endpoint may contribute to an incident.

### 13.8 Internal approval

Execution of this DPA does not replace Customer's procurement, budget, security, director, or legal approval requirements.

*NYA-DPA-EU-2026-04 · Page 29 of 34*

<div style="page-break-after: always;"></div>

## Page 30 of 34 — 14. Liability, precedence, and changes

### 14.1 Agreement limits

Liability arising from this DPA is subject to the exclusions and limitations in the Agreement unless Applicable Data Protection Law prohibits that treatment. This DPA does not create a separate unlimited liability regime.

### 14.2 No third-party expansion

Except where the SCCs or law provide otherwise, this DPA does not grant rights to a person who is not a party.

### 14.3 Order of precedence

For a conflict concerning Customer Data, the order is: applicable SCCs; a signed customer-specific data-protection amendment; this DPA; the order form; and the general Agreement. A later assurance controls only matters it expressly amends.

### 14.4 Standard updates

Nerythica may update its standard DPA for legal, security, or operational reasons. An update does not automatically replace this executed version unless the Agreement provides an update mechanism or the parties execute the change.

### 14.5 Severability

If a provision is unenforceable, it is modified only to the minimum extent necessary, and the remaining provisions continue.

### 14.6 Waiver

Failure to enforce a provision is not a waiver. A waiver must be written and applies only to the stated circumstance.

### 14.7 Entire processing agreement

This DPA and incorporated documents state the parties' agreement about Nerythica's Processing of Customer Data. A questionnaire response is evidence for review but is not a contractual amendment unless expressly incorporated.

*NYA-DPA-EU-2026-04 · Page 30 of 34*

<div style="page-break-after: always;"></div>

## Page 31 of 34 — 15. Term and termination

### 15.1 Term

This DPA begins on the Effective Date and continues while Nerythica Processes Customer Data under the Agreement.

### 15.2 Survival

Confidentiality, security, deletion, transfer, audit, and other provisions that by nature apply after termination survive while Nerythica retains Customer Data.

### 15.3 Suspension

Nerythica may suspend affected Processing to address a material security risk, unlawful instruction, non-payment, prohibited use, or absence of a lawful transfer mechanism. Where practicable, Nerythica will provide notice and an opportunity to cure.

### 15.4 Termination assistance

Customer may export supported data during the retrieval period. Additional migration support requires separate scope and fees.

### 15.5 Unresolved subprocessor objection

The remedy for an unresolved objection under section 9.6 is limited to the affected feature as stated there and does not automatically terminate unrelated services.

### 15.6 Effect on commitments

Termination does not erase accrued payment obligations, confidentiality duties, or records that law requires a party to retain.

### 15.7 Counterparts and electronic execution

This DPA may be executed in counterparts and by electronic signature. Each counterpart is deemed an original and together they form one instrument.

### 15.8 Governing terms

The governing law and dispute forum are those in the Agreement, subject to mandatory rights under Applicable Data Protection Law and the SCCs.

*NYA-DPA-EU-2026-04 · Page 31 of 34*

<div style="page-break-after: always;"></div>

## Page 32 of 34 — Annex I: Processing details

### A. Parties

**Controller:** Caldera Works Europe S.A.S., fictional European operations company. Contact role: Operations Lead.  
**Processor:** Nerythica AI Ltd., fictional AI SaaS provider. Contact role: Privacy Office.

### B. Subject matter

Provision, security, support, and maintenance of Nerythica Workspace Enterprise for document drafting, analysis, internal research, and configured workflows.

### C. Duration

The Agreement term plus retrieval, deletion, backup rotation, and legally required retention periods.

### D. Nature and purpose

Hosting Customer Content; parsing and indexing documents; generating prompts and model responses; extracting structured information; user and workspace administration; security monitoring; support; backup; deletion; and customer-instructed exports.

### E. Data Subjects

Customer personnel, business contacts, customer contacts, prospective customers, suppliers, and individuals mentioned in documents submitted by Authorized Users.

### F. Personal Data categories

Names, roles, business contact details, account identifiers, support communications, commercial records, contract text, customer-service content, and other ordinary business information chosen by Customer.

### G. Sensitive data

No special-category or similarly sensitive data is intended. Customer must obtain express approval and suitable controls before submitting it.

### H. Frequency

Continuous or user-initiated during the Service term.

### I. Retention

As described in sections 8.3 and 8.4, subject to Customer configuration and legal requirements.

### J. Competent authority

Determined under Applicable Data Protection Law and any SCC module.

*NYA-DPA-EU-2026-04 · Page 32 of 34*

<div style="page-break-after: always;"></div>

## Page 33 of 34 — Annex II: Technical and organizational measures

Nerythica's measures include, according to risk and system applicability:

1. **Governance:** assigned security ownership, policies, risk assessment, exceptions, and management review.
2. **Identity:** unique accounts, MFA for privileged access, least privilege, joiner-mover-leaver processes, and periodic access review.
3. **Confidentiality:** personnel obligations, training, and restricted support access.
4. **Encryption:** TLS for public-network transit and encryption at rest for production stores and managed backups.
5. **Development:** source control, peer review, environment separation, dependency checks, and change management.
6. **Vulnerability management:** scanning, severity-based triage, remediation tracking, and annual independent penetration testing.
7. **Logging:** authentication, privileged action, security, and operational logging protected from ordinary user modification.
8. **Incident response:** documented roles, triage, containment, evidence preservation, communication, exercises, and lessons learned.
9. **Resilience:** backups, restoration testing, recovery planning, dependency review, and continuity exercises.
10. **Subprocessors:** due diligence, written protection, access scoping, monitoring, and transfer measures.
11. **Data lifecycle:** configurable retention, active-system deletion, backup expiry, export, and legal-hold controls.
12. **Tenant controls:** logical separation, authorization checks, enterprise SSO support, administrative roles, and feature configuration.
13. **AI safeguards:** enterprise shared-training opt-out by contract, human-review messaging, abuse controls, and restricted diagnostic access.

Measures describe a control programme, not a guarantee that no incident, error, model failure, or unauthorized action can occur. Customer controls remain part of the shared-responsibility model.

*NYA-DPA-EU-2026-04 · Page 33 of 34*

<div style="page-break-after: always;"></div>

## Page 34 of 34 — Execution

The fictional parties agree to this DPA, including its Annexes, as of the Effective Date. Signature names and marks below are synthetic fixture data and have no legal effect.

### Caldera Works Europe S.A.S. — Controller

Authorized signatory: **Mara Ellison**  
Title: **Director of Operations**  
Signature: `/s/ DEMO-MARA-ELLISON-CW-20260712`  
Date: **2026-07-12**

### Nerythica AI Ltd. — Processor

Authorized signatory: **Dr. Iona Mercer**  
Title: **Chief Security and Privacy Officer**  
Signature: `/s/ DEMO-IONA-MERCER-NYA-20260712`
Date: **2026-07-12**

### Execution metadata

| Field | Value |
|---|---|
| Agreement reference | NYA-MSA-CW-2026-07 |
| DPA reference | NYA-DPA-EU-2026-04 |
| DPA version | 4.3 |
| Effective date | 2026-07-12 |
| Controller signature status | Executed — fictional fixture |
| Processor signature status | Executed — fictional fixture |
| Customer-specific EU-only term | Not present at execution; later assurance required |
| Subprocessor-notice amendment | None |

The parties acknowledge that internal procurement and director approval remain separate from contract execution. The DPA's executed status satisfies document execution evidence but does not resolve regional configuration, certification status, price routing, or the conflict between questionnaire SUB-02 and section 9.6.

**END OF DOCUMENT**

*NYA-DPA-EU-2026-04 · Page 34 of 34*
