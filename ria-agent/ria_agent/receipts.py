"""Receipt schema and validator (Step 3).

Nothing in this system may act before it can prove what it did. The receipt is
that proof, and the validator here is what makes the proof mean something: a
receipt claiming success with no evidence is rejected, not stored.

Four outcomes, not three. The plan's original three lanes had nowhere to put
the genuinely dangerous case -- the agent stopped *after* something had already
changed. A stop before any change needs a retry; a stop after a partial change
needs cleanup. Collapsing them is how a half-finished write goes unnoticed, so
they are separate outcomes with separate lanes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from . import AGENT_VERSION
from .stops import STOP_REASONS

# --- Enumerations ----------------------------------------------------------

READ = "read"
PROPOSE = "propose"
WRITE = "write"
APPROVE = "approve"
REJECT = "reject"

#: ``approve``/``reject`` extend the plan's read/propose/write set because
#: Step 9 makes approval itself a receipted event.
ACTION_TYPES = frozenset({READ, PROPOSE, WRITE, APPROVE, REJECT})

VERIFIED = "verified"
PENDING_APPROVAL = "pending_approval"
STOPPED_NO_CHANGE = "stopped_no_change"
STOPPED_CLEANUP_REQUIRED = "stopped_cleanup_required"

OUTCOMES = frozenset({
    VERIFIED, PENDING_APPROVAL, STOPPED_NO_CHANGE, STOPPED_CLEANUP_REQUIRED,
})
STOPPED_OUTCOMES = frozenset({STOPPED_NO_CHANGE, STOPPED_CLEANUP_REQUIRED})

#: Rejection reasons are a short list on purpose (Step 9). This is the training
#: signal, and free text alone would not aggregate.
WRONG_TARGET = "wrong_target"
WRONG_DOCUMENT = "wrong_document"
WRONG_NAMING = "wrong_naming"
BAD_EXTRACTION = "bad_extraction"
NOT_NEEDED = "not_needed"
ALREADY_DONE = "already_done"
POLICY = "against_policy"
OTHER = "other"

REJECTION_REASONS = frozenset({
    WRONG_TARGET, WRONG_DOCUMENT, WRONG_NAMING, BAD_EXTRACTION,
    NOT_NEEDED, ALREADY_DONE, POLICY, OTHER,
})

# --- Evidence --------------------------------------------------------------

SCREENSHOT = "screenshot"
FILE_HASH = "file_hash"
URL = "url"
EXTRACTED_VALUE = "extracted_value"
PAGE_SIGNATURE = "page_signature"
FIELD_VALUES = "field_values"

EVIDENCE_KINDS = frozenset({
    SCREENSHOT, FILE_HASH, URL, EXTRACTED_VALUE, PAGE_SIGNATURE, FIELD_VALUES,
})


@dataclass
class Evidence:
    """One piece of proof attached to a receipt.

    ``source_location`` is where the value came from -- a page URL plus a
    selector, a PDF page and region, a CRM field path. Constitution V: an
    extraction returns a value *and* its source, or it returns nothing.
    """

    kind: str
    value: Any
    source_location: str | None = None
    captured_at: str | None = None

    def __post_init__(self) -> None:
        if self.captured_at is None:
            self.captured_at = now_iso()

    def errors(self) -> list[str]:
        problems: list[str] = []
        if self.kind not in EVIDENCE_KINDS:
            problems.append(f"evidence.kind {self.kind!r} is not a known kind")
        if self.value is None or self.value == "":
            problems.append(f"evidence[{self.kind}].value is empty")
        if self.kind == EXTRACTED_VALUE and not self.source_location:
            problems.append(
                "evidence[extracted_value] has no source_location "
                "(Constitution V: no value without provenance)"
            )
        return problems

    def to_dict(self) -> dict:
        return asdict(self)


def now_iso() -> str:
    """UTC timestamp, second precision, stable string form."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- The receipt -----------------------------------------------------------


