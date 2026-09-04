"""Verification, retrieval, the attended gate, promotion, and the canary."""

import tempfile
import unittest
from pathlib import Path

from ria_agent import stops
from ria_agent.attended import AttendedHarness, OFF_PATH
from ria_agent.browser import (
    FakePortal, FakePortalConfig, Statement, render_statement_pdf,
)
from ria_agent.canary import Canary
from ria_agent.log_store import LogStore
from ria_agent.navigator import RetrievalGoal
from ria_agent.pdf import extract_text
from ria_agent.promotion import (
    Criteria, Evidence, PromotionRegistry, decide, gather,
)
from ria_agent.receipts import PENDING_APPROVAL, STOPPED_NO_CHANGE, VERIFIED
from ria_agent.retrieval import StatementRetrieval
from ria_agent.seeded_errors import SeedRegistry
from ria_agent.verification import period_present, verify_statement

PERIODS = [f"2026-{month:02d}" for month in range(1, 9)]
STATEMENTS = [Statement("1234-5678", period, "Helen Barrow") for period in PERIODS]
STATEMENTS.append(Statement("9983-3570", "2026-08", "Rosalind Whitcombe"))
GOAL = RetrievalGoal("1234-5678", "2026-08", "Helen Barrow")


class Extraction(unittest.TestCase):
    def test_text_comes_back_out_of_a_generated_pdf(self):
        text = extract_text(render_statement_pdf(STATEMENTS[7]))
        self.assertIn("1234-5678", text)
        self.assertIn("Helen Barrow", text)

    def test_a_non_pdf_yields_nothing(self):
        self.assertEqual(extract_text(b"just some bytes"), "")


