"""The validator is the thing that makes a receipt mean something (Step 3)."""

import unittest

from ria_agent.receipts import (
    APPROVE, Evidence, InvalidReceipt, PENDING_APPROVAL, PROPOSE, READ, REJECT,
    Receipt, STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED, WRITE,
)


def a_receipt(**overrides) -> Receipt:
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id="RT-1",
        workflow_id="statement_retrieval", step_id="retrieve",
        system_touched="schwab", action_type=READ,
        target_identifier="1234-5678", outcome=VERIFIED,
        model_version="claude-x-1",
        evidence=[Evidence("file_hash", "9f2a")],
    )
    base.update(overrides)
    return Receipt(**base)


class ValidReceipts(unittest.TestCase):
    def test_a_complete_receipt_passes(self):
        self.assertEqual(a_receipt().errors(), [])

    def test_validate_returns_self(self):
        receipt = a_receipt()
        self.assertIs(receipt.validate(), receipt)

    def test_round_trips_through_dict(self):
        original = a_receipt()
        restored = Receipt.from_dict(original.to_dict())
        self.assertEqual(restored.to_dict(), original.to_dict())
        self.assertIsInstance(restored.evidence[0], Evidence)


class EvidenceRules(unittest.TestCase):
    def test_success_without_evidence_is_rejected(self):
        problems = a_receipt(evidence=[]).errors()
        self.assertTrue(any("no evidence" in p for p in problems), problems)

    def test_a_stop_may_carry_no_evidence(self):
        receipt = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[],
            stop_reason="session_expired", stop_next_step="Log back in.",
        )
        self.assertEqual(receipt.errors(), [])

    def test_extracted_value_requires_provenance(self):
        problems = a_receipt(evidence=[Evidence("extracted_value", "414118.42")]).errors()
        self.assertTrue(any("provenance" in p for p in problems), problems)

    def test_extracted_value_with_provenance_passes(self):
        receipt = a_receipt(
            evidence=[Evidence("extracted_value", "414118.42", "orion:/positions#total")]
        )
        self.assertEqual(receipt.errors(), [])

    def test_unknown_evidence_kind_is_rejected(self):
        problems = a_receipt(evidence=[Evidence("vibes", "seems right")]).errors()
        self.assertTrue(any("not a known kind" in p for p in problems), problems)


class StopRules(unittest.TestCase):
    def test_stop_needs_a_reason(self):
        problems = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[], stop_next_step="Do it by hand."
        ).errors()
        self.assertTrue(any("must name a stop_reason" in p for p in problems), problems)

    def test_stop_reason_must_be_in_the_taxonomy(self):
        problems = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[],
            stop_reason="it broke", stop_next_step="Do it by hand.",
        ).errors()
        self.assertTrue(any("not in the taxonomy" in p for p in problems), problems)

    def test_stop_needs_a_human_next_step(self):
        problems = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[], stop_reason="timeout"
        ).errors()
        self.assertTrue(any("next step" in p for p in problems), problems)

    def test_cleanup_lane_must_say_what_was_left_changed(self):
        problems = a_receipt(
            outcome=STOPPED_CLEANUP_REQUIRED, evidence=[],
            stop_reason="session_expired", stop_next_step="Log back in.",
        ).errors()
        self.assertTrue(any("cleanup_required" in p for p in problems), problems)

    def test_cleanup_lane_with_an_instruction_passes(self):
        receipt = a_receipt(
            outcome=STOPPED_CLEANUP_REQUIRED, evidence=[],
            stop_reason="session_expired", stop_next_step="Log back in.",
            cleanup_instruction="A document was uploaded but not renamed.",
        )
        self.assertEqual(receipt.errors(), [])

    def test_cleanup_instruction_on_a_clean_stop_is_rejected(self):
        problems = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[], stop_reason="timeout",
            stop_next_step="Retry.", cleanup_instruction="something",
        ).errors()
        self.assertTrue(any("left nothing changed" in p for p in problems), problems)

    def test_stop_reason_on_a_success_is_rejected(self):
        problems = a_receipt(stop_reason="timeout").errors()
        self.assertTrue(any("did not stop" in p for p in problems), problems)


