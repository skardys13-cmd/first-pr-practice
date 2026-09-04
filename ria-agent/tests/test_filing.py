"""Naming, filing proposals, and the executor (Steps 25-28)."""

import tempfile
import unittest
from pathlib import Path

from ria_agent import stops
from ria_agent.crm import FixtureCrmWriter, UnknownDocument
from ria_agent.executor import AlreadyExecuted, Executor, NotApproved
from ria_agent.filing import DocumentFiling
from ria_agent.log_store import LogStore
from ria_agent.naming import Convention, Document, IncompleteDocument, dry_run
from ria_agent.promotion import Evidence as PromotionEvidence, PromotionRegistry, decide
from ria_agent.queue import Queue
from ria_agent.receipts import PENDING_APPROVAL, VERIFIED, WRITE

DOCUMENT = Document("Barrow", "1234-5678", "2026-08", "Statement", "schwab", "scan_0041.pdf")


class Naming(unittest.TestCase):
    def setUp(self):
        self.convention = Convention()

    def test_the_rules_produce_a_name_and_a_home(self):
        rendered = self.convention.render(DOCUMENT)
        self.assertEqual(rendered["filename"],
                         "2026-08 Schwab Statement - Barrow 1234-5678.pdf")
        self.assertEqual(rendered["folder"], "Barrow / Statements / 2026")
        self.assertEqual(rendered["linked_account"], "1234-5678")

    def test_a_missing_value_is_refused_rather_than_invented(self):
        with self.assertRaises(IncompleteDocument) as caught:
            self.convention.render(Document("", "1234-5678", "2026-08"))
        self.assertIn("household", str(caught.exception))

    def test_characters_that_break_a_filesystem_are_removed(self):
        rendered = self.convention.render(
            Document("O'Brien/Smith", "1234-5678", "2026-08", custodian="schwab"))
        for character in '<>:"/\\|?*':
            self.assertNotIn(character, rendered["filename"])

    def test_a_convention_round_trips_through_a_file(self):
        path = Path(tempfile.mkdtemp()) / "convention.json"
        self.convention.save(path)
        self.assertEqual(Convention.load(path), self.convention)

    def test_a_consistent_history_passes_the_dry_run(self):
        history = [
            (Document("Barrow", "1234-5678", f"2026-{m:02d}", custodian="schwab"),
             f"2026-{m:02d} Schwab Statement - Barrow 1234-5678.pdf")
            for m in range(1, 9)
        ]
        result = dry_run(self.convention, history)
        self.assertTrue(result.passes())
        self.assertEqual(result.disagreements, [])

    def test_an_inconsistent_history_fails_the_dry_run(self):
        history = [
            (Document("Barrow", "1234-5678", f"2026-{m:02d}", custodian="schwab"),
             f"scan_{m}.pdf")
            for m in range(1, 9)
        ]
        result = dry_run(self.convention, history)
        self.assertFalse(result.passes())
        self.assertIn("Fix the human convention before automating it", result.summary())

    def test_documents_the_rules_cannot_name_are_counted_separately(self):
        result = dry_run(self.convention, [(Document("", "1234-5678", "2026-08"), "x.pdf")])
        self.assertEqual(len(result.unnameable), 1)
        self.assertEqual(result.agreed, 0)

    def test_no_history_concludes_nothing(self):
        result = dry_run(self.convention, [])
        self.assertIsNone(result.agreement_rate)
        self.assertFalse(result.passes())


class FilingTestCase(unittest.TestCase):
    def setUp(self):
        directory = Path(tempfile.mkdtemp())
        self.log = LogStore(directory / "log")
        self.addCleanup(self.log.close)
        self.writer = FixtureCrmWriter({"doc-1": {
            "filename": "scan_0041.pdf", "folder": "Unfiled",
            "linked_account": "", "tags": ""}})
        self.promotions = PromotionRegistry(directory / "promotions.jsonl")
        self.filing = DocumentFiling(
            self.log, self.writer, Convention(), operator="Ant",
            role="para_planner", model_version="claude-x-1")
        self.executor = Executor(self.log, self.writer, model_version="claude-x-1",
                                 promotions=self.promotions)
        self.queue = Queue(self.log, model_version="claude-x-1")

    def a_proposal(self, task="RT-1", document=DOCUMENT):
        return self.filing.propose(task, "doc-1", document, file_hash="9f2a")


class Proposing(FilingTestCase):
    def test_a_proposal_waits_and_changes_nothing(self):
        proposal = self.a_proposal()
        self.assertEqual(proposal.receipt.outcome, PENDING_APPROVAL)
        self.assertEqual(self.writer.calls, [])
        self.assertEqual(self.writer.documents["doc-1"]["filename"], "scan_0041.pdf")

    def test_the_proposal_is_a_diff_of_every_field(self):
        receipt = self.a_proposal().receipt
        self.assertEqual(set(receipt.after_state),
                         {"filename", "folder", "linked_account", "tags"})
        self.assertEqual(receipt.before_state["filename"], "scan_0041.pdf")

    def test_the_evidence_names_where_each_value_was_read(self):
        receipt = self.a_proposal().receipt
        sources = {piece.source_location for piece in receipt.evidence}
        self.assertIn("scan_0041.pdf:account number", sources)
        self.assertIn("scan_0041.pdf:addressee", sources)

    def test_a_document_the_rules_cannot_name_stops(self):
        receipt = self.a_proposal(document=Document("", "1234-5678", "2026-08")).receipt
        self.assertEqual(receipt.stop_reason, stops.MISSING_INFORMATION)
        self.assertEqual(self.writer.calls, [])

    def test_an_account_that_disagrees_with_the_crm_stops(self):
        self.writer.documents["doc-1"]["expected_account"] = "9999-0000"
        receipt = self.a_proposal().receipt
        self.assertEqual(receipt.stop_reason, stops.DATA_MISMATCH)

    def test_a_household_that_disagrees_with_the_crm_stops(self):
        self.writer.documents["doc-1"]["expected_household"] = "Okonkwo"
        receipt = self.a_proposal().receipt
        self.assertEqual(receipt.stop_reason, stops.DATA_MISMATCH)

    def test_the_same_account_written_differently_is_not_a_mismatch(self):
        self.writer.documents["doc-1"]["expected_account"] = "1234 5678"
        self.assertEqual(self.a_proposal().receipt.outcome, PENDING_APPROVAL)

    def test_an_unknown_document_is_refused(self):
        with self.assertRaises(UnknownDocument):
            self.filing.propose("RT-1", "doc-nope", DOCUMENT)


