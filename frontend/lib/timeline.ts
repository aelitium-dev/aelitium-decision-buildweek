export type TimelineOriginType =
  | "repository_fixture"
  | "precomputed_assessment"
  | "openai_live_assessment"
  | "deterministic_policy_engine"
  | "declared_human"
  | "receipt_builder"
  | "integrity_verifier";

export type TimelineEventType =
  | "CASE_CREATED"
  | "EVIDENCE_INGESTED"
  | "ASSESSMENT_RECORDED"
  | "POLICY_EVALUATED"
  | "ROUTING_DECIDED"
  | "HUMAN_APPROVAL_RECORDED"
  | "RECEIPT_ISSUED"
  | "RECEIPT_VERIFIED";

export type TimelineReference = {
  reference_type:
    | "case"
    | "document"
    | "assessment"
    | "policy_result"
    | "control"
    | "role"
    | "approval"
    | "receipt"
    | "verification_result";
  reference_id: string;
  commitment_sha256: string | null;
};

export type TimelineEvent = {
  schema_version: "decision-timeline-event/v1";
  event_id: string;
  case_id: string;
  sequence: number;
  event_type: TimelineEventType;
  state: string;
  occurred_at: string;
  origin: {
    origin_type: TimelineOriginType;
    actor_id: string;
    execution_mode: "DEMO" | "LIVE";
  };
  summary: string;
  references: TimelineReference[];
  previous_event_hash: string;
  event_hash: string;
};

export type DecisionTimeline = {
  timeline_version: "decision-timeline/v1";
  case_id: string;
  event_count: number;
  head_hash: string;
  events: TimelineEvent[];
  limitations: string[];
};

const HASH_PATTERN = /^[0-9a-f]{64}$/;
const UTC_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const STATE_PATTERN = /^[A-Z][A-Z0-9_]{1,63}$/;
const EVENT_TYPES = new Set<TimelineEventType>([
  "CASE_CREATED",
  "EVIDENCE_INGESTED",
  "ASSESSMENT_RECORDED",
  "POLICY_EVALUATED",
  "ROUTING_DECIDED",
  "HUMAN_APPROVAL_RECORDED",
  "RECEIPT_ISSUED",
  "RECEIPT_VERIFIED",
]);
const ORIGIN_TYPES = new Set<TimelineOriginType>([
  "repository_fixture",
  "precomputed_assessment",
  "openai_live_assessment",
  "deterministic_policy_engine",
  "declared_human",
  "receipt_builder",
  "integrity_verifier",
]);
const REFERENCE_TYPES = new Set<TimelineReference["reference_type"]>([
  "case",
  "document",
  "assessment",
  "policy_result",
  "control",
  "role",
  "approval",
  "receipt",
  "verification_result",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, expected: string[]): boolean {
  const actual = Object.keys(value).sort();
  return actual.length === expected.length
    && actual.every((key, index) => key === [...expected].sort()[index]);
}

function reject(message: string): never {
  throw new Error(`Decision Timeline contract rejected: ${message}`);
}

/**
 * Fail closed before UI rendering. This checks the closed API shape, order,
 * timestamps, and hash-link continuity. Cryptographic hash recomputation stays
 * authoritative in the backend and offline verifier.
 */
export function requireDecisionTimeline(
  value: unknown,
  expectedCaseId?: string,
): DecisionTimeline {
  if (!isRecord(value) || !exactKeys(value, [
    "timeline_version",
    "case_id",
    "event_count",
    "head_hash",
    "events",
    "limitations",
  ])) {
    return reject("root fields are invalid");
  }
  if (
    value.timeline_version !== "decision-timeline/v1"
    || typeof value.case_id !== "string"
    || (expectedCaseId !== undefined && value.case_id !== expectedCaseId)
    || typeof value.event_count !== "number"
    || !Number.isInteger(value.event_count)
    || value.event_count < 1
    || typeof value.head_hash !== "string"
    || !HASH_PATTERN.test(value.head_hash)
    || !Array.isArray(value.events)
    || value.events.length !== value.event_count
    || !Array.isArray(value.limitations)
    || !value.limitations.every((item) => typeof item === "string")
  ) {
    return reject("root values are inconsistent");
  }

  let previousHash = "0".repeat(64);
  let previousTime = -Infinity;
  const events: TimelineEvent[] = value.events.map((candidate, index) => {
    if (!isRecord(candidate) || !exactKeys(candidate, [
      "schema_version",
      "event_id",
      "case_id",
      "sequence",
      "event_type",
      "state",
      "occurred_at",
      "origin",
      "summary",
      "references",
      "previous_event_hash",
      "event_hash",
    ])) {
      return reject(`event ${index + 1} fields are invalid`);
    }
    const sequence = index + 1;
    const eventType = candidate.event_type;
    const expectedEventId = typeof eventType === "string"
      ? `event-${String(sequence).padStart(4, "0")}-${eventType.toLowerCase().replaceAll("_", "-")}`
      : "";
    if (
      candidate.schema_version !== "decision-timeline-event/v1"
      || candidate.case_id !== value.case_id
      || candidate.sequence !== sequence
      || candidate.event_id !== expectedEventId
      || !EVENT_TYPES.has(eventType as TimelineEventType)
      || typeof candidate.state !== "string"
      || !STATE_PATTERN.test(candidate.state)
      || typeof candidate.occurred_at !== "string"
      || !UTC_PATTERN.test(candidate.occurred_at)
      || Number.isNaN(Date.parse(candidate.occurred_at))
      || Date.parse(candidate.occurred_at) < previousTime
      || typeof candidate.summary !== "string"
      || candidate.summary.length === 0
      || candidate.previous_event_hash !== previousHash
      || typeof candidate.event_hash !== "string"
      || !HASH_PATTERN.test(candidate.event_hash)
    ) {
      return reject(`event ${sequence} values are inconsistent`);
    }
    if (!isRecord(candidate.origin) || !exactKeys(candidate.origin, [
      "origin_type",
      "actor_id",
      "execution_mode",
    ]) || !ORIGIN_TYPES.has(candidate.origin.origin_type as TimelineOriginType)
      || typeof candidate.origin.actor_id !== "string"
      || !["DEMO", "LIVE"].includes(candidate.origin.execution_mode as string)) {
      return reject(`event ${sequence} origin is invalid`);
    }
    if (!Array.isArray(candidate.references) || candidate.references.length === 0) {
      return reject(`event ${sequence} references are missing`);
    }
    candidate.references.forEach((item) => {
      if (!isRecord(item) || !exactKeys(item, [
        "reference_type",
        "reference_id",
        "commitment_sha256",
      ]) || !REFERENCE_TYPES.has(item.reference_type as TimelineReference["reference_type"])
        || typeof item.reference_id !== "string"
        || (item.commitment_sha256 !== null
          && (typeof item.commitment_sha256 !== "string"
            || !HASH_PATTERN.test(item.commitment_sha256)))) {
        reject(`event ${sequence} contains an invalid reference`);
      }
    });
    previousHash = candidate.event_hash;
    previousTime = Date.parse(candidate.occurred_at);
    return candidate as TimelineEvent;
  });

  if (previousHash !== value.head_hash) {
    return reject("head hash does not match the final event");
  }
  return { ...value, events } as DecisionTimeline;
}