class WriteRules(unittest.TestCase):
    def test_write_without_an_approval_reference_is_rejected(self):
        problems = a_receipt(
            action_type=WRITE, before_state={"name": "scan_0041.pdf"},
            after_state={"name": "2026-08 Schwab Statement.pdf"},
        ).errors()
        self.assertTrue(
            any("Constitution II" in p for p in problems), problems
        )

    def test_write_under_an_approval_passes(self):
        receipt = a_receipt(
            action_type=WRITE, references_receipt_id="approval-1",
            before_state={"name": "scan_0041.pdf"},
            after_state={"name": "2026-08 Schwab Statement.pdf"},
        )
        self.assertEqual(receipt.errors(), [])

    def test_auto_executed_write_passes_without_a_reference(self):
        receipt = a_receipt(
            action_type=WRITE, auto_executed=True,
            before_state={"name": "scan_0041.pdf"},
            after_state={"name": "2026-08 Schwab Statement.pdf"},
        )
        self.assertEqual(receipt.errors(), [])

    def test_write_must_record_before_state(self):
        problems = a_receipt(
            action_type=WRITE, references_receipt_id="approval-1",
            after_state={"name": "x"},
        ).errors()
        self.assertTrue(any("before_state" in p for p in problems), problems)


class ApprovalRules(unittest.TestCase):
    def test_approval_records_who_and_when_and_what(self):
        receipt = a_receipt(
            action_type=APPROVE, approver="Ant",
            approval_timestamp="2026-09-04T10:42:00+00:00",
            references_receipt_id="proposal-1",
        )
        self.assertEqual(receipt.errors(), [])

    def test_approval_without_an_approver_is_rejected(self):
        problems = a_receipt(
            action_type=APPROVE, approval_timestamp="2026-09-04T10:42:00+00:00",
            references_receipt_id="proposal-1",
        ).errors()
        self.assertTrue(any("who did it" in p for p in problems), problems)

    def test_approval_must_reference_what_it_decided_on(self):
        problems = a_receipt(
            action_type=APPROVE, approver="Ant",
            approval_timestamp="2026-09-04T10:42:00+00:00",
        ).errors()
        self.assertTrue(any("reference what it decided" in p for p in problems), problems)

    def test_rejection_reason_must_come_from_the_short_list(self):
        problems = a_receipt(
            action_type=REJECT, approver="Ant",
            approval_timestamp="2026-09-04T10:42:00+00:00",
            references_receipt_id="proposal-1", rejection_reason="just no",
        ).errors()
        self.assertTrue(any("short list" in p for p in problems), problems)

    def test_rejection_with_a_listed_reason_passes(self):
        receipt = a_receipt(
            action_type=REJECT, approver="Ant",
            approval_timestamp="2026-09-04T10:42:00+00:00",
            references_receipt_id="proposal-1", rejection_reason="wrong_target",
            rejection_note="This is the Barrow trust, not the personal account.",
        )
        self.assertEqual(receipt.errors(), [])

    def test_approver_on_a_non_approval_is_rejected(self):
        problems = a_receipt(approver="Ant").errors()
        self.assertTrue(any("not an approval" in p for p in problems), problems)


class OtherFieldRules(unittest.TestCase):
    def test_model_version_must_be_pinned(self):
        problems = a_receipt(model_version="unset").errors()
        self.assertTrue(any("pinned" in p for p in problems), problems)

    def test_missing_owner_is_rejected(self):
        problems = a_receipt(human_owner="   ").errors()
        self.assertTrue(any("human_owner is required" in p for p in problems), problems)

    def test_confidence_outside_the_unit_interval_is_rejected(self):
        self.assertTrue(a_receipt(confidence=1.4).errors())
        self.assertTrue(a_receipt(confidence=-0.1).errors())
        self.assertEqual(a_receipt(confidence=0.0).errors(), [])

    def test_end_before_start_is_rejected(self):
        problems = a_receipt(
            timestamp_start="2026-09-04T10:42:00+00:00",
            timestamp_end="2026-09-04T10:41:00+00:00",
        ).errors()
        self.assertTrue(any("before timestamp_start" in p for p in problems), problems)

    def test_unknown_outcome_is_rejected(self):
        problems = a_receipt(outcome="probably_fine").errors()
        self.assertTrue(any("not a known outcome" in p for p in problems), problems)

    def test_from_dict_rejects_unknown_fields(self):
        data = a_receipt().to_dict()
        data["definitely_worked"] = True
        with self.assertRaises(InvalidReceipt):
            Receipt.from_dict(data)

    def test_invalid_receipt_lists_every_problem(self):
        with self.assertRaises(InvalidReceipt) as caught:
            a_receipt(evidence=[], human_owner="", model_version="unset").validate()
        self.assertGreaterEqual(len(caught.exception.problems), 3)


if __name__ == "__main__":
    unittest.main()
