"""The log is the firm's record. It only grows (Step 4)."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ria_agent.log_store import DuplicateReceipt, LogStore
from ria_agent.receipts import (
    Evidence, InvalidReceipt, PENDING_APPROVAL, PROPOSE, READ, Receipt, VERIFIED,
)


def a_receipt(**overrides) -> Receipt:
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id="RT-1",
        workflow_id="statement_retrieval", step_id="retrieve",
        system_touched="schwab", action_type=READ,
        target_identifier="1234-5678", outcome=VERIFIED,
        model_version="claude-x-1", evidence=[Evidence("file_hash", "9f2a")],
    )
    base.update(overrides)
    return Receipt(**base)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = LogStore(self._dir.name)
        self.addCleanup(self.store.close)


class Appending(StoreTestCase):
    def test_stores_and_reads_back(self):
        receipt = self.store.append(a_receipt())
        self.assertEqual(self.store.get(receipt.receipt_id).to_dict(), receipt.to_dict())

    def test_invalid_receipts_are_never_stored(self):
        with self.assertRaises(InvalidReceipt):
            self.store.append(a_receipt(evidence=[]))
        self.assertEqual(self.store.count(), 0)

    def test_a_receipt_id_is_written_once(self):
        receipt = a_receipt()
        self.store.append(receipt)
        with self.assertRaises(DuplicateReceipt):
            self.store.append(receipt)

    def test_the_step_4_gate_one_thousand_receipts(self):
        for index in range(1000):
            self.store.append(a_receipt(crm_task_id=f"RT-{index}"))
        self.assertEqual(self.store.count(), 1000)
        self.assertEqual(self.store.verify_mirror(), [])


class AppendOnly(StoreTestCase):
    def test_the_store_exposes_no_update_or_delete(self):
        surface = {name for name in dir(self.store) if not name.startswith("_")}
        forbidden = {"update", "edit", "delete", "remove", "amend", "set", "purge"}
        self.assertEqual(surface & forbidden, set())

    def test_the_database_refuses_an_update(self):
        self.store.append(a_receipt())
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._conn.execute("UPDATE receipts SET human_owner = 'mallory'")

    def test_the_database_refuses_a_delete(self):
        self.store.append(a_receipt())
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._conn.execute("DELETE FROM receipts")

    def test_a_correction_is_a_new_receipt_pointing_at_the_old_one(self):
        original = self.store.append(a_receipt())
        correction = self.store.append(
            a_receipt(references_receipt_id=original.receipt_id)
        )
        self.assertEqual(self.store.count(), 2)
        self.assertIsNotNone(self.store.get(original.receipt_id))
        found = self.store.query(references_receipt_id=original.receipt_id)
        self.assertEqual([r.receipt_id for r in found], [correction.receipt_id])


class Mirror(StoreTestCase):
    def test_mirror_matches_after_writes(self):
        for index in range(5):
            self.store.append(a_receipt(crm_task_id=f"RT-{index}"))
        self.assertEqual(self.store.verify_mirror(), [])
        lines = Path(self.store.jsonl_path).read_text().strip().splitlines()
        self.assertEqual(len(lines), 5)
        self.assertEqual(json.loads(lines[0])["human_owner"], "Ant")

    def test_an_edit_to_the_mirror_alone_is_detected(self):
        self.store.append(a_receipt())
        path = Path(self.store.jsonl_path)
        path.write_text(path.read_text().replace('"Ant"', '"Mallory"'))
        self.assertTrue(any("differs" in p for p in self.store.verify_mirror()))

    def test_a_missing_mirror_is_detected(self):
        self.store.append(a_receipt())
        Path(self.store.jsonl_path).unlink()
        self.assertTrue(self.store.verify_mirror())


class Querying(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.store.append(a_receipt(
            human_owner="Ant", workflow_id="statement_retrieval",
            timestamp_start="2026-09-01T09:00:00+00:00",
            timestamp_end="2026-09-01T09:00:05+00:00"))
        self.store.append(a_receipt(
            human_owner="Bea", workflow_id="document_filing",
            outcome=PENDING_APPROVAL, action_type=PROPOSE,
            timestamp_start="2026-09-02T09:00:00+00:00",
            timestamp_end="2026-09-02T09:00:05+00:00"))
        self.store.append(a_receipt(
            human_owner="Ant", workflow_id="document_filing",
            timestamp_start="2026-09-03T09:00:00+00:00",
            timestamp_end="2026-09-03T09:00:05+00:00"))

    def test_filter_by_person(self):
        self.assertEqual(len(self.store.query(human_owner="Ant")), 2)

    def test_filter_by_workflow(self):
        self.assertEqual(len(self.store.query(workflow_id="document_filing")), 2)

    def test_filter_by_outcome(self):
        self.assertEqual(len(self.store.query(outcome=PENDING_APPROVAL)), 1)

    def test_filter_by_date_range(self):
        found = self.store.query(
            since="2026-09-02T00:00:00+00:00", until="2026-09-02T23:59:59+00:00"
        )
        self.assertEqual([r.human_owner for r in found], ["Bea"])

    def test_filters_combine(self):
        found = self.store.query(human_owner="Ant", workflow_id="document_filing")
        self.assertEqual(len(found), 1)

    def test_results_are_in_time_order(self):
        stamps = [r.timestamp_start for r in self.store.query()]
        self.assertEqual(stamps, sorted(stamps))

    def test_reopening_the_store_keeps_everything(self):
        self.store.close()
        reopened = LogStore(self._dir.name)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.count(), 3)


if __name__ == "__main__":
    unittest.main()
