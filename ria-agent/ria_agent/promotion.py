"""Promotion and demotion (Step 30's mechanism, and OPEN_FINDINGS.md #2 and #9).

The plan promotes a workflow to auto-execute when approval-without-edit passes
95% over 200 filings. That gate cannot work as written, because approval fatigue
and high accuracy produce the same number: people approving without editing.
F-35 calls approval fatigue the most likely failure of the whole system, and the
gate as specified fires on it.

So promotion needs a second, independent signal that the reviewer is actually
reading: the measured catch rate on seeded errors. A workflow whose approval
rate is 99% and whose catch rate is 20% is not trusted, it is unread.

Read-only workflows are gated differently again (#9). There is nothing to edit
on a retrieval, so approval-without-edit is 100% from the first item and means
nothing. What matters there is whether the artifact passed its checks.

Promotion is per workflow, per role, and reversible. One incorrect
auto-execution demotes immediately.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import workflows
from .log_store import LogStore
from .receipts import APPROVE, REJECT, VERIFIED, now_iso
from .seeded_errors import SeedRegistry

PROMOTED = "promoted"
DEMOTED = "demoted"


@dataclass(frozen=True)
class Criteria:
    """What a workflow must show before it runs without a person."""

    #: Writes: the plan's own gate.
    min_decisions: int = 200
    min_approval_rate: float = 0.95

    #: Writes: the gate the plan is missing. Without this, the one above is
    #: satisfied by nobody reading.
    min_catch_rate: float = 0.80
    min_catch_samples: int = 20

    #: Read-only: Step 24's fifty consecutive clean runs.
    min_verified_runs: int = 50
    min_verification_rate: float = 1.0


DEFAULT_CRITERIA = Criteria()


@dataclass
class Evidence:
    """The numbers a decision was made on."""

    decisions: int = 0
    approvals: int = 0
    rejections: int = 0
    verified_runs: int = 0
    failed_runs: int = 0
    catch_caught: int = 0
    catch_decided: int = 0

    @property
    def approval_rate(self) -> float | None:
        return self.approvals / self.decisions if self.decisions else None

    @property
    def verification_rate(self) -> float | None:
        total = self.verified_runs + self.failed_runs
        return self.verified_runs / total if total else None

    @property
    def catch_rate(self) -> float | None:
        return self.catch_caught / self.catch_decided if self.catch_decided else None


@dataclass
class Decision:
    promote: bool
    reasons: list[str] = field(default_factory=list)
    evidence: Evidence = field(default_factory=Evidence)

    def explain(self) -> str:
        verdict = "may auto-execute" if self.promote else "stays approval-gated"
        return f"{verdict}: " + "; ".join(self.reasons)


def gather(
    log: LogStore, seeds: SeedRegistry | None, workflow_id: str, role_id: str
) -> Evidence:
    """Read the numbers out of the log rather than trusting a counter."""
    evidence = Evidence()
    decided_ids = set()

    for receipt in log.query(workflow_id=workflow_id):
        if receipt.role != role_id:
            continue
        if receipt.action_type in (APPROVE, REJECT):
            decided_ids.add(receipt.references_receipt_id)
            evidence.decisions += 1
            if receipt.action_type == APPROVE:
                evidence.approvals += 1
            else:
                evidence.rejections += 1
        elif receipt.step_id.startswith("retrieve"):
            if receipt.outcome == VERIFIED or receipt.outcome == "pending_approval":
                evidence.verified_runs += 1
            else:
                evidence.failed_runs += 1

    if seeds is not None:
        rate = seeds.catch_rate(workflow_id)
        evidence.catch_caught = rate.caught
        evidence.catch_decided = rate.decided
    return evidence


def decide(
    workflow_id: str, evidence: Evidence, criteria: Criteria = DEFAULT_CRITERIA
) -> Decision:
    """Should this workflow run without a person in front of it?"""
    workflow = workflows.get(workflow_id)
    if workflow is None:
        return Decision(False, [f"{workflow_id} is not a known workflow"], evidence)

    if workflow.read_only:
        return _decide_read_only(evidence, criteria)
    return _decide_write(evidence, criteria)


def _decide_read_only(evidence: Evidence, criteria: Criteria) -> Decision:
    reasons: list[str] = []
    rate = evidence.verification_rate

    if evidence.verified_runs < criteria.min_verified_runs:
        reasons.append(
            f"{evidence.verified_runs} verified runs, {criteria.min_verified_runs} needed"
        )
    if rate is None:
        reasons.append("no runs to judge")
    elif rate < criteria.min_verification_rate:
        reasons.append(
            f"verification passed on {rate:.0%} of runs, {criteria.min_verification_rate:.0%} needed"
        )

    if reasons:
        return Decision(False, reasons, evidence)
    return Decision(True, [
        f"{evidence.verified_runs} consecutive runs verified, none failed",
        "gated on artifacts passing their checks, not on approvals — there is "
        "nothing to edit on a read",
    ], evidence)


def _decide_write(evidence: Evidence, criteria: Criteria) -> Decision:
    reasons: list[str] = []

    if evidence.decisions < criteria.min_decisions:
        reasons.append(
            f"{evidence.decisions} decisions, {criteria.min_decisions} needed"
        )
    approval_rate = evidence.approval_rate
    if approval_rate is not None and approval_rate < criteria.min_approval_rate:
        reasons.append(
            f"approved without edit {approval_rate:.0%} of the time, "
            f"{criteria.min_approval_rate:.0%} needed"
        )

    # The condition the plan is missing.
    catch_rate = evidence.catch_rate
    if evidence.catch_decided < criteria.min_catch_samples:
        reasons.append(
            f"only {evidence.catch_decided} seeded errors have been decided, "
            f"{criteria.min_catch_samples} needed — without them a high approval "
            "rate is indistinguishable from nobody reading"
        )
    elif catch_rate is not None and catch_rate < criteria.min_catch_rate:
        reasons.append(
            f"reviewers caught {catch_rate:.0%} of seeded errors, "
            f"{criteria.min_catch_rate:.0%} needed — the approval rate here "
            "measures fatigue, not accuracy"
        )

    if reasons:
        return Decision(False, reasons, evidence)
    return Decision(True, [
        f"{evidence.decisions} decisions at {approval_rate:.0%} approved without edit",
        f"and reviewers caught {catch_rate:.0%} of seeded errors, so that "
        "approval rate reflects attention",
    ], evidence)


class PromotionRegistry:
    """Which workflows may auto-execute, per role. Append-only."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict[tuple[str, str], dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                self._state[(entry["workflow_id"], entry["role_id"])] = entry

    def _write(self, entry: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        self._state[(entry["workflow_id"], entry["role_id"])] = entry

    def is_promoted(self, workflow_id: str, role_id: str) -> bool:
        entry = self._state.get((workflow_id, role_id))
        return bool(entry) and entry["event"] == PROMOTED

    def promote(self, workflow_id: str, role_id: str, decision: Decision) -> dict:
        if not decision.promote:
            raise ValueError(
                f"refusing to promote {workflow_id}: {decision.explain()}"
            )
        entry = {"event": PROMOTED, "workflow_id": workflow_id, "role_id": role_id,
                 "reasons": decision.reasons, "at": now_iso()}
        self._write(entry)
        return entry

    def demote(self, workflow_id: str, role_id: str, reason: str) -> dict:
        """One incorrect auto-execution is enough. No threshold, no appeal."""
        entry = {"event": DEMOTED, "workflow_id": workflow_id, "role_id": role_id,
                 "reasons": [reason], "at": now_iso()}
        self._write(entry)
        return entry

    def promoted(self) -> list[tuple[str, str]]:
        return [key for key, entry in self._state.items() if entry["event"] == PROMOTED]

    def history(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
