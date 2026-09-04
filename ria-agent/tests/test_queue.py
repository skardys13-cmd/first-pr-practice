"""Lanes, decisions, and the cap (Steps 7-10)."""

import tempfile
import unittest

from ria_agent.log_store import LogStore
from ria_agent.queue import (
    AlreadyDecided, LANE_ORDER, NotAwaitingApproval, Queue,
)
from ria_agent.receipts import (
    APPROVE, Evidence, PENDING_APPROVAL, PROPOSE, READ, REJECT, Receipt,
    STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED,
)


def proposal(**overrides) -> Receipt:
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id="RT-1",
        workflow_id="document_filing", step_id="propose_filing",
        system_touched="redtail", action_type=PROPOSE,
        target_identifier="Barrow / 1234-5678", outcome=PENDING_APPROVAL,
        model_version="claude-x-1",
        before_state={"filename": "scan_0041.pdf", "folder": "Unfiled"},
        after_state={"filename": "2026-08 Statement.pdf", "folder": "Barrow"},
        evidence=[Evidence("file_hash", "9f2a")],
    )
    base.update(overrides)
    return Receipt(**base)


def stopped(**overrides) -> Receipt:
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id="RT-2",
        workflow_id="statement_retrieval", step_id="retrieve",
        system_touched="schwab", action_type=READ,
        target_identifier="1234-5678", outcome=STOPPED_NO_CHANGE,
        stop_reason="session_expired", stop_next_step="Log back in.",
        model_version="claude-x-1", evidence=[],
    )
    base.update(overrides)
    return Receipt(**base)


class QueueTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = LogStore(self._dir.name)
        self.addCleanup(self.store.close)
        self.queue = Queue(self.store, model_version="claude-x-1")

    def lane(self, key):
        return next(lane for lane in self.queue.lanes() if lane.key == key)


class Lanes(QueueTestCase):
    def test_there_are_four_lanes_most_urgent_first(self):
        keys = [lane.key for lane in self.queue.lanes()]
        self.assertEqual(keys, list(LANE_ORDER))
        self.assertEqual(keys[0], STOPPED_CLEANUP_REQUIRED)

    def test_items_land_in_the_lane_matching_their_outcome(self):
        self.store.append(proposal())
        self.store.append(stopped())
        self.store.append(stopped(
            outcome=STOPPED_CLEANUP_REQUIRED,
            cleanup_instruction="A document was uploaded but not renamed."))
        self.store.append(proposal(outcome=VERIFIED, action_type=READ,
                                   before_state=None, after_state=None))
        counts = {lane.key: len(lane) for lane in self.queue.lanes()}
        self.assertEqual(counts[PENDING_APPROVAL], 1)
        self.assertEqual(counts[STOPPED_NO_CHANGE], 1)
        self.assertEqual(counts[STOPPED_CLEANUP_REQUIRED], 1)
        self.assertEqual(counts[VERIFIED], 1)

    def test_decisions_are_not_themselves_queue_items(self):
        item = self.store.append(proposal())
        self.queue.approve(item.receipt_id, "Ant")
        self.assertEqual(sum(len(lane) for lane in self.queue.lanes()), 0)

    def test_an_approved_item_leaves_the_waiting_lane(self):
        item = self.store.append(proposal())
        self.assertEqual(len(self.lane(PENDING_APPROVAL)), 1)
        self.queue.approve(item.receipt_id, "Ant")
        self.assertEqual(len(self.lane(PENDING_APPROVAL)), 0)

    def test_the_approval_lane_is_capped(self):
        queue = Queue(self.store, model_version="claude-x-1", approval_cap=5)
        for index in range(12):
            self.store.append(proposal(crm_task_id=f"RT-{index}"))
        lane = next(l for l in queue.lanes() if l.key == PENDING_APPROVAL)
        self.assertEqual(len(lane.items), 5)
        self.assertEqual(lane.hidden_count, 7)

    def test_the_cap_does_not_apply_to_other_lanes(self):
        for index in range(12):
            self.store.append(stopped(crm_task_id=f"RT-{index}"))
        queue = Queue(self.store, model_version="claude-x-1", approval_cap=5)
        lane = next(l for l in queue.lanes() if l.key == STOPPED_NO_CHANGE)
        self.assertEqual(len(lane.items), 12)
        self.assertEqual(lane.hidden_count, 0)

    def test_lanes_can_be_filtered_by_person(self):
        self.store.append(proposal(human_owner="Ant"))
        self.store.append(proposal(human_owner="Bea"))
        lanes = self.queue.lanes(human_owner="Bea")
        waiting = next(l for l in lanes if l.key == PENDING_APPROVAL)
        self.assertEqual([i.receipt.human_owner for i in waiting.items], ["Bea"])


