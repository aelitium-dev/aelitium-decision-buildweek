"""Minimal D1 FastAPI surface for cases and deterministic policy evaluation."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request, status

from .paths import POLICIES_DIR, REPOSITORY_ROOT
from .persistence import SQLiteStore, StoreConflictError
from .policy import PolicyEngine, load_policy_pack
from .schema_validation import CanonicalSchemaError, validate_canonical


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _default_database_path() -> Path:
    configured = os.environ.get("AELITIUM_DB_PATH")
    return Path(configured) if configured else REPOSITORY_ROOT / "runtime" / "aelitium.db"


def create_app(*, database_path: Path | None = None) -> FastAPI:
    store = SQLiteStore(database_path or _default_database_path())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.initialize()
        app.state.store = store
        yield

    app = FastAPI(
        title="AELITIUM — Verifiable Decision Workflows",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

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
