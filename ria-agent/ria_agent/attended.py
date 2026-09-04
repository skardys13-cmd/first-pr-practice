"""Attended runs and the unattended gate (Steps 23-24).

Fifty real retrievals with a human watching each one, every deviation logged.
Only after fifty consecutive clean runs may retrieval run unattended -- and even
then it lands in Ready for approval, never Done, until the workflow is promoted.

A deviation is anything other than "went where it was supposed to, came back
with the right artifact". A stop counts. A page nobody expected counts, even if
the run still succeeded, because that is the drift showing up before it breaks
anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from .navigator import RetrievalGoal
from .retrieval import Retrieval, StatementRetrieval

OFF_PATH = "off_path_navigation"
STOPPED = "stopped"
VERIFICATION = "verification_failed"
UNEXPECTED_PAGE = "unexpected_page_shape"


@dataclass(frozen=True)
class Deviation:
    run: int
    crm_task_id: str
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"run {self.run} ({self.crm_task_id}): {self.kind} — {self.detail}"


@dataclass
class AttendedReport:
    runs: int = 0
    succeeded: int = 0
    deviations: list[Deviation] = field(default_factory=list)
    consecutive_clean: int = 0
    best_streak: int = 0
    pages_seen: set[str] = field(default_factory=set)

    @property
    def off_path(self) -> list[Deviation]:
        return [d for d in self.deviations if d.kind == OFF_PATH]

    def gate(self, required: int = 50) -> tuple[bool, list[str]]:
        """May retrieval now run unattended?"""
        reasons: list[str] = []
        if self.consecutive_clean < required:
            reasons.append(
                f"{self.consecutive_clean} consecutive clean runs, {required} needed"
                + (f" (best streak so far {self.best_streak})"
                   if self.best_streak > self.consecutive_clean else "")
            )
        if self.off_path:
            reasons.append(
                f"{len(self.off_path)} run(s) navigated somewhere unexpected; "
                "that has to be zero"
            )
        if reasons:
            return False, reasons
        return True, [
            f"{self.consecutive_clean} consecutive verified retrievals, "
            "no off-path navigation",
            "unattended runs still land in Ready for approval until the "
            "workflow is promoted",
        ]

    def summary(self) -> str:
        allowed, reasons = self.gate()
        lines = [
            f"{self.runs} attended runs, {self.succeeded} verified, "
            f"{len(self.deviations)} deviation(s).",
            f"Longest clean streak: {self.best_streak}.",
            ("May run unattended." if allowed else "Not yet cleared: " + "; ".join(reasons)),
        ]
        if self.deviations:
            lines.append("")
            lines.append("Deviations:")
            lines += [f"  {deviation}" for deviation in self.deviations[:20]]
            if len(self.deviations) > 20:
                lines.append(f"  ... and {len(self.deviations) - 20} more")
        return "\n".join(lines)


def expected_paths(goal: RetrievalGoal) -> set[str]:
    """Where a statement retrieval is supposed to go, and nowhere else."""
    return {"/dashboard", f"/accounts/{goal.account}"}


class AttendedHarness:
    """Runs retrievals under supervision and records every deviation."""

    def __init__(self, retrieval: StatementRetrieval):
        self.retrieval = retrieval
        self.report = AttendedReport()

    def run(self, crm_task_id: str, goal: RetrievalGoal) -> Retrieval:
        index = self.report.runs + 1
        outcome = self.retrieval.run(crm_task_id, goal)
        self.report.runs = index

        deviations = self._deviations(index, crm_task_id, goal, outcome)
        self.report.deviations.extend(deviations)

        if outcome.succeeded:
            self.report.succeeded += 1
        if deviations:
            self.report.consecutive_clean = 0
        else:
            self.report.consecutive_clean += 1
            self.report.best_streak = max(
                self.report.best_streak, self.report.consecutive_clean)
        return outcome

    def run_batch(self, cases: list[tuple[str, RetrievalGoal]]) -> AttendedReport:
        for crm_task_id, goal in cases:
            self.run(crm_task_id, goal)
        return self.report

    def _deviations(self, index, crm_task_id, goal, outcome) -> list[Deviation]:
        found: list[Deviation] = []

        if outcome.receipt.stop_reason:
            kind = (VERIFICATION if outcome.receipt.stop_reason == "verification_failed"
                    else STOPPED)
            found.append(Deviation(
                index, crm_task_id, kind,
                f"{outcome.receipt.stop_reason}: {outcome.receipt.stop_next_step}"))

        allowed = expected_paths(goal)
        for url in (outcome.navigation.pages_visited if outcome.navigation else []):
            path = urlparse(url).path
            self.report.pages_seen.add(path)
            if path not in allowed:
                found.append(Deviation(
                    index, crm_task_id, OFF_PATH,
                    f"visited {path}, which is not part of this workflow"))
        return found
