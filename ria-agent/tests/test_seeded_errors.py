"""Seeded errors and catch rate (F-35, OPEN_FINDINGS.md #2)."""

import random
import tempfile
import unittest
from pathlib import Path

from ria_agent.receipts import (
    Evidence, PENDING_APPROVAL, PROPOSE, READ, Receipt, VERIFIED,
)
from ria_agent.seeded_errors import (
    FAULTS, SeedRegistry, SeededErrorInjector,
)


def proposal(**overrides) -> Receipt:
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id="RT-1",
        workflow_id="document_filing", step_id="propose", system_touched="redtail",
        action_type=PROPOSE, target_identifier="1234-5678",
        outcome=PENDING_APPROVAL, model_version="claude-x-1",
        before_state={"filename": "scan_0041.pdf", "balance": "412300.00"},
        after_state={"filename": "2026-08 Schwab Statement.pdf",
                     "period": "2026-08", "balance": "414118.42"},
        evidence=[Evidence("file_hash", "9f2a")],
    )
    base.update(overrides)
    return Receipt(**base)


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = Path(self._dir.name) / "seeds.jsonl"
        self.registry = SeedRegistry(self.path)


class Injection(RegistryTestCase):
    def test_disabled_by_default(self):
        injector = SeededErrorInjector(self.registry)
        receipt, fault = injector.maybe_seed(proposal())
        self.assertIsNone(fault)
        self.assertFalse(self.registry.is_seeded(receipt.receipt_id))

    def test_enabled_at_full_rate_always_seeds(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        receipt, fault = injector.maybe_seed(proposal())
        self.assertIsNotNone(fault)
        self.assertTrue(self.registry.is_seeded(receipt.receipt_id))

    def test_only_items_awaiting_approval_are_seeded(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        for outcome, action in ((VERIFIED, READ), ("stopped_no_change", READ)):
            with self.subTest(outcome=outcome):
                receipt = proposal(
                    outcome=outcome, action_type=action,
                    before_state=None, after_state=None,
                    stop_reason="timeout" if outcome != VERIFIED else None,
                    stop_next_step="Retry." if outcome != VERIFIED else None)
                _, fault = injector.maybe_seed(receipt)
                self.assertIsNone(fault)

    def test_a_seeded_item_differs_from_the_original(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        original = proposal()
        seeded, _ = injector.maybe_seed(original)
        self.assertNotEqual(
            (seeded.target_identifier, seeded.after_state),
            (original.target_identifier, original.after_state))

    def test_a_seeded_item_gets_its_own_receipt_id(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        original = proposal()
        seeded, _ = injector.maybe_seed(original)
        self.assertNotEqual(seeded.receipt_id, original.receipt_id)

    def test_a_seeded_item_is_still_a_valid_receipt(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        for index in range(30):
            injector._rng = random.Random(index)
            seeded, _ = injector.maybe_seed(proposal())
            self.assertEqual(seeded.errors(), [])

    def test_each_fault_changes_something_and_names_a_reason(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        original = proposal()
        for name, fault in FAULTS.items():
            with self.subTest(fault=name):
                seeded = injector._apply(original, fault)
                self.assertIsNotNone(seeded)
                self.assertNotEqual(
                    (seeded.target_identifier, seeded.after_state),
                    (original.target_identifier, original.after_state))
                self.assertTrue(fault.expected_reason)

    def test_transposed_digits_land_on_an_amount_not_a_filename(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        seeded = injector._apply(proposal(), FAULTS["transposed_value"])
        self.assertEqual(seeded.after_state["filename"],
                         "2026-08 Schwab Statement.pdf")
        self.assertNotEqual(seeded.after_state["balance"], "414118.42")

    def test_a_fault_with_nothing_to_corrupt_is_skipped(self):
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        bare = proposal(after_state={"note": "no numbers here"})
        self.assertIsNone(injector._apply(bare, FAULTS["transposed_value"]))

    def test_a_rate_outside_the_unit_interval_is_refused(self):
        with self.assertRaises(ValueError):
            SeededErrorInjector(self.registry, enabled=True, rate=1.5)

    def test_the_rate_is_roughly_honoured(self):
        injector = SeededErrorInjector(
            self.registry, enabled=True, rate=0.3, rng=random.Random(1))
        seeded = sum(bool(injector.maybe_seed(proposal())[1]) for _ in range(400))
        self.assertGreater(seeded, 70)
        self.assertLess(seeded, 170)


class CatchRate(RegistryTestCase):
    def _seed(self, workflow_id="document_filing") -> str:
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        seeded, _ = injector.maybe_seed(proposal(workflow_id=workflow_id))
        return seeded.receipt_id

    def test_nothing_decided_is_not_a_rate_of_zero(self):
        self._seed()
        rate = self.registry.catch_rate()
        self.assertIsNone(rate.rate)
        self.assertEqual(rate.pending, 1)

    def test_a_rejection_counts_as_caught(self):
        receipt_id = self._seed()
        self.registry.resolve(receipt_id, caught=True, decided_by="Ant",
                              reason_given="wrong_target")
        self.assertEqual(self.registry.catch_rate().rate, 1.0)

    def test_an_approval_counts_as_missed(self):
        receipt_id = self._seed()
        self.registry.resolve(receipt_id, caught=False, decided_by="Ant")
        self.assertEqual(self.registry.catch_rate().rate, 0.0)

    def test_the_right_reason_is_recorded_separately_from_the_catch(self):
        receipt_id = self._seed()
        record = self.registry.resolve(
            receipt_id, caught=True, decided_by="Ant", reason_given="not_needed")
        self.assertTrue(record["resolution"]["caught"])
        self.assertFalse(record["resolution"]["right_reason"])

    def test_the_rate_can_be_read_per_workflow(self):
        self.registry.resolve(self._seed("document_filing"), caught=True, decided_by="Ant")
        self.registry.resolve(self._seed("statement_retrieval"), caught=False, decided_by="Ant")
        self.assertEqual(self.registry.catch_rate("document_filing").rate, 1.0)
        self.assertEqual(self.registry.catch_rate("statement_retrieval").rate, 0.0)
        self.assertEqual(self.registry.catch_rate().rate, 0.5)

    def test_resolving_something_that_was_not_seeded_is_refused(self):
        with self.assertRaises(LookupError):
            self.registry.resolve("nope", caught=True, decided_by="Ant")

    def test_the_registry_survives_a_restart(self):
        receipt_id = self._seed()
        self.registry.resolve(receipt_id, caught=True, decided_by="Ant")
        reloaded = SeedRegistry(self.path)
        self.assertTrue(reloaded.is_seeded(receipt_id))
        self.assertEqual(reloaded.catch_rate().rate, 1.0)

    def test_unresolved_items_are_listed(self):
        self._seed()
        decided = self._seed()
        self.registry.resolve(decided, caught=True, decided_by="Ant")
        self.assertEqual(len(self.registry.unresolved()), 1)


if __name__ == "__main__":
    unittest.main()