class Executing(FilingTestCase):
    def test_an_unapproved_proposal_is_refused_and_writes_nothing(self):
        proposal = self.a_proposal()
        with self.assertRaises(NotApproved):
            self.executor.execute(proposal.receipt.receipt_id)
        self.assertEqual(self.writer.calls, [])

    def test_an_approved_proposal_is_applied(self):
        proposal = self.a_proposal()
        self.queue.approve(proposal.receipt.receipt_id, "Ant")
        execution = self.executor.execute(proposal.receipt.receipt_id)
        self.assertTrue(execution.applied)
        self.assertEqual(self.writer.documents["doc-1"]["filename"],
                         "2026-08 Schwab Statement - Barrow 1234-5678.pdf")

    def test_the_write_receipt_names_the_approval_that_authorised_it(self):
        proposal = self.a_proposal()
        approval = self.queue.approve(proposal.receipt.receipt_id, "Ant")
        receipt = self.executor.execute(proposal.receipt.receipt_id).receipt
        self.assertEqual(receipt.action_type, WRITE)
        self.assertEqual(receipt.references_receipt_id, approval.receipt_id)
        self.assertEqual(receipt.errors(), [])

    def test_a_rejected_proposal_is_refused(self):
        proposal = self.a_proposal()
        self.queue.reject(proposal.receipt.receipt_id, "Ant", reason="wrong_target")
        with self.assertRaises(NotApproved):
            self.executor.execute(proposal.receipt.receipt_id)
        self.assertEqual(self.writer.calls, [])

    def test_executing_twice_writes_once(self):
        proposal = self.a_proposal()
        self.queue.approve(proposal.receipt.receipt_id, "Ant")
        self.executor.execute(proposal.receipt.receipt_id)
        with self.assertRaises(AlreadyExecuted):
            self.executor.execute(proposal.receipt.receipt_id)
        self.assertEqual(len(self.writer.calls), 1)

    def test_a_promoted_workflow_needs_no_per_item_approval(self):
        self.promotions.promote("document_filing", "para_planner", decide(
            "document_filing",
            PromotionEvidence(decisions=200, approvals=198, rejections=2,
                              catch_caught=18, catch_decided=20)))
        proposal = self.a_proposal()
        execution = self.executor.execute(proposal.receipt.receipt_id)
        self.assertTrue(execution.applied)
        self.assertTrue(execution.receipt.auto_executed)
        self.assertEqual(execution.receipt.errors(), [])

    def test_a_stopped_proposal_cannot_be_executed(self):
        proposal = self.a_proposal(document=Document("", "1234-5678", "2026-08"))
        with self.assertRaises(NotApproved):
            self.executor.execute(proposal.receipt.receipt_id)

    def test_a_failing_write_lands_in_the_cleanup_lane(self):
        proposal = self.a_proposal()
        self.queue.approve(proposal.receipt.receipt_id, "Ant")

        def explode(document_id, state):
            raise RuntimeError("the CRM rejected the update halfway through")

        self.writer.file_document = explode
        execution = self.executor.execute(proposal.receipt.receipt_id)
        receipt = execution.receipt
        self.assertEqual(receipt.outcome, "stopped_cleanup_required")
        self.assertIn("failed partway", receipt.cleanup_instruction)
        self.assertEqual(receipt.errors(), [])


class Reversing(FilingTestCase):
    def applied(self):
        proposal = self.a_proposal()
        self.queue.approve(proposal.receipt.receipt_id, "Ant")
        return self.executor.execute(proposal.receipt.receipt_id).receipt

    def test_a_reversal_is_a_proposal_not_an_undo_button(self):
        reversal = self.filing.propose_reversal(self.applied().receipt_id)
        self.assertEqual(reversal.receipt.outcome, PENDING_APPROVAL)
        self.assertEqual(len(self.writer.calls), 1)

    def test_an_unapproved_reversal_writes_nothing(self):
        reversal = self.filing.propose_reversal(self.applied().receipt_id)
        with self.assertRaises(NotApproved):
            self.executor.execute(reversal.receipt.receipt_id)
        self.assertEqual(len(self.writer.calls), 1)

    def test_an_approved_reversal_restores_the_previous_state(self):
        reversal = self.filing.propose_reversal(self.applied().receipt_id)
        self.queue.approve(reversal.receipt.receipt_id, "Ant")
        self.executor.execute(reversal.receipt.receipt_id)
        self.assertEqual(self.writer.documents["doc-1"]["filename"], "scan_0041.pdf")

    def test_the_reversal_points_at_what_it_reverses(self):
        applied = self.applied()
        reversal = self.filing.propose_reversal(applied.receipt_id)
        self.assertEqual(reversal.receipt.references_receipt_id, applied.receipt_id)

    def test_only_a_write_can_be_reversed(self):
        proposal = self.a_proposal()
        with self.assertRaises(ValueError):
            self.filing.propose_reversal(proposal.receipt.receipt_id)


if __name__ == "__main__":
    unittest.main()
