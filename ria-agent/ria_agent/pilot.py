"""Pilot scoring (Steps 49-50, against the plan's §1.10).

Four criteria. Two can be computed from the log; two cannot, and this refuses to
infer them.

Time saved is computed against a baseline someone timed by hand. Unapproved
writes are counted. But whether a stranger can read the log and understand what
happened is answered by handing it to a stranger, and whether the person prefers
using it is answered by asking them in week four. Both are recorded here as
someone's stated answer, with their name against it, or the pilot does not pass.

Marking a pilot passed on the two computable criteria alone would be exactly the
prototype-called-a-product the plan warns about.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .health import Baselines
from .log_store import LogStore
from .receipts import (
    APPROVE, PENDING_APPROVAL, REJECT, STOPPED_CLEANUP_REQUIRED, VERIFIED, WRITE,
)


@dataclass
class HumanAnswer:
    """A criterion only a person can answer, and who answered it."""

    question: str
    answered: bool | None = None
    answered_by: str = ""
    answered_on: str = ""
    note: str = ""

    @property
    def recorded(self) -> bool:
        return self.answered is not None and bool(self.answered_by)

    def to_dict(self) -> dict:
        return {"question": self.question, "answered": self.answered,
                "answered_by": self.answered_by, "answered_on": self.answered_on,
                "note": self.note}


@dataclass
class Criterion:
    name: str
    passed: bool | None
    detail: str

    @property
    def undecided(self) -> bool:
        return self.passed is None


@dataclass
class PilotResult:
    workflow_id: str
    person: str
    completed: int = 0
    unapproved_writes: int = 0
    receipts_without_evidence: int = 0
    invalid_receipts: int = 0
    needs_cleanup: int = 0
    baseline_minutes: float | None = None
    agent_minutes: float | None = None
    review_minutes: float | None = None
    criteria: list[Criterion] = field(default_factory=list)

    @property
    def end_to_end_minutes(self) -> float | None:
        """Agent time plus the review it created. F-38.

        The agent's step time alone always looks excellent, because the human
        half is where the time goes. If the person is doing the hard half by
        hand, the total will not move — and that is the number the pilot is
        judged on.
        """
        if self.agent_minutes is None or self.review_minutes is None:
            return None
        return self.agent_minutes + self.review_minutes

    @property
    def time_saved(self) -> float | None:
        total = self.end_to_end_minutes
        if self.baseline_minutes is None or total is None or not self.baseline_minutes:
            return None
        return 1 - (total / self.baseline_minutes)

    @property
    def passed(self) -> bool:
        return bool(self.criteria) and all(c.passed for c in self.criteria)

    def summary(self) -> str:
        lines = [
            f"Pilot: {self.workflow_id} for {self.person}",
            f"  {self.completed} completed run(s)",
            "",
        ]
        for criterion in self.criteria:
            mark = "PASS" if criterion.passed else ("....." if criterion.undecided else "FAIL")
            lines.append(f"  {mark:5} {criterion.name}")
            lines.append(f"        {criterion.detail}")
        lines.append("")
        if self.passed:
            lines.append("  All four criteria met.")
        elif any(c.undecided for c in self.criteria):
            lines.append(
                "  Not decided. The criteria marked ..... need a person to answer "
                "them; they are not computed and not assumed.")
        else:
            lines.append("  Not met. This is a prototype, not a product.")
        return "\n".join(lines)


def score(
    log: LogStore,
    *,
    workflow_id: str,
    person: str,
    baselines: Baselines,
    log_is_readable: HumanAnswer,
    person_prefers_it: HumanAnswer,
    since: str | None = None,
) -> PilotResult:
    result = PilotResult(workflow_id=workflow_id, person=person)
    receipts = [
        receipt for receipt in log.query(workflow_id=workflow_id, since=since)
        if receipt.human_owner == person
    ]

    durations: list[float] = []
    for receipt in receipts:
        if receipt.errors():
            result.invalid_receipts += 1
        if receipt.action_type in (APPROVE, REJECT):
            continue
        if receipt.outcome in (VERIFIED, PENDING_APPROVAL):
            result.completed += 1
            if not receipt.evidence:
                result.receipts_without_evidence += 1
            try:
                start = datetime.fromisoformat(receipt.timestamp_start)
                end = datetime.fromisoformat(receipt.timestamp_end)
                durations.append((end - start).total_seconds() / 60)
            except ValueError:
                pass
        if receipt.outcome == STOPPED_CLEANUP_REQUIRED:
            result.needs_cleanup += 1
        if (receipt.action_type == WRITE and not receipt.auto_executed
                and not receipt.references_receipt_id):
            result.unapproved_writes += 1

    result.baseline_minutes = baselines.get(workflow_id)
    result.review_minutes = baselines.review(workflow_id)
    result.agent_minutes = (sum(durations) / len(durations)) if durations else None

    result.criteria = [
        _time_criterion(result),
        Criterion(
            "Zero unapproved writes",
            result.unapproved_writes == 0,
            "no write happened without an approval in the log"
            if not result.unapproved_writes
            else f"{result.unapproved_writes} write(s) with no approval — stop the pilot",
        ),
        _evidence_criterion(result, log_is_readable),
        Criterion(
            "The person prefers using it, unprompted, in week four",
            person_prefers_it.answered if person_prefers_it.recorded else None,
            _answer_detail(person_prefers_it),
        ),
    ]
    return result


NAME = "End-to-end time drops by at least 50%"


def _time_criterion(result: PilotResult) -> Criterion:
    if result.baseline_minutes is None:
        return Criterion(NAME, None, (
            "no manual baseline was recorded, so there is nothing to compare "
            "against. Time the workflow by hand before claiming anything."))
    if result.agent_minutes is None:
        return Criterion(NAME, None, "no completed runs to measure")
    if result.review_minutes is None:
        return Criterion(NAME, None, (
            f"the agent's own step time averages {result.agent_minutes:.1f} min, "
            "which is not the number that matters. Nobody has timed how long "
            "reviewing its output takes, and without that the end-to-end total "
            "is unknown. Agent step time always looks excellent (F-38)."))
    saved = result.time_saved
    total = result.end_to_end_minutes
    return Criterion(
        NAME,
        saved is not None and saved >= 0.5,
        f"{total:.1f} min end to end ({result.agent_minutes:.1f} agent + "
        f"{result.review_minutes:.1f} review) against a "
        f"{result.baseline_minutes:.1f} min manual baseline — {saved:.0%} faster",
    )


def _evidence_criterion(result: PilotResult, readable: HumanAnswer) -> Criterion:
    if result.receipts_without_evidence or result.invalid_receipts:
        return Criterion(
            "Every action has a receipt a stranger can read", False,
            f"{result.receipts_without_evidence} receipt(s) with no evidence, "
            f"{result.invalid_receipts} invalid",
        )
    if not readable.recorded:
        return Criterion(
            "Every action has a receipt a stranger can read", None,
            "every receipt carries evidence, but nobody unfamiliar with the "
            "system has been handed the export and asked what happened",
        )
    return Criterion(
        "Every action has a receipt a stranger can read",
        readable.answered,
        _answer_detail(readable),
    )


def _answer_detail(answer: HumanAnswer) -> str:
    if not answer.recorded:
        return f"not answered. {answer.question}"
    verdict = "yes" if answer.answered else "no"
    detail = f"{verdict}, per {answer.answered_by} on {answer.answered_on or 'an unrecorded date'}"
    return f"{detail}. {answer.note}" if answer.note else detail


def load_answers(path: str | Path) -> dict[str, HumanAnswer]:
    """Answers a person recorded, kept in a file rather than inferred."""
    path = Path(path)
    defaults = {
        "log_is_readable": HumanAnswer(
            "Hand the week's PDF export to someone who has never seen the system. "
            "Could they tell you what happened?"),
        "person_prefers_it": HumanAnswer(
            "In week four, does the person prefer using it to not using it, "
            "unprompted?"),
    }
    if not path.exists():
        return defaults
    stored = json.loads(path.read_text(encoding="utf-8"))
    for key, answer in defaults.items():
        if key in stored:
            defaults[key] = HumanAnswer(**{**answer.to_dict(), **stored[key]})
    return defaults


def save_answers(path: str | Path, answers: dict[str, HumanAnswer]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({k: v.to_dict() for k, v in answers.items()}, indent=2) + "\n",
        encoding="utf-8")
    return path
