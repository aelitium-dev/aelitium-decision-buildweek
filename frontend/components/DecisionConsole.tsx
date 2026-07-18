"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_ROOT = "/api/backend";

type TypedValue = {
  value_type: "string" | "integer" | "boolean" | "unknown";
  string_value: string | null;
  integer_value: number | null;
  boolean_value: boolean | null;
};

type EvidenceRef = {
  document_id: string;
  locator: string;
  quoted_text: string;
  reference_level: string;
};

type Fact = {
  fact_id: string;
  fact_key: string;
  statement: string;
  value: TypedValue;
  evidence_refs: EvidenceRef[];
};

type Conflict = {
  conflict_id: string;
  summary: string;
  severity: string;
  requires_resolution: boolean;
  evidence_refs: EvidenceRef[];
};

type RuleEvaluation = {
  control_id: string;
  description: string;
  result: "PASS" | "FAIL" | "NOT_APPLICABLE";
  observed_value: string | number | boolean | null;
  expected_value: string | number | boolean | null;
  effect: string;
};

type DocumentRecord = {
  document_id: string;
  document_type: string;
  filename: string;
  sha256: string;
  version: string;
};

type PolicyResult = {
  state: string;
  policy_version: string;
  blocking_controls: Array<{ control_id: string; description: string }>;
  rules_evaluated: RuleEvaluation[];
  required_approval_roles: string[];
  routing_reasons: string[];
  evaluated_at: string;
};

type Assessment = {
  case_summary: string;
  facts: Fact[];
  conflicts: Conflict[];
  confidence: number;
  requires_human_review: boolean;
};

type DemoSnapshot = {
  mode: "DEMO";
  company: string;
  vendor: string;
  case: {
    case_id: string;
    title: string;
    case_version: number;
    state: string;
    documents: DocumentRecord[];
    updated_at: string;
  };
  assessment: Assessment;
  policy_result: PolicyResult;
  before_f5: {
    assessment: Assessment;
    policy_result: PolicyResult;
  };
  evidence_diff: Array<{
    label: string;
    fact_key: string;
    before: string;
    after: string;
    evidence_ref: string;
  }>;
  policy: {
    policy_version: string;
    rules: Array<{ control_id: string; description: string }>;
  };
  actions: { allowed: string[]; prohibited: string[] };
  trust_notice: string;
};

type Approval = {
  approval_id: string;
  decision: string;
  decided_at: string;
  approver: { display_name: string; role: string; identity_assurance: string };
  conditions: Array<{ text: string; due_event: string }>;
  justification: string;
};

type Receipt = {
  decision_content: {
    model_assessment: { facts: Fact[] };
    human_approval: Approval;
  };
  signed_receipt_payload: {
    receipt_id: string;
    receipt_version: string;
    content_hash: string;
    issued_at: string;
    signing_metadata: {
      key_id: string;
      signature_algorithm: string;
      public_key_fingerprint_sha256: string;
    };
  };
  signature: string;
};

type ReceiptResponse = {
  receipt: Receipt;
  trust_anchor: {
    source: string;
    key_id: string;
    public_key_fingerprint_sha256: string;
  };
};

type Verification = {
  status: "VALID" | "INVALID";
  reason: string;
};

const FACT_LABELS: Record<string, string> = {
  "commercial.annual_price_eur": "Annual recurring price",
  "privacy.eu_eea_only_residency_confirmed": "EU / EEA-only residency",
  "privacy.dpa_executed_by_both_parties": "DPA executed by both parties",
  "security.assurance_report_issued": "Assurance report issued",
};

const DOCUMENT_LABELS: Record<string, string> = {
  commercial_proposal: "Commercial proposal",
  internal_policy: "Internal policy",
  security_questionnaire: "Security questionnaire",
  executed_dpa: "Executed DPA",
  vendor_assurance_letter: "Assurance letter",
};

async function callApi<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const payload = (await response.json()) as T & { detail?: string };
  if (!response.ok) {
    throw new Error(payload.detail ?? `Request failed with status ${response.status}`);
  }
  return payload;
}

