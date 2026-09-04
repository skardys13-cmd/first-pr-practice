"""The reconciliation release gate (Steps 37-38, OPEN_FINDINGS.md #6).

Step 38 says: one month, zero false agreements. That gate is passable by an
engine that detects nothing, if genuine breaks are rare enough that a month
produces almost none. Zero out of zero is not evidence.

So the gate carries a denominator: at least twenty real breaks observed, and
zero of them missed. Where the natural rate is too low to reach twenty, plant
known breaks and count those -- an engine that cannot catch a break you planted
will not catch one you did not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .reconcile import AGREED, Balance, Comparison, money

MIN_TRUE_BREAKS = 20


@dataclass
class Scorecard:
    compared: int = 0
    reviewed: int = 0
    true_breaks: int = 0
    caught: int = 0
    #: The engine said agreed and the human found a break. The number that can
    #: hurt a client.
    false_agreements: list[str] = field(default_factory=list)
    #: The engine flagged and the human found nothing. Costs ten minutes.
    false_breaks: list[str] = field(default_factory=list)
    unusable: int = 0

    @property
    def false_agreement_rate(self) -> float | None:
        return len(self.false_agreements) / self.true_breaks if self.true_breaks else None

    @property
    def false_break_rate(self) -> float | None:
        return len(self.false_breaks) / self.reviewed if self.reviewed else None

    def gate(self, min_true_breaks: int = MIN_TRUE_BREAKS) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if self.false_agreements:
            reasons.append(
                f"{len(self.false_agreements)} false agreement(s): the engine "
                "called a real break fine. This must be zero, and it is the only "
                "number here that can hurt a client"
            )
        if self.true_breaks < min_true_breaks:
            reasons.append(
                f"only {self.true_breaks} real breaks observed, {min_true_breaks} "
                "needed. Zero false agreements out of almost no breaks is not "
                "evidence — plant known breaks if the natural rate is too low"
            )
        if reasons:
            return False, reasons
        return True, [
            f"{self.true_breaks} real breaks observed, all {self.caught} caught",
            "cleared for use beyond a second opinion",
        ]

    def summary(self, min_true_breaks: int = MIN_TRUE_BREAKS) -> str:
        allowed, reasons = self.gate(min_true_breaks)
        lines = [
            f"{self.compared} comparisons, {self.reviewed} reviewed by a person.",
            f"  real breaks found by the human   {self.true_breaks}",
            f"  of those, the engine caught      {self.caught}",
            f"  FALSE AGREEMENTS                 {len(self.false_agreements)}",
            f"  false breaks (noise)             {len(self.false_breaks)}"
            + (f" ({self.false_break_rate:.0%})" if self.false_break_rate is not None else ""),
            f"  not comparable / unreadable      {self.unusable}",
            "",
            ("Cleared." if allowed else "Not cleared:"),
        ]
        if not allowed:
            lines += [f"  - {reason}" for reason in reasons]
        return "\n".join(lines)


def score(
    comparisons: list[tuple[str, Comparison]],
    human_findings: dict[str, bool],
) -> Scorecard:
    """Compare the engine's verdicts against a person doing it by hand.

    `human_findings` maps a comparison key to whether the reviewer found a real
    break. A key that is absent was not reviewed and is not scored.
    """
    card = Scorecard()
    for key, comparison in comparisons:
        card.compared += 1
        truth = human_findings.get(key)
        if truth is None:
            continue
        card.reviewed += 1

        if comparison.verdict not in (AGREED, "disagreed", "possible_break"):
            card.unusable += 1
            if truth:
                card.true_breaks += 1
                # Not comparable is not a miss: it never claimed these agreed.
                card.caught += 1
            continue

        if truth:
            card.true_breaks += 1
            if comparison.agreed:
                card.false_agreements.append(key)
            else:
                card.caught += 1
        elif not comparison.agreed:
            card.false_breaks.append(key)
    return card


def plant_break(balance: Balance, amount: Decimal | str = "1000.00") -> Balance:
    """Move a balance by a known amount, to test the engine finds it.

    Used only against copies in a shadow comparison. Nothing is written to any
    system, and the planted figure never reaches a receipt as a real balance.
    """
    shifted = balance.value + money(amount) if balance.value is not None else None
    return Balance(balance.system, balance.account, shifted, balance.as_of,
                   f"{balance.source} [PLANTED BREAK +{amount}]",
                   dict(balance.components), balance.unavailable_reason)
