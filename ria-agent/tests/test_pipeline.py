"""End to end: a CRM task becomes a receipted, approvable retrieval.

Every phase has its own tests. This one asks the question none of them can:
do the four phases actually join up, and does a hostile task get all the way
through without anything unexpected happening?
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from ria_agent.browser import FakePortal, FakePortalConfig, Statement
from ria_agent.classifier import Classifier
from ria_agent.crm import FixtureCrm
from ria_agent.export import export_csv, export_pdf
from ria_agent.navigator import RetrievalGoal
from ria_agent.normalizer import normalise
from ria_agent.queue import Queue
from ria_agent.receipts import APPROVE, PENDING_APPROVAL, VERIFIED, WRITE
from ria_agent.retrieval import StatementRetrieval
from ria_agent.seeded_errors import SeedRegistry
from ria_agent.shadow import ShadowRunner, build_report
from ria_agent.startup import Application
from ria_agent.whitelist import Gate, Whitelist

TODAY = date(2026, 9, 4)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.app = Application(self._dir.name, model_version="claude-x-1",
                               operator="Ant", role="para_planner")
        self.addCleanup(self.app.close)
        self.crm = FixtureCrm.from_bundled_fixtures()
        self.classifier = Classifier()

        # Phase 2: shadow, review, whitelist.
        observations = ShadowRunner(
            self.crm, self.classifier, self.app.log, operator="Ant",
            role="para_planner", model_version="claude-x-1").run(today=TODAY)
        labels = {o.task_id: {"workflow": o.workflow} for o in observations}
        self.whitelist = Whitelist.from_report(
            build_report(observations, labels), min_samples=1)
        self.gate = Gate(self.whitelist, "para_planner")

        statements = [Statement("8443-1468", f"2026-{m:02d}", "Kenji Nakamura")
                      for m in range(1, 9)]
        self.retrieval = StatementRetrieval(
            FakePortal(statements, FakePortalConfig()), self.app.log,
            operator="Ant", role="para_planner", model_version="claude-x-1",
            allowed_domains={"portal.schwab.example"},
            evidence_dir=self.app.evidence_dir)
        self.queue = Queue(self.app.log, model_version="claude-x-1",
                           seed_registry=SeedRegistry(
                               Path(self.app.storage_dir) / "seeds.jsonl"))

    def admit(self, task_id):
        task = self.crm.task(task_id)
        intent = normalise(task, self.classifier.classify(task), TODAY)
        return task, intent, self.gate.admit(task, intent)

    def test_a_real_task_runs_all_the_way_to_an_approval(self):
        task, intent, admission = self.admit("RT-4503")
        self.assertTrue(admission.allowed)

        outcome = self.retrieval.run(task.task_id, RetrievalGoal(
            intent.account.value, intent.get("period"), intent.get("household")))
        self.assertEqual(outcome.receipt.outcome, PENDING_APPROVAL)

        waiting = [i for i in self.queue.open_approvals()
                   if i.receipt.crm_task_id == task.task_id]
        self.assertEqual(len(waiting), 1)

        decision = self.queue.approve(waiting[0].receipt_id, "Ant")
        self.assertEqual(decision.action_type, APPROVE)
        self.assertEqual(decision.references_receipt_id, waiting[0].receipt_id)
        self.assertEqual(self.queue.open_approvals(), [])

    def test_a_task_with_a_prompt_injection_in_its_notes_behaves_normally(self):
        task, intent, admission = self.admit("RT-4570")
        self.assertTrue(intent.injection_flags)
        self.assertTrue(admission.allowed)
        # The note demands every pending item be approved. Nothing was.
        self.assertEqual(intent.workflow_guess, "statement_retrieval")
        before = len(self.queue.open_approvals())
        self.retrieval.run(task.task_id, RetrievalGoal("8443-1468", "2026-08"))
        self.assertEqual(len(self.queue.open_approvals()), before + 1)
        self.assertEqual(
            [r for r in self.app.log.query() if r.action_type == APPROVE], [])

    def test_an_ambiguous_task_never_reaches_the_custodian(self):
        _, _, admission = self.admit("RT-4501")
        self.assertFalse(admission.allowed)
        self.assertEqual(admission.stop_reason, "ambiguous_match")
        self.assertTrue(admission.next_step)

    def test_an_unrecognised_task_never_reaches_the_custodian(self):
        _, _, admission = self.admit("RT-4560")
        self.assertFalse(admission.allowed)
        self.assertEqual(admission.stop_reason, "unrecognised_task")

    def test_nothing_in_the_whole_run_wrote_anywhere(self):
        for task_id in ("RT-4503", "RT-4570"):
            task, intent, admission = self.admit(task_id)
            if admission.allowed:
                self.retrieval.run(task.task_id, RetrievalGoal("8443-1468", "2026-08"))
        writes = [r for r in self.app.log.query() if r.action_type == WRITE]
        self.assertEqual(writes, [])

    def test_every_receipt_in_the_log_is_valid(self):
        self.admit("RT-4503")
        self.retrieval.run("RT-4503", RetrievalGoal("8443-1468", "2026-08"))
        receipts = self.app.log.query()
        self.assertGreater(len(receipts), 30)
        for receipt in receipts:
            with self.subTest(receipt=receipt.receipt_id):
                self.assertEqual(receipt.errors(), [])

    def test_the_log_still_verifies_after_the_whole_run(self):
        self.retrieval.run("RT-4503", RetrievalGoal("8443-1468", "2026-08"))
        self.assertEqual(self.app.log.verify_mirror(), [])

    def test_the_day_can_be_exported_for_a_review(self):
        self.retrieval.run("RT-4503", RetrievalGoal("8443-1468", "2026-08"))
        out = Path(self.app.storage_dir) / "exports"
        csv_path = export_csv(self.app.log, out / "day.csv")
        pdf_path = export_pdf(self.app.log, out / "day.pdf", firm="Reference RIA")
        self.assertIn("8443-1468", csv_path.read_text())
        self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))
        self.assertGreater(pdf_path.stat().st_size, 5000)

    def test_startup_still_finds_no_credentials_after_a_full_run(self):
        self.retrieval.run("RT-4503", RetrievalGoal("8443-1468", "2026-08"))
        from ria_agent.secrets_posture import scan
        self.assertEqual(scan(self.app.storage_dir), [])


if __name__ == "__main__":
    unittest.main()
