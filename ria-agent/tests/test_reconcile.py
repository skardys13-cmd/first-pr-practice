"""Reconciliation, linkage, and the release gate (Steps 31-38).

RECONCILIATION.md is the specification; these are its assertions.
"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from ria_agent.executor import Executor, NothingToWrite
from ria_agent.crm import FixtureCrmWriter
from ria_agent.linkage import (
    AccountRecord, DUPLICATE, NOT_LINKED, ORPHAN, WRONG_HOUSEHOLD, check,
)
from ria_agent.log_store import LogStore
from ria_agent.queue import Queue
from ria_agent.receipts import PENDING_APPROVAL, PROPOSE, STOPPED_NO_CHANGE, VERIFIED
from ria_agent.recon_scoring import Scorecard, plant_break, score
from ria_agent.reconcile import (
    AGREED, Balance, CANNOT_COMPARE, DISAGREED, EXACT, PRICED, PENDING_TRADES,
    Reconciliation, SOURCE_UNAVAILABLE, Tolerance, compare, money, tolerance_for,
)

WHEN = "2026-08-31T21:00:00+00:00"
EARLIER = "2026-08-31T13:00:00+00:00"


def balance(system, value, as_of=WHEN, account="1234-5678", **components):
    return Balance(system, account,
                   money(value) if value is not None else None,
                   as_of, f"{system}:/positions", components)


class Tolerances(unittest.TestCase):
    def test_a_cached_pair_allows_rounding_only(self):
        self.assertEqual(tolerance_for("schwab", "redtail"), EXACT)
        self.assertEqual(EXACT.limit(money("8000000")), Decimal("0.01"))

    def test_independently_pricing_systems_get_a_proportional_allowance(self):
        self.assertEqual(tolerance_for("schwab", "orion"), PRICED)
        self.assertEqual(PRICED.limit(money("414118.42")), Decimal("82.82"))

    def test_the_proportional_allowance_is_capped(self):
        """Uncapped, 0.02% of $8m is $1,600 — a tolerance that grows where the money is."""
        self.assertEqual(PRICED.limit(money("8000000")), Decimal("250.00"))

    def test_the_allowance_never_falls_below_the_floor(self):
        self.assertGreaterEqual(PRICED.limit(money("1.00")), Decimal("0.01"))

    def test_an_unknown_system_is_treated_as_independently_pricing(self):
        self.assertEqual(tolerance_for("someothersystem", "orion"), PRICED)

    def test_a_tolerance_describes_itself(self):
        self.assertIn("capped", PRICED.describe())
        self.assertNotIn("capped", EXACT.describe())


class Comparing(unittest.TestCase):
    def test_identical_figures_agree(self):
        result = compare(balance("schwab", "414118.42"), balance("redtail", "414118.42"))
        self.assertEqual(result.verdict, AGREED)
        self.assertTrue(result.agreed)

    def test_a_penny_apart_agrees(self):
        self.assertEqual(
            compare(balance("schwab", "414118.42"), balance("redtail", "414118.41")).verdict,
            AGREED)

    def test_a_dollar_apart_against_the_cached_crm_disagrees(self):
        result = compare(balance("schwab", "414118.42"), balance("redtail", "414117.42"))
        self.assertEqual(result.verdict, DISAGREED)
        self.assertEqual(result.difference, Decimal("1.00"))

    def test_a_small_pricing_difference_between_analytics_agrees(self):
        self.assertEqual(
            compare(balance("schwab", "414118.42"), balance("orion", "414036.00")).verdict,
            AGREED)

    def test_a_difference_past_the_allowance_disagrees(self):
        self.assertEqual(
            compare(balance("schwab", "414118.42"), balance("orion", "414035.00")).verdict,
            DISAGREED)

    def test_a_large_gap_on_a_large_account_disagrees(self):
        self.assertEqual(
            compare(balance("schwab", "8000000.00"), balance("orion", "7998400.00")).verdict,
            DISAGREED)

    def test_the_difference_is_reported_as_an_absolute_amount(self):
        left = compare(balance("schwab", "100.00"), balance("redtail", "90.00"))
        right = compare(balance("schwab", "90.00"), balance("redtail", "100.00"))
        self.assertEqual(left.difference, right.difference)


class AsOfAlignment(unittest.TestCase):
    """Section 2: alignment is checked before tolerance, always."""

    def test_mismatched_as_of_cannot_be_compared(self):
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "414118.42", EARLIER))
        self.assertEqual(result.verdict, CANNOT_COMPARE)

    def test_identical_figures_at_different_instants_do_not_agree(self):
        """The dangerous case: the numbers match, so a naive engine says fine."""
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "414118.42", EARLIER))
        self.assertNotEqual(result.verdict, AGREED)
        self.assertFalse(result.agreed)

    def test_different_figures_at_different_instants_do_not_disagree_either(self):
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "1.00", EARLIER))
        self.assertEqual(result.verdict, CANNOT_COMPARE)

    def test_a_firm_may_widen_the_window_deliberately(self):
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "414118.42", EARLIER),
                         alignment_seconds=60 * 60 * 12)
        self.assertEqual(result.verdict, AGREED)

    def test_a_balance_with_no_timestamp_is_unusable(self):
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "414118.42", None))
        self.assertEqual(result.verdict, SOURCE_UNAVAILABLE)

    def test_an_unreadable_timestamp_is_unusable(self):
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "414118.42", "last Tuesday"))
        self.assertEqual(result.verdict, SOURCE_UNAVAILABLE)

    def test_a_system_that_could_not_be_read_is_unusable(self):
        unavailable = Balance("orion", "1234-5678", None, None, "orion",
                              {}, "the session expired at 10:42")
        result = compare(balance("schwab", "414118.42"), unavailable)
        self.assertEqual(result.verdict, SOURCE_UNAVAILABLE)
        self.assertIn("session expired", result.detail)

    def test_cannot_compare_says_what_to_do_about_it(self):
        result = compare(balance("schwab", "414118.42"),
                         balance("redtail", "414118.42", EARLIER))
        self.assertIn("same instant", result.proposed_resolution())


class Explaining(unittest.TestCase):
    def test_a_pending_trade_that_matches_the_gap_is_offered_as_the_cause(self):
        result = compare(
            balance("schwab", "414118.42", pending_trades="0"),
            balance("orion", "412300.00", pending_trades="1818.42"))
        self.assertEqual(result.verdict, DISAGREED)
        self.assertIn("pending trade", result.explanations[0])

    def test_an_explanation_is_never_a_resolution(self):
        result = compare(
            balance("schwab", "414118.42", pending_trades="0"),
            balance("orion", "412300.00", pending_trades="1818.42"))
        self.assertEqual(result.verdict, DISAGREED)
        self.assertIn("Confirm", result.proposed_resolution())

    def test_a_component_explaining_part_of_the_gap_says_so(self):
        result = compare(
            balance("schwab", "414118.42", accrued_dividends="0"),
            balance("orion", "410000.00", accrued_dividends="100.00"))
        self.assertTrue(any("part of the difference" in e for e in result.explanations))

    def test_an_unexplained_difference_says_where_to_look_first(self):
        result = compare(balance("schwab", "414118.42"), balance("redtail", "400000.00"))
        self.assertEqual(result.explanations, [])
        self.assertIn("account mapping", result.proposed_resolution())


class Receipting(unittest.TestCase):
    def setUp(self):
        directory = Path(tempfile.mkdtemp())
        self.log = LogStore(directory / "log")
        self.addCleanup(self.log.close)
        self.writer = FixtureCrmWriter({"doc-1": {"filename": "x.pdf"}})
        self.reconciliation = Reconciliation(
            self.log, operator="Ant", role="para_planner", model_version="claude-x-1")

    def test_every_pair_of_systems_is_compared(self):
        results = self.reconciliation.reconcile("RT-4550", [
            balance("schwab", "100.00"), balance("redtail", "100.00"),
            balance("orion", "100.00")])
        self.assertEqual(len(results), 3)
        self.assertEqual(self.log.count(), 3)

    def test_an_agreement_is_receipted_with_both_figures(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "100.00")])
        receipt = self.log.query()[0]
        self.assertEqual(receipt.outcome, VERIFIED)
        values = " ".join(str(piece.value) for piece in receipt.evidence)
        self.assertIn("schwab=100.00", values)
        self.assertIn("redtail=100.00", values)

    def test_a_disagreement_becomes_a_proposal_awaiting_a_person(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "90.00")])
        receipt = self.log.query()[0]
        self.assertEqual(receipt.action_type, PROPOSE)
        self.assertEqual(receipt.outcome, PENDING_APPROVAL)

    def test_the_exception_carries_both_values_both_sources_both_timestamps(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "90.00")])
        receipt = self.log.query()[0]
        self.assertEqual(receipt.before_state, {
            "schwab balance": "100.00", "schwab as of": WHEN,
            "redtail balance": "90.00", "redtail as of": WHEN})
        sources = {piece.source_location for piece in receipt.evidence}
        self.assertIn("schwab:/positions", sources)
        self.assertIn("redtail:/positions", sources)

    def test_the_exception_carries_a_proposed_cause_and_resolution(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "414118.42", pending_trades="0"),
            balance("orion", "412300.00", pending_trades="1818.42")])
        receipt = self.log.query()[0]
        fields = next(p.value for p in receipt.evidence if isinstance(p.value, dict))
        self.assertIn("pending trade", fields["proposed_cause"])
        self.assertTrue(fields["proposed_resolution"])

    def test_an_exception_proposes_no_change_to_any_record(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "90.00")])
        self.assertIsNone(self.log.query()[0].after_state)

    def test_an_approved_exception_still_cannot_be_executed(self):
        """Constitution III: there is no code path from a break to a correction."""
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "90.00")])
        exception = self.log.query()[0]
        Queue(self.log, model_version="claude-x-1").approve(exception.receipt_id, "Ant")
        executor = Executor(self.log, self.writer, model_version="claude-x-1")
        with self.assertRaises(NothingToWrite):
            executor.execute(exception.receipt_id)
        self.assertEqual(self.writer.calls, [])

    def test_cannot_compare_is_a_stop_not_an_exception(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "100.00", EARLIER)])
        receipt = self.log.query()[0]
        self.assertEqual(receipt.outcome, STOPPED_NO_CHANGE)
        self.assertTrue(receipt.stop_next_step)

    def test_every_receipt_it_writes_is_valid(self):
        self.reconciliation.reconcile("RT-1", [
            balance("schwab", "100.00"), balance("redtail", "90.00"),
            balance("orion", "100.00", EARLIER)])
        for receipt in self.log.query():
            with self.subTest(receipt=receipt.receipt_id):
                self.assertEqual(receipt.errors(), [])


class Linkage(unittest.TestCase):
    def test_a_fully_linked_book_is_clean(self):
        report = check([
            AccountRecord("schwab", "1234-5678", "Barrow"),
            AccountRecord("redtail", "1234-5678", "Barrow"),
            AccountRecord("orion", "1234-5678", "Barrow")])
        self.assertTrue(report.clean)
        self.assertEqual(report.accounts_checked, 1)

    def test_formatting_differences_are_not_linkage_problems(self):
        report = check([
            AccountRecord("schwab", "1234-5678", "Barrow"),
            AccountRecord("redtail", "1234 5678", "Barrow")])
        self.assertTrue(report.clean)

    def test_a_missing_link_is_found(self):
        report = check([
            AccountRecord("schwab", "1234-5678", "Barrow"),
            AccountRecord("redtail", "1234-5678", "Barrow"),
            AccountRecord("orion", "9999-0000", "Other")])
        self.assertEqual(len(report.of_kind(NOT_LINKED)), 1)
        self.assertIn("orion", report.of_kind(NOT_LINKED)[0].detail)

    def test_a_household_disagreement_is_found(self):
        report = check([
            AccountRecord("schwab", "4417-2290", "Oyelaran"),
            AccountRecord("redtail", "4417-2290", "Okonkwo")])
        finding = report.of_kind(WRONG_HOUSEHOLD)[0]
        self.assertIn("Oyelaran", finding.detail)
        self.assertIn("Okonkwo", finding.detail)

    def test_a_duplicate_in_one_system_is_found(self):
        report = check([
            AccountRecord("schwab", "1234-5678", "Barrow"),
            AccountRecord("redtail", "1234-5678", "Barrow"),
            AccountRecord("redtail", "1234-5678", "Barrow")])
        self.assertEqual(len(report.of_kind(DUPLICATE)), 1)

    def test_an_account_at_no_custodian_is_an_orphan(self):
        report = check([
            AccountRecord("schwab", "1234-5678", "Barrow"),
            AccountRecord("redtail", "1234-5678", "Barrow"),
            AccountRecord("orion", "5555-0000", "Ghost")])
        self.assertEqual(len(report.of_kind(ORPHAN)), 1)

    def test_every_finding_says_what_to_do(self):
        report = check([
            AccountRecord("schwab", "1234-5678", "Barrow"),
            AccountRecord("redtail", "9999-0000", "Other")])
        self.assertTrue(report.findings)
        for finding in report.findings:
            with self.subTest(finding=finding.kind):
                self.assertTrue(finding.resolution)

    def test_nothing_to_check_concludes_nothing(self):
        self.assertIn("No accounts", check([]).summary())


class TheReleaseGate(unittest.TestCase):
    def comparisons(self, agreeing=0, breaking=0, missed=0):
        out, truth = [], {}
        for index in range(agreeing):
            key = f"ok{index}"
            out.append((key, compare(balance("schwab", "100.00"),
                                     balance("redtail", "100.00"))))
            truth[key] = False
        for index in range(breaking):
            key = f"br{index}"
            out.append((key, compare(balance("schwab", "100.00"),
                                     balance("redtail", "90.00"))))
            truth[key] = True
        for index in range(missed):
            # The engine agrees, but the reviewer found a real break.
            key = f"miss{index}"
            out.append((key, compare(balance("schwab", "100.00"),
                                     balance("redtail", "100.00"))))
            truth[key] = True
        return out, truth

    def test_zero_false_agreements_out_of_few_breaks_does_not_clear(self):
        card = score(*self.comparisons(agreeing=200, breaking=5))
        self.assertEqual(card.false_agreements, [])
        allowed, reasons = card.gate()
        self.assertFalse(allowed)
        self.assertIn("not evidence", reasons[0])

    def test_enough_breaks_all_caught_clears(self):
        card = score(*self.comparisons(agreeing=200, breaking=20))
        self.assertTrue(card.gate()[0])
        self.assertEqual(card.false_agreement_rate, 0.0)

    def test_a_single_false_agreement_blocks(self):
        card = score(*self.comparisons(agreeing=200, breaking=25, missed=1))
        allowed, reasons = card.gate()
        self.assertFalse(allowed)
        self.assertIn("false agreement", reasons[0])

    def test_false_breaks_are_counted_but_do_not_block(self):
        comparisons, truth = self.comparisons(breaking=20)
        for index in range(3):
            key = f"noise{index}"
            comparisons.append((key, compare(balance("schwab", "100.00"),
                                             balance("redtail", "90.00"))))
            truth[key] = False
        card = score(comparisons, truth)
        self.assertEqual(len(card.false_breaks), 3)
        self.assertTrue(card.gate()[0])

    def test_unreviewed_comparisons_are_not_scored(self):
        comparisons, _ = self.comparisons(agreeing=10)
        card = score(comparisons, {})
        self.assertEqual(card.compared, 10)
        self.assertEqual(card.reviewed, 0)
        self.assertIsNone(card.false_agreement_rate)

    def test_cannot_compare_is_never_counted_as_a_miss(self):
        key = "x"
        comparison = compare(balance("schwab", "100.00"),
                             balance("redtail", "100.00", EARLIER))
        card = score([(key, comparison)], {key: True})
        self.assertEqual(card.false_agreements, [])
        self.assertEqual(card.unusable, 1)

    def test_a_planted_break_is_caught(self):
        planted = plant_break(balance("redtail", "100000.00"), "1000.00")
        result = compare(balance("schwab", "100000.00"), planted)
        self.assertEqual(result.verdict, DISAGREED)
        self.assertIn("PLANTED", planted.source)

    def test_planting_reaches_the_gate_when_the_natural_rate_is_low(self):
        comparisons, truth = self.comparisons(agreeing=200, breaking=2)
        for index in range(20):
            key = f"plant{index}"
            comparisons.append((key, compare(
                balance("schwab", "100000.00"),
                plant_break(balance("redtail", "100000.00")))))
            truth[key] = True
        card = score(comparisons, truth)
        self.assertEqual(card.true_breaks, 22)
        self.assertTrue(card.gate()[0])


if __name__ == "__main__":
    unittest.main()
