"""Custodian profiles and the scaling cost (Steps 39-40).

Step 39: add a second custodian with no custodian-specific script. If it needs
one, the navigator is not general enough -- fix the navigator.

Step 40: measure how much per-custodian tuning each one takes. That number is
the scaling cost, and it is the honest answer to "will this work at another
firm". A profile that needs three adjustments is a warning; a profile that needs
none is the goal.

**What the number here currently means.** It is measured against fake portals
in four shapes. Zero tuning across four shapes we wrote ourselves is weak
evidence and should be read as "the navigator is not obviously
custodian-shaped", not as "adding a custodian is free". The number only becomes
real when it is measured against portals nobody here designed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

FLAT = "flat"
TABBED = "tabbed"
YEAR_FIRST = "year_first"
DASHBOARD_DIRECT = "dashboard_direct"


@dataclass(frozen=True)
class CustodianProfile:
    """One custodian, as this install knows it."""

    name: str
    domains: frozenset[str]
    #: The shape its portal takes, for the fake used in tests. A real profile
    #: does not need this: the navigator discovers the shape by looking.
    layout: str = FLAT
    #: Anything the general navigator could NOT work out for itself. Every
    #: entry here is a point of scaling cost, and each one wants a reason.
    adjustments: dict[str, str] = field(default_factory=dict)

    @property
    def tuning_cost(self) -> int:
        return len(self.adjustments)

    def allowed_domains(self) -> set[str]:
        return set(self.domains)


CUSTODIANS: dict[str, CustodianProfile] = {
    profile.name: profile for profile in [
        CustodianProfile("schwab", frozenset({"portal.schwab.example"}), FLAT),
        CustodianProfile("fidelity", frozenset({"portal.fidelity.example"}), TABBED),
        CustodianProfile("pershing", frozenset({"portal.pershing.example"}), YEAR_FIRST),
        CustodianProfile("altruist", frozenset({"portal.altruist.example"}), DASHBOARD_DIRECT),
        CustodianProfile("raymond_james", frozenset({"portal.rj.example"}), TABBED),
        CustodianProfile("lpl", frozenset({"portal.lpl.example"}), YEAR_FIRST),
        CustodianProfile("axos", frozenset({"portal.axos.example"}), FLAT),
    ]
}


def get(name: str) -> CustodianProfile | None:
    return CUSTODIANS.get(name.lower())


def all_allowed_domains() -> set[str]:
    domains: set[str] = set()
    for profile in CUSTODIANS.values():
        domains |= profile.allowed_domains()
    return domains


@dataclass
class TuningResult:
    custodian: str
    layout: str
    retrieved: bool
    verified: bool
    steps: int
    tuning_cost: int
    detail: str = ""


def measure(profile: CustodianProfile, *, period: str = "2026-08") -> TuningResult:
    """Run the one navigator against this custodian and see what it costs."""
    import tempfile

    from .browser import FakePortal, FakePortalConfig, Statement
    from .guardrails import Guardrails
    from .navigator import Navigator, RetrievalGoal, StatementRetrievalPolicy
    from .verification import verify_statement

    account, holder = "1234-5678", "Helen Barrow"
    statements = [Statement(account, f"2026-{month:02d}", holder) for month in range(1, 9)]
    host = next(iter(profile.domains))
    directory = Path(tempfile.mkdtemp())

    portal = FakePortal(statements, FakePortalConfig(host=host, layout=profile.layout))
    navigator = Navigator(portal, Guardrails(profile.allowed_domains()),
                          StatementRetrievalPolicy(), evidence_dir=directory)
    result = navigator.pursue(RetrievalGoal(account, period, holder),
                              destination=directory / "statement.pdf")

    verified = False
    if result.reached and result.artifact:
        verified = verify_statement(result.artifact, account=account, period=period,
                                    holder=holder).passed
    return TuningResult(
        profile.name, profile.layout, result.reached, verified,
        len(result.steps), profile.tuning_cost,
        result.detail or ("" if verified else "retrieved but failed verification"),
    )


def scaling_report() -> str:
    """Step 40's number, with the caveat it needs."""
    results = [measure(profile) for profile in CUSTODIANS.values()]
    total = sum(result.tuning_cost for result in results)
    working = sum(1 for result in results if result.verified)
    lines = [
        f"{len(results)} custodians, {len(set(r.layout for r in results))} portal shapes.",
        f"  retrieved and verified   {working}/{len(results)}",
        f"  total per-custodian tuning   {total}",
        "",
    ]
    for result in results:
        flag = "" if result.verified else f"  <-- {result.detail}"
        lines.append(
            f"  {result.custodian:15} {result.layout:17} steps={result.steps} "
            f"tuning={result.tuning_cost}{flag}"
        )
    lines += [
        "",
        "Measured against fake portals in shapes we wrote ourselves, so a total of",
        "zero is weak evidence. It says the navigator is not obviously",
        "custodian-shaped. It does not say adding a real custodian is free, and it",
        "will not until it is measured against a portal nobody here designed.",
    ]
    return "\n".join(lines)
