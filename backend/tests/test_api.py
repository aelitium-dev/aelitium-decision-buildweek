from __future__ import annotations

import asyncio
import copy
import json

from aelitium_decision.api import create_app
from aelitium_decision.demo import load_golden_manifest
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

            status, approval_response = await _request(
                app,
                "POST",
                "/v1/demo/approvals",
                {
                    "display_name": "Mara Ellison",
                    "justification": (
                        "Blocking evidence is complete; the contractual conflict "
                        "remains an explicit condition."
                    ),
                    "condition": (
                        "Renegotiate the subprocessor clause before renewal."
                    ),
                },
            )
            assert status == 200
            approval = approval_response["approval"]
            assert approval["decision"] == "approve_with_conditions"
            assert approval["approver"]["identity_assurance"] == "declared_only"

            status, receipt_response = await _request(
                app,
                "POST",
                "/v1/demo/receipts",
                {"approval": approval},
            )
            assert status == 201
            receipt = receipt_response["receipt"]
            serialized_response = json.dumps(receipt_response)
            assert "PRIVATE KEY" not in serialized_response
            assert str(private_key_path) not in serialized_response

            status, verification = await _request(
                app,
                "POST",
                "/v1/demo/receipts/verify",
                {"receipt": receipt},
            )
            assert status == 200
            assert verification == {"status": "VALID", "reason": "VERIFIED"}

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
            assert verification == {
                "status": "INVALID",
                "reason": "ASSESSMENT_HASH_MISMATCH",
            }

    asyncio.run(scenario())
