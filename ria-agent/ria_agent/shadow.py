"""Shadow mode and its report (Steps 15-16).

The classifier runs against real tasks and takes no action at all. It cannot:
the runner holds a read-only CRM reader and a classifier, and nothing that
touches a custodian or a browser. Everything it produces is a receipt.

Step 16's question is not "how accurate is it". It is **how often is it
confidently wrong**, because that is the number that executes the wrong
workflow against a real client. Two departures from the plan as written, both
recorded in OPEN_FINDINGS.md:

- Reported per task template as well as in aggregate (#7). A 2% aggregate
  permits one template to be wrong every single time.
- Scored on the resolved plan, not only the workflow label (#8). A perfectly
  classified retrieval pointed at the wrong account is the failure that matters.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .classifier import CONFIDENCE_FLOOR, Classifier
from .crm import CrmReader, CrmTask
from .log_store import LogStore
from .normalizer import Intent, normalise
from .receipts import EXTRACTED_VALUE, Evidence, FIELD_VALUES, READ, Receipt, VERIFIED, now_iso
from .workflows import UNRECOGNISED

SHADOW_WORKFLOW = "task_classification"


@dataclass(frozen=True)
class Observation:
    """One classification, taken no further."""

    task_id: str
    template: str
    workflow: str
    confidence: float
    basis: str
    plan: dict
    receipt_id: str

    @property
    def recognised(self) -> bool:
        return self.workflow != UNRECOGNISED

    @property
    def confident(self) -> bool:
        return self.confidence >= CONFIDENCE_FLOOR


class ShadowRunner:
    """Classifies real tasks and writes receipts. Acts on nothing."""

    def __init__(
        self,
        crm: CrmReader,
        classifier: Classifier,
        log: LogStore,
        *,
        operator: str,
        role: str,
        model_version: str,
    ):
        self.crm = crm
        self.classifier = classifier
        self.log = log
        self.operator = operator
        self.role = role
        self.model_version = model_version

    def observe(self, task: CrmTask, today: date | None = None) -> Observation:
        started = now_iso()
        verdict = self.classifier.classify(task)
        intent = normalise(task, verdict, today)
        receipt = self._receipt(task, intent, started)
        self.log.append(receipt)
        return Observation(
            task_id=task.task_id,
            template=task.template or f"(no template: {task.category or 'uncategorised'})",
            workflow=intent.workflow_guess,
            confidence=intent.confidence,
            basis=intent.basis,
            plan=intent.resolved_plan(),
            receipt_id=receipt.receipt_id,
        )

    def run(self, owner: str | None = None, today: date | None = None) -> list[Observation]:
        return [self.observe(task, today) for task in self.crm.open_tasks(owner)]

    def _receipt(self, task: CrmTask, intent: Intent, started: str) -> Receipt:
        plan = intent.resolved_plan()
        evidence = [
            Evidence(FIELD_VALUES, plan, source_location=f"{self.crm.name}:task/{task.task_id}"),
            Evidence(EXTRACTED_VALUE, intent.workflow_guess,
                     source_location=f"classifier:{intent.basis}"),
        ]
        for name, entity in sorted(intent.entities.items()):
            evidence.append(Evidence(EXTRACTED_VALUE, f"{name}={entity.value}",
                                     source_location=entity.source))
        if intent.injection_flags:
            evidence.append(Evidence(
                FIELD_VALUES, f"instruction-shaped text ignored: {intent.injection_flags}",
                source_location=f"{self.crm.name}:task/{task.task_id}"))
        return Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=task.task_id,
            workflow_id=SHADOW_WORKFLOW, step_id="classify_task",
            system_touched=self.crm.name, action_type=READ,
            target_identifier=task.task_id, outcome=VERIFIED,
            timestamp_start=started, timestamp_end=now_iso(),
            confidence=intent.confidence, model_version=self.model_version,
            evidence=evidence,
        )


def observations_from_log(log: LogStore) -> list[Observation]:
    """Rebuild observations from receipts.

    Step 16's review happens days or weeks after the run, in a different
    process. The log is the record, so the report reads it rather than needing
    the shadow run to still be in memory.
    """
    out: list[Observation] = []
    for receipt in log.query(workflow_id=SHADOW_WORKFLOW):
        plan = next(
            (e.value for e in receipt.evidence if isinstance(e.value, dict)), None
        )
        if plan is None:
            continue
        out.append(Observation(
            task_id=receipt.crm_task_id,
            template=plan.get("template") or _template_of(receipt),
            workflow=plan.get("workflow", UNRECOGNISED),
            confidence=receipt.confidence or 0.0,
            basis=plan.get("basis", ""),
            plan=plan,
            receipt_id=receipt.receipt_id,
        ))
    return out


def _template_of(receipt: Receipt) -> str:
    for piece in receipt.evidence:
        if piece.kind == EXTRACTED_VALUE and piece.source_location.startswith("classifier:"):
            return f"(basis: {piece.source_location.split(':', 1)[1]})"
    return "(unknown template)"


# --- Scoring ---------------------------------------------------------------


@dataclass
class Stats:
    """Counts for one template, or for everything."""

    total: int = 0
    labelled: int = 0
    correct: int = 0
    unrecognised: int = 0
    confidently_wrong: int = 0
    quietly_wrong: int = 0
    resolution_wrong: int = 0

    def _share(self, count: int) -> float | None:
        return count / self.labelled if self.labelled else None

    @property
    def correct_rate(self) -> float | None:
        return self._share(self.correct)

    @property
    def unrecognised_rate(self) -> float | None:
        return self._share(self.unrecognised)

    @property
    def confidently_wrong_rate(self) -> float | None:
        """The only number that matters (Step 16)."""
        return self._share(self.confidently_wrong)

    @property
    def resolution_wrong_rate(self) -> float | None:
        return self._share(self.resolution_wrong)


@dataclass
class ShadowReport:
    by_template: dict[str, Stats] = field(default_factory=dict)
    totals: Stats = field(default_factory=Stats)
    unlabelled: list[str] = field(default_factory=list)

    def clean_templates(self, *, min_samples: int = 20) -> set[str]:
        """Templates fit to be whitelisted.

        Zero confidently wrong and zero misresolved, over enough samples to mean
        something. Not "below 2%" -- per template, the tolerance is zero, and an
        aggregate threshold is what lets a broken template hide (#7).
        """
        return {
            template for template, stats in self.by_template.items()
            if stats.labelled >= min_samples
            and stats.confidently_wrong == 0
            and stats.resolution_wrong == 0
            and stats.correct > 0
        }

    def summary(self) -> str:
        lines = [
            f"{self.totals.total} classifications, {self.totals.labelled} reviewed.",
        ]
        if not self.totals.labelled:
            lines.append("Nothing has been labelled yet, so nothing can be concluded.")
            return "\n".join(lines)
        lines += [
            f"  correct              {self.totals.correct_rate:.1%}",
            f"  unrecognised         {self.totals.unrecognised_rate:.1%}  (a success state)",
            f"  CONFIDENTLY WRONG    {self.totals.confidently_wrong_rate:.1%}  <- the number that matters",
            f"  wrong but unsure     {self.totals.quietly_wrong} of {self.totals.labelled}",
            f"  right workflow,",
            f"    wrong account/period {self.totals.resolution_wrong_rate:.1%}",
            "",
            "Per template:",
        ]
        for template, stats in sorted(self.by_template.items()):
            if not stats.labelled:
                continue
            flag = "  <-- not fit to whitelist" if (
                stats.confidently_wrong or stats.resolution_wrong) else ""
            lines.append(
                f"  {template[:44]:44} n={stats.labelled:3}  "
                f"correct={stats.correct_rate:5.0%}  "
                f"confidently wrong={stats.confidently_wrong_rate:5.0%}{flag}"
            )
        return "\n".join(lines)


def build_report(observations: list[Observation], labels: dict[str, dict]) -> ShadowReport:
    """Score observations against manually reviewed labels (Step 16).

    A label is `{"workflow": ..., "account": ..., "period": ...}`; the account
    and period are optional and only scored when present.
    """
    report = ShadowReport()
    grouped: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.template].append(observation)

    for template, group in grouped.items():
        stats = Stats(total=len(group))
        for observation in group:
            report.totals.total += 1
            label = labels.get(observation.task_id)
            if label is None:
                report.unlabelled.append(observation.task_id)
                continue

            stats.labelled += 1
            report.totals.labelled += 1
            truth = label.get("workflow")

            if not observation.recognised:
                stats.unrecognised += 1
                report.totals.unrecognised += 1
                continue

            if observation.workflow != truth:
                if observation.confident:
                    stats.confidently_wrong += 1
                    report.totals.confidently_wrong += 1
                else:
                    stats.quietly_wrong += 1
                    report.totals.quietly_wrong += 1
                continue

            stats.correct += 1
            report.totals.correct += 1
            if _misresolved(observation, label):
                stats.resolution_wrong += 1
                report.totals.resolution_wrong += 1

        report.by_template[template] = stats
    return report


def _misresolved(observation: Observation, label: dict) -> bool:
    """Right workflow, wrong target. Invisible to a classification-only score."""
    for key in ("account", "period"):
        expected = label.get(key)
        if expected is not None and observation.plan.get(key) != expected:
            return True
    return False
