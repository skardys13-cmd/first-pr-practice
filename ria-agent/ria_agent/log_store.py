"""Append-only receipt log (Step 4).

SQLite for querying, a mirrored JSONL file for reading without tooling. The
store exposes no update and no delete. A correction is a new receipt whose
``references_receipt_id`` points at the one being corrected.

The plan asked for "an append-only discipline", meaning no update or delete
paths in code. Discipline is a property of the author, so the constraint is
pushed into the database as well: UPDATE and DELETE on the receipts table abort
at the trigger. That is still not tamper-*proof* -- anyone who can drop a
trigger can edit a row -- and OPEN_FINDINGS.md carries that as finding #3.
``verify_mirror`` is the cheap check that remains: the JSONL and the database
must still agree.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from .receipts import Receipt

SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id            TEXT PRIMARY KEY,
    timestamp_start       TEXT NOT NULL,
    timestamp_end         TEXT NOT NULL,
    human_owner           TEXT NOT NULL,
    role                  TEXT NOT NULL,
    crm_task_id           TEXT NOT NULL,
    workflow_id           TEXT NOT NULL,
    step_id               TEXT NOT NULL,
    system_touched        TEXT NOT NULL,
    action_type           TEXT NOT NULL,
    outcome               TEXT NOT NULL,
    references_receipt_id TEXT,
    payload               TEXT NOT NULL,
    appended_at           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_receipts_owner    ON receipts (human_owner);
CREATE INDEX IF NOT EXISTS ix_receipts_workflow ON receipts (workflow_id);
CREATE INDEX IF NOT EXISTS ix_receipts_outcome  ON receipts (outcome);
CREATE INDEX IF NOT EXISTS ix_receipts_start    ON receipts (timestamp_start);
CREATE INDEX IF NOT EXISTS ix_receipts_refs     ON receipts (references_receipt_id);

CREATE TRIGGER IF NOT EXISTS receipts_no_update
BEFORE UPDATE ON receipts
BEGIN
    SELECT RAISE(ABORT, 'receipts are append-only: correct by appending a new receipt');
END;

CREATE TRIGGER IF NOT EXISTS receipts_no_delete
BEFORE DELETE ON receipts
BEGIN
    SELECT RAISE(ABORT, 'receipts are append-only: nothing is ever deleted');
END;
"""


class LogStore:
    """The firm's record of what the agent did. Append-only, by construction."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db_path = self.directory / "receipts.db"
        self.jsonl_path = self.directory / "receipts.jsonl"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # -- the only write path -----------------------------------------------

    def append(self, receipt: Receipt) -> Receipt:
        """Validate and store. Invalid receipts are never written."""
        receipt.validate()
        payload = json.dumps(receipt.to_dict(), sort_keys=True)
        appended_at = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            self._conn.execute(
                "INSERT INTO receipts (receipt_id, timestamp_start, timestamp_end,"
                " human_owner, role, crm_task_id, workflow_id, step_id,"
                " system_touched, action_type, outcome, references_receipt_id,"
                " payload, appended_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    receipt.receipt_id, receipt.timestamp_start, receipt.timestamp_end,
                    receipt.human_owner, receipt.role, receipt.crm_task_id,
                    receipt.workflow_id, receipt.step_id, receipt.system_touched,
                    receipt.action_type, receipt.outcome,
                    receipt.references_receipt_id, payload, appended_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateReceipt(receipt.receipt_id) from exc
        self._conn.commit()
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        return receipt

    def append_all(self, receipts: Iterable[Receipt]) -> int:
        return sum(1 for r in receipts if self.append(r))

    # -- reads --------------------------------------------------------------

    def get(self, receipt_id: str) -> Receipt | None:
        row = self._conn.execute(
            "SELECT payload FROM receipts WHERE receipt_id = ?", (receipt_id,)
        ).fetchone()
        return Receipt.from_dict(json.loads(row["payload"])) if row else None

    def query(
        self,
        *,
        human_owner: str | None = None,
        workflow_id: str | None = None,
        outcome: str | None = None,
        crm_task_id: str | None = None,
        action_type: str | None = None,
        references_receipt_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int | None = None,
    ) -> list[Receipt]:
        """Filter by the dimensions a compliance review actually asks about."""
        clauses: list[str] = []
        params: list[str] = []
        for column, value in (
            ("human_owner", human_owner),
            ("workflow_id", workflow_id),
            ("outcome", outcome),
            ("crm_task_id", crm_task_id),
            ("action_type", action_type),
            ("references_receipt_id", references_receipt_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if since is not None:
            clauses.append("timestamp_start >= ?")
            params.append(since)
        if until is not None:
            clauses.append("timestamp_start <= ?")
            params.append(until)

        sql = "SELECT payload FROM receipts"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY timestamp_start, appended_at, rowid"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        return [
            Receipt.from_dict(json.loads(row["payload"]))
            for row in self._conn.execute(sql, params)
        ]

    def __iter__(self) -> Iterator[Receipt]:
        return iter(self.query())

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) AS n FROM receipts").fetchone()["n"]

    # -- integrity ----------------------------------------------------------

    def verify_mirror(self) -> list[str]:
        """Check the JSONL mirror still matches the database.

        Not a tamper-proof guarantee -- see OPEN_FINDINGS.md #3 -- but an edit
        to either copy alone shows up here.
        """
        problems: list[str] = []
        if not self.jsonl_path.exists():
            return ["the JSONL mirror is missing"]

        mirror: dict[str, dict] = {}
        for number, line in enumerate(
            self.jsonl_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"mirror line {number} is not valid JSON")
                continue
            mirror[record["receipt_id"]] = record

        rows = {
            row["receipt_id"]: json.loads(row["payload"])
            for row in self._conn.execute("SELECT receipt_id, payload FROM receipts")
        }
        for receipt_id in rows.keys() - mirror.keys():
            problems.append(f"{receipt_id} is in the database but not the mirror")
        for receipt_id in mirror.keys() - rows.keys():
            problems.append(f"{receipt_id} is in the mirror but not the database")
        for receipt_id in rows.keys() & mirror.keys():
            if rows[receipt_id] != mirror[receipt_id]:
                problems.append(f"{receipt_id} differs between the database and the mirror")
        return problems

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "LogStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


class DuplicateReceipt(ValueError):
    """A receipt id may be written exactly once."""

    def __init__(self, receipt_id: str):
        super().__init__(f"receipt {receipt_id} has already been written")
