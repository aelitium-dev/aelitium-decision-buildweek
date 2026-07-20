from __future__ import annotations

import asyncio
import copy
import json
from dataclasses import replace

from aelitium_decision.api import create_app
from aelitium_decision.demo import load_golden_manifest
from aelitium_decision.hashing import hash_json
from aelitium_decision.paths import REPOSITORY_ROOT
from aelitium_decision.signing import generate_private_key_file, public_key_record


def _case_payload(case_id="case-api-demo"):
    return {
        "schema_version": "decision-case/v1",
        "case_id": case_id,
        "decision_domain": "ai_vendor_approval",
        "title": "API demo case",
        "case_version": 1,
        "state": "DRAFT",
        "documents": [],
        "created_at": "2026-07-19T10:00:00Z",
        "updated_at": "2026-07-19T10:00:00Z",
    }


def _assessment(case_name="T2"):
    manifest = load_golden_manifest()
    path = REPOSITORY_ROOT / manifest["cases"][case_name]["assessment_path"]
    return json.loads(path.read_text(encoding="utf-8"))


def _demo_approval_payload(role="director"):
    return {
        "display_name": "Mara Ellison",
        "approver_role": role,
        "justification": (
            "Blocking evidence is complete; the contractual conflict remains "
            "an explicit condition."
        ),
        "condition": "Renegotiate the subprocessor clause before renewal.",
    }


