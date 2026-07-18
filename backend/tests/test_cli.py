from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from aelitium_decision.paths import REPOSITORY_ROOT


@pytest.mark.parametrize("case_name", ["T1", "T2", "T3"])
def test_each_golden_case_is_executable_from_cli(case_name):
    environment = os.environ.copy()
    source_root = str(REPOSITORY_ROOT / "backend" / "src")
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-m", "aelitium_decision.cli", "demo", case_name, "--compact"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["demo_case"] == case_name
    assert payload["mode"] == "DEMO"
    assert all(payload["golden_checks"].values())
