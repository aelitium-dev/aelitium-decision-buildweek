from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.validate_scaffold import (
    ValidationFailure,
    is_local_absolute_path,
    iter_strings,
    validate_optional_upstream_checkout,
)

from aelitium_decision.paths import REPOSITORY_ROOT


MANIFEST_PATH = REPOSITORY_ROOT / "PREEXISTING_ASSETS.json"
VALIDATOR_PATH = REPOSITORY_ROOT / "scripts/validate_scaffold.py"


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_preexisting_manifest_contains_no_machine_local_paths():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == "1.1"
    assert not any(is_local_absolute_path(value) for value in iter_strings(manifest))
    assert all("source_checkout" not in asset for asset in manifest["assets"])


def test_scaffold_validator_runs_without_upstream_checkout_from_another_cwd(
    tmp_path: Path,
):
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PREEXISTING_ASSETS=VALID" in completed.stdout
    assert "UPSTREAM_CHECKOUT=SKIPPED optional" in completed.stdout
    assert "SCAFFOLD_STATUS=VALID" in completed.stdout
    assert str(REPOSITORY_ROOT.parent) not in completed.stdout


def test_optional_upstream_checkout_reads_blobs_from_the_pinned_commit(
    tmp_path: Path,
):
    checkout = tmp_path / "upstream"
    checkout.mkdir()
    _git(checkout, "init", "--quiet")

    sources = {
        "engine/canonical.py": b"canonical helper\n",
        "LICENSE": b"license text\n",
        "NOTICE": b"notice text\n",
    }
    for relative_path, content in sources.items():
        path = checkout / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    _git(checkout, "add", ".")
    _git(
        checkout,
        "-c",
        "user.name=AELITIUM Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "test fixture",
    )
    commit = _git(checkout, "rev-parse", "HEAD")
    assets = [
        {
            "source_commit": commit,
            "source_path": relative_path,
            "source_sha256": hashlib.sha256(content).hexdigest(),
        }
        for relative_path, content in sources.items()
    ]

    assert validate_optional_upstream_checkout(checkout, assets) == commit

    # The strengthened check reads the pinned Git object, not mutable worktree bytes.
    (checkout / "engine/canonical.py").write_bytes(b"uncommitted change\n")
    assert validate_optional_upstream_checkout(checkout, assets) == commit

    mismatched_assets = copy.deepcopy(assets)
    mismatched_assets[0]["source_sha256"] = "0" * 64
    with pytest.raises(ValidationFailure, match="UPSTREAM_SOURCE_HASH_MISMATCH"):
        validate_optional_upstream_checkout(checkout, mismatched_assets)
