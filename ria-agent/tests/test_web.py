"""The queue over HTTP (Steps 7-10), driven the way a person drives it."""

import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ria_agent.queue import Queue
from ria_agent.receipts import (
    Evidence, PENDING_APPROVAL, PROPOSE, READ, Receipt,
    STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED,
)
from ria_agent.seeded_errors import FAULTS, SeedRegistry, SeededErrorInjector
from ria_agent.startup import Application
from ria_agent.web import build_server


def proposal(**overrides) -> Receipt:
    base = dict(
        human_owner="Ant", role="para_planner", crm_task_id="RT-1",
        workflow_id="document_filing", step_id="propose_filing",
        system_touched="redtail", action_type=PROPOSE,
        target_identifier="Barrow / 1234-5678", outcome=PENDING_APPROVAL,
        model_version="claude-x-1",
        before_state={"filename": "scan_0041.pdf", "folder": "Unfiled"},
        after_state={"filename": "2026-08 Statement.pdf", "folder": "Barrow"},
        evidence=[Evidence("file_hash", "9f2a"),
                  Evidence("extracted_value", "1234-5678", "pdf:page 1")],
    )
    base.update(overrides)
    return Receipt(**base)


class WebTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.app = Application(self._dir.name, model_version="claude-x-1",
                               operator="Ant", role="para_planner")
        self.addCleanup(self.app.close)
        self.registry = SeedRegistry(Path(self.app.storage_dir) / "seeds.jsonl")
        self.queue = Queue(self.app.log, model_version="claude-x-1",
                           seed_registry=self.registry)
        self.server = build_server(self.app, self.queue, port=0)
        self.addCleanup(self.server.server_close)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as response:
            return response.status, response.read().decode()

    def post(self, path, fields):
        request = urllib.request.Request(
            self.base + path, data=urllib.parse.urlencode(fields).encode())
        with urllib.request.urlopen(request) as response:
            return response.status, response.read().decode()

    def token_for(self, receipt_id):
        page = self.get(f"/item/{receipt_id}")[1]
        found = re.search(r"name='token' value='([^']+)'", page)
        return found.group(1) if found else None


class Binding(unittest.TestCase):
    def test_it_refuses_to_bind_beyond_loopback(self):
        with self.assertRaises(ValueError):
            build_server(None, None, host="0.0.0.0", port=0)


class QueuePage(WebTestCase):
    def test_all_four_lanes_render(self):
        page = self.get("/")[1]
        for name in ("Stopped — needs cleanup", "Ready for approval",
                     "Stopped — nothing changed", "Done &amp; verified"):
            self.assertIn(name, page)

    def test_lane_counts_are_shown(self):
        self.app.log.append(proposal())
        page = self.get("/")[1]
        self.assertIn("Ready for approval <span class='count'>1</span>", page)

    def test_the_cap_message_appears_when_items_are_hidden(self):
        for index in range(8):
            self.app.log.append(proposal(crm_task_id=f"RT-{index}"))
        self.queue.approval_cap = 3
        page = self.get("/")[1]
        self.assertIn("5 more waiting, not shown", page)

    def test_an_unknown_page_is_a_404(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get("/nope")
        self.assertEqual(caught.exception.code, 404)


class ItemPage(WebTestCase):
    def test_the_proposal_is_shown_as_a_diff(self):
        receipt = self.app.log.append(proposal())
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertIn("<th>Now</th><th>Proposed</th>", page)
        self.assertIn("scan_0041.pdf", page)
        self.assertIn("2026-08 Statement.pdf", page)

    def test_evidence_is_shown_with_its_source(self):
        receipt = self.app.log.append(proposal())
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertIn("pdf:page 1", page)
        self.assertIn("9f2a", page)

    def test_missing_evidence_is_called_out(self):
        receipt = self.app.log.append(proposal(
            outcome=STOPPED_NO_CHANGE, action_type=READ, evidence=[],
            before_state=None, after_state=None,
            stop_reason="timeout", stop_next_step="Retry."))
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertIn("not proof of anything", page)

    def test_a_stop_shows_its_reason_and_next_step(self):
        receipt = self.app.log.append(proposal(
            outcome=STOPPED_NO_CHANGE, action_type=READ, evidence=[],
            before_state=None, after_state=None,
            stop_reason="mfa_challenge",
            stop_next_step="Complete the MFA challenge yourself, then re-run."))
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertIn("Why it stopped", page)
        self.assertIn("Complete the MFA challenge yourself", page)
        self.assertNotIn("class='approve'", page)

    def test_the_cleanup_lane_shows_what_was_left_changed(self):
        receipt = self.app.log.append(proposal(
            outcome=STOPPED_CLEANUP_REQUIRED, action_type=READ, evidence=[],
            before_state=None, after_state=None,
            stop_reason="session_expired", stop_next_step="Log back in.",
            cleanup_instruction="A document was uploaded but not renamed."))
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertIn("This one needs you", page)
        self.assertIn("uploaded but not renamed", page)

    def test_every_rejection_reason_is_offered(self):
        receipt = self.app.log.append(proposal())
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertEqual(page.count("<option"), 8)

    def test_html_in_a_field_is_escaped(self):
        receipt = self.app.log.append(proposal(
            target_identifier="<script>alert(1)</script>"))
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)


