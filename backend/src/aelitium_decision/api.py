"""FastAPI surface for deterministic cases and the clickable DEMO workflow."""

from __future__ import annotations

import copy
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from .approval import ApprovalAuthorizationError
from .demo_workflow import (
    DEMO_KEYRING_PATH,
    DEMO_PRIVATE_KEY_PATH,
    TRUST_LIMITATIONS,
    DemoConfigurationError,
    build_demo_snapshot,
    create_demo_approval,
    issue_demo_receipt,
    record_demo_approval,
    verify_demo_receipt,
)
from .paths import POLICIES_DIR, REPOSITORY_ROOT
from .persistence import SQLiteStore, StoreConflictError
from .policy import PolicyEngine, load_policy_pack
from .receipt import ReceiptBuildError
from .schema_validation import CanonicalSchemaError, validate_canonical


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _default_database_path() -> Path:
    configured = os.environ.get("AELITIUM_DB_PATH")
    return Path(configured) if configured else REPOSITORY_ROOT / "runtime" / "aelitium.db"


class DemoApprovalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=200)
    approver_role: str = Field(pattern="^[a-z][a-z0-9_]{1,63}$")
    justification: str = Field(min_length=1, max_length=5000)
    condition: str = Field(min_length=1, max_length=1000)


class DemoReceiptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str = Field(pattern="^approval-[a-z0-9][a-z0-9-]{2,63}$")


class DemoVerificationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt: dict[str, Any]


def _verification_response(status_value: str, reason: str) -> dict[str, Any]:
    return {
        "status": status_value,
        "reason": reason,
        "provenance": {
            "result_source": "aelitium_local_integrity_verifier",
            "trusted_key_source": "external_demo_keyring",
            "checks": [
                "canonical_schema",
                "external_material_commitments",
                "content_hash",
                "ed25519_signature",
            ],
            "does_not_prove": TRUST_LIMITATIONS,
        },
    }


