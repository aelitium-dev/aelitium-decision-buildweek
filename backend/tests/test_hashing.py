from __future__ import annotations

import pytest

from aelitium_decision.hashing import (
    CanonicalizationError,
    DuplicateKeyError,
    canonical_json,
    parse_json_strict,
)
from aelitium_decision.paths import REPOSITORY_ROOT


def test_internal_boundary_preserves_pinned_canonical_contract():
    assert canonical_json({"z": "é", "a": [2, 1]}) == '{"a":[2,1],"z":"é"}'


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"value":NaN}', '{"value":1.5}'])
def test_strict_parser_rejects_noncanonical_json(raw):
    with pytest.raises((DuplicateKeyError, CanonicalizationError)):
        parse_json_strict(raw)


def test_canonical_boundary_rejects_python_float():
    with pytest.raises(CanonicalizationError, match="must be integers"):
        canonical_json({"confidence": 70.0})


def test_only_internal_hashing_boundary_imports_vendor_canonicalization():
    source_root = REPOSITORY_ROOT / "backend" / "src" / "aelitium_decision"
    importers = []
    for path in source_root.rglob("*.py"):
        if "vendor" in path.parts:
            continue
        if "vendor.aelitium_v3" in path.read_text(encoding="utf-8"):
            importers.append(path.relative_to(source_root).as_posix())

    assert importers == ["hashing.py"]