@dataclass
class Receipt:
    """One action, and the proof of it."""

    # who and what, always required
    human_owner: str
    role: str
    crm_task_id: str
    workflow_id: str
    step_id: str
    system_touched: str
    action_type: str
    target_identifier: str
    outcome: str

    # timing
    timestamp_start: str = field(default_factory=now_iso)
    timestamp_end: str = field(default_factory=now_iso)

    # identity
    receipt_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # state, required for writes
    before_state: dict | None = None
    after_state: dict | None = None

    evidence: list[Evidence] = field(default_factory=list)

    # stops
    stop_reason: str | None = None
    stop_next_step: str | None = None
    cleanup_instruction: str | None = None

    # linkage: corrections, approvals, and the write an approval authorised
    references_receipt_id: str | None = None

    # approval (Step 9)
    approver: str | None = None
    approval_timestamp: str | None = None
    rejection_reason: str | None = None
    rejection_note: str | None = None

    # judgement (Steps 13-16)
    confidence: float | None = None

    #: True only when a promoted workflow executed without a per-item approval.
    #: Constitution II: a write is either approved or auto-executed under a
    #: promotion, never neither.
    auto_executed: bool = False

    model_version: str = "unset"
    agent_version: str = AGENT_VERSION

    # -- validation --------------------------------------------------------

    REQUIRED_TEXT = (
        "receipt_id", "timestamp_start", "timestamp_end", "human_owner",
        "role", "crm_task_id", "workflow_id", "step_id", "system_touched",
        "target_identifier", "model_version", "agent_version",
    )

    def errors(self) -> list[str]:
        """Return every reason this receipt is not acceptable. Empty means valid."""
        problems: list[str] = []

        for name in self.REQUIRED_TEXT:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{name} is required and must be non-empty")

        if self.model_version == "unset":
            problems.append(
                "model_version must be pinned and recorded (F-34: behaviour "
                "shifts with model version and the receipt is the only record)"
            )

        if self.action_type not in ACTION_TYPES:
            problems.append(f"action_type {self.action_type!r} is not a known action type")
        if self.outcome not in OUTCOMES:
            problems.append(f"outcome {self.outcome!r} is not a known outcome")

        problems.extend(self._timing_errors())

        # Constitution IV: evidence is what makes success mean anything.
        if self.outcome == VERIFIED and not self.evidence:
            problems.append(
                "outcome=verified with no evidence -- a receipt with no "
                "evidence is a failed action, not a successful one"
            )

        for item in self.evidence:
            problems.extend(item.errors())

        problems.extend(self._stop_errors())
        problems.extend(self._write_errors())
        problems.extend(self._approval_errors())

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            problems.append(f"confidence {self.confidence!r} is outside [0.0, 1.0]")

        return problems

    def _timing_errors(self) -> list[str]:
        try:
            start = datetime.fromisoformat(self.timestamp_start)
            end = datetime.fromisoformat(self.timestamp_end)
        except (TypeError, ValueError):
            return ["timestamp_start and timestamp_end must be ISO 8601"]
        if end < start:
            return ["timestamp_end is before timestamp_start"]
        return []

    def _stop_errors(self) -> list[str]:
        problems: list[str] = []
        if self.outcome in STOPPED_OUTCOMES:
            if not self.stop_reason:
                problems.append("a stopped receipt must name a stop_reason")
            elif self.stop_reason not in STOP_REASONS:
                problems.append(f"stop_reason {self.stop_reason!r} is not in the taxonomy")
            if not (self.stop_next_step or "").strip():
                problems.append(
                    "a stopped receipt must suggest a human next step "
                    "(Step 10: 'error' is not a reason)"
                )
        elif self.stop_reason:
            problems.append("stop_reason is set on a receipt that did not stop")

        if self.outcome == STOPPED_CLEANUP_REQUIRED:
            if not (self.cleanup_instruction or "").strip():
                problems.append(
                    "outcome=stopped_cleanup_required must say what was left "
                    "changed and what the human has to undo"
                )
        elif self.cleanup_instruction:
            problems.append(
                "cleanup_instruction is set on a receipt that left nothing changed"
            )
        return problems

    def _write_errors(self) -> list[str]:
        if self.action_type != WRITE:
            return []
        problems: list[str] = []
        if self.before_state is None:
            problems.append("a write must record before_state")
        if self.after_state is None and self.outcome == VERIFIED:
            problems.append("a completed write must record after_state")
        # Constitution II, enforced at the data layer as well as the executor.
        if not self.auto_executed and not self.references_receipt_id:
            problems.append(
                "a write must reference the approval that authorised it, or be "
                "marked auto_executed under a promoted workflow "
                "(Constitution II: no writes without approval)"
            )
        return problems

    def _approval_errors(self) -> list[str]:
        problems: list[str] = []
        if self.action_type in (APPROVE, REJECT):
            if not (self.approver or "").strip():
                problems.append("an approval or rejection must record who did it")
            if not (self.approval_timestamp or "").strip():
                problems.append("an approval or rejection must record when it happened")
            if not self.references_receipt_id:
                problems.append("an approval or rejection must reference what it decided on")
        else:
            if self.approver or self.approval_timestamp:
                problems.append(
                    "approver/approval_timestamp set on a receipt that is not "
                    "an approval or rejection"
                )

        if self.action_type == REJECT:
            if self.rejection_reason not in REJECTION_REASONS:
                problems.append(
                    f"rejection_reason {self.rejection_reason!r} is not in the "
                    "short list (Step 9: this is the training signal)"
                )
        elif self.rejection_reason or self.rejection_note:
            problems.append("rejection fields set on a receipt that is not a rejection")
        return problems

    def is_valid(self) -> bool:
        return not self.errors()

    def validate(self) -> "Receipt":
        """Return self, or raise. Use at every boundary that stores a receipt."""
        problems = self.errors()
        if problems:
            raise InvalidReceipt(self.receipt_id, problems)
        return self

    # -- serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        data = asdict(self)
        data["evidence"] = [e if isinstance(e, dict) else e for e in data["evidence"]]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Receipt":
        data = dict(data)
        data["evidence"] = [
            item if isinstance(item, Evidence) else Evidence(**item)
            for item in data.get("evidence", [])
        ]
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            raise InvalidReceipt(
                data.get("receipt_id", "?"),
                [f"unknown field(s): {sorted(unknown)}"],
            )
        return cls(**data)


class InvalidReceipt(ValueError):
    """Raised when a receipt is incomplete. It is never stored."""

    def __init__(self, receipt_id: str, problems: list[str]):
        self.receipt_id = receipt_id
        self.problems = problems
        detail = "\n  - ".join(problems)
        super().__init__(f"receipt {receipt_id} is not valid:\n  - {detail}")
