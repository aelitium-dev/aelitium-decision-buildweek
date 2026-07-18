"""Repository path resolution shared by the CLI and application services."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPOSITORY_ROOT / "schemas"
POLICIES_DIR = REPOSITORY_ROOT / "policies"
FIXTURES_DIR = REPOSITORY_ROOT / "fixtures"
