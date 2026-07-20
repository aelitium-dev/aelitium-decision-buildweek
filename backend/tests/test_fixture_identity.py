from __future__ import annotations

import json
import subprocess

from aelitium_decision.paths import REPOSITORY_ROOT


def test_fictional_vendor_identity_and_dpa_reference_are_consistent():
    manifest = json.loads(
        (REPOSITORY_ROOT / "fixtures/manifest.json").read_text(encoding="utf-8")
    )
    dpa = (
        REPOSITORY_ROOT
        / "fixtures/documents/F4_executed_data_processing_addendum.md"
    ).read_text(encoding="utf-8")

    assert manifest["vendor"] == "Nerythica AI Ltd. (fictional)"
    assert "As described in sections 8.3 and 8.4" in dpa
    stale_reference = "As described in sections " + "17 and 18"
    assert stale_reference not in dpa


def test_previous_vendor_name_and_identifiers_are_absent_from_tracked_files():
    previous_name = "Nova" + "Mind"
    previous_identifier_prefix = "N" + "M-"
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    text_suffixes = {".json", ".md", ".py", ".tsx", ".ts"}
    failures: list[str] = []

    for encoded_path in tracked:
        if not encoded_path:
            continue
        relative_path = encoded_path.decode("utf-8")
        path = REPOSITORY_ROOT / relative_path
        if path.suffix not in text_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if previous_name in text or previous_identifier_prefix in text:
            failures.append(relative_path)

    assert not failures, f"stale fictional vendor identity in: {failures}"
