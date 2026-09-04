"""Reading the shared brain (Step 12).

The CRM is the system of record for what needs doing and who owns it. The agent
does not keep its own task queue; it reads the firm's.

Read-only, and structurally so: there is no write method on the interface, so
there is nothing to disable, misconfigure, or call by accident.

The real Redtail adapter is not here. It goes behind `CrmReader` unchanged, and
until it exists the fixture reader below stands in -- which also means every
test runs against known tasks including ones designed to be hostile.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .untrusted import Untrusted


@dataclass(frozen=True)
class CrmTask:
    """One open task, as the CRM has it.

    `subject` and `notes` are free text written by staff. They are untrusted
    input and reach a prompt only through `untrusted_parts`.
    """

    task_id: str
    subject: str
    owner: str
    status: str = "open"
    notes: str = ""
    category: str = ""
    template: str = ""
    due_date: str = ""
    priority: str = ""
    contact_name: str = ""
    household: str = ""
    account_numbers: tuple[str, ...] = ()
    custodian: str = ""

    def untrusted_parts(self) -> list[Untrusted]:
        parts = [Untrusted("task_subject", self.subject, f"redtail:task/{self.task_id}")]
        if self.notes:
            parts.append(Untrusted("task_notes", self.notes, f"redtail:task/{self.task_id}"))
        return parts

    def to_dict(self) -> dict:
        data = asdict(self)
        data["account_numbers"] = list(self.account_numbers)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "CrmTask":
        data = dict(data)
        data["account_numbers"] = tuple(data.get("account_numbers", ()))
        return cls(**data)


class CrmReader(ABC):
    """Read-only access to the firm's task system.

    Deliberately has no write method. Constitution II is easier to keep when
    there is no door.
    """

    name = "crm"

    @abstractmethod
    def open_tasks(self, owner: str | None = None) -> list[CrmTask]:
        """Every open task, optionally just one person's."""

    @abstractmethod
    def task(self, task_id: str) -> CrmTask | None:
        """One task by id, or None."""

    def owners(self) -> list[str]:
        return sorted({task.owner for task in self.open_tasks()})


class FixtureCrm(CrmReader):
    """A CrmReader backed by a JSON fixture. Stands in for Redtail."""

    name = "redtail"

    def __init__(self, tasks: list[CrmTask] | None = None, path: str | Path | None = None):
        if path is not None:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            tasks = [CrmTask.from_dict(entry) for entry in raw]
        self._tasks = list(tasks or [])

    def open_tasks(self, owner: str | None = None) -> list[CrmTask]:
        return [
            task for task in self._tasks
            if task.status == "open" and (owner is None or task.owner == owner)
        ]

    def task(self, task_id: str) -> CrmTask | None:
        return next((task for task in self._tasks if task.task_id == task_id), None)

    @classmethod
    def from_bundled_fixtures(cls) -> "FixtureCrm":
        return cls(path=Path(__file__).parent / "fixtures" / "redtail_tasks.json")