class Decisions(QueueTestCase):
    def test_approval_is_itself_a_receipt(self):
        item = self.store.append(proposal())
        decision = self.queue.approve(item.receipt_id, "Ant")
        self.assertEqual(decision.action_type, APPROVE)
        self.assertEqual(decision.approver, "Ant")
        self.assertEqual(decision.references_receipt_id, item.receipt_id)
        self.assertTrue(decision.approval_timestamp)
        self.assertEqual(self.store.count(), 2)

    def test_the_original_receipt_is_untouched_by_a_decision(self):
        item = self.store.append(proposal())
        before = self.store.get(item.receipt_id).to_dict()
        self.queue.approve(item.receipt_id, "Ant")
        self.assertEqual(self.store.get(item.receipt_id).to_dict(), before)

    def test_rejection_records_the_reason_and_the_note(self):
        item = self.store.append(proposal())
        decision = self.queue.reject(
            item.receipt_id, "Ant", reason="wrong_target",
            note="Barrow trust, not the personal account")
        self.assertEqual(decision.action_type, REJECT)
        self.assertEqual(decision.rejection_reason, "wrong_target")
        self.assertIn("Barrow trust", decision.rejection_note)

    def test_a_rejection_reason_outside_the_short_list_is_refused(self):
        item = self.store.append(proposal())
        with self.assertRaises(ValueError):
            self.queue.reject(item.receipt_id, "Ant", reason="just no")
        self.assertEqual(self.store.count(), 1)

    def test_an_anonymous_approval_is_refused(self):
        item = self.store.append(proposal())
        with self.assertRaises(ValueError):
            self.queue.approve(item.receipt_id, "   ")

    def test_deciding_twice_is_refused(self):
        item = self.store.append(proposal())
        self.queue.approve(item.receipt_id, "Ant")
        with self.assertRaises(AlreadyDecided):
            self.queue.approve(item.receipt_id, "Ant")
        with self.assertRaises(AlreadyDecided):
            self.queue.reject(item.receipt_id, "Ant", reason="not_needed")

    def test_a_stopped_item_cannot_be_approved(self):
        item = self.store.append(stopped())
        with self.assertRaises(NotAwaitingApproval):
            self.queue.approve(item.receipt_id, "Ant")

    def test_a_verified_item_cannot_be_approved(self):
        item = self.store.append(proposal(outcome=VERIFIED, action_type=READ,
                                          before_state=None, after_state=None))
        with self.assertRaises(NotAwaitingApproval):
            self.queue.approve(item.receipt_id, "Ant")

    def test_deciding_on_something_that_does_not_exist(self):
        with self.assertRaises(LookupError):
            self.queue.approve("no-such-receipt", "Ant")


class ItemRendering(QueueTestCase):
    def test_a_proposal_exposes_its_diff(self):
        item = self.queue.item(self.store.append(proposal()).receipt_id)
        fields = {field for field, _, _ in item.diff}
        self.assertEqual(fields, {"filename", "folder"})

    def test_open_approvals_are_the_ones_waiting_on_a_person(self):
        first = self.store.append(proposal(crm_task_id="RT-1"))
        self.store.append(proposal(crm_task_id="RT-2"))
        self.store.append(stopped())
        self.assertEqual(len(self.queue.open_approvals()), 2)
        self.queue.approve(first.receipt_id, "Ant")
        self.assertEqual(len(self.queue.open_approvals()), 1)


if __name__ == "__main__":
    unittest.main()


class DoneLaneCap(QueueTestCase):
    """The lane that asks nothing of anyone must not dominate the page."""

    def test_the_done_lane_is_capped(self):
        for index in range(20):
            self.store.append(proposal(
                crm_task_id=f"RT-{index}", outcome=VERIFIED, action_type=READ,
                before_state=None, after_state=None))
        queue = Queue(self.store, model_version="claude-x-1", done_cap=8)
        lane = next(l for l in queue.lanes() if l.key == VERIFIED)
        self.assertEqual(len(lane.items), 8)
        self.assertEqual(lane.hidden_count, 12)

    def test_stopped_items_are_never_hidden(self):
        for index in range(20):
            self.store.append(stopped(crm_task_id=f"RT-{index}"))
        queue = Queue(self.store, model_version="claude-x-1",
                      approval_cap=2, done_cap=2)
        lane = next(l for l in queue.lanes() if l.key == STOPPED_NO_CHANGE)
        self.assertEqual(len(lane.items), 20)
        self.assertEqual(lane.hidden_count, 0)

    def test_the_newest_finished_work_is_the_part_shown(self):
        for index in range(12):
            self.store.append(proposal(
                crm_task_id=f"RT-{index}", outcome=VERIFIED, action_type=READ,
                before_state=None, after_state=None,
                timestamp_start=f"2026-09-04T{8 + index:02d}:00:00+00:00",
                timestamp_end=f"2026-09-04T{8 + index:02d}:00:05+00:00"))
        queue = Queue(self.store, model_version="claude-x-1", done_cap=3)
        lane = next(l for l in queue.lanes() if l.key == VERIFIED)
        self.assertEqual([i.receipt.crm_task_id for i in lane.items],
                         ["RT-11", "RT-10", "RT-9"])
