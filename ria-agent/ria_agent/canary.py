"""Portal drift canary (F-16, and OPEN_FINDINGS.md #13).

The plan's canary alerts on a change in path length. A goal-directed navigator
has naturally variable path length, so that canary would be noisy, its threshold
would be raised, and it would then detect nothing. It measures the wrong thing.

What is stable is *where* the agent goes and *what it comes back with*: the set
of pages visited, their shapes, and an artifact that still passes its checks. A
redesign that renames every control but keeps the same structure is not drift
worth waking anyone for -- and correctly does not fire here. A redesign that
routes the agent somewhere new does fire, whether the path got longer or shorter.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .navigator import RetrievalGoal
from .receipts import now_iso
from .retrieval import Retrieval


@dataclass
class Baseline:
    custodian: str
    account: str
    period: str
    paths: set[str] = field(default_factory=set)
    signatures: set[str] = field(default_factory=set)
    recorded_at: str = ""

    def to_dict(self) -> dict:
        return {
            "custodian": self.custodian, "account": self.account,
            "period": self.period, "paths": sorted(self.paths),
            "signatures": sorted(self.signatures), "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        return cls(
            custodian=data["custodian"], account=data["account"],
            period=data["period"], paths=set(data.get("paths", ())),
            signatures=set(data.get("signatures", ())),
            recorded_at=data.get("recorded_at", ""),
        )


@dataclass
class CanaryResult:
    custodian: str
    drifted: bool
    changes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if not self.drifted:
            return f"{self.custodian}: unchanged."
        return f"{self.custodian} has drifted:\n  " + "\n  ".join(self.changes)


def observe(retrieval: Retrieval, custodian: str, goal: RetrievalGoal) -> Baseline:
    paths = {
        urlparse(url).path
        for url in (retrieval.navigation.pages_visited if retrieval.navigation else [])
    }
    signatures = {
        step.signature for step in (retrieval.navigation.steps if retrieval.navigation else [])
    }
    return Baseline(custodian, goal.account, goal.period, paths, signatures, now_iso())


class Canary:
    """A known account, retrieved on a schedule, compared to what it did before."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._baselines: dict[str, Baseline] = {}
        if self.path.exists():
            for custodian, data in json.loads(
                self.path.read_text(encoding="utf-8")
            ).items():
                self._baselines[custodian] = Baseline.from_dict(data)

    def baseline_for(self, custodian: str) -> Baseline | None:
        return self._baselines.get(custodian)

    def record(self, baseline: Baseline) -> Baseline:
        self._baselines[baseline.custodian] = baseline
        self.path.write_text(
            json.dumps(
                {name: b.to_dict() for name, b in self._baselines.items()}, indent=2
            ) + "\n",
            encoding="utf-8",
        )
        return baseline

    def check(self, retrieval: Retrieval, custodian: str, goal: RetrievalGoal) -> CanaryResult:
        """Compare a canary run against the recorded baseline."""
        current = observe(retrieval, custodian, goal)
        baseline = self._baselines.get(custodian)
        if baseline is None:
            self.record(current)
            return CanaryResult(custodian, False, ["no baseline yet; recorded this run"])

        changes: list[str] = []
        if not retrieval.succeeded:
            changes.append(
                f"the canary retrieval stopped: {retrieval.receipt.stop_reason}")
        if retrieval.verification is not None and not retrieval.verification.passed:
            changes.append(f"the artifact failed its checks: {retrieval.verification.summary()}")

        new_paths = current.paths - baseline.paths
        gone_paths = baseline.paths - current.paths
        if new_paths:
            changes.append(f"pages the agent had never visited before: {sorted(new_paths)}")
        if gone_paths:
            changes.append(f"pages it no longer visits: {sorted(gone_paths)}")

        # Page shapes are reported, not alarmed on by themselves: a cosmetic
        # relabelling changes every signature and breaks nothing.
        if current.signatures != baseline.signatures and not (new_paths or gone_paths):
            changes.append(
                "the same pages have a different shape (controls renamed or "
                "rearranged). The retrieval still worked, so this is a note, "
                "not a failure."
            )
        drifted = bool(new_paths or gone_paths) or not retrieval.succeeded
        return CanaryResult(custodian, drifted, changes)