def _demo_signing_paths(tmp_path):
    private_key_path = tmp_path / "demo.key"
    keyring_path = tmp_path / "keyring.json"
    private_key = generate_private_key_file(private_key_path)
    keyring_path.write_text(
        json.dumps(
            {
                "keyring_version": "aelitium-trusted-keyring/v1",
                "keys": [
                    public_key_record(
                        "buildweek-demo-2026", private_key.public_key()
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    return private_key_path, keyring_path


async def _request(app, method, path, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    request_sent = False
    messages = []

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "client": ("asgi-test", 1234),
        "server": ("asgi-test", 80),
        "state": {},
    }
    await app(scope, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body)


async def _record_valid_demo_approval(app):
    status, response = await _request(
        app,
        "POST",
        "/v1/demo/approvals",
        _demo_approval_payload(),
    )
    assert status == 200
    return response["approval"]


def _error_code(response):
    return response["detail"]["code"]


def test_case_and_policy_result_round_trip(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "round-trip.db")
        async with app.router.lifespan_context(app):
            status, _ = await _request(app, "POST", "/v1/cases", _case_payload())
            assert status == 201

            status, evaluated = await _request(
                app,
                "POST",
                "/v1/cases/case-api-demo/evaluate",
                _assessment("T2"),
            )
            assert status == 200
            assert evaluated["state"] == "NEEDS_MORE_EVIDENCE"

            status, stored_case = await _request(
                app, "GET", "/v1/cases/case-api-demo"
            )
            assert status == 200
            assert stored_case["state"] == "NEEDS_MORE_EVIDENCE"
            status, latest = await _request(
                app, "GET", "/v1/cases/case-api-demo/policy-result"
            )
            assert status == 200
            assert latest == evaluated

    asyncio.run(scenario())


def test_api_revalidates_assessment_against_canonical_schema(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "canonical-validation.db")
        case_id = "case-api-invalid"
        assessment = _assessment("T1")
        assessment["case_summary"] = ""
        async with app.router.lifespan_context(app):
            status, _ = await _request(
                app, "POST", "/v1/cases", _case_payload(case_id)
            )
            assert status == 201
            status, response = await _request(
                app, "POST", f"/v1/cases/{case_id}/evaluate", assessment
            )
            assert status == 422
            assert "case_summary" in response["detail"]

    asyncio.run(scenario())


def test_duplicate_case_is_conflict(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "duplicate.db")
        case_id = "case-api-duplicate"
        async with app.router.lifespan_context(app):
            assert (
                await _request(app, "POST", "/v1/cases", _case_payload(case_id))
            )[0] == 201
            assert (
                await _request(app, "POST", "/v1/cases", _case_payload(case_id))
            )[0] == 409

    asyncio.run(scenario())


def test_demo_ui_api_approval_receipt_verify_and_tamper(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "demo.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            status, snapshot = await _request(app, "GET", "/v1/demo/case")
            assert status == 200
            assert snapshot["mode"] == "DEMO"
            assert snapshot["before_f5"]["policy_result"]["state"] == (
                "NEEDS_MORE_EVIDENCE"
            )
            assert snapshot["policy_result"]["state"] == "HUMAN_APPROVAL_REQUIRED"
            assert snapshot["policy_result"]["blocking_controls"] == []
            assert snapshot["evidence_diff"][0]["before"] == "UNKNOWN"
            assert snapshot["evidence_diff"][0]["after"] == "PASS"
            provenance = snapshot["provenance"]
            assert provenance["source_documents"]["origin"] == (
                "build_week_repository_fixtures"
            )
            assert provenance["source_documents"]["authenticity_verified"] is False
            for relative_path in provenance["source_documents"]["repository_paths"]:
                assert not relative_path.startswith("/")
                assert (REPOSITORY_ROOT / relative_path).is_file()
            assert provenance["demo_assessment"] == {
                "execution_mode": "DEMO",
                "assessment_source": "precomputed_fixture",
                "base_artifact_path": "fixtures/demo/T2_assessment.json",
                "derivation_version": "demo-fixture-derivation/v1",
                "runtime_model_call": False,
                "used_for_current_demo": True,
            }
            assert provenance["live_assessment"]["model"] == "gpt-5.6"
            assert provenance["live_assessment"]["assessment_source"] == (
                "gpt_generated_live"
            )
            assert provenance["live_assessment"]["runtime_model_call"] is True
            live_artifact = json.loads(
                (
                    REPOSITORY_ROOT
                    / "fixtures/live/gpt-5.6-t2-assessment.json"
                ).read_text(encoding="utf-8")
            )
            assert provenance["live_assessment"]["prompt_version"] == (
                live_artifact["prompt_version"]
            )
            assert provenance["live_assessment"][
                "post_validation_transformations"
            ] == live_artifact["post_validation_transformations"]
            assert provenance["live_assessment"]["used_for_current_demo"] is False

            status, approval_response = await _request(
                app,
                "POST",
                "/v1/demo/approvals",
                _demo_approval_payload(),
            )
            assert status == 200
            approval = approval_response["approval"]
            assert approval["decision"] == "approve_with_conditions"
            assert approval["approver"]["identity_assurance"] == "declared_only"
            assert approval_response["provenance"] == {
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
            }

            status, receipt_response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )
            assert status == 201
            receipt = receipt_response["receipt"]
            serialized_response = json.dumps(receipt_response)
            assert "PRIVATE KEY" not in serialized_response
            assert str(private_key_path) not in serialized_response
            assert receipt_response["provenance"]["assessment"] == {
                "execution_mode": "DEMO",
                "assessment_source": "precomputed_fixture",
                "runtime_model_call": False,
            }
            assert receipt_response["provenance"]["policy_result"]["source"] == (
                "aelitium_deterministic_policy_engine"
            )
            assert receipt_response["provenance"][
                "source_document_authenticity_verified"
            ] is False

            status, verification = await _request(
                app,
                "POST",
                "/v1/demo/receipts/verify",
                {"receipt": receipt},
            )
            assert status == 200
            assert verification["status"] == "VALID"
            assert verification["reason"] == "VERIFIED"
            assert verification["provenance"]["result_source"] == (
                "aelitium_local_integrity_verifier"
            )
            assert "source_document_authenticity" in verification["provenance"][
                "does_not_prove"
            ]
            assert "decision_fairness" in verification["provenance"][
                "does_not_prove"
            ]

            tampered = copy.deepcopy(receipt)
            price = next(
                fact
                for fact in tampered["decision_content"]["model_assessment"]["facts"]
                if fact["fact_key"] == "commercial.annual_price_eur"
            )
            price["value"]["integer_value"] = 14000
            status, verification = await _request(
                app,
                "POST",
                "/v1/demo/receipts/verify",
                {"receipt": tampered},
            )
            assert status == 200
            assert verification["status"] == "INVALID"
            assert verification["reason"] == "ASSESSMENT_HASH_MISMATCH"
            assert verification["provenance"]["result_source"] == (
                "aelitium_local_integrity_verifier"
            )

    asyncio.run(scenario())


def test_approval_authorization_direct_receipt_object_bypass_is_rejected(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "direct-bypass.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            approval["approver"]["role"] = "intern"
            approval["decision"] = "approve"
            approval["conditions"] = []

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval": approval},
            )

            assert status == 422
            assert any(
                error["loc"][-1] == "approval" and error["type"] == "extra_forbidden"
                for error in response["detail"]
            )
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_unknown_approval_id_is_rejected(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "unknown-approval.db")
        async with app.router.lifespan_context(app):
            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": "approval-unknown-001"},
            )

            assert status == 404
            assert _error_code(response) == "APPROVAL_NOT_FOUND"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_missing_role_is_rejected_at_admission(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "missing-role.db")
        payload = _demo_approval_payload()
        del payload["approver_role"]
        async with app.router.lifespan_context(app):
            status, response = await _request(
                app, "POST", "/v1/demo/approvals", payload
            )

            assert status == 422
            assert any(
                error["loc"][-1] == "approver_role" and error["type"] == "missing"
                for error in response["detail"]
            )
            assert app.state.demo_approvals == {}

    asyncio.run(scenario())


def test_approval_authorization_wrong_role_is_rejected_at_admission(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "wrong-role-admission.db")
        async with app.router.lifespan_context(app):
            status, response = await _request(
                app,
                "POST",
                "/v1/demo/approvals",
                _demo_approval_payload("operations_reviewer"),
            )

            assert status == 422
            assert _error_code(response) == "APPROVER_ROLE_NOT_AUTHORIZED"
            assert app.state.demo_approvals == {}

    asyncio.run(scenario())


def test_approval_authorization_second_case_approval_is_rejected(tmp_path):
    async def scenario():
        app = create_app(database_path=tmp_path / "duplicate-approval.db")
        async with app.router.lifespan_context(app):
            first = await _record_valid_demo_approval(app)
            status, response = await _request(
                app,
                "POST",
                "/v1/demo/approvals",
                _demo_approval_payload(),
            )

            assert status == 409
            assert _error_code(response) == "APPROVAL_ALREADY_RECORDED"
            assert list(app.state.demo_approvals) == [first["approval_id"]]
            assert app.state.demo_approval_by_case == {
                first["case_id"]: first["approval_id"]
            }

    asyncio.run(scenario())


def test_approval_authorization_wrong_stored_role_is_rejected_at_issuance(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "wrong-role-issuance.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            record = app.state.demo_approvals[approval["approval_id"]]
            wrong_role = copy.deepcopy(record.approval)
            wrong_role["approver"]["role"] = "operations_reviewer"
            app.state.demo_approvals[approval["approval_id"]] = replace(
                record,
                approval=wrong_role,
                approval_hash=hash_json(wrong_role),
            )

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "APPROVER_ROLE_NOT_AUTHORIZED"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_other_case_is_rejected(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "other-case.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            record = app.state.demo_approvals[approval["approval_id"]]
            other_case = copy.deepcopy(record.approval)
            other_case["case_id"] = "case-other-decision"
            app.state.demo_approvals[approval["approval_id"]] = replace(
                record,
                approval=other_case,
                approval_hash=hash_json(other_case),
            )

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "APPROVAL_CASE_MISMATCH"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_unconditional_approval_is_rejected(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "unconditional.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            record = app.state.demo_approvals[approval["approval_id"]]
            unconditional = copy.deepcopy(record.approval)
            unconditional["decision"] = "approve"
            unconditional["conditions"] = []
            app.state.demo_approvals[approval["approval_id"]] = replace(
                record,
                approval=unconditional,
                approval_hash=hash_json(unconditional),
            )

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "APPROVAL_CONDITIONS_REQUIRED"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_stale_assessment_is_rejected(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "stale-assessment.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            price = next(
                fact
                for fact in app.state.demo_snapshot["assessment"]["facts"]
                if fact["fact_key"] == "commercial.annual_price_eur"
            )
            price["value"]["integer_value"] = 19000

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "CURRENT_ASSESSMENT_MISMATCH"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_stale_policy_result_is_rejected(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "stale-policy.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            app.state.demo_snapshot["policy_result"]["evaluated_at"] = (
                "2026-07-19T11:06:00Z"
            )

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "APPROVAL_STALE"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_modified_record_is_rejected(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "modified-record.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            record = app.state.demo_approvals[approval["approval_id"]]
            record.approval["justification"] = "Modified after admission."

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "APPROVAL_RECORD_MODIFIED"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())


def test_approval_authorization_blocking_controls_reject_receipt(tmp_path):
    async def scenario():
        private_key_path, keyring_path = _demo_signing_paths(tmp_path)
        app = create_app(
            database_path=tmp_path / "blocked-receipt.db",
            demo_private_key_path=private_key_path,
            demo_keyring_path=keyring_path,
        )
        async with app.router.lifespan_context(app):
            approval = await _record_valid_demo_approval(app)
            app.state.demo_snapshot["policy_result"]["blocking_controls"] = [
                {
                    "control_id": "R2_EU_DATA_RESIDENCY",
                    "description": "Residency evidence required.",
                    "missing_evidence": ["EU-only confirmation"],
                    "suggested_request": "Provide EU-only confirmation.",
                }
            ]

            status, response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval_id": approval["approval_id"]},
            )

            assert status == 409
            assert _error_code(response) == "POLICY_BLOCKING_CONTROLS"
            assert app.state.demo_receipts == {}

    asyncio.run(scenario())