class Verifying(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "statement.pdf"
        self.path.write_bytes(render_statement_pdf(
            Statement("1234-5678", "2026-08", "Helen Barrow")))

    def verify(self, **overrides):
        arguments = dict(account="1234-5678", period="2026-08", holder="Helen Barrow")
        arguments.update(overrides)
        return verify_statement(self.path, **arguments)

    def test_the_right_artifact_passes_every_check(self):
        result = self.verify()
        self.assertTrue(result.passed)
        self.assertEqual(result.failures, [])
        self.assertTrue(result.file_hash)

    def test_a_different_account_fails(self):
        self.assertFalse(self.verify(account="1234-5679").passed)

    def test_a_lookalike_account_fails(self):
        self.assertFalse(self.verify(account="1234-56789").passed)

    def test_a_different_period_fails(self):
        self.assertFalse(self.verify(period="2026-07").passed)

    def test_a_different_holder_fails(self):
        result = self.verify(holder="Ada Okonkwo")
        self.assertFalse(result.passed)
        self.assertIn("account number alone", result.failures[0].detail)

    def test_a_file_that_is_not_a_pdf_fails(self):
        self.path.write_bytes(b"this is not a pdf")
        self.assertFalse(self.verify().passed)

    def test_an_empty_file_fails(self):
        self.path.write_bytes(b"")
        self.assertFalse(self.verify().passed)

    def test_a_missing_file_fails(self):
        self.path.unlink()
        result = self.verify()
        self.assertFalse(result.passed)
        self.assertIn("nothing was downloaded", result.failures[0].detail)

    def test_a_scan_with_no_readable_text_fails_rather_than_passing(self):
        # An image-only PDF yields no text, so the account cannot be confirmed.
        self.path.write_bytes(b"%PDF-1.4\n% no text streams here\n%%EOF")
        result = self.verify()
        self.assertFalse(result.passed)
        self.assertIn("needs a human", result.failures[0].detail)

    def test_period_formats_that_should_match(self):
        for text in ("period 2026-08", "August 2026", "Aug 2026", "08/2026"):
            with self.subTest(text=text):
                self.assertTrue(period_present(text, "2026-08"))

    def test_period_formats_that_should_not_match(self):
        for text in ("July 2026", "August 2025", "2026-09", ""):
            with self.subTest(text=text):
                self.assertFalse(period_present(text, "2026-08"))


class RetrievalTestCase(unittest.TestCase):
    def build(self, config=None, promotions=None):
        directory = Path(tempfile.mkdtemp())
        log = LogStore(directory / "log")
        self.addCleanup(log.close)
        retrieval = StatementRetrieval(
            FakePortal(STATEMENTS, config), log, operator="Ant", role="para_planner",
            model_version="claude-x-1", allowed_domains={"portal.schwab.example"},
            evidence_dir=directory / "evidence", promotions=promotions)
        return retrieval, log


class Retrieving(RetrievalTestCase):
    def test_a_good_run_waits_for_a_person(self):
        retrieval, _ = self.build()
        outcome = retrieval.run("RT-1", GOAL)
        self.assertEqual(outcome.receipt.outcome, PENDING_APPROVAL)
        self.assertTrue(outcome.succeeded)

    def test_the_receipt_carries_what_step_22_requires(self):
        retrieval, _ = self.build()
        receipt = retrieval.run("RT-1", GOAL).receipt
        kinds = {piece.kind for piece in receipt.evidence}
        self.assertIn("file_hash", kinds)
        self.assertIn("url", kinds)
        self.assertIn("screenshot", kinds)
        values = {str(piece.value) for piece in receipt.evidence}
        self.assertIn("1234-5678", values)
        self.assertIn("2026-08", values)

    def test_every_receipt_is_valid_and_stored(self):
        retrieval, log = self.build()
        retrieval.run("RT-1", GOAL)
        self.assertEqual(log.count(), 1)
        self.assertTrue(log.query()[0].is_valid())

    def test_a_promoted_workflow_lands_in_done(self):
        registry = PromotionRegistry(Path(tempfile.mkdtemp()) / "p.jsonl")
        registry.promote("statement_retrieval", "para_planner",
                         decide("statement_retrieval", Evidence(verified_runs=50)))
        retrieval, _ = self.build(promotions=registry)
        receipt = retrieval.run("RT-1", GOAL).receipt
        self.assertEqual(receipt.outcome, VERIFIED)
        self.assertTrue(receipt.auto_executed)

    def test_verification_failure_is_a_stop_not_a_done(self):
        retrieval, _ = self.build()
        outcome = retrieval.run("RT-1", RetrievalGoal("1234-5678", "2026-08", "Ada Okonkwo"))
        self.assertEqual(outcome.receipt.outcome, STOPPED_NO_CHANGE)
        self.assertEqual(outcome.stop_reason, stops.VERIFICATION_FAILED)

    def test_a_failed_verification_still_evidences_what_it_found(self):
        retrieval, _ = self.build()
        receipt = retrieval.run(
            "RT-1", RetrievalGoal("1234-5678", "2026-08", "Ada Okonkwo")).receipt
        detail = " ".join(str(piece.value) for piece in receipt.evidence)
        self.assertIn("holder matches", detail)

    def test_each_way_of_failing_names_its_own_reason(self):
        cases = {
            stops.CONSENT_INTERSTITIAL: FakePortalConfig(interstitial=True),
            stops.MFA_CHALLENGE: FakePortalConfig(mfa_on_entry=True),
            stops.NOT_LOGGED_IN: FakePortalConfig(authenticated=False),
            stops.SESSION_EXPIRED: FakePortalConfig(expire_after=0),
        }
        for expected, config in cases.items():
            with self.subTest(reason=expected):
                retrieval, _ = self.build(config)
                receipt = retrieval.run("RT-1", GOAL).receipt
                self.assertEqual(receipt.stop_reason, expected)
                self.assertTrue(receipt.stop_next_step)

    def test_a_stop_leaves_nothing_needing_cleanup(self):
        retrieval, _ = self.build(FakePortalConfig(expire_after=0))
        receipt = retrieval.run("RT-1", GOAL).receipt
        self.assertEqual(receipt.outcome, STOPPED_NO_CHANGE)
        self.assertIsNone(receipt.cleanup_instruction)


class TheAttendedGate(RetrievalTestCase):
    def cases(self, count):
        return [(f"RT-{index}", RetrievalGoal("1234-5678", PERIODS[index % 8], "Helen Barrow"))
                for index in range(count)]

    def test_fifty_clean_runs_open_the_gate(self):
        retrieval, _ = self.build()
        report = AttendedHarness(retrieval).run_batch(self.cases(50))
        self.assertEqual(report.deviations, [])
        self.assertEqual(report.consecutive_clean, 50)
        self.assertTrue(report.gate(50)[0])

    def test_forty_nine_do_not(self):
        retrieval, _ = self.build()
        report = AttendedHarness(retrieval).run_batch(self.cases(49))
        allowed, reasons = report.gate(50)
        self.assertFalse(allowed)
        self.assertIn("49 consecutive", reasons[0])

    def test_one_stop_resets_the_streak(self):
        retrieval, _ = self.build()
        harness = AttendedHarness(retrieval)
        harness.run_batch(self.cases(20))
        harness.run("RT-BAD", RetrievalGoal("1234-5678", "2026-11"))
        self.assertEqual(harness.report.consecutive_clean, 0)
        self.assertEqual(harness.report.best_streak, 20)
        self.assertFalse(harness.report.gate(50)[0])

    def test_a_deviation_is_recorded_with_its_reason(self):
        retrieval, _ = self.build()
        harness = AttendedHarness(retrieval)
        harness.run("RT-BAD", RetrievalGoal("1234-5678", "2026-11"))
        self.assertEqual(len(harness.report.deviations), 1)
        self.assertIn("element_not_found", str(harness.report.deviations[0]))

    def test_going_somewhere_unexpected_counts_even_without_a_stop(self):
        retrieval, _ = self.build(FakePortalConfig(interstitial=True))
        harness = AttendedHarness(retrieval)
        harness.run("RT-1", GOAL)
        self.assertTrue(any(d.kind == OFF_PATH for d in harness.report.deviations))
        self.assertFalse(harness.report.gate(1)[0])

    def test_the_report_reads_without_explanation(self):
        retrieval, _ = self.build()
        summary = AttendedHarness(retrieval).run_batch(self.cases(3)).summary()
        self.assertIn("attended runs", summary)
        self.assertIn("clean streak", summary)


class Promoting(unittest.TestCase):
    def setUp(self):
        self.criteria = Criteria()

    def test_a_read_only_workflow_is_gated_on_verification_not_approvals(self):
        decision = decide("statement_retrieval", Evidence(verified_runs=50), self.criteria)
        self.assertTrue(decision.promote)
        self.assertIn("nothing to edit on a read", decision.explain())

    def test_one_failed_verification_holds_a_read_only_workflow_back(self):
        decision = decide("statement_retrieval",
                          Evidence(verified_runs=50, failed_runs=1), self.criteria)
        self.assertFalse(decision.promote)

    def test_too_few_runs_holds_it_back(self):
        self.assertFalse(decide("statement_retrieval",
                                Evidence(verified_runs=49), self.criteria).promote)

    def test_a_perfect_approval_rate_alone_does_not_promote_a_write(self):
        """The whole point of the fix: 99% approval with nobody reading."""
        decision = decide("document_filing",
                          Evidence(decisions=200, approvals=198, rejections=2),
                          self.criteria)
        self.assertFalse(decision.promote)
        self.assertIn("indistinguishable from nobody reading", decision.explain())

    def test_a_low_catch_rate_blocks_promotion(self):
        decision = decide("document_filing",
                          Evidence(decisions=200, approvals=198, rejections=2,
                                   catch_caught=4, catch_decided=20), self.criteria)
        self.assertFalse(decision.promote)
        self.assertIn("measures fatigue", decision.explain())

    def test_a_good_approval_rate_with_a_good_catch_rate_promotes(self):
        decision = decide("document_filing",
                          Evidence(decisions=200, approvals=198, rejections=2,
                                   catch_caught=18, catch_decided=20), self.criteria)
        self.assertTrue(decision.promote)

    def test_a_poor_approval_rate_blocks_even_with_a_good_catch_rate(self):
        decision = decide("document_filing",
                          Evidence(decisions=200, approvals=150, rejections=50,
                                   catch_caught=20, catch_decided=20), self.criteria)
        self.assertFalse(decision.promote)

    def test_an_unknown_workflow_is_never_promoted(self):
        self.assertFalse(decide("do_the_needful", Evidence(verified_runs=999)).promote)

    def test_promotion_is_recorded_and_reversible(self):
        registry = PromotionRegistry(Path(tempfile.mkdtemp()) / "p.jsonl")
        decision = decide("statement_retrieval", Evidence(verified_runs=50))
        registry.promote("statement_retrieval", "para_planner", decision)
        self.assertTrue(registry.is_promoted("statement_retrieval", "para_planner"))
        registry.demote("statement_retrieval", "para_planner", "filed to the wrong household")
        self.assertFalse(registry.is_promoted("statement_retrieval", "para_planner"))
        self.assertEqual([e["event"] for e in registry.history()], ["promoted", "demoted"])

    def test_promotion_is_per_role(self):
        registry = PromotionRegistry(Path(tempfile.mkdtemp()) / "p.jsonl")
        registry.promote("statement_retrieval", "para_planner",
                         decide("statement_retrieval", Evidence(verified_runs=50)))
        self.assertFalse(registry.is_promoted("statement_retrieval", "client_service"))

    def test_promoting_against_a_refusing_decision_is_itself_refused(self):
        registry = PromotionRegistry(Path(tempfile.mkdtemp()) / "p.jsonl")
        with self.assertRaises(ValueError):
            registry.promote("statement_retrieval", "para_planner",
                             decide("statement_retrieval", Evidence(verified_runs=2)))

    def test_the_registry_survives_a_restart(self):
        path = Path(tempfile.mkdtemp()) / "p.jsonl"
        PromotionRegistry(path).promote(
            "statement_retrieval", "para_planner",
            decide("statement_retrieval", Evidence(verified_runs=50)))
        self.assertTrue(PromotionRegistry(path).is_promoted(
            "statement_retrieval", "para_planner"))

    def test_the_numbers_are_read_out_of_the_log(self):
        directory = Path(tempfile.mkdtemp())
        log = LogStore(directory / "log")
        self.addCleanup(log.close)
        retrieval = StatementRetrieval(
            FakePortal(STATEMENTS), log, operator="Ant", role="para_planner",
            model_version="claude-x-1", allowed_domains={"portal.schwab.example"},
            evidence_dir=directory / "ev")
        for index in range(3):
            retrieval.run(f"RT-{index}", RetrievalGoal("1234-5678", PERIODS[index], "Helen Barrow"))
        evidence = gather(log, None, "statement_retrieval", "para_planner")
        self.assertEqual(evidence.verified_runs, 3)
        self.assertEqual(evidence.failed_runs, 0)


class TheCanary(RetrievalTestCase):
    def check(self, canary, config=None):
        retrieval, _ = self.build(config)
        return canary.check(retrieval.run("CANARY", GOAL), "schwab", GOAL)

    def setUp(self):
        self.canary = Canary(Path(tempfile.mkdtemp()) / "canary.json")

    def test_the_first_run_records_a_baseline(self):
        result = self.check(self.canary)
        self.assertFalse(result.drifted)
        self.assertIsNotNone(self.canary.baseline_for("schwab"))

    def test_an_unchanged_portal_does_not_fire(self):
        self.check(self.canary)
        self.assertFalse(self.check(self.canary).drifted)

    def test_a_cosmetic_rename_does_not_fire(self):
        self.check(self.canary)
        result = self.check(self.canary, FakePortalConfig(redesigned=True))
        self.assertFalse(result.drifted)
        self.assertIn("note, not a failure", " ".join(result.changes))

    def test_a_new_page_in_the_flow_fires(self):
        self.check(self.canary)
        result = self.check(self.canary, FakePortalConfig(interstitial=True))
        self.assertTrue(result.drifted)
        self.assertIn("/notice", " ".join(result.changes))

    def test_a_failed_canary_retrieval_fires(self):
        self.check(self.canary)
        result = self.check(self.canary, FakePortalConfig(authenticated=False))
        self.assertTrue(result.drifted)

    def test_the_baseline_survives_a_restart(self):
        self.check(self.canary)
        reloaded = Canary(self.canary.path)
        self.assertIsNotNone(reloaded.baseline_for("schwab"))


if __name__ == "__main__":
    unittest.main()
