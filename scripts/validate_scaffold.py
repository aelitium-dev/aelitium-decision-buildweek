#!/usr/bin/env python3
"""Validate Build Week scaffold provenance, schemas, and demo fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ValidationFailure(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"JSON_INVALID {path.relative_to(ROOT)} {type(exc).__name__}") from exc


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValidationFailure(reason)


def iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


def is_local_absolute_path(value: str) -> bool:
    return (
        value.startswith("/")
        or value.startswith("\\\\")
        or value.lower().startswith("file:")
        or re.match(r"^[A-Za-z]:[\\/]", value) is not None
    )


def validate_relative_path(value: Any, *, reason: str) -> PurePosixPath:
    require(isinstance(value, str) and bool(value), reason)
    require("\\" not in value, reason)
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts, reason)
    return path


def _git_bytes(checkout: Path, arguments: list[str], failure: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(checkout), *arguments],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise ValidationFailure(failure) from exc
    require(completed.returncode == 0, failure)
    return completed.stdout


def validate_optional_upstream_checkout(
    checkout: Path, assets: list[dict[str, Any]]
) -> str:
    """Verify pinned source blobs when a reviewer supplies an upstream clone."""

    require(checkout.is_dir(), "UPSTREAM_CHECKOUT_NOT_DIRECTORY")
    inside = _git_bytes(
        checkout,
        ["rev-parse", "--is-inside-work-tree"],
        "UPSTREAM_CHECKOUT_NOT_GIT",
    )
    require(inside.strip() == b"true", "UPSTREAM_CHECKOUT_NOT_GIT")

    commits = {asset["source_commit"] for asset in assets}
    require(len(commits) == 1, "ALLOWLIST_SOURCE_COMMIT_INCONSISTENT")
    commit = next(iter(commits))
    _git_bytes(
        checkout,
        ["cat-file", "-e", f"{commit}^{{commit}}"],
        "UPSTREAM_PINNED_COMMIT_MISSING",
    )
    for asset in assets:
        source_path = asset["source_path"]
        source_bytes = _git_bytes(
            checkout,
            ["cat-file", "blob", f"{commit}:{source_path}"],
            f"UPSTREAM_SOURCE_MISSING {source_path}",
        )
        require(
            sha256_bytes(source_bytes) == asset["source_sha256"],
            f"UPSTREAM_SOURCE_HASH_MISMATCH {source_path}",
        )
    return commit


def validate_preexisting_assets(upstream_checkout: Path | None = None) -> str | None:
    manifest = load_json(ROOT / "PREEXISTING_ASSETS.json")
    require(manifest.get("manifest_version") == "1.1", "ALLOWLIST_MANIFEST_VERSION_INVALID")
    require(
        not any(is_local_absolute_path(value) for value in iter_strings(manifest)),
        "ALLOWLIST_LOCAL_ABSOLUTE_PATH_PROHIBITED",
    )
    assets = manifest.get("assets")
    require(isinstance(assets, list) and len(assets) == 3, "ALLOWLIST_MUST_HAVE_EXACTLY_THREE_ASSETS")

    expected_fields = {
        "component",
        "source_repository",
        "source_commit",
        "source_path",
        "source_sha256",
        "destination_path",
        "modification_status",
        "classification",
    }

    for asset in assets:
        require(isinstance(asset, dict), "ALLOWLIST_ASSET_INVALID")
        require(expected_fields.issubset(asset), f"ALLOWLIST_FIELDS_MISSING {asset.get('component', 'unknown')}")
        require("source_checkout" not in asset, "ALLOWLIST_LOCAL_CHECKOUT_FIELD_PROHIBITED")
        require(asset["classification"] == "pre-existing", "ALLOWLIST_CLASSIFICATION_INVALID")
        require(
            isinstance(asset["source_sha256"], str)
            and SHA256_RE.fullmatch(asset["source_sha256"]) is not None,
            "ALLOWLIST_SOURCE_HASH_INVALID",
        )
        require(
            isinstance(asset["source_commit"], str)
            and GIT_COMMIT_RE.fullmatch(asset["source_commit"]) is not None,
            "ALLOWLIST_SOURCE_COMMIT_INVALID",
        )
        require(isinstance(asset["source_repository"], str) and asset["source_repository"], "ALLOWLIST_SOURCE_REPOSITORY_INVALID")
        require(isinstance(asset["modification_status"], str) and asset["modification_status"], "ALLOWLIST_MODIFICATION_STATUS_INVALID")

        validate_relative_path(asset["source_path"], reason="ALLOWLIST_SOURCE_PATH_INVALID")
        destination_relative = validate_relative_path(
            asset["destination_path"], reason="ALLOWLIST_DESTINATION_PATH_INVALID"
        )
        destination = (ROOT / Path(destination_relative)).resolve()
        require(destination.is_relative_to(ROOT), "ALLOWLIST_DESTINATION_ESCAPES_REPOSITORY")
        require(destination.is_file(), f"ALLOWLIST_DESTINATION_MISSING {destination.relative_to(ROOT)}")
        require(
            sha256_file(destination) == asset["source_sha256"],
            f"ALLOWLIST_DESTINATION_HASH_MISMATCH {destination.relative_to(ROOT)}",
        )

    repositories = {asset["source_repository"] for asset in assets}
    commits = {asset["source_commit"] for asset in assets}
    require(len(repositories) == 1, "ALLOWLIST_SOURCE_REPOSITORY_INCONSISTENT")
    require(len(commits) == 1, "ALLOWLIST_SOURCE_COMMIT_INCONSISTENT")
    if upstream_checkout is None:
        return None
    return validate_optional_upstream_checkout(upstream_checkout, assets)


def validate_fixture_manifest() -> None:
    manifest = load_json(ROOT / "fixtures" / "manifest.json")
    require(
        manifest.get("vendor") == "Nerythica AI Ltd. (fictional)",
        "FIXTURE_VENDOR_IDENTITY_INVALID",
    )
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
    require(
        "As described in sections 8.3 and 8.4" in text,
        "F4_RETENTION_SECTION_REFERENCE_INVALID",
    )


def validate_no_key_material() -> None:
    prohibited_suffixes = {".key", ".pem", ".p12"}
    detector_path = Path(__file__).resolve()
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationFailure("GIT_FILE_ENUMERATION_FAILED") from exc
    files = []
    for relative_path in completed.stdout.split("\0"):
        if not relative_path:
            continue
        path = ROOT / relative_path
        if path.is_file() and path.resolve() != detector_path:
            files.append(path)
    require(not any(path.suffix.lower() in prohibited_suffixes for path in files), "PRIVATE_KEY_FILE_DETECTED")

    markers = ("BEGIN PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY", "AEL_ED25519_PRIVKEY_B64=")
    for path in files:
        if path.suffix.lower() not in {".md", ".json", ".py", ".txt", ".example"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        require(not any(marker in text for marker in markers), f"PRIVATE_KEY_MARKER_DETECTED {path.relative_to(ROOT)}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the standalone Build Week repository; optionally verify "
            "allowlisted blobs against a local upstream Git checkout."
        )
    )
    parser.add_argument(
        "--upstream-checkout",
        type=Path,
        help=(
            "optional path to an aelitium-v3 Git checkout containing the pinned "
            "commit; never required for standalone validation"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    checks = [
        ("FIXTURES", validate_fixture_manifest),
        ("SCHEMAS", validate_schemas),
        ("LONG_DPA", validate_long_dpa),
        ("KEY_MATERIAL", validate_no_key_material),
    ]
    try:
        upstream_commit = validate_preexisting_assets(args.upstream_checkout)
        print("PREEXISTING_ASSETS=VALID")
        if upstream_commit is None:
            print("UPSTREAM_CHECKOUT=SKIPPED optional")
        else:
            print(f"UPSTREAM_CHECKOUT=VALID commit={upstream_commit}")
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
