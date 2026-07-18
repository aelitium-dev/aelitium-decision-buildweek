#!/usr/bin/env python3
"""Validate Build Week scaffold provenance, schemas, and demo fixtures."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ValidationFailure(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"JSON_INVALID {path.relative_to(ROOT)} {type(exc).__name__}") from exc


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValidationFailure(reason)


def validate_preexisting_assets() -> None:
    manifest = load_json(ROOT / "PREEXISTING_ASSETS.json")
    assets = manifest.get("assets")
    require(isinstance(assets, list) and len(assets) == 3, "ALLOWLIST_MUST_HAVE_EXACTLY_THREE_ASSETS")

    expected_fields = {
        "source_repository",
        "source_commit",
        "source_path",
        "destination_path",
        "modification_status",
        "classification",
    }

    for asset in assets:
        require(expected_fields.issubset(asset), f"ALLOWLIST_FIELDS_MISSING {asset.get('component', 'unknown')}")
        require(asset["classification"] == "pre-existing", "ALLOWLIST_CLASSIFICATION_INVALID")
        require(SHA256_RE.fullmatch(asset["source_sha256"]) is not None, "ALLOWLIST_SOURCE_HASH_INVALID")

        source = Path(asset["source_checkout"]) / asset["source_path"]
        destination = ROOT / asset["destination_path"]
        require(source.is_file(), f"ALLOWLIST_SOURCE_MISSING {source}")
        require(destination.is_file(), f"ALLOWLIST_DESTINATION_MISSING {destination.relative_to(ROOT)}")
        require(sha256_file(source) == asset["source_sha256"], f"ALLOWLIST_SOURCE_HASH_MISMATCH {source}")
        require(
            sha256_file(destination) == asset["source_sha256"],
            f"ALLOWLIST_DESTINATION_HASH_MISMATCH {destination.relative_to(ROOT)}",
        )


def validate_fixture_manifest() -> None:
    manifest = load_json(ROOT / "fixtures" / "manifest.json")
    documents = manifest.get("documents")
    require(isinstance(documents, list) and len(documents) == 5, "FIXTURE_MANIFEST_REQUIRES_F1_TO_F5")
    require([document["document_id"] for document in documents] == ["F1", "F2", "F3", "F4", "F5"], "FIXTURE_ORDER_INVALID")

    for document in documents:
        expected_hash = document.get("sha256")
        require(isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash) is not None, "FIXTURE_HASH_INVALID")
        path = ROOT / "fixtures" / document["path"]
        require(path.is_file(), f"FIXTURE_MISSING {document['document_id']}")
        require(sha256_file(path) == expected_hash, f"FIXTURE_HASH_MISMATCH {document['document_id']}")


def walk_strict_objects(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        if value.get("type") == "object" and "properties" in value:
            require(value.get("additionalProperties") is False, f"STRICT_ADDITIONAL_PROPERTIES_MISSING {path}")
            properties = set(value["properties"])
            required = set(value.get("required", []))
            require(properties == required, f"STRICT_REQUIRED_FIELDS_MISMATCH {path}")
        for key, child in value.items():
            walk_strict_objects(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_strict_objects(child, f"{path}/{index}")


def validate_schemas() -> None:
    paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    require(len(paths) == 5, "EXACTLY_FIVE_V1_SCHEMAS_REQUIRED")
    schemas = [(path, load_json(path)) for path in paths]

    model_path = ROOT / "schemas" / "model_assessment.v1.schema.json"
    model_schema = load_json(model_path)
    walk_strict_objects(model_schema)

    receipt = load_json(ROOT / "schemas" / "decision_receipt.v1.schema.json")
    require(
        set(receipt["required"]) == {"decision_content", "signed_receipt_payload", "signature"},
        "RECEIPT_TOP_LEVEL_CONTRACT_INVALID",
    )
    require(receipt.get("additionalProperties") is False, "RECEIPT_MUST_FAIL_ON_ADDITIONAL_FIELDS")

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("SCHEMA_METAVALIDATION=SKIPPED jsonschema-not-installed")
    else:
        for path, schema in schemas:
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:  # jsonschema exposes multiple schema error types
                raise ValidationFailure(f"SCHEMA_INVALID {path.name} {type(exc).__name__}") from exc
        print("SCHEMA_METAVALIDATION=VALID count=5")


def validate_long_dpa() -> None:
    text = (ROOT / "fixtures" / "documents" / "F4_executed_data_processing_addendum.md").read_text(encoding="utf-8")
    pages = [int(value) for value in re.findall(r"^## Page (\d+) of 34", text, flags=re.MULTILINE)]
    require(pages == list(range(1, 35)), "F4_PAGE_SEQUENCE_INVALID")
    require(text.count('page-break-after: always') == 33, "F4_PAGE_BREAK_COUNT_INVALID")

    page_23 = text.split("## Page 23 of 34", maxsplit=1)[1].split("## Page 24 of 34", maxsplit=1)[0]
    require("without providing Customer prior notice" in page_23, "F4_PAGE_23_MATERIAL_CLAUSE_MISSING")
    require("30 days' advance notice" in page_23, "F4_PAGE_23_CONFLICT_ACKNOWLEDGEMENT_MISSING")
    require("Page 34 of 34 — Execution" in text, "F4_EXECUTION_PAGE_MISSING")


def validate_no_key_material() -> None:
    prohibited_suffixes = {".key", ".pem", ".p12"}
    excluded_parts = {
        ".git",
        ".venv",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
        ".next",
    }
    detector_path = Path(__file__).resolve()
    files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not excluded_parts.intersection(path.parts)
        and path.resolve() != detector_path
    ]
    require(not any(path.suffix.lower() in prohibited_suffixes for path in files), "PRIVATE_KEY_FILE_DETECTED")

    markers = ("BEGIN PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY", "AEL_ED25519_PRIVKEY_B64=")
    for path in files:
        if path.suffix.lower() not in {".md", ".json", ".py", ".txt", ".example"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        require(not any(marker in text for marker in markers), f"PRIVATE_KEY_MARKER_DETECTED {path.relative_to(ROOT)}")


def main() -> int:
    checks = [
        ("PREEXISTING_ASSETS", validate_preexisting_assets),
        ("FIXTURES", validate_fixture_manifest),
        ("SCHEMAS", validate_schemas),
        ("LONG_DPA", validate_long_dpa),
        ("KEY_MATERIAL", validate_no_key_material),
    ]
    try:
        for name, check in checks:
            check()
            print(f"{name}=VALID")
    except ValidationFailure as exc:
        print(f"SCAFFOLD_STATUS=INVALID reason={exc}")
        return 2

    print("SCAFFOLD_STATUS=VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
