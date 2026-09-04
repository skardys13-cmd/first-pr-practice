"""Client-service workflows (Step 42).

E-sign follow-up and document requests. Both read, both prepare, neither sends.

Constitution VIII: nothing goes to a client without a person approving it. A
drafted follow-up is a proposal in the queue like any other, and the queue's
approval means "send this", not "the agent already did".
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime

from .log_store import LogStore
from .receipts import (
    EXTRACTED_VALUE, Evidence, FIELD_VALUES, PENDING_APPROVAL, PROPOSE, READ,
    Receipt, STOPPED_NO_CHANGE, VERIFIED, now_iso,
)
from . import stops

ESIGN_WORKFLOW = "esign_chase"
REQUEST_WORKFLOW = "document_request"

SENT = "sent"
VIEWED = "viewed"
SIGNED = "signed"
DECLINED = "declined"
EXPIRED = "expired"


@dataclass(frozen=True)
class Envelope:
    envelope_id: str
    household: str
    recipient: str
    subject: str
    status: str
    sent_on: str
    last_reminder: str = ""

    def days_outstanding(self, today: date | None = None) -> int:
        today = today or date.today()
        try:
            sent = datetime.fromisoformat(self.sent_on).date()
        except ValueError:
            return 0
        return (today - sent).days

    @property
    def outstanding(self) -> bool:
        return self.status in (SENT, VIEWED)


class ESignReader(ABC):
    """Read-only access to the e-sign service. No send method, deliberately."""

    name = "esign"

    @abstractmethod
    def envelopes(self, household: str | None = None) -> list[Envelope]:
        """Every envelope, optionally for one household."""


class FixtureESign(ESignReader):
    def __init__(self, envelopes: list[Envelope]):
        self._envelopes = list(envelopes)

    def envelopes(self, household: str | None = None) -> list[Envelope]:
        return [e for e in self._envelopes
                if household is None or e.household == household]


class ESignChase:
    """Finds envelopes going stale and drafts the nudge. Sends nothing."""

    def __init__(
        self,
        reader: ESignReader,
        log: LogStore,
        *,
        operator: str,
        role: str,
        model_version: str,
        chase_after_days: int = 3,
    ):
        self.reader = reader
        self.log = log
        self.operator = operator
        self.role = role
        self.model_version = model_version
        self.chase_after_days = chase_after_days

    def run(self, crm_task_id: str, household: str | None = None,
            today: date | None = None) -> list[Receipt]:
        receipts = []
        for envelope in self.reader.envelopes(household):
            if not envelope.outstanding:
                continue
            days = envelope.days_outstanding(today)
            if days < self.chase_after_days:
                continue
            receipts.append(self._draft(crm_task_id, envelope, days))
        return receipts

    def _draft(self, crm_task_id: str, envelope: Envelope, days: int) -> Receipt:
        started = now_iso()
        draft = (
            f"Hello {envelope.recipient},\n\n"
            f"Following up on \"{envelope.subject}\", sent {days} days ago and "
            "not yet signed. If anything is unclear or the link has expired, "
            "reply and we will re-send it.\n\n"
            "Thank you."
        )
        receipt = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
            workflow_id=ESIGN_WORKFLOW, step_id="draft_follow_up",
            system_touched=self.reader.name, action_type=PROPOSE,
            target_identifier=f"{envelope.household} / {envelope.envelope_id}",
            outcome=PENDING_APPROVAL,
            before_state={"status": envelope.status,
                          "days outstanding": str(days),
                          "last reminder": envelope.last_reminder or "none"},
            after_state={"send to": envelope.recipient, "message": draft},
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version,
            evidence=[
                Evidence(EXTRACTED_VALUE, envelope.status,
                         source_location=f"{self.reader.name}:envelope/{envelope.envelope_id}"),
                Evidence(EXTRACTED_VALUE, f"sent {envelope.sent_on}",
                         source_location=f"{self.reader.name}:envelope/{envelope.envelope_id}"),
                Evidence(FIELD_VALUES, {"draft": draft}, source_location="agent draft"),
            ],
        )
        self.log.append(receipt)
        return receipt


@dataclass
class RequestResult:
    requested: int = 0
    retrieved: list[str] = field(default_factory=list)
    stopped: list[tuple[str, str]] = field(default_factory=list)
    receipts: list[Receipt] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return bool(self.requested) and len(self.retrieved) == self.requested


class DocumentRequest:
    """A client asked for a run of statements. Retrieve each, report the gaps."""

    def __init__(self, retrieval, log: LogStore, *, operator: str, role: str,
                 model_version: str):
        self.retrieval = retrieval
        self.log = log
        self.operator = operator
        self.role = role
        self.model_version = model_version

    def run(self, crm_task_id: str, account: str, periods: list[str],
            holder: str = "") -> RequestResult:
        from .navigator import RetrievalGoal

        result = RequestResult(requested=len(periods))
        for period in periods:
            outcome = self.retrieval.run(crm_task_id, RetrievalGoal(account, period, holder))
            result.receipts.append(outcome.receipt)
            if outcome.succeeded:
                result.retrieved.append(period)
            else:
                result.stopped.append((period, outcome.receipt.stop_reason or "unknown"))

        summary = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
            workflow_id=REQUEST_WORKFLOW, step_id="summarise_request",
            system_touched="custodian", action_type=READ,
            target_identifier=account,
            outcome=VERIFIED if result.complete else STOPPED_NO_CHANGE,
            stop_reason=None if result.complete else stops.MISSING_INFORMATION,
            stop_next_step=None if result.complete else (
                "Retrieve the missing periods by hand before sending anything to "
                "the client. A partial set is worse than none."),
            timestamp_start=now_iso(), timestamp_end=now_iso(),
            model_version=self.model_version,
            evidence=[Evidence(FIELD_VALUES, {
                "requested": periods, "retrieved": result.retrieved,
                "not retrieved": [f"{p} ({r})" for p, r in result.stopped],
            }, source_location=f"custodian:{account}")],
        )
        self.log.append(summary)
        result.receipts.append(summary)
        return result
