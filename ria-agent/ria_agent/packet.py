"""Meeting prep packet (Step 43).

The compound workflow: retrieval, then reconciliation, then a linkage check,
then a document a person can read before walking into a meeting. Everything the
earlier phases built, chained.

What it is not: it contains no advice, no view on suitability, no performance
commentary. Constitution VIII. It says what was retrieved, what agrees, what
does not, and what nobody has checked. Deciding what any of that means is the
adviser's job and stays that way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .linkage import AccountRecord, LinkageReport, check as check_linkage
from .log_store import LogStore
from .navigator import RetrievalGoal
from .pdf import PdfDocument
from .receipts import (
    Evidence, FIELD_VALUES, PENDING_APPROVAL, PROPOSE, Receipt, now_iso,
)
from .reconcile import Balance, Comparison, Reconciliation

WORKFLOW_ID = "meeting_prep_packet"


@dataclass
class PacketRequest:
    crm_task_id: str
    household: str
    period: str
    accounts: list[str]
    balances: dict[str, list[Balance]] = field(default_factory=dict)
    linkage_records: list[AccountRecord] = field(default_factory=list)
    holder: str = ""


@dataclass
class Packet:
    request: PacketRequest
    retrieved: list[str] = field(default_factory=list)
    missing: list[tuple[str, str]] = field(default_factory=list)
    comparisons: list[Comparison] = field(default_factory=list)
    linkage: LinkageReport | None = None
    path: Path | None = None
    receipt: Receipt | None = None

    @property
    def exceptions(self) -> list[Comparison]:
        return [c for c in self.comparisons if c.needs_a_human]

    @property
    def complete(self) -> bool:
        return not self.missing and not self.exceptions and bool(
            self.linkage is None or self.linkage.clean)


class MeetingPrepPacket:
    """Assembles a packet. Sends nothing, decides nothing."""

    def __init__(
        self,
        retrieval,
        log: LogStore,
        *,
        operator: str,
        role: str,
        model_version: str,
        output_dir: Path,
    ):
        self.retrieval = retrieval
        self.log = log
        self.operator = operator
        self.role = role
        self.model_version = model_version
        self.output_dir = Path(output_dir)

    def build(self, request: PacketRequest) -> Packet:
        packet = Packet(request)
        started = now_iso()

        for account in request.accounts:
            outcome = self.retrieval.run(
                request.crm_task_id,
                RetrievalGoal(account, request.period, request.holder))
            if outcome.succeeded:
                packet.retrieved.append(account)
            else:
                packet.missing.append((account, outcome.receipt.stop_reason or "unknown"))

        reconciliation = Reconciliation(
            self.log, operator=self.operator, role=self.role,
            model_version=self.model_version)
        for account, balances in request.balances.items():
            packet.comparisons.extend(
                reconciliation.reconcile(request.crm_task_id, balances))

        if request.linkage_records:
            packet.linkage = check_linkage(request.linkage_records)

        packet.path = self._render(packet)
        packet.receipt = self._receipt(packet, started)
        return packet

    # -- the document ------------------------------------------------------

    def _render(self, packet: Packet) -> Path:
        request = packet.request
        doc = PdfDocument(footer=f"{request.household} — prep for {request.period}")
        doc.heading(f"{request.household}", size=19)
        doc.text(f"Meeting preparation, period {request.period}", size=11)
        doc.text(
            "Operational summary only. It contains no advice, no view on "
            "suitability, and no performance commentary.", size=9)
        doc.rule()

        doc.heading("Statements", size=13)
        for account in packet.retrieved:
            doc.text(f"retrieved   {account}   {request.period}", size=10, indent=8, space_after=1)
        for account, reason in packet.missing:
            doc.text(f"MISSING     {account}   {reason.replace('_', ' ')}",
                     size=10, bold=True, indent=8, space_after=1)
        if not packet.retrieved and not packet.missing:
            doc.text("Nothing was requested.", size=10, indent=8)
        doc.spacer(6)

        doc.heading("Balances", size=13)
        if not packet.comparisons:
            doc.text("No balances were compared.", size=10, indent=8)
        for comparison in packet.comparisons:
            doc.text(comparison.summary(), size=10, indent=8,
                     bold=comparison.needs_a_human, space_after=1)
            if comparison.needs_a_human:
                doc.text(comparison.proposed_resolution(), size=9, indent=20, space_after=3)
        doc.spacer(6)

        doc.heading("Account linkage", size=13)
        if packet.linkage is None:
            doc.text("Not checked.", size=10, indent=8)
        else:
            for line in packet.linkage.summary().splitlines():
                doc.text(line.strip(), size=10, indent=8, space_after=1)
        doc.spacer(6)

        doc.rule()
        doc.heading("What still needs a person", size=13)
        outstanding = (
            [f"{account}: statement not retrieved ({reason.replace('_', ' ')})"
             for account, reason in packet.missing]
            + [comparison.summary() for comparison in packet.exceptions]
            + [f"{f.account}: {f.detail}"
               for f in (packet.linkage.findings if packet.linkage else [])]
        )
        if not outstanding:
            doc.text("Nothing. Everything requested was retrieved, every balance "
                     "compared agreed, and every account is linked.", size=10, indent=8)
        for item in outstanding:
            doc.text(f"- {item}", size=10, indent=8, space_after=2)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        name = f"{request.household}-{request.period}-prep.pdf".replace(" ", "-")
        return doc.save(self.output_dir / name)

    def _receipt(self, packet: Packet, started: str) -> Receipt:
        request = packet.request
        receipt = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=request.crm_task_id,
            workflow_id=WORKFLOW_ID, step_id="assemble_packet",
            system_touched="custodian+redtail+orion", action_type=PROPOSE,
            target_identifier=f"{request.household} / {request.period}",
            outcome=PENDING_APPROVAL,
            before_state={"accounts requested": ", ".join(request.accounts)},
            after_state={"packet": str(packet.path)},
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version,
            evidence=[Evidence(FIELD_VALUES, {
                "retrieved": packet.retrieved,
                "missing": [f"{a} ({r})" for a, r in packet.missing],
                "balance_exceptions": [c.summary() for c in packet.exceptions],
                "linkage_problems": [f.detail for f in
                                     (packet.linkage.findings if packet.linkage else [])],
                "complete": packet.complete,
            }, source_location=str(packet.path))],
        )
        self.log.append(receipt)
        return receipt
