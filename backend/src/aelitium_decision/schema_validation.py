"""Fail-closed validation against the repository's canonical JSON Schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .paths import SCHEMAS_DIR


class CanonicalSchemaError(ValueError):
    """Raised when an instance fails its authoritative backend schema."""


@lru_cache(maxsize=None)
def load_schema(filename: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def validate_canonical(instance: Any, schema_filename: str) -> None:
    """Validate fully and report every canonical-schema violation at once."""

    schema = load_schema(schema_filename)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if not errors:
        return

    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        details.append(f"{location}: {error.message}")
    raise CanonicalSchemaError("; ".join(details))


def load_and_validate(path: Path, schema_filename: str) -> dict[str, Any]:
    instance = json.loads(path.read_text(encoding="utf-8"))
    validate_canonical(instance, schema_filename)
    return instance
