"""The review queue (Steps 7-10).

The queue is a *view* over the append-only log, never a second source of truth.
An item's lane is its receipt's outcome, and a decision on an item is another
receipt pointing back at it. Nothing here mutates anything.

Four lanes, not three. See OPEN_FINDINGS.md #4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .log_store import LogStore
from .plain import LANE_BLURBS, diff_rows, headline, lane_name
from .receipts import (
    APPROVE, PENDING_APPROVAL, REJECT, REJECTION_REASONS, Receipt,
    STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED, now_iso,
)

#: Most urgent first. A stop that left state changed outranks everything,
#: because it is the only lane where the system is in a state nobody can
#: reason about until a human acts.
LANE_ORDER = (
    STOPPED_CLEANUP_REQUIRED,
    PENDING_APPROVAL,
    STOPPED_NO_CHANGE,
    VERIFIED,
)

#: F-35(c): cap the approval lane so it never becomes a wall. Attention is the
#: scarce resource; a queue of two hundred items spends it all on scrolling.
DEFAULT_APPROVAL_CAP = 20

#: Done & verified is the one lane that asks nothing of anyone, so it must not
#: be the biggest thing on the page. A day of successful retrievals would
#: otherwise bury the two items that actually need a person. The full record is
#: always one export away.
DEFAULT_DONE_CAP = 8


@dataclass
class QueueItem:
    """One receipt as the queue sees it."""

    receipt: Receipt
    decision: Receipt | None = None
    seeded: bool = False

    @property
    def receipt_id(self) -> str:
        return self.receipt.receipt_id

    @property
    def lane(self) -> str:
        return self.receipt.outcome

    @property
    def is_open(self) -> bool:
        """Waiting on a person."""
        return self.receipt.outcome == PENDING_APPROVAL and self.decision is None

    @property
    def headline(self) -> str:
        return headline(self.receipt)

    @property
    def diff(self) -> list[tuple[str, str, str]]:
        return diff_rows(self.receipt.before_state, self.receipt.after_state)

    @property
    def decision_word(self) -> str | None:
        if self.decision is None:
            return None
        return "approved" if self.decision.action_type == APPROVE else "rejected"


@dataclass
class Lane:
    key: str
    name: str
    blurb: str
    items: list[QueueItem]
    hidden_count: int = 0

    def __len__(self) -> int:
        return len(self.items)


class Queue:
    """Reads lanes out of the log and writes decisions back into it."""

    def __init__(
        self,
        store: LogStore,
        *,
        model_version: str,
        approval_cap: int = DEFAULT_APPROVAL_CAP,
        done_cap: int = DEFAULT_DONE_CAP,
        seed_registry=None,
    ):
        self.store = store
        self.model_version = model_version
        self.approval_cap = approval_cap
        self.done_cap = done_cap
        self.seeds = seed_registry

    # -- reading -----------------------------------------------------------

    def _decisions(self) -> dict[str, Receipt]:
        decided: dict[str, Receipt] = {}
        for receipt in self.store.query():
            if receipt.action_type in (APPROVE, REJECT) and receipt.references_receipt_id:
                decided[receipt.references_receipt_id] = receipt
        return decided

    def items(self, **filters) -> list[QueueItem]:
        decisions = self._decisions()
        out = []
        for receipt in self.store.query(**filters):
            if receipt.action_type in (APPROVE, REJECT):
                continue  # a decision is not itself a queue item
            out.append(QueueItem(
                receipt=receipt,
                decision=decisions.get(receipt.receipt_id),
                seeded=bool(self.seeds and self.seeds.is_seeded(receipt.receipt_id)),
            ))
        return out

    def item(self, receipt_id: str) -> QueueItem | None:
        receipt = self.store.get(receipt_id)
        if receipt is None:
            return None
        return QueueItem(
            receipt=receipt,
            decision=self._decisions().get(receipt_id),
            seeded=bool(self.seeds and self.seeds.is_seeded(receipt_id)),
        )

    def lanes(self, **filters) -> list[Lane]:
        """The four lanes, most urgent first, with the approval lane capped."""
        by_lane: dict[str, list[QueueItem]] = {key: [] for key in LANE_ORDER}
        for item in self.items(**filters):
            if item.lane == PENDING_APPROVAL and not item.is_open:
                continue  # decided; it is no longer waiting on anyone
            by_lane.setdefault(item.lane, []).append(item)

        lanes = []
        for key in LANE_ORDER:
            items = sorted(
                by_lane.get(key, []),
                key=lambda i: i.receipt.timestamp_start,
                reverse=(key == VERIFIED),
            )
            cap = {PENDING_APPROVAL: self.approval_cap, VERIFIED: self.done_cap}.get(key)
            hidden = 0
            if cap is not None and len(items) > cap:
                hidden = len(items) - cap
                items = items[:cap]
            lanes.append(Lane(
                key=key, name=lane_name(key), blurb=LANE_BLURBS.get(key, ""),
                items=items, hidden_count=hidden,
            ))
        return lanes

    def open_approvals(self) -> list[QueueItem]:
        return [i for i in self.items() if i.is_open]

    # -- deciding (Step 9) -------------------------------------------------

    def approve(self, receipt_id: str, approver: str, note: str = "") -> Receipt:
        """Approve an item. The approval is itself a receipted event."""
        return self._decide(receipt_id, APPROVE, approver, note=note)

    def reject(
        self, receipt_id: str, approver: str, reason: str, note: str = ""
    ) -> Receipt:
        """Reject an item. A reason from the short list is required.

        Step 9: the reason is the training signal, which is why free text alone
        will not do -- free text does not aggregate.
        """
        if reason not in REJECTION_REASONS:
            raise ValueError(
                f"{reason!r} is not one of the accepted rejection reasons: "
                f"{sorted(REJECTION_REASONS)}"
            )
        return self._decide(receipt_id, REJECT, approver, reason=reason, note=note)

    def _decide(
        self, receipt_id: str, action: str, approver: str,
        reason: str | None = None, note: str = "",
    ) -> Receipt:
        item = self.item(receipt_id)
        if item is None:
            raise LookupError(f"no receipt {receipt_id}")
        if item.receipt.outcome != PENDING_APPROVAL:
            raise NotAwaitingApproval(item)
        if item.decision is not None:
            raise AlreadyDecided(item)
        if not approver.strip():
            raise ValueError("an approval must record who made it")

        original = item.receipt
        stamp = now_iso()
        decision = Receipt(
            human_owner=original.human_owner,
            role=original.role,
            crm_task_id=original.crm_task_id,
            workflow_id=original.workflow_id,
            step_id=f"{action}_proposal",
            system_touched="review_queue",
            action_type=action,
            target_identifier=original.target_identifier,
            outcome=VERIFIED,
            timestamp_start=stamp,
            timestamp_end=stamp,
            references_receipt_id=receipt_id,
            approver=approver,
            approval_timestamp=stamp,
            rejection_reason=reason if action == REJECT else None,
            rejection_note=(note or None) if action == REJECT else None,
            model_version=self.model_version,
            evidence=[],
        )
        # A decision's evidence is the decision itself: who, when, on what.
        from .receipts import Evidence, FIELD_VALUES
        decision.evidence = [Evidence(
            FIELD_VALUES,
            f"{action} by {approver} at {stamp}",
            source_location=f"review_queue:/item/{receipt_id}",
        )]
        self.store.append(decision)

        if self.seeds and self.seeds.is_seeded(receipt_id):
            self.seeds.resolve(
                receipt_id, caught=(action == REJECT), reason_given=reason,
                decided_by=approver,
            )
        return decision


class QueueError(Exception):
    """Base for refusals the UI shows back to the person."""


class AlreadyDecided(QueueError):
    def __init__(self, item: QueueItem):
        self.item = item
        super().__init__(
            f"this was already {item.decision_word} by {item.decision.approver} "
            f"at {item.decision.approval_timestamp}"
        )


class NotAwaitingApproval(QueueError):
    def __init__(self, item: QueueItem):
        self.item = item
        super().__init__(
            f"this item is in \"{lane_name(item.lane)}\" and is not waiting for a decision"
        )
