"""The whitelist, and the entry point that enforces it (Step 17).

The agent acts only on task types that scored clean in shadow mode. Everything
else goes to Stopped by design -- not as a failure, but as the intended
behaviour for anything unproven.

`Gate.admit` is the single door. Nothing downstream re-decides whether a task is
allowed, because a second place to decide is a second place to get it wrong.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import roles, stops
from .crm import CrmTask
from .normalizer import Intent
from .shadow import ShadowReport


@dataclass(frozen=True)
class Admission:
    """Whether this task may proceed, and if not, exactly why."""

    allowed: bool
    stop_reason: str | None = None
    detail: str = ""

    @property
    def next_step(self) -> str | None:
        return stops.next_step_for(self.stop_reason) if self.stop_reason else None


ALLOWED = Admission(True)


class Whitelist:
    """Task templates proven clean in shadow mode, and the workflows they map to."""

    def __init__(self, templates: set[str] | None = None, workflows: set[str] | None = None):
        self.templates = set(templates or ())
        self.workflows = set(workflows or ())

    def __contains__(self, template: str) -> bool:
        return template in self.templates

    def permits_workflow(self, workflow_id: str) -> bool:
        # An empty workflow set means the whitelist is scoped by template only.
        return not self.workflows or workflow_id in self.workflows

    @classmethod
    def from_report(cls, report: ShadowReport, *, min_samples: int = 20) -> "Whitelist":
        return cls(templates=report.clean_templates(min_samples=min_samples))

    @classmethod
    def load(cls, path: str | Path) -> "Whitelist":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(set(data.get("templates", ())), set(data.get("workflows", ())))

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"templates": sorted(self.templates), "workflows": sorted(self.workflows)},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        return path


class Gate:
    """The entry point. Every task passes through here or does not run."""

    def __init__(self, whitelist: Whitelist, role_id: str):
        self.whitelist = whitelist
        self.role = roles.require(role_id)

    def admit(self, task: CrmTask, intent: Intent) -> Admission:
        if not intent.recognised:
            return Admission(
                False, stops.UNRECOGNISED_TASK,
                "No rule matched and the model could not place this task either.",
            )

        template = task.template.strip()
        if not template or template not in self.whitelist:
            return Admission(
                False, stops.NOT_WHITELISTED,
                f"{template or 'A task with no template'} has not been proven in "
                "shadow mode, so the agent will not act on it.",
            )

        if not self.whitelist.permits_workflow(intent.workflow_guess):
            return Admission(
                False, stops.NOT_WHITELISTED,
                f"The workflow {intent.workflow_guess} is not on the whitelist.",
            )

        refusal = self.role.refusal(intent.workflow_guess)
        if refusal:
            return Admission(False, stops.ROLE_NOT_PERMITTED, refusal + ".")

        for blocker in intent.blockers:
            if "confidence" in blocker:
                return Admission(False, stops.LOW_CONFIDENCE, blocker.capitalize() + ".")
            if "which account" in blocker or "not linked" in blocker:
                return Admission(False, stops.AMBIGUOUS_MATCH, blocker.capitalize() + ".")
            return Admission(False, stops.MISSING_INFORMATION, blocker.capitalize() + ".")

        return ALLOWED
