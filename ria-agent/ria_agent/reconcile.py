"""Balance reconciliation (Steps 31-35).

Implements RECONCILIATION.md and nothing beyond it. Read that first; the rules
are the substance and this is the transcription.

Three properties carry the whole thing:

1. As-of alignment is checked before tolerance. Mismatched instants produce
   "cannot compare", never "agreed" and never "disagreed" (F-24).
2. Where the engine is uncertain it reports a possible break. It never resolves
   uncertainty toward fine, because a false agreement hides a real break and a
   false break wastes ten minutes (F-25).
3. It never writes a correction. A disagreement becomes an exception carrying
   both values, both sources, both timestamps, a proposed cause and a proposed
   resolution. A human decides. Constitution III.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .log_store import LogStore
from .receipts import (
    EXTRACTED_VALUE, Evidence, FIELD_VALUES, PENDING_APPROVAL, PROPOSE, READ,
    Receipt, STOPPED_NO_CHANGE, VERIFIED, now_iso,
)
from . import stops

WORKFLOW_ID = "balance_reconciliation"

# --- Verdicts --------------------------------------------------------------

AGREED = "agreed"
DISAGREED = "disagreed"
POSSIBLE_BREAK = "possible_break"
CANNOT_COMPARE = "cannot_compare"
SOURCE_UNAVAILABLE = "source_unavailable"

#: Anything that is not an agreement needs a person.
NEEDS_A_HUMAN = frozenset({DISAGREED, POSSIBLE_BREAK, CANNOT_COMPARE, SOURCE_UNAVAILABLE})

# --- Systems ---------------------------------------------------------------

CACHED = "cached"        # stores what another system told it (the CRM)
CUSTODIAN = "custodian"  # the book of record
PRICING = "pricing"      # prices independently (analytics, performance)

SYSTEM_KINDS = {
    "redtail": CACHED,
    "schwab": CUSTODIAN, "fidelity": CUSTODIAN, "pershing": CUSTODIAN,
    "orion": PRICING, "nitrogen": PRICING,
}


@dataclass(frozen=True)
class Tolerance:
    """RECONCILIATION.md section 3.

    A percentage with no ceiling is a tolerance that grows exactly where the
    money is: 0.02% of $8m is $1,600, and $1,600 missing is not rounding. So the
    proportional allowance is clamped between a floor and a materiality cap.
    """

    floor: Decimal = Decimal("0.01")
    percent: Decimal | None = None
    cap: Decimal | None = None

    def limit(self, value: Decimal) -> Decimal:
        if self.percent is None:
            return self.floor
        proportional = (abs(value) * self.percent / Decimal(100)).quantize(Decimal("0.01"))
        allowed = max(self.floor, proportional)
        return min(allowed, self.cap) if self.cap is not None else allowed

    def describe(self) -> str:
        if self.percent is None:
            return f"${self.floor}"
        ceiling = f", capped at ${self.cap}" if self.cap is not None else ""
        return f"{self.percent}% (at least ${self.floor}{ceiling})"


EXACT = Tolerance(Decimal("0.01"))
PRICED = Tolerance(Decimal("0.01"), Decimal("0.02"), Decimal("250.00"))


def tolerance_for(left_system: str, right_system: str) -> Tolerance:
    kinds = {SYSTEM_KINDS.get(left_system.lower(), PRICING),
             SYSTEM_KINDS.get(right_system.lower(), PRICING)}
    # A cached figure stores what it was told, so nothing should differ but
    # rounding. Only two independently pricing systems get the percentage.
    return EXACT if CACHED in kinds else PRICED


# --- Balances --------------------------------------------------------------

PENDING_TRADES = "pending_trades"
UNSETTLED_CASH = "unsettled_cash"
ACCRUED_DIVIDENDS = "accrued_dividends"
ACCRUED_FEES = "accrued_fees"
SAME_DAY_ACTIVITY = "same_day_activity"

COMPONENT_NAMES = {
    PENDING_TRADES: "a pending trade",
    UNSETTLED_CASH: "unsettled cash",
    ACCRUED_DIVIDENDS: "a dividend in transit",
    ACCRUED_FEES: "a fee accrued in one system and not the other",
    SAME_DAY_ACTIVITY: "activity on the as-of date",
}


def money(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as failure:
        raise ValueError(f"{value!r} is not a balance") from failure


@dataclass(frozen=True)
class Balance:
    """One system's figure, and the instant it claims to describe."""

    system: str
    account: str
    value: Decimal | None
    as_of: str | None
    source: str
    components: dict = field(default_factory=dict)
    unavailable_reason: str = ""

    @property
    def available(self) -> bool:
        return self.value is not None and bool(self.as_of)

    def component(self, name: str) -> Decimal:
        raw = self.components.get(name)
        return money(raw) if raw is not None else Decimal("0")

    def as_of_instant(self) -> datetime | None:
        try:
            return datetime.fromisoformat(self.as_of) if self.as_of else None
        except ValueError:
            return None


