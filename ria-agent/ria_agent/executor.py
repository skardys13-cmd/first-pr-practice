"""The only path to a write (Constitution II).

Every change to a system outside this application goes through `execute`, and
`execute` refuses unless one of exactly two things is true:

1. a human approved this specific proposal, and that approval is in the log; or
2. this workflow has been promoted for this role, on evidence, and the write is
   marked as auto-executed so the log says so.

There is no third branch, no force flag, and no way to pass the approval in as
an argument -- it is looked up in the append-only log, which is why it cannot be
fabricated by a caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from .crm import CrmWriter
from .log_store import LogStore
from .promotion import PromotionRegistry
from .receipts import (
    APPROVE, PENDING_APPROVAL, PROPOSE, REJECT, Evidence, FIELD_VALUES, Receipt,
    STOPPED_CLEANUP_REQUIRED, VERIFIED, WRITE, now_iso,
)


class NotApproved(PermissionError):
    """Refused. This is the system's central safety property, not an error path."""


class NothingToWrite(NotApproved):
    """The proposal is a finding, not a change. Constitution III."""


class AlreadyExecuted(RuntimeError):
    """A proposal is applied at most once (F-27)."""


@dataclass
class Execution:
    receipt: Receipt
    before: dict
    after: dict

    @property
    def applied(self) -> bool:
        return self.receipt.outcome == VERIFIED


class Executor:
    """Applies approved proposals, and nothing else."""

    def __init__(
        self,
        log: LogStore,
        writer: CrmWriter,
        *,
        model_version: str,
        promotions: PromotionRegistry | None = None,
    ):
        self.log = log
        self.writer = writer
        self.model_version = model_version
        self.promotions = promotions

    def authorisation(self, proposal: Receipt) -> tuple[str | None, bool]:
        """Return (approval receipt id, auto_executed). Raises if neither holds."""
        pointing_at_proposal = self.log.query(references_receipt_id=proposal.receipt_id)
        approval = None
        for receipt in pointing_at_proposal:
            if receipt.action_type == REJECT:
                raise NotApproved(
                    f"{proposal.receipt_id} was rejected by {receipt.approver} "
                    f"({receipt.rejection_reason}). It is not applied."
                )
            if receipt.action_type == APPROVE:
                approval = receipt

        # A write references the approval that authorised it, not the proposal,
        # so looking only at what points at the proposal misses it -- and a
        # retry would file the same document a second time (F-27).
        self._refuse_if_already_written(proposal, approval)

        if approval is not None:
            return approval.receipt_id, False

        promoted = bool(
            self.promotions
            and self.promotions.is_promoted(proposal.workflow_id, proposal.role)
        )
        if promoted:
            return None, True

        raise NotApproved(
            f"{proposal.receipt_id} has no approval in the log, and "
            f"{proposal.workflow_id} is not promoted for {proposal.role}. "
            "Nothing was written."
        )

    def _refuse_if_already_written(self, proposal: Receipt, approval: Receipt | None) -> None:
        """Has this proposal already been applied, under any authorisation?"""
        candidates = list(self.log.query(
            workflow_id=proposal.workflow_id, action_type=WRITE))
        for receipt in candidates:
            if receipt.target_identifier != proposal.target_identifier:
                continue
            if approval is not None and receipt.references_receipt_id == approval.receipt_id:
                raise AlreadyExecuted(
                    f"{proposal.receipt_id} was already applied by "
                    f"{receipt.receipt_id}. A repeat is skipped, not repeated."
                )
            # Auto-executed writes carry no approval id, so they are matched on
            # the target and the state they wrote.
            if (receipt.references_receipt_id is None
                    and receipt.after_state == proposal.after_state):
                raise AlreadyExecuted(
                    f"the same change to {proposal.target_identifier} was already "
                    f"applied by {receipt.receipt_id}. A repeat is skipped."
                )

    def execute(self, proposal_receipt_id: str) -> Execution:
        proposal = self.log.get(proposal_receipt_id)
        if proposal is None:
            raise LookupError(f"no receipt {proposal_receipt_id}")
        if proposal.action_type != PROPOSE or proposal.outcome != PENDING_APPROVAL:
            raise NotApproved(
                f"{proposal_receipt_id} is not a proposal awaiting approval "
                f"(it is a {proposal.action_type} that is {proposal.outcome})"
            )
        if not proposal.after_state:
            # A reconciliation exception is a proposal with nothing to write:
            # it carries two balances and a proposed cause, and a person decides
            # what to do about it. Constitution III means there is no code path
            # that turns one into a correction, and this is that absence.
            raise NothingToWrite(
                f"{proposal_receipt_id} proposes no change to any record. It is a "
                "finding for a person, not something to apply. Nothing was written."
            )

        approval_id, auto = self.authorisation(proposal)
        started = now_iso()
        document_id = proposal.target_identifier
        before = self.writer.document_state(document_id)

        try:
            after = self.writer.file_document(document_id, dict(proposal.after_state or {}))
        except Exception as failure:  # the write half-happened or did not happen
            receipt = Receipt(
                human_owner=proposal.human_owner, role=proposal.role,
                crm_task_id=proposal.crm_task_id, workflow_id=proposal.workflow_id,
                step_id="apply_proposal", system_touched=self.writer.name,
                action_type=WRITE, target_identifier=document_id,
                outcome=STOPPED_CLEANUP_REQUIRED,
                stop_reason="unexpected_page",
                stop_next_step="Open the record and check whether the change landed.",
                cleanup_instruction=(
                    f"The write to {document_id} failed partway: {failure}. "
                    f"It was {before} before the attempt. Check what it is now."
                ),
                before_state=before, after_state=None,
                references_receipt_id=approval_id, auto_executed=auto,
                timestamp_start=started, timestamp_end=now_iso(),
                model_version=self.model_version,
                evidence=[Evidence(FIELD_VALUES, {"error": str(failure)},
                                   source_location=f"{self.writer.name}:{document_id}")],
            )
            self.log.append(receipt)
            return Execution(receipt, before, {})

        receipt = Receipt(
            human_owner=proposal.human_owner, role=proposal.role,
            crm_task_id=proposal.crm_task_id, workflow_id=proposal.workflow_id,
            step_id="apply_proposal", system_touched=self.writer.name,
            action_type=WRITE, target_identifier=document_id, outcome=VERIFIED,
            before_state=before, after_state=after,
            references_receipt_id=approval_id, auto_executed=auto,
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version,
            evidence=[
                Evidence(FIELD_VALUES, before,
                         source_location=f"{self.writer.name}:{document_id} before"),
                Evidence(FIELD_VALUES, after,
                         source_location=f"{self.writer.name}:{document_id} after"),
            ],
        )
        self.log.append(receipt)
        return Execution(receipt, before, after)