class Deciding(WebTestCase):
    def test_approving_records_a_decision(self):
        receipt = self.app.log.append(proposal())
        status, page = self.post(f"/item/{receipt.receipt_id}/approve",
                                 {"token": self.token_for(receipt.receipt_id)})
        self.assertEqual(status, 200)
        self.assertIn("Ant approved this", page)
        self.assertEqual(self.app.log.count(), 2)

    def test_rejecting_records_the_reason_and_note(self):
        receipt = self.app.log.append(proposal())
        _, page = self.post(f"/item/{receipt.receipt_id}/reject", {
            "token": self.token_for(receipt.receipt_id),
            "reason": "wrong_target", "note": "Barrow trust, not personal"})
        self.assertIn("Ant rejected this", page)
        self.assertIn("Wrong client or account", page)
        self.assertIn("Barrow trust, not personal", page)

    def test_a_decided_item_offers_no_further_decision(self):
        receipt = self.app.log.append(proposal())
        self.post(f"/item/{receipt.receipt_id}/approve",
                  {"token": self.token_for(receipt.receipt_id)})
        self.assertIsNone(self.token_for(receipt.receipt_id))

    def test_deciding_twice_is_refused_and_explained(self):
        receipt = self.app.log.append(proposal())
        token = self.token_for(receipt.receipt_id)
        self.post(f"/item/{receipt.receipt_id}/approve", {"token": token})
        _, page = self.post(f"/item/{receipt.receipt_id}/approve", {"token": token})
        self.assertIn("already approved", page)
        self.assertEqual(self.app.log.count(), 2)

    def test_a_reason_outside_the_short_list_is_refused(self):
        receipt = self.app.log.append(proposal())
        _, page = self.post(f"/item/{receipt.receipt_id}/reject", {
            "token": self.token_for(receipt.receipt_id), "reason": "just no"})
        self.assertIn("not one of the accepted rejection reasons", page)
        self.assertEqual(self.app.log.count(), 1)

    def test_a_decision_without_the_form_token_is_refused(self):
        receipt = self.app.log.append(proposal())
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post(f"/item/{receipt.receipt_id}/approve", {"token": "wrong"})
        self.assertEqual(caught.exception.code, 403)
        self.assertEqual(self.app.log.count(), 1)

    def test_a_cross_origin_decision_is_refused(self):
        receipt = self.app.log.append(proposal())
        request = urllib.request.Request(
            f"{self.base}/item/{receipt.receipt_id}/approve",
            data=urllib.parse.urlencode(
                {"token": self.token_for(receipt.receipt_id)}).encode(),
            headers={"Origin": "https://evil.example"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 403)
        self.assertEqual(self.app.log.count(), 1)


class SeededReveal(WebTestCase):
    def _seeded(self) -> Receipt:
        injector = SeededErrorInjector(self.registry, enabled=True, rate=1.0)
        seeded = injector._apply(proposal(), FAULTS["wrong_account"])
        self.registry.record(seeded.receipt_id, seeded.workflow_id,
                             FAULTS["wrong_account"])
        return self.app.log.append(seeded)

    def test_catching_a_seeded_item_is_revealed(self):
        receipt = self._seeded()
        _, page = self.post(f"/item/{receipt.receipt_id}/reject", {
            "token": self.token_for(receipt.receipt_id), "reason": "wrong_target"})
        self.assertIn("seeded check", page)
        self.assertIn("You caught it", page)
        self.assertEqual(self.registry.catch_rate().rate, 1.0)

    def test_missing_a_seeded_item_is_revealed_too(self):
        receipt = self._seeded()
        _, page = self.post(f"/item/{receipt.receipt_id}/approve",
                            {"token": self.token_for(receipt.receipt_id)})
        self.assertIn("seeded check", page)
        self.assertIn("got through", page)
        self.assertEqual(self.registry.catch_rate().rate, 0.0)

    def test_an_ordinary_item_never_claims_to_be_seeded(self):
        receipt = self.app.log.append(proposal())
        _, page = self.post(f"/item/{receipt.receipt_id}/approve",
                            {"token": self.token_for(receipt.receipt_id)})
        self.assertNotIn("seeded check", page)

    def test_a_seeded_item_is_not_flagged_before_the_decision(self):
        receipt = self._seeded()
        page = self.get(f"/item/{receipt.receipt_id}")[1]
        self.assertNotIn("seeded", page.lower())


class EvidenceAndExports(WebTestCase):
    def test_an_image_is_served(self):
        (self.app.evidence_dir / "shot.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"/>')
        status, body = self.get("/evidence/shot.svg")
        self.assertEqual(status, 200)
        self.assertIn("svg", body)

    def test_traversal_out_of_the_evidence_directory_is_refused(self):
        for probe in ("..%2f..%2flog%2freceipts.jsonl", "%2Fetc%2Fpasswd",
                      "../../CONSTITUTION.md"):
            with self.subTest(probe=probe):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    self.get("/evidence/" + probe)
                self.assertIn(caught.exception.code, (403, 404))

    def test_a_non_image_in_the_evidence_directory_is_not_served(self):
        (self.app.evidence_dir / "notes.txt").write_text("secret")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get("/evidence/notes.txt")
        self.assertEqual(caught.exception.code, 403)

    def test_the_csv_export_downloads(self):
        self.app.log.append(proposal())
        status, body = self.get("/export.csv")
        self.assertEqual(status, 200)
        self.assertIn("receipt_id,", body)

    def test_the_pdf_export_downloads(self):
        self.app.log.append(proposal())
        with urllib.request.urlopen(self.base + "/export.pdf") as response:
            blob = response.read()
        self.assertTrue(blob.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
