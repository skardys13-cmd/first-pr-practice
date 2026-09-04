"""The weekly health report (Step 45).

What the firm's owner looks at, and what you look at when you have customers.

On "time saved": it is only computed where the firm has recorded how long the
work takes by hand. Without that baseline the report says so and reports
nothing, because a time-saved figure derived from the agent's own run time is a
number about the agent, not about the firm. §1.10 requires time-to-complete to
drop by half and nothing in the plan ever measures the "before" — that gap is
OPEN_FINDINGS.md #10, and this is where it bites.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from .log_store import LogStore
from .plain import workflow_name
from .receipts import (
    APPROVE, PENDING_APPROVAL, PROPOSE, REJECT, STOPPED_CLEANUP_REQUIRED,
    STOPPED_NO_CHANGE, VERIFIED, WRITE,
)


class Baselines:
    """Minutes each workflow takes, measured rather than guessed.

    Two numbers per workflow, and the second one matters as much as the first:

    - `manual` — how long a person takes doing the whole thing by hand.
    - `review` — how long a person takes reviewing what the agent prepared.

    F-38: measure end-to-end task completion, not agent step time. The agent's
    own step time always looks excellent and says nothing, because the human
    half is where the time actually goes. A workflow is only faster if
    agent time *plus* review time beats the manual baseline.
    """

    def __init__(
        self,
        minutes: dict[str, float] | None = None,
        review_minutes: dict[str, float] | None = None,
    ):
        self.minutes = dict(minutes or {})
        self.review_minutes = dict(review_minutes or {})

    def get(self, workflow_id: str) -> float | None:
        return self.minutes.get(workflow_id)

    def review(self, workflow_id: str) -> float | None:
        return self.review_minutes.get(workflow_id)

    @classmethod
    def load(cls, path: str | Path) -> "Baselines":
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        if "manual" in data or "review" in data:
            return cls(data.get("manual"), data.get("review"))
        # An older file is a flat mapping of manual minutes only.
        return cls(data)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"manual": self.minutes, "review": self.review_minutes},
                       indent=2) + "\n",
            encoding="utf-8")
        return path


@dataclass
class WorkflowLine:
    workflow_id: str
    handled: int = 0
    verified: int = 0
    awaiting: int = 0
    stopped: int = 0
    needs_cleanup: int = 0
    approved: int = 0
    rejected: int = 0
    baseline_minutes: float | None = None

    @property
    def minutes_returned(self) -> float | None:
        """Only on work that finished.

        An item still waiting for approval saved the retrieval, but the review
        it is waiting for is new cost. Counting it as fully returned would
        overstate exactly the number §1.10 is judged on.
        """
        if self.baseline_minutes is None:
            return None
        return self.verified * self.baseline_minutes


@dataclass
class HealthReport:
    since: str = ""
    until: str = ""
    lines: dict[str, WorkflowLine] = field(default_factory=dict)
    stops: Counter = field(default_factory=Counter)
    exceptions: int = 0
    unapproved_writes: int = 0
    missing_baselines: list[str] = field(default_factory=list)

    @property
    def handled(self) -> int:
        return sum(line.handled for line in self.lines.values())

    @property
    def hours_returned(self) -> float | None:
        measured = [line.minutes_returned for line in self.lines.values()
                    if line.minutes_returned is not None]
        return round(sum(measured) / 60, 1) if measured else None

    def summary(self) -> str:
        lines = [
            f"Agent activity, {self.since[:10]} to {self.until[:10]}",
            f"  {self.handled} tasks handled",
        ]
        if self.hours_returned is not None:
            lines.append(
                f"  {self.hours_returned} hours returned (finished work only; "
                "items still awaiting review are not counted)")
        if self.missing_baselines:
            lines.append(
                "  time returned NOT measurable for: "
                + ", ".join(workflow_name(w) for w in sorted(self.missing_baselines))
            )
            lines.append(
                "    Nobody has timed these by hand, so there is no 'before' to "
                "subtract from. Time one of each with a stopwatch."
            )
        lines.append("")

        for workflow_id, line in sorted(self.lines.items()):
            bits = [f"{line.verified} done"]
            if line.awaiting:
                bits.append(f"{line.awaiting} waiting")
            if line.stopped:
                bits.append(f"{line.stopped} stopped")
            if line.needs_cleanup:
                bits.append(f"{line.needs_cleanup} NEEDS CLEANUP")
            if line.rejected:
                bits.append(f"{line.rejected} rejected")
            lines.append(f"  {workflow_name(workflow_id):28} {', '.join(bits)}")

        if self.exceptions:
            lines += ["", f"  {self.exceptions} exception(s) raised for a person to resolve"]
        if self.stops:
            lines += ["", "  Why it stopped:"]
            for reason, count in self.stops.most_common():
                lines.append(f"    {count:3}  {reason.replace('_', ' ')}")

        lines += ["", (
            "  Unapproved writes: 0."
            if not self.unapproved_writes else
            f"  UNAPPROVED WRITES: {self.unapproved_writes}. Investigate before anything else."
        )]
        return "\n".join(lines)


def build(log: LogStore, baselines: Baselines | None = None, *, days: int = 7,
          now: datetime | None = None) -> HealthReport:
    baselines = baselines or Baselines()
    now = now or datetime.now().astimezone()
    since = (now - timedelta(days=days)).isoformat(timespec="seconds")
    report = HealthReport(since=since, until=now.isoformat(timespec="seconds"))

    for receipt in log.query(since=since):
        if receipt.action_type in (APPROVE, REJECT):
            line = report.lines.setdefault(
                receipt.workflow_id, WorkflowLine(receipt.workflow_id))
            if receipt.action_type == APPROVE:
                line.approved += 1
            else:
                line.rejected += 1
            continue

        line = report.lines.setdefault(
            receipt.workflow_id, WorkflowLine(receipt.workflow_id))
        line.handled += 1
        if receipt.outcome == VERIFIED:
            line.verified += 1
        elif receipt.outcome == PENDING_APPROVAL:
            line.awaiting += 1
            if receipt.action_type == PROPOSE and not receipt.after_state:
                report.exceptions += 1
        elif receipt.outcome == STOPPED_CLEANUP_REQUIRED:
            line.needs_cleanup += 1
        elif receipt.outcome == STOPPED_NO_CHANGE:
            line.stopped += 1

        if receipt.stop_reason:
            report.stops[receipt.stop_reason] += 1
        if (receipt.action_type == WRITE and not receipt.auto_executed
                and not receipt.references_receipt_id):
            report.unapproved_writes += 1

    for workflow_id, line in report.lines.items():
        line.baseline_minutes = baselines.get(workflow_id)
        # Flagged whenever the workflow ran at all, not only when it finished.
        # Otherwise a week of work still waiting for review reports nothing
        # about time and says nothing about why.
        if line.baseline_minutes is None and line.handled:
            report.missing_baselines.append(workflow_id)
    return report
