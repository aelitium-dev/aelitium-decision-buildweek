"""Small SQLite boundary using a versioned SQL schema and no migration framework."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .paths import REPOSITORY_ROOT
from .vendor.aelitium_v3.canonical import canonical_json


class StoreConflictError(RuntimeError):
    """Raised when an immutable identifier already exists."""


class SQLiteStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        sql = (REPOSITORY_ROOT / "backend" / "sql" / "001_initial.sql").read_text(
            encoding="utf-8"
        )
        with self._connection() as connection:
            connection.executescript(sql)

    def put_case(self, case: dict[str, Any]) -> None:
        try:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO cases (
                        case_id, decision_domain, title, state, payload_json,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case["case_id"],
                        case["decision_domain"],
                        case["title"],
                        case["state"],
                        canonical_json(case),
                        case["created_at"],
                        case["updated_at"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise StoreConflictError(f"case already exists: {case['case_id']}") from exc

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM cases WHERE case_id = ?", (case_id,)
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def record_policy_result(self, result: dict[str, Any]) -> None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM cases WHERE case_id = ?", (result["case_id"],)
            ).fetchone()
            if row is None:
                raise KeyError(result["case_id"])

            case = json.loads(row["payload_json"])
            case["state"] = result["state"]
            case["updated_at"] = result["evaluated_at"]
            connection.execute(
                """
                INSERT INTO policy_results (
                    case_id, assessment_hash, policy_version, state,
                    payload_json, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result["case_id"],
                    result["assessment_hash"],
                    result["policy_version"],
                    result["state"],
                    canonical_json(result),
                    result["evaluated_at"],
                ),
            )
            connection.execute(
                """
                UPDATE cases
                SET state = ?, payload_json = ?, updated_at = ?
                WHERE case_id = ?
                """,
                (
                    case["state"],
                    canonical_json(case),
                    case["updated_at"],
                    case["case_id"],
                ),
            )

    def latest_policy_result(self, case_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT payload_json FROM policy_results
                WHERE case_id = ? ORDER BY result_id DESC LIMIT 1
                """,
                (case_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()