@dataclass
class Comparison:
    """A verdict, never a bare number."""

    left: Balance
    right: Balance
    verdict: str
    difference: Decimal | None = None
    tolerance: Tolerance | None = None
    explanations: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def agreed(self) -> bool:
        return self.verdict == AGREED

    @property
    def needs_a_human(self) -> bool:
        return self.verdict in NEEDS_A_HUMAN

    def summary(self) -> str:
        left, right = self.left, self.right
        if self.verdict == AGREED:
            return (f"{left.system} and {right.system} agree on {left.account} "
                    f"(${left.value} vs ${right.value}, within {self.tolerance.describe()})")
        if self.verdict == DISAGREED:
            return (f"{left.system} says ${left.value} and {right.system} says "
                    f"${right.value} for {left.account} — a difference of "
                    f"${self.difference}")
        return f"{left.account}: {self.detail}"

    def proposed_resolution(self) -> str:
        if self.verdict == AGREED:
            return "Nothing to do."
        if self.verdict == CANNOT_COMPARE:
            return ("Pull both figures as of the same instant and compare again. "
                    "The agent will not compare across as-of times.")
        if self.verdict == SOURCE_UNAVAILABLE:
            return "Read the missing figure by hand, then compare."
        if self.explanations:
            return (f"Most likely {self.explanations[0]}. Confirm that, and if it "
                    "is right the difference should clear on its own. If it does "
                    "not, this is a real break.")
        return ("No known cause accounts for this difference. Check the account "
                "mapping in both systems first, then look for activity on the "
                "as-of date.")


def compare(
    left: Balance,
    right: Balance,
    *,
    tolerance: Tolerance | None = None,
    alignment_seconds: int = 0,
) -> Comparison:
    """Compare two balances under RECONCILIATION.md."""
    if not left.available or not right.available:
        missing = [b for b in (left, right) if not b.available]
        detail = "; ".join(
            f"{b.system} gave no {'timestamp' if b.value is not None else 'figure'}"
            + (f" ({b.unavailable_reason})" if b.unavailable_reason else "")
            for b in missing
        )
        return Comparison(left, right, SOURCE_UNAVAILABLE, detail=detail)

    # Section 2: alignment before tolerance, always.
    left_instant, right_instant = left.as_of_instant(), right.as_of_instant()
    if left_instant is None or right_instant is None:
        return Comparison(left, right, SOURCE_UNAVAILABLE,
                          detail="an as-of timestamp could not be read")
    drift = abs((left_instant - right_instant).total_seconds())
    if drift > alignment_seconds:
        return Comparison(
            left, right, CANNOT_COMPARE,
            detail=(f"{left.system} is as of {left.as_of} and {right.system} is as "
                    f"of {right.as_of}, {int(drift)}s apart. These were never "
                    "describing the same moment."),
        )

    tolerance = tolerance or tolerance_for(left.system, right.system)
    difference = (left.value - right.value).copy_abs()
    limit = tolerance.limit(max(abs(left.value), abs(right.value)))

    if difference <= limit:
        return Comparison(left, right, AGREED, difference, tolerance)

    explanations = explain(left, right, difference)
    return Comparison(left, right, DISAGREED, difference, tolerance, explanations)


