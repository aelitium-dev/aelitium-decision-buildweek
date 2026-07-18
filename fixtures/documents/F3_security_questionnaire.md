# F3 — NovaMind AI Security Questionnaire

> FICTIONAL BUILD WEEK DEMO DOCUMENT — INCOMPLETE VENDOR RESPONSE

| Field | Value |
|---|---|
| Questionnaire ID | CW-SEC-2026-044 |
| Vendor | NovaMind AI Ltd. |
| Service | NovaMind Workspace Enterprise |
| Submitted | 2026-07-11 |
| Respondent | Mina Vale, Vendor Security Operations |
| Completion status | 82%; follow-up required |

## Governance and assurance

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| GOV-01 | Do you maintain an information-security programme approved by management? | Yes. Reviewed annually. | Security Overview v4.1 | Supplied |
| GOV-02 | Do you hold ISO/IEC 27001 certification? | No. | — | Not certified |
| GOV-03 | Is a SOC 2 Type II report currently issued? | In progress. | Readiness summary only | Missing issued report |
| GOV-04 | Expected SOC 2 issue date | Not provided. | — | **Blank / follow-up required** |
| GOV-05 | Independent penetration test in last 12 months? | Yes. | Executive letter dated 2026-03-28 | Summary only |

## Data location and transfers

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| DATA-01 | Production data-hosting regions | US–EU, configurable for enterprise plans. | Architecture sheet §3 | Region not selected |
| DATA-02 | Can all Customer Data be restricted to EU/EEA storage? | Yes, when the EU region flag is enabled during implementation. | No contractual attachment supplied | Written commitment missing |
| DATA-03 | Are backups restricted to the selected region? | Generally aligned with the selected primary region. | No evidence supplied | “Generally” is insufficient |
| DATA-04 | Can personnel outside the EEA access Customer Data? | Support access may occur from approved locations under access controls. | DPA reference | Locations not listed |
| DATA-05 | Transfer mechanism for non-EEA processing | Standard Contractual Clauses where required. | DPA reference | Must inspect DPA |

## Subprocessors

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| SUB-01 | Is a current subprocessor list available? | Yes, in the customer trust portal. | Portal link omitted from export | Follow-up |
| SUB-02 | Will customers receive advance notice of a new subprocessor? | **Yes. Customers receive at least 30 days' advance notice before a material new subprocessor is authorized to process Customer Data.** | Standard process, no clause cited | Must verify against DPA |
| SUB-03 | Can customers object to a new subprocessor? | Yes, on reasonable data-protection grounds. | DPA reference | Must verify against DPA |
| SUB-04 | Can subprocessors process data outside the EEA? | Only with an appropriate transfer mechanism. | DPA reference | Location scope unclear |

## Access control

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| IAM-01 | Is MFA required for privileged production access? | Yes. | Security Overview v4.1 | Supplied |
| IAM-02 | Are privileged rights reviewed? | Quarterly. | Access Review Procedure | Procedure named, not supplied |
| IAM-03 | Is customer SSO supported? | Yes, SAML 2.0 on enterprise plans. | Product guide | Supplied |
| IAM-04 | Are support-access sessions logged? | Yes. | Logging Standard | Standard named, not supplied |

## Encryption and key management

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| CRY-01 | Encryption in transit | TLS 1.2 or later. | Security Overview v4.1 | Supplied |
| CRY-02 | Encryption at rest | AES-256 or cloud-provider equivalent. | Security Overview v4.1 | Supplied |
| CRY-03 | Customer-managed keys | Not currently supported. | Product roadmap | Accepted limitation for review |
| CRY-04 | Key rotation | Managed according to cloud-provider and internal schedules. | No schedule supplied | Follow-up optional |

## Incident response and resilience

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| IR-01 | Documented incident-response plan | Yes, tested annually. | Incident Response Standard | Named, not supplied |
| IR-02 | Customer security-incident notification | Without undue delay after confirmation, subject to contract. | DPA reference | Verify timing |
| BCM-01 | Recovery point objective | 24 hours. | Resilience Summary | Supplied |
| BCM-02 | Recovery time objective | 12 hours for core service. | Resilience Summary | Supplied |
| BCM-03 | Tested restoration | Quarterly sample restoration. | No test result supplied | Follow-up optional |

## Retention and deletion

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| RET-01 | Default active-data retention | Contract term unless deleted by customer. | Product guide | Broad |
| RET-02 | Deletion after termination | Within 45 days, excluding legally required records. | DPA reference | Verify DPA |
| RET-03 | Backup deletion | Rolling expiry, normally within 90 days. | No schedule supplied | Confirm region and maximum |

## AI-specific controls

| ID | Question | Vendor response | Evidence reference | Reviewer note |
|---|---|---|---|---|
| AI-01 | Is Customer Content used to train shared foundation models? | No, not by default for enterprise customers. | Enterprise Data Use Statement | “By default” needs contractual confirmation |
| AI-02 | Are model outputs reviewed by vendor staff? | Only for support or abuse investigation under controlled access. | Data Use Statement | Scope unclear |
| AI-03 | Can customer administrators restrict features? | Yes, by workspace policy. | Admin guide | Supplied |
| AI-04 | Are model and material subprocessor changes communicated? | Material service changes are communicated through release notices. | No specific notice period | Follow-up |

## Open follow-up items

1. Provide an issued SOC 2 Type II report or equivalent dated assurance.
2. Provide written confirmation that primary data and backups for this customer will remain in the EU/EEA.
3. Identify support-access countries and the applicable transfer mechanism.
4. Provide the current subprocessor list.
5. Cite the DPA clause supporting the stated 30-day advance subprocessor notice.
6. Confirm the maximum backup-deletion period.

Vendor declaration: Responses are believed accurate as of the submission date but remain subject to the executed agreement and service configuration.

Signed for questionnaire submission: Mina Vale, Vendor Security Operations (fictional)  
Date: 2026-07-11
