from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from aelitium_decision.demo_workflow import build_demo_snapshot
from aelitium_decision.paths import REPOSITORY_ROOT


FIXTURES_DIR = REPOSITORY_ROOT / "fixtures"
DEMO_MANIFEST_PATH = FIXTURES_DIR / "demo/golden_cases.v1.json"
FIXTURE_MANIFEST_PATH = FIXTURES_DIR / "manifest.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"expected an object in {path}"
    return value


def _evidence_sources() -> dict[str, Path]:
    fixture_manifest = _load_json(FIXTURE_MANIFEST_PATH)
    sources: dict[str, Path] = {}
    for document in fixture_manifest["documents"]:
        source_path = FIXTURES_DIR / document["path"]
        sources[document["document_id"]] = source_path
        sources[document["filename"]] = source_path

    demo_manifest = _load_json(DEMO_MANIFEST_PATH)
    for document_id, relative_path in demo_manifest["evidence_sources"].items():
        sources[document_id] = REPOSITORY_ROOT / relative_path
    return sources


def _quoted_references(
    value: Any, json_path: str = "$"
) -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if "quoted_text" in value or "document_id" in value:
            assert "quoted_text" in value and "document_id" in value, (
                f"incomplete evidence reference at {json_path}"
            )
            yield json_path, value
        for key, child in value.items():
            yield from _quoted_references(child, f"{json_path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _quoted_references(child, f"{json_path}[{index}]")


def _assert_literal_quotes(
    artifact_name: str, value: Any, sources: dict[str, Path]
) -> int:
    failures: list[str] = []
    checked = 0
    repository_root = REPOSITORY_ROOT.resolve()

    for json_path, reference in _quoted_references(value):
        checked += 1
        document_id = reference["document_id"]
        quoted_text = reference["quoted_text"]
        source_path = sources.get(document_id)
        if source_path is None:
            failures.append(
                f"{artifact_name}{json_path}: unknown document_id {document_id!r}"
            )
            continue

        resolved_path = source_path.resolve()
        if not resolved_path.is_relative_to(repository_root):
            failures.append(
                f"{artifact_name}{json_path}: source escapes repository: {source_path}"
            )
            continue
        if not resolved_path.is_file():
            failures.append(
                f"{artifact_name}{json_path}: source does not exist: {source_path}"
            )
            continue
        if not isinstance(quoted_text, str) or not quoted_text:
            failures.append(
                f"{artifact_name}{json_path}: quoted_text must be a non-empty string"
            )
            continue

        source_text = resolved_path.read_text(encoding="utf-8")
        if quoted_text not in source_text:
            failures.append(
                f"{artifact_name}{json_path}: quoted_text is not a literal substring "
                f"of {resolved_path.relative_to(repository_root)}"
            )

    assert not failures, "\n".join(failures)
    return checked


def test_all_checked_in_assessment_quotes_are_literal_source_substrings():
    sources = _evidence_sources()
    artifact_paths = sorted((FIXTURES_DIR / "demo").glob("*_assessment.json"))
    artifact_paths += sorted((FIXTURES_DIR / "live").glob("*assessment.json"))

    checked = 0
    for artifact_path in artifact_paths:
        checked += _assert_literal_quotes(
            str(artifact_path.relative_to(REPOSITORY_ROOT)),
            _load_json(artifact_path),
            sources,
        )

    assert checked > 0, "no quoted evidence references were checked"


def test_generated_post_f5_demo_quotes_are_literal_source_substrings():
    checked = _assert_literal_quotes(
        "build_demo_snapshot().assessment",
        build_demo_snapshot()["assessment"],
        _evidence_sources(),
    )

    assert checked > 0, "the generated DEMO assessment had no evidence references"
