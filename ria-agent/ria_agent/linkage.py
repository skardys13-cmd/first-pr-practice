"""Account linkage (Step 36).

Checked separately from reconciliation, and worth running on its own.

A missing or wrong link is the commonest upstream cause of a break nobody can
explain: the balances differ because the two systems are not describing the same
account at all, and no amount of timing analysis will ever account for it. Found
here, it is a five-minute data fix. Found during a reconciliation, it is an hour
of looking for a phantom.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .matching import accounts_equal, normalise_account
from .reconcile import CUSTODIAN, SYSTEM_KINDS


@dataclass(frozen=True)
class AccountRecord:
    system: str
    account: str
    household: str

    @property
    def key(self) -> str:
        return normalise_account(self.account)


@dataclass(frozen=True)
class Finding:
    kind: str
    account: str
    detail: str
    resolution: str


NOT_LINKED = "not_linked"
ORPHAN = "orphan"
WRONG_HOUSEHOLD = "wrong_household"
DUPLICATE = "duplicate_in_one_system"


@dataclass
class LinkageReport:
    findings: list[Finding] = field(default_factory=list)
    accounts_checked: int = 0
    systems: tuple[str, ...] = ()

    @property
    def clean(self) -> bool:
        return not self.findings

    def of_kind(self, kind: str) -> list[Finding]:
        return [f for f in self.findings if f.kind == kind]

    def summary(self) -> str:
        if not self.accounts_checked:
            return "No accounts to check."
        if self.clean:
            return (f"All {self.accounts_checked} custodial accounts are linked "
                    f"correctly across {', '.join(self.systems)}.")
        lines = [
            f"{self.accounts_checked} accounts checked across "
            f"{', '.join(self.systems)}. {len(self.findings)} problem(s):",
        ]
        for finding in self.findings:
            lines.append(f"  {finding.account}: {finding.detail}")
            lines.append(f"    -> {finding.resolution}")
        return "\n".join(lines)


#: Systems this firm expects every custodial account to appear in. A system
#: that contributes no records at all is a finding, not silence: a book where
#: the CRM returned nothing would otherwise report "all linked correctly",
#: which is the most dangerous possible answer.
DEFAULT_EXPECTED = ("redtail",)


def check(
    records: list[AccountRecord],
    expected_systems: tuple[str, ...] = DEFAULT_EXPECTED,
) -> LinkageReport:
    """Is every custodial account linked correctly in every system?"""
    present = {record.system for record in records}
    systems = sorted(present | set(expected_systems))
    report = LinkageReport(systems=tuple(systems))

    for system in expected_systems:
        if system not in present and any(
            SYSTEM_KINDS.get(r.system.lower()) == CUSTODIAN for r in records
        ):
            report.findings.append(Finding(
                NOT_LINKED, f"(every account)",
                f"{system} returned no accounts at all",
                f"Check {system} is readable and actually holds these accounts. "
                "A system that returns nothing looks identical to a system where "
                "everything is linked, and it is the opposite.",
            ))

    by_system: dict[str, list[AccountRecord]] = {system: [] for system in systems}
    for system in systems:
        by_system.setdefault(system, [])
    for record in records:
        by_system[record.system].append(record)

    custodial = [
        record for record in records
        if SYSTEM_KINDS.get(record.system.lower()) == CUSTODIAN
    ]
    downstream = [system for system in systems
                  if SYSTEM_KINDS.get(system.lower()) != CUSTODIAN]

    seen: set[str] = set()
    for record in custodial:
        if record.key in seen:
            continue
        seen.add(record.key)
        report.accounts_checked += 1

        for system in downstream:
            matches = [other for other in by_system[system]
                       if accounts_equal(other.account, record.account)]
            if not matches:
                report.findings.append(Finding(
                    NOT_LINKED, record.account,
                    f"held at {record.system} but not linked in {system}",
                    f"Link {record.account} to the {record.household} household in "
                    f"{system}. Until then, anything comparing these two systems "
                    "for this account is meaningless.",
                ))
                continue
            if len(matches) > 1:
                report.findings.append(Finding(
                    DUPLICATE, record.account,
                    f"appears {len(matches)} times in {system}",
                    f"Remove the duplicate in {system}. Two records for one "
                    "account will disagree with each other eventually.",
                ))
            for other in matches:
                if other.household.strip().lower() != record.household.strip().lower():
                    report.findings.append(Finding(
                        WRONG_HOUSEHOLD, record.account,
                        f"{record.system} has it under {record.household}, "
                        f"{system} has it under {other.household}",
                        "One of these mappings is wrong. Confirm which household "
                        "owns this account before comparing any balance on it — a "
                        "wrong mapping produces a difference no timing analysis "
                        "will explain.",
                    ))

    custodial_keys = {record.key for record in custodial}
    for system in downstream:
        for record in by_system[system]:
            if record.key not in custodial_keys:
                report.findings.append(Finding(
                    ORPHAN, record.account,
                    f"exists in {system} but at no custodian this install can read",
                    f"Either the account is closed and should be archived in "
                    f"{system}, or it is held somewhere the agent cannot see. "
                    "Both need a person.",
                ))
    return report