function truncate(value: string, front = 12, back = 8) {
  return `${value.slice(0, front)}…${value.slice(-back)}`;
}

function formatValue(value: TypedValue) {
  if (value.value_type === "unknown") return "UNKNOWN";
  if (value.value_type === "integer") {
    return new Intl.NumberFormat("en-IE", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value.integer_value ?? 0);
  }
  if (value.value_type === "boolean") return value.boolean_value ? "PASS" : "FAIL";
  return value.string_value ?? "—";
}

function friendlyAction(action: string) {
  return action.replaceAll("_", " ");
}

function StatusPill({ state }: { state: string }) {
  return <span className={`status-pill status-${state.toLowerCase()}`}>{state.replaceAll("_", " ")}</span>;
}

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  );
}

export function DecisionConsole() {
  const [snapshot, setSnapshot] = useState<DemoSnapshot | null>(null);
  const [activeStep, setActiveStep] = useState<0 | 1 | 2>(0);
  const [receiptResponse, setReceiptResponse] = useState<ReceiptResponse | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [verificationMode, setVerificationMode] = useState<"original" | "tampered" | null>(null);
  const [displayName, setDisplayName] = useState("Mara Ellison");
  const [justification, setJustification] = useState(
    "Blocking evidence is complete; the contractual conflict remains an explicit condition.",
  );
  const [condition, setCondition] = useState(
    "Renegotiate the subprocessor clause before renewal.",
  );
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    callApi<DemoSnapshot>("/v1/demo/case")
      .then((data) => {
        if (!cancelled) setSnapshot(data);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Could not load DEMO case");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const priceFact = useMemo(
    () =>
      snapshot?.assessment.facts.find(
        (fact) => fact.fact_key === "commercial.annual_price_eur",
      ),
    [snapshot],
  );

  async function approveAndIssue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setWorking(true);
    setError(null);
    try {
      const approvalResponse = await callApi<{ approval: Approval }>("/v1/demo/approvals", {
        method: "POST",
        body: JSON.stringify({ display_name: displayName, justification, condition }),
      });
      const issued = await callApi<ReceiptResponse>("/v1/demo/receipts", {
        method: "POST",
        body: JSON.stringify({ approval: approvalResponse.approval }),
      });
      setReceiptResponse(issued);
      setVerification(null);
      setVerificationMode(null);
      setActiveStep(2);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Approval could not be recorded");
    } finally {
      setWorking(false);
    }
  }

  async function verify(tamper: boolean) {
    if (!receiptResponse) return;
    setWorking(true);
    setError(null);
    try {
      const candidate = structuredClone(receiptResponse.receipt);
      if (tamper) {
        const price = candidate.decision_content.model_assessment.facts.find(
          (fact) => fact.fact_key === "commercial.annual_price_eur",
        );
        if (!price) throw new Error("Receipt has no annual-price fact to alter");
        price.value.integer_value = 14000;
      }
      const result = await callApi<Verification>("/v1/demo/receipts/verify", {
        method: "POST",
        body: JSON.stringify({ receipt: candidate }),
      });
      setVerification(result);
      setVerificationMode(tamper ? "tampered" : "original");
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Verification failed");
    } finally {
      setWorking(false);
    }
  }

  if (!snapshot && !error) {
    return (
      <main className="loading-shell">
        <BrandMark />
        <p>Loading the deterministic decision case…</p>
      </main>
    );
  }

  if (!snapshot) {
    return (
      <main className="loading-shell error-shell">
        <BrandMark />
        <p className="eyebrow">BACKEND UNAVAILABLE</p>
        <h1>The Decision Console could not load its DEMO case.</h1>
        <p>{error}</p>
        <code>uvicorn aelitium_decision.api:app --port 8000</code>
      </main>
    );
  }

  const steps = [
    { label: "Case & evidence", caption: "Review the record" },
    { label: "Human approval", caption: "Exercise authority" },
    { label: "Receipt & verify", caption: "Test integrity" },
  ];

  return (
    <div className="console-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="AELITIUM Decision Console home">
          <BrandMark />
          <span>
            <strong>AELITIUM</strong>
            <small>Decision Console</small>
          </span>
        </a>
        <div className="topbar-meta">
          <span className="mode-badge"><i /> BUILD WEEK · DEMO</span>
          <span className="case-code">{snapshot.case.case_id}</span>
        </div>
      </header>

      <div className="workspace" id="top">
        <aside className="step-rail" aria-label="Decision workflow">
          <div className="rail-intro">
            <p className="eyebrow">VERIFIABLE WORKFLOW</p>
            <h2>Evidence before authority.</h2>
            <p>A model interprets. Rules route. A person decides.</p>
          </div>
          <nav>
            {steps.map((step, index) => {
              const disabled = index === 2 && !receiptResponse;
              const complete = index < activeStep || (index === 1 && receiptResponse !== null);
              return (
                <button
                  className={`step-button ${activeStep === index ? "active" : ""} ${complete ? "complete" : ""}`}
                  disabled={disabled}
                  key={step.label}
                  onClick={() => setActiveStep(index as 0 | 1 | 2)}
                  type="button"
                >
                  <span className="step-index">{complete ? "✓" : `0${index + 1}`}</span>
                  <span>
                    <strong>{step.label}</strong>
                    <small>{step.caption}</small>
                  </span>
                </button>
              );
            })}
          </nav>
          <div className="rail-trust">
            <span className="trust-icon">≠</span>
            <p><strong>Verifiable is not infallible.</strong> Integrity checks do not prove truth or legal validity.</p>
          </div>
        </aside>

        <main className="decision-main">
          {error && (
            <div className="error-banner" role="alert">
              <span>!</span>
              <p>{error}</p>
              <button onClick={() => setError(null)} type="button">Dismiss</button>
            </div>
          )}

          {activeStep === 0 && (
            <CaseView
              onContinue={() => setActiveStep(1)}
              priceFact={priceFact}
              snapshot={snapshot}
            />
          )}
          {activeStep === 1 && (
            <ApprovalView
              condition={condition}
              displayName={displayName}
              justification={justification}
              onCondition={setCondition}
              onDisplayName={setDisplayName}
              onJustification={setJustification}
              onSubmit={approveAndIssue}
              snapshot={snapshot}
              working={working}
            />
          )}
          {activeStep === 2 && receiptResponse && (
            <ReceiptView
              onVerify={verify}
              receiptResponse={receiptResponse}
              trustNotice={snapshot.trust_notice}
              verification={verification}
              verificationMode={verificationMode}
              working={working}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function CaseView({
  snapshot,
  priceFact,
  onContinue,
}: {
  snapshot: DemoSnapshot;
  priceFact?: Fact;
  onContinue: () => void;
}) {
  return (
    <section className="screen-section">
      <div className="screen-header">
        <div>
          <p className="eyebrow">CASE 01 · AI VENDOR APPROVAL</p>
          <h1>{snapshot.case.title}</h1>
          <p>{snapshot.vendor} for {snapshot.company}</p>
        </div>
        <StatusPill state={snapshot.policy_result.state} />
      </div>

      <div className="case-metrics">
        <article>
          <span>Annual value</span>
          <strong>{priceFact ? formatValue(priceFact.value) : "—"}</strong>
          <small>€15,000 director threshold</small>
        </article>
        <article>
          <span>Evidence set</span>
          <strong>{snapshot.case.documents.length} documents</strong>
          <small>F1–F5 · version {snapshot.case.case_version}</small>
        </article>
        <article>
          <span>Assessment confidence</span>
          <strong>{snapshot.assessment.confidence}%</strong>
          <small>Canonical integer score</small>
        </article>
        <article>
          <span>Blocking controls</span>
          <strong className="good-number">{snapshot.policy_result.blocking_controls.length}</strong>
          <small>2 resolved when F5 arrived</small>
        </article>
      </div>

      <div className="content-grid">
        <div className="primary-column">
          <article className="panel assessment-summary">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">STRUCTURED ASSESSMENT</p>
                <h2>What the evidence says</h2>
              </div>
              <span className="model-chip">PRE-COMPUTED · NO API KEY</span>
            </div>
            <p className="summary-copy">{snapshot.assessment.case_summary}</p>
            <div className="fact-list">
              {snapshot.assessment.facts.map((fact) => (
                <div className="fact-row" key={fact.fact_id}>
                  <span className={`fact-indicator value-${fact.value.value_type}`} />
                  <div>
                    <strong>{FACT_LABELS[fact.fact_key] ?? fact.fact_key}</strong>
                    <p>{fact.statement}</p>
                    <div className="citations">
                      {fact.evidence_refs.map((reference) => (
                        <a href={`#document-${reference.document_id}`} key={`${fact.fact_id}-${reference.document_id}-${reference.locator}`}>
                          {reference.document_id} · {reference.locator}
                        </a>
                      ))}
                    </div>
                  </div>
                  <b>{formatValue(fact.value)}</b>
                </div>
              ))}
            </div>
          </article>

          <article className="panel conflict-panel">
            <div className="panel-heading compact">
              <div>
                <p className="eyebrow">MATERIAL CONFLICT</p>
                <h2>Human judgement remains mandatory</h2>
              </div>
              <span className="severity">HIGH</span>
            </div>
            {snapshot.assessment.conflicts.map((conflict) => (
              <div key={conflict.conflict_id}>
                <p className="summary-copy">{conflict.summary}</p>
                <div className="conflict-sources">
                  {conflict.evidence_refs.map((reference) => (
                    <a href={`#document-${reference.document_id}`} key={`${conflict.conflict_id}-${reference.document_id}`}>
                      <span>{reference.document_id}</span>
                      <div>
                        <strong>{reference.locator}</strong>
                        <small>“{reference.quoted_text}”</small>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </article>
        </div>

        <aside className="secondary-column">
          <article className="panel diff-panel">
            <div className="panel-heading compact">
              <div>
                <p className="eyebrow">AFTER F5</p>
                <h2>Evidence diff</h2>
              </div>
              <span className="diff-arrow">↗</span>
            </div>
            <p className="muted">A full re-analysis moved two evidence controls. Deterministic thresholds did not change.</p>
            {snapshot.evidence_diff.map((change) => (
              <div className="diff-row" key={change.fact_key}>
                <strong>{change.label}</strong>
                <div><span>{change.before}</span><i>→</i><b>{change.after}</b></div>
                <a href="#document-F5">{change.evidence_ref}</a>
              </div>
            ))}
            <div className="route-change">
              <small>ROUTE</small>
              <span>{snapshot.before_f5.policy_result.state.replaceAll("_", " ")}</span>
              <i>→</i>
              <b>{snapshot.policy_result.state.replaceAll("_", " ")}</b>
            </div>
          </article>

          <article className="panel documents-panel">
            <div className="panel-heading compact">
              <div>
                <p className="eyebrow">SOURCE RECORD</p>
                <h2>Documents</h2>
              </div>
              <span className="count-badge">{snapshot.case.documents.length}</span>
            </div>
            <div className="document-list">
              {snapshot.case.documents.map((document) => (
                <div className="document-row" id={`document-${document.document_id}`} key={document.document_id}>
                  <span>{document.document_id}</span>
                  <div>
                    <strong>{DOCUMENT_LABELS[document.document_type] ?? document.document_type}</strong>
                    <small>{document.filename}</small>
                    <code>{truncate(document.sha256, 8, 6)}</code>
                  </div>
                  <b>v{document.version}</b>
                </div>
              ))}
            </div>
          </article>
        </aside>
      </div>

      <div className="screen-actions">
        <div><span className="pulse-dot" /> No blocking evidence controls remain</div>
        <button className="primary-button" onClick={onContinue} type="button">
          Review human decision <span>→</span>
        </button>
      </div>
    </section>
  );
}

function ApprovalView({
  snapshot,
  displayName,
  justification,
  condition,
  onDisplayName,
  onJustification,
  onCondition,
  onSubmit,
  working,
}: {
  snapshot: DemoSnapshot;
  displayName: string;
  justification: string;
  condition: string;
  onDisplayName: (value: string) => void;
  onJustification: (value: string) => void;
  onCondition: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  working: boolean;
}) {
  return (
    <section className="screen-section">
      <div className="screen-header">
        <div>
          <p className="eyebrow">HUMAN AUTHORITY GATE</p>
          <h1>Record the decision</h1>
          <p>The model recommendation cannot approve this €18,000 commitment.</p>
        </div>
        <span className="authority-badge">DIRECTOR REQUIRED</span>
      </div>

      <div className="approval-grid">
        <div>
          <article className="panel control-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">DETERMINISTIC POLICY</p>
                <h2>Six controls, fixed inputs</h2>
              </div>
              <code>{snapshot.policy.policy_version}</code>
            </div>
            <div className="control-list">
              {snapshot.policy_result.rules_evaluated.map((rule) => (
                <div className="control-row" key={rule.control_id}>
                  <span className={rule.result === "PASS" ? "control-pass" : "control-route"}>
                    {rule.result === "PASS" ? "✓" : "↗"}
                  </span>
                  <div>
                    <code>{rule.control_id}</code>
                    <strong>{rule.description}</strong>
                    {rule.effect !== "NONE" && <small>Effect: {rule.effect.replaceAll("_", " ")}</small>}
                  </div>
                  <b>{rule.result === "PASS" ? "PASS" : "ROUTE"}</b>
                </div>
              ))}
            </div>
          </article>

          <article className="panel authority-panel">
            <div>
              <p className="eyebrow">ACTION BOUNDARY</p>
              <h2>What this gate permits</h2>
            </div>
            <div className="action-groups">
              <div>
                <small>ALLOWED</small>
                {snapshot.actions.allowed.map((action) => <span className="allowed-action" key={action}>✓ {friendlyAction(action)}</span>)}
              </div>
              <div>
                <small>PROHIBITED</small>
                {snapshot.actions.prohibited.map((action) => <span className="prohibited-action" key={action}>× {friendlyAction(action)}</span>)}
              </div>
            </div>
            <p className="boundary-copy">Policy packs select existing platform operators. Neither this form nor model output can change thresholds or waive a blocking control.</p>
          </article>
        </div>

        <form className="panel approval-form" onSubmit={onSubmit}>
          <div>
            <p className="eyebrow">DECISION</p>
            <h2>Approve with conditions</h2>
            <p className="muted">The unresolved F3 ↔ F4 conflict is carried into the signed record as an explicit condition.</p>
          </div>

          <label>
            <span>Declared approver name</span>
            <input
              maxLength={200}
              onChange={(event) => onDisplayName(event.target.value)}
              required
              value={displayName}
            />
            <small>Identity is declarative only in this MVP; it is not authenticated.</small>
          </label>

          <label>
            <span>Condition</span>
            <textarea
              maxLength={1000}
              onChange={(event) => onCondition(event.target.value)}
              required
              rows={3}
              value={condition}
            />
            <small>Owner: operations reviewer · Due before contract renewal</small>
          </label>

          <label>
            <span>Decision justification</span>
            <textarea
              maxLength={5000}
              onChange={(event) => onJustification(event.target.value)}
              required
              rows={4}
              value={justification}
            />
          </label>

          <div className="evidence-note">
            <span>§</span>
            <p><strong>Decision evidence bound to the receipt</strong>F4 page 23, clause 9.6 · F5 sections 1 and 2</p>
          </div>

          <button className="primary-button full-button" disabled={working} type="submit">
            {working ? "Recording & signing…" : "Approve with condition & issue receipt"}
            {!working && <span>→</span>}
          </button>
          <p className="form-footnote">The private signing key stays in the ignored local runtime directory and is never returned by the API.</p>
        </form>
      </div>
    </section>
  );
}

function ReceiptView({
  receiptResponse,
  verification,
  verificationMode,
  onVerify,
  working,
  trustNotice,
}: {
  receiptResponse: ReceiptResponse;
  verification: Verification | null;
  verificationMode: "original" | "tampered" | null;
  onVerify: (tamper: boolean) => void;
  working: boolean;
  trustNotice: string;
}) {
  const { receipt, trust_anchor: trustAnchor } = receiptResponse;
  const payload = receipt.signed_receipt_payload;
  const approval = receipt.decision_content.human_approval;
  const isInvalid = verification?.status === "INVALID";

  return (
    <section className="screen-section receipt-screen">
      <div className="screen-header">
        <div>
          <p className="eyebrow">ADR-001 DECISION RECEIPT</p>
          <h1>Decision recorded. Integrity test ready.</h1>
          <p>Three-part envelope: deterministic content, signed issuance metadata, detached signature.</p>
        </div>
        <span className="issued-badge">RECEIPT ISSUED</span>
      </div>

      <div className="receipt-grid">
        <div>
          <article className="panel receipt-card">
            <div className="receipt-card-head">
              <div>
                <span className="receipt-seal"><BrandMark /></span>
                <div>
                  <p className="eyebrow">DECISION RECEIPT</p>
                  <h2>{payload.receipt_id}</h2>
                </div>
              </div>
              <span>v1</span>
            </div>

            <div className="receipt-decision">
              <small>HUMAN DECISION</small>
              <strong>APPROVED WITH CONDITIONS</strong>
              <p>“{approval.conditions[0]?.text}”</p>
            </div>

            <dl className="receipt-fields">
              <div><dt>Approver</dt><dd>{approval.approver.display_name}<small>declared · {approval.approver.role}</small></dd></div>
              <div><dt>Issued at</dt><dd>{payload.issued_at}</dd></div>
              <div><dt>Content hash</dt><dd><code>{truncate(payload.content_hash, 18, 12)}</code></dd></div>
              <div><dt>Signing key</dt><dd><code>{payload.signing_metadata.key_id}</code><small>{payload.signing_metadata.signature_algorithm}</small></dd></div>
              <div><dt>Fingerprint</dt><dd><code>{truncate(trustAnchor.public_key_fingerprint_sha256, 18, 12)}</code><small>external trusted keyring</small></dd></div>
              <div><dt>Signature</dt><dd><code>{truncate(receipt.signature, 18, 12)}</code><small>detached · base64</small></dd></div>
            </dl>

            <details className="raw-receipt">
              <summary>Inspect canonical receipt envelope</summary>
              <pre>{JSON.stringify(receipt, null, 2)}</pre>
            </details>
          </article>

          <div className="trust-notice">
            <span>i</span>
            <p>{trustNotice}</p>
          </div>
        </div>

        <aside>
          <article className={`panel verifier-card ${verification ? verification.status.toLowerCase() : "idle"}`}>
            <div className="verifier-visual">
              <div className="verification-ring">
                <span>{verification ? (isInvalid ? "×" : "✓") : "⌁"}</span>
              </div>
              <p className="eyebrow">OFFLINE VERIFIER</p>
              <h2>{verification ? verification.status : "NOT YET VERIFIED"}</h2>
              <p>
                {verification
                  ? verificationMode === "tampered"
                    ? "The edited decision content no longer matches its committed assessment hash."
                    : "Content commitments and the Ed25519 signature match the external trust material."
                  : "Choose the original receipt or alter one material fact before verification."}
              </p>
              {verification && <code>{verification.reason}</code>}
            </div>

            <div className="verify-actions">
              <button className="primary-button full-button" disabled={working} onClick={() => onVerify(false)} type="button">
                {working ? "Verifying…" : "Verify original receipt"}<span>✓</span>
              </button>
              <button className="tamper-button" disabled={working} onClick={() => onVerify(true)} type="button">
                <span>⌁</span>
                <div><strong>Tamper & verify</strong><small>Change annual price €18,000 → €14,000</small></div>
              </button>
            </div>
          </article>

          <article className="integrity-map">
            <p className="eyebrow">WHAT IS PROTECTED</p>
            <div><span>01</span><p><strong>Decision content</strong>Evidence, model record, policy result and human approval.</p></div>
            <div><span>02</span><p><strong>Signed metadata</strong>Content hash, issue time, version and signing identity.</p></div>
            <div><span>03</span><p><strong>External trust</strong>The receipt cannot substitute its own verification key.</p></div>
          </article>
        </aside>
      </div>
    </section>
  );
}
