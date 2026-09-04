"""Document filing (Steps 26-28).

The first write, chosen because it is the most reversible thing the agent does.

On reversal, honestly (OPEN_FINDINGS.md #5): the plan promised undo was "one
click from the receipt". It is not, and it cannot be. A reversal is a write, so
it goes through the same approval as any other write -- otherwise the system has
an unapproved write path, which is the one thing it claims not to have. What is
built here is a *reversal proposal*: one click prepares it, and a person still
approves it.

Whether Redtail permits a clean undo at all is unverified. If it does not, the
compensating action is still receipted and still visible, which is the part that
matters.
"""

from __future__ import annotations

from dataclasses import dataclass

from .crm import CrmWriter
from .log_store import LogStore
from .naming import Convention, Document, IncompleteDocument
from .receipts import (
    Evidence, EXTRACTED_VALUE, FIELD_VALUES, FILE_HASH, PENDING_APPROVAL, PROPOSE,
    Receipt, STOPPED_NO_CHANGE, WRITE, now_iso,
)
from . import stops

WORKFLOW_ID = "document_filing"


@dataclass
class Proposal:
    receipt: Receipt

    @property
    def awaiting_approval(self) -> bool:
        return self.receipt.outcome == PENDING_APPROVAL


class DocumentFiling:
    """Prepares filings. Applies none of them."""

    def __init__(
        self,
        log: LogStore,
        writer: CrmWriter,
        convention: Convention,
        *,
        operator: str,
        role: str,
        model_version: str,
    ):
        self.log = log
        self.writer = writer
        self.convention = convention
        self.operator = operator
        self.role = role
        self.model_version = model_version

    def propose(
        self,
        crm_task_id: str,
        document_id: str,
        document: Document,
        *,
        file_hash: str = "",
        confidence: float | None = None,
    ) -> Proposal:
        """Prepare a filing as a diff, and put it in front of a person."""
        started = now_iso()
        before = self.writer.document_state(document_id)

        try:
            after = self.convention.render(document)
        except IncompleteDocument as failure:
            return Proposal(self._stopped(
                crm_task_id, document_id, started, stops.MISSING_INFORMATION, str(failure)))

        # Three-way match before any filing (F-22): the document, the account,
        # and the household must all agree with what the CRM has.
        mismatch = self._three_way_mismatch(before, document)
        if mismatch:
            return Proposal(self._stopped(
                crm_task_id, document_id, started, stops.DATA_MISMATCH, mismatch))

        evidence = [
            Evidence(FIELD_VALUES, before,
                     source_location=f"{self.writer.name}:{document_id} current"),
            Evidence(EXTRACTED_VALUE, document.account,
                     source_location=f"{document.source_filename}:account number"),
            Evidence(EXTRACTED_VALUE, document.household,
                     source_location=f"{document.source_filename}:addressee"),
            Evidence(EXTRACTED_VALUE, document.period,
                     source_location=f"{document.source_filename}:statement period"),
        ]
        if file_hash:
            evidence.insert(0, Evidence(FILE_HASH, file_hash,
                                        source_location=document.source_filename))

        receipt = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
            workflow_id=WORKFLOW_ID, step_id="propose_filing",
            system_touched=self.writer.name, action_type=PROPOSE,
            target_identifier=document_id, outcome=PENDING_APPROVAL,
            before_state=before, after_state=after,
            confidence=confidence, timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version, evidence=evidence,
        )
        self.log.append(receipt)
        return Proposal(receipt)

    def propose_reversal(self, write_receipt_id: str) -> Proposal:
        """Prepare the undo of an applied filing. A person still approves it."""
        applied = self.log.get(write_receipt_id)
        if applied is None:
            raise LookupError(f"no receipt {write_receipt_id}")
        if applied.action_type != WRITE:
            raise ValueError(
                f"{write_receipt_id} is a {applied.action_type}, not a write. "
                "There is nothing to reverse."
            )
        if applied.before_state is None:
            raise ValueError(
                f"{write_receipt_id} did not record what it replaced, so it "
                "cannot be reversed automatically."
            )

        started = now_iso()
        current = self.writer.document_state(applied.target_identifier)
        receipt = Receipt(
            human_owner=applied.human_owner, role=applied.role,
            crm_task_id=applied.crm_task_id, workflow_id=WORKFLOW_ID,
            step_id="propose_reversal", system_touched=self.writer.name,
            action_type=PROPOSE, target_identifier=applied.target_identifier,
            outcome=PENDING_APPROVAL,
            before_state=current, after_state=dict(applied.before_state),
            references_receipt_id=write_receipt_id,
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version,
            evidence=[Evidence(
                FIELD_VALUES,
                {"reverses": write_receipt_id, "restores": applied.before_state},
                source_location=f"receipt/{write_receipt_id}")],
        )
        self.log.append(receipt)
        return Proposal(receipt)

    # -- refusals ----------------------------------------------------------

    @staticmethod
    def _three_way_mismatch(before: dict, document: Document) -> str | None:
        """Document, account and household must agree. Any one out is a stop."""
        from .matching import accounts_equal

        expected_account = before.get("expected_account")
        if expected_account and not accounts_equal(expected_account, document.account):
            return (
                f"the CRM has this document against account {expected_account}, "
                f"but the document itself says {document.account}"
            )
        expected_household = before.get("expected_household")
        if expected_household and expected_household.lower() != document.household.lower():
            return (
                f"the CRM has this document under {expected_household}, but the "
                f"document is addressed to {document.household}"
            )
        return None

    def _stopped(self, crm_task_id, document_id, started, reason, detail) -> Receipt:
        receipt = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
            workflow_id=WORKFLOW_ID, step_id="propose_filing",
            system_touched=self.writer.name, action_type=PROPOSE,
            target_identifier=document_id, outcome=STOPPED_NO_CHANGE,
            stop_reason=reason, stop_next_step=stops.next_step_for(reason),
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version,
            evidence=[Evidence(FIELD_VALUES, {"refused": detail},
                               source_location=f"{self.writer.name}:{document_id}")],
        )
        self.log.append(receipt)
        return receipt