def create_app(
    *,
    database_path: Path | None = None,
    demo_private_key_path: Path = DEMO_PRIVATE_KEY_PATH,
    demo_keyring_path: Path = DEMO_KEYRING_PATH,
) -> FastAPI:
    store = SQLiteStore(database_path or _default_database_path())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.initialize()
        app.state.store = store
        app.state.demo_snapshot = build_demo_snapshot()
        app.state.demo_approvals = {}
        app.state.demo_approval_by_case = {}
        app.state.demo_receipts = {}
        yield

    app = FastAPI(
        title="AELITIUM — Verifiable Decision Workflows",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/demo/case")
    async def demo_case(request: Request) -> dict[str, Any]:
        """Return the complete no-API-key case, evidence diff, and policy state."""

        return copy.deepcopy(request.app.state.demo_snapshot)

    @app.post("/v1/demo/approvals")
    async def demo_approval(
        request: Request, payload: DemoApprovalInput
    ) -> dict[str, Any]:
        try:
            approval = create_demo_approval(
                snapshot=request.app.state.demo_snapshot,
                display_name=payload.display_name,
                approver_role=payload.approver_role,
                justification=payload.justification,
                condition=payload.condition,
            )
            recorded = record_demo_approval(
                approval=approval,
                snapshot=request.app.state.demo_snapshot,
            )
        except ApprovalAuthorizationError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": exc.code, "message": exc.message},
            ) from exc
        except (CanonicalSchemaError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        case_id = approval["case_id"]
        if case_id in request.app.state.demo_approval_by_case:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "APPROVAL_ALREADY_RECORDED",
                    "message": (
                        "the decision case already has its authoritative approval"
                    ),
                },
            )
        request.app.state.demo_approvals[approval["approval_id"]] = recorded
        request.app.state.demo_approval_by_case[case_id] = approval["approval_id"]
        return {
            "approval": approval,
            "identity_notice": (
                "Approver identity is declared only and is not authenticated in the MVP."
            ),
            "provenance": {
                "record_source": "human_entered_at_runtime",
                "human_entered_fields": [
                    "approver.display_name",
                    "conditions[0].text",
                    "justification",
                ],
                "aelitium_bound_fields": [
                    "approval_id",
                    "case_id",
                    "policy_result_hash",
                    "approver.role",
                    "decision",
                    "conditions[0].owner_role",
                    "conditions[0].due_event",
                    "decided_at",
                ],
            },
        }

    @app.post("/v1/demo/receipts", status_code=status.HTTP_201_CREATED)
    async def demo_receipt(
        request: Request, payload: DemoReceiptInput
    ) -> dict[str, Any]:
        recorded = request.app.state.demo_approvals.get(payload.approval_id)
        if recorded is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "APPROVAL_NOT_FOUND",
                    "message": "server-recorded approval was not found",
                },
            )
        current_case_id = request.app.state.demo_snapshot["case"]["case_id"]
        if (
            request.app.state.demo_approval_by_case.get(current_case_id)
            != payload.approval_id
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "APPROVAL_NOT_AUTHORITATIVE",
                    "message": (
                        "approval is not the authoritative record for the current case"
                    ),
                },
            )
        try:
            issued = issue_demo_receipt(
                recorded_approval=recorded,
                snapshot=request.app.state.demo_snapshot,
                private_key_path=demo_private_key_path,
                keyring_path=demo_keyring_path,
            )
        except DemoConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ApprovalAuthorizationError as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": exc.code, "message": exc.message},
            ) from exc
        except (CanonicalSchemaError, ReceiptBuildError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        signed_payload = issued.receipt["signed_receipt_payload"]
        receipt_id = signed_payload["receipt_id"]
        request.app.state.demo_receipts[receipt_id] = issued
        signing_metadata = signed_payload["signing_metadata"]
        return {
            "receipt": issued.receipt,
            "trust_anchor": {
                "source": "external_demo_keyring",
                "key_id": signing_metadata["key_id"],
                "public_key_fingerprint_sha256": signing_metadata[
                    "public_key_fingerprint_sha256"
                ],
            },
            "provenance": {
                "assessment": {
                    "execution_mode": "DEMO",
                    "assessment_source": "precomputed_fixture",
                    "runtime_model_call": False,
                },
                "human_approval": {
                    "source": "server_recorded_human_approval",
                    "approval_id": recorded.approval["approval_id"],
                },
                "policy_result": {
                    "source": "aelitium_deterministic_policy_engine"
                },
                "hashes": {"source": "aelitium_canonical_sha256"},
                "signature": {"source": "aelitium_local_ed25519_signer"},
                "receipt": {"source": "aelitium_receipt_builder"},
                "source_document_authenticity_verified": False,
            },
        }

    @app.post("/v1/demo/receipts/verify")
    async def demo_verify(
        request: Request, payload: DemoVerificationInput
    ) -> dict[str, Any]:
        try:
            receipt_id = payload.receipt["signed_receipt_payload"]["receipt_id"]
        except (KeyError, TypeError):
            return _verification_response("INVALID", "EXTERNAL_MATERIALS_NOT_FOUND")
        issued = request.app.state.demo_receipts.get(receipt_id)
        if issued is None:
            return _verification_response("INVALID", "EXTERNAL_MATERIALS_NOT_FOUND")
        result = verify_demo_receipt(
            payload.receipt,
            materials=issued.materials,
            keyring=issued.keyring,
        )
        return _verification_response(result.status, result.reason)

    @app.post("/v1/cases", status_code=status.HTTP_201_CREATED)
    async def create_case(
        request: Request, case: dict[str, Any] = Body(...)
    ) -> dict[str, Any]:
        try:
            validate_canonical(case, "decision_case.v1.schema.json")
            request.app.state.store.put_case(case)
        except CanonicalSchemaError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except StoreConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return case

    @app.get("/v1/cases/{case_id}")
    async def get_case(request: Request, case_id: str) -> dict[str, Any]:
        case = request.app.state.store.get_case(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="case not found")
        return case

    @app.post("/v1/cases/{case_id}/evaluate")
    async def evaluate_case(
        request: Request,
        case_id: str,
        assessment: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        if request.app.state.store.get_case(case_id) is None:
            raise HTTPException(status_code=404, detail="case not found")
        try:
            validate_canonical(assessment, "model_assessment.v1.schema.json")
            policy_pack = load_policy_pack(
                POLICIES_DIR / "ai_vendor_approval.v1.json"
            )
            result = PolicyEngine().evaluate(
                case_id=case_id,
                assessment=assessment,
                policy_pack=policy_pack,
                evaluated_at=_utc_now(),
            )
            validate_canonical(result, "policy_result.v1.schema.json")
            request.app.state.store.record_policy_result(result)
        except (CanonicalSchemaError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result

    @app.get("/v1/cases/{case_id}/policy-result")
    async def latest_policy_result(
        request: Request, case_id: str
    ) -> dict[str, Any]:
        result = request.app.state.store.latest_policy_result(case_id)
        if result is None:
            raise HTTPException(status_code=404, detail="policy result not found")
        return result

    return app


app = create_app()
