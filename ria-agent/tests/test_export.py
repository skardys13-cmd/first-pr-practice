"""Exports (Step 5) and the plain language they are written in (Step 8)."""

import csv
import re
import tempfile
import unittest
from pathlib import Path

from ria_agent.export import CSV_COLUMNS, describe_filters, export_csv, export_pdf
from ria_agent.log_store import LogStore
from ria_agent.pdf import PdfDocument, text_width, wrap
from ria_agent.plain import as_text, describe, diff_rows, headline
from ria_agent.receipts import (
    APPROVE, Evidence, PENDING_APPROVAL, PROPOSE, READ, Receipt,
    STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED, WRITE,
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


class ExportTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)
        self.store = LogStore(self.root / "log")
        self.addCleanup(self.store.close)
        self.store.append(a_receipt())
        self.store.append(a_receipt(
            human_owner="Bea", action_type=PROPOSE, outcome=PENDING_APPROVAL,
            workflow_id="document_filing", confidence=0.93,
            before_state={"filename": "scan_0041.pdf"},
            after_state={"filename": "2026-08 Schwab Statement.pdf"},
            evidence=[Evidence("extracted_value", "2026-08", "pdf:p1")]))
        self.store.append(a_receipt(
            outcome=STOPPED_CLEANUP_REQUIRED, evidence=[],
            stop_reason="session_expired",
            stop_next_step="Log back into Redtail, then check the Barrow folder.",
            cleanup_instruction="A document was uploaded but not renamed."))


class CsvExport(ExportTestCase):
    def test_writes_a_row_per_receipt(self):
        path = export_csv(self.store, self.root / "out.csv")
        with path.open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual(list(rows[0]), CSV_COLUMNS)

    def test_filters_apply(self):
        path = export_csv(self.store, self.root / "ant.csv", human_owner="Ant")
        with path.open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["human_owner"] == "Ant" for row in rows))

    def test_evidence_is_readable_in_a_cell(self):
        path = export_csv(self.store, self.root / "out.csv", human_owner="Bea")
        with path.open() as handle:
            row = next(csv.DictReader(handle))
        self.assertIn("extracted_value=2026-08", row["evidence"])
        self.assertIn("pdf:p1", row["evidence"])
        self.assertEqual(row["evidence_count"], "1")

    def test_cleanup_instruction_survives_the_export(self):
        path = export_csv(self.store, self.root / "out.csv",
                          outcome=STOPPED_CLEANUP_REQUIRED)
        with path.open() as handle:
            row = next(csv.DictReader(handle))
        self.assertIn("not renamed", row["cleanup_instruction"])


class PdfExport(ExportTestCase):
    def test_produces_a_structurally_valid_pdf(self):
        path = export_pdf(self.store, self.root / "out.pdf", firm="Reference RIA")
        blob = path.read_bytes()
        self.assertTrue(blob.startswith(b"%PDF-1.4"))
        self.assertTrue(blob.rstrip().endswith(b"%%EOF"))
        self._assert_xref_is_sound(blob)

    def test_an_empty_period_still_exports(self):
        path = export_pdf(self.store, self.root / "none.pdf", human_owner="Nobody")
        self.assertTrue(path.read_bytes().startswith(b"%PDF"))

    def _assert_xref_is_sound(self, blob: bytes):
        start = int(re.search(rb"startxref\s+(\d+)", blob).group(1))
        self.assertEqual(blob[start:start + 4], b"xref")
        lines = blob[start:].split(b"\n")
        count = int(lines[1].split()[1])
        for number, line in enumerate(lines[2:2 + count]):
            if line.endswith(b"f "):
                continue
            offset = int(line.split()[0])
            self.assertTrue(blob[offset:].startswith(b"%d 0 obj" % number))

    def test_filter_description_is_human_readable(self):
        self.assertEqual(describe_filters({}), "everything in the log, unfiltered")
        self.assertIn("person = Ant", describe_filters({"human_owner": "Ant"}))


class PdfPrimitives(unittest.TestCase):
    def test_wrapping_respects_the_measured_width(self):
        lines = wrap("the quick brown fox " * 20, size=10, max_width=200)
        self.assertTrue(all(text_width(line, 10) <= 200 for line in lines))
        self.assertGreater(len(lines), 1)

    def test_a_word_longer_than_the_line_is_split(self):
        lines = wrap("x" * 400, size=10, max_width=100)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(text_width(line, 10) <= 100 for line in lines))

    def test_content_paginates(self):
        doc = PdfDocument()
        for index in range(200):
            doc.text(f"line {index}")
        self.assertGreater(doc.to_bytes().count(b"/Type /Page "), 1)

    def test_parentheses_are_escaped(self):
        doc = PdfDocument()
        doc.text("a (tricky) string with a backslash \\ in it")
        self.assertIn(b"\\(tricky\\)", doc.to_bytes())


class PlainLanguage(ExportTestCase):
    def test_headline_names_the_system_and_target(self):
        line = headline(a_receipt())
        self.assertIn("Schwab", line)
        self.assertIn("1234-5678", line)

    def test_no_enum_values_leak_into_the_prose(self):
        receipt = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[], stop_reason="session_expired",
            stop_next_step="Log back in.")
        text = as_text(receipt)
        self.assertNotIn("stopped_no_change", text)
        self.assertIn("Stopped — nothing changed", text)

    def test_a_stop_always_tells_the_reader_what_to_do(self):
        receipt = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[], stop_reason="mfa_challenge",
            stop_next_step="Complete the MFA challenge yourself, then re-run.")
        titles = [title for title, _ in describe(receipt)]
        self.assertIn("Why it stopped", titles)
        self.assertIn("What to do next", titles)

    def test_the_cleanup_lane_says_what_was_left_changed(self):
        receipt = a_receipt(
            outcome=STOPPED_CLEANUP_REQUIRED, evidence=[],
            stop_reason="session_expired", stop_next_step="Log back in.",
            cleanup_instruction="A document was uploaded but not renamed.")
        self.assertIn("What was left changed", [t for t, _ in describe(receipt)])

    def test_a_proposal_is_shown_as_a_diff(self):
        rows = diff_rows({"filename": "scan_0041.pdf"},
                         {"filename": "2026-08 Schwab Statement.pdf"})
        self.assertEqual(rows, [("filename", "scan_0041.pdf", "2026-08 Schwab Statement.pdf")])

    def test_a_diff_shows_added_and_removed_fields(self):
        rows = dict((f, (b, a)) for f, b, a in diff_rows({"a": 1}, {"b": 2}))
        self.assertEqual(rows["a"], ("1", "—"))
        self.assertEqual(rows["b"], ("—", "2"))

    def test_missing_evidence_is_said_out_loud(self):
        receipt = a_receipt(
            outcome=STOPPED_NO_CHANGE, evidence=[], stop_reason="timeout",
            stop_next_step="Retry.")
        body = dict(describe(receipt))["Evidence"]
        self.assertIn("not proof of anything", body)

    def test_an_approval_names_the_person(self):
        receipt = a_receipt(
            action_type=APPROVE, approver="Ant",
            approval_timestamp="2026-09-04T10:42:00+00:00",
            references_receipt_id="proposal-1")
        self.assertIn("Ant approved this", dict(describe(receipt))["Approval"])


if __name__ == "__main__":
    unittest.main()