def explain(left: Balance, right: Balance, difference: Decimal) -> list[str]:
    """Candidate causes for a difference already found (section 4).

    Never a reason to skip a comparison, and never a resolution. A component
    that exactly accounts for the gap is the likeliest story, not a verdict.
    """
    found: list[str] = []
    for name, phrase in COMPONENT_NAMES.items():
        gap = (left.component(name) - right.component(name)).copy_abs()
        if gap and gap == difference:
            found.append(f"{phrase} of ${gap}, present in one system and not the other")
    for name, phrase in COMPONENT_NAMES.items():
        gap = (left.component(name) - right.component(name)).copy_abs()
        if gap and gap != difference and gap <= difference:
            found.append(f"{phrase} of ${gap}, which explains part of the difference")
    return found


class Reconciliation:
    """Compares, receipts, and raises exceptions. Writes nothing, ever."""

    def __init__(
        self,
        log: LogStore,
        *,
        operator: str,
        role: str,
        model_version: str,
        alignment_seconds: int = 0,
    ):
        self.log = log
        self.operator = operator
        self.role = role
        self.model_version = model_version
        self.alignment_seconds = alignment_seconds

    def reconcile(self, crm_task_id: str, balances: list[Balance]) -> list[Comparison]:
        """Compare every pair of systems holding this account."""
        results: list[Comparison] = []
        for index, left in enumerate(balances):
            for right in balances[index + 1:]:
                comparison = compare(left, right,
                                     alignment_seconds=self.alignment_seconds)
                results.append(comparison)
                self._receipt(crm_task_id, comparison)
        return results

    def _receipt(self, crm_task_id: str, comparison: Comparison) -> Receipt:
        left, right = comparison.left, comparison.right
        evidence = [
            Evidence(EXTRACTED_VALUE, f"{left.system}={left.value} as of {left.as_of}",
                     source_location=left.source),
            Evidence(EXTRACTED_VALUE, f"{right.system}={right.value} as of {right.as_of}",
                     source_location=right.source),
            Evidence(FIELD_VALUES, {
                "verdict": comparison.verdict,
                "difference": str(comparison.difference) if comparison.difference is not None else None,
                "tolerance": comparison.tolerance.describe() if comparison.tolerance else None,
                "proposed_cause": comparison.explanations[0] if comparison.explanations else None,
                "proposed_resolution": comparison.proposed_resolution(),
            }, source_location="reconciliation"),
        ]
        started = now_iso()
        target = f"{left.account} ({left.system} vs {right.system})"

        if comparison.agreed:
            receipt = Receipt(
                human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
                workflow_id=WORKFLOW_ID, step_id="compare_balances",
                system_touched=f"{left.system}+{right.system}", action_type=READ,
                target_identifier=target, outcome=VERIFIED,
                timestamp_start=started, timestamp_end=now_iso(),
                model_version=self.model_version, evidence=evidence,
            )
        elif comparison.verdict in (CANNOT_COMPARE, SOURCE_UNAVAILABLE):
            reason = (stops.DATA_MISMATCH if comparison.verdict == CANNOT_COMPARE
                      else stops.PERMISSION_DENIED)
            receipt = Receipt(
                human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
                workflow_id=WORKFLOW_ID, step_id="compare_balances",
                system_touched=f"{left.system}+{right.system}", action_type=READ,
                target_identifier=target, outcome=STOPPED_NO_CHANGE,
                stop_reason=reason, stop_next_step=comparison.proposed_resolution(),
                timestamp_start=started, timestamp_end=now_iso(),
                model_version=self.model_version, evidence=evidence,
            )
        else:
            # An exception. A proposal with nothing to write: the executor
            # cannot apply it, and a human decides what to do.
            receipt = Receipt(
                human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
                workflow_id=WORKFLOW_ID, step_id="raise_exception",
                system_touched=f"{left.system}+{right.system}", action_type=PROPOSE,
                target_identifier=target, outcome=PENDING_APPROVAL,
                before_state={
                    f"{left.system} balance": str(left.value),
                    f"{left.system} as of": left.as_of,
                    f"{right.system} balance": str(right.value),
                    f"{right.system} as of": right.as_of,
                },
                after_state=None,
                timestamp_start=started, timestamp_end=now_iso(),
                model_version=self.model_version, evidence=evidence,
            )
        self.log.append(receipt)
        return receipt
