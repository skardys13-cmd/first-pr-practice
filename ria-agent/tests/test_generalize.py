"""Custodians, the packet, client service, health, and install (Steps 39-45)."""

import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from ria_agent import health
from ria_agent.browser import FakePortal, FakePortalConfig, Statement
from ria_agent.client_service import (
    DECLINED, DocumentRequest, ESignChase, Envelope, FixtureESign, SENT, SIGNED, VIEWED,
)
from ria_agent.custodians import CUSTODIANS, CustodianProfile, measure, scaling_report
from ria_agent.guardrails import Guardrails
from ria_agent.install import check_python, check_version, diagnostic_bundle, doctor
from ria_agent.linkage import AccountRecord
from ria_agent.log_store import LogStore
from ria_agent.navigator import Navigator, RetrievalGoal, StatementRetrievalPolicy
from ria_agent.packet import MeetingPrepPacket, PacketRequest
from ria_agent.pdf import extract_text
from ria_agent.receipts import PENDING_APPROVAL, VERIFIED
from ria_agent.reconcile import Balance, money
from ria_agent.retrieval import StatementRetrieval
from ria_agent.verification import verify_statement

WHEN = "2026-08-31T21:00:00+00:00"


def statements(account="1234-5678", holder="Helen Barrow"):
    return [Statement(account, f"2026-{month:02d}", holder) for month in range(1, 9)]


def a_retrieval(log, config=None, directory=None):
    directory = directory or Path(tempfile.mkdtemp())
    return StatementRetrieval(
        FakePortal(statements() + [Statement("1234-5679", "2026-08", "Helen Barrow")],
                   config or FakePortalConfig()),
        log, operator="Ant", role="para_planner", model_version="claude-x-1",
        allowed_domains={"portal.schwab.example"}, evidence_dir=directory / "evidence")


class OneNavigatorManyPortals(unittest.TestCase):
    """Step 39: a second custodian must not need a script of its own."""

    def retrieve(self, layout, period="2026-08", redesigned=False):
        directory = Path(tempfile.mkdtemp())
        host = f"portal.{layout}.example"
        portal = FakePortal(statements(), FakePortalConfig(
            host=host, layout=layout, redesigned=redesigned))
        navigator = Navigator(portal, Guardrails({host}), StatementRetrievalPolicy(),
                              evidence_dir=directory)
        return navigator.pursue(RetrievalGoal("1234-5678", period, "Helen Barrow"),
                                destination=directory / "statement.pdf")

    def test_every_portal_shape_works_with_the_same_policy(self):
        for layout in ("flat", "tabbed", "year_first", "dashboard_direct"):
            with self.subTest(layout=layout):
                result = self.retrieve(layout)
                self.assertTrue(result.reached, result.detail)
                self.assertTrue(verify_statement(
                    result.artifact, account="1234-5678", period="2026-08",
                    holder="Helen Barrow").passed)

    def test_every_shape_still_works_after_a_redesign(self):
        for layout in ("flat", "tabbed", "year_first", "dashboard_direct"):
            with self.subTest(layout=layout):
                self.assertTrue(self.retrieve(layout, redesigned=True).reached)

    def test_a_statement_behind_a_year_page_is_still_found(self):
        directory = Path(tempfile.mkdtemp())
        portal = FakePortal(
            statements() + [Statement("1234-5678", "2025-12", "Helen Barrow")],
            FakePortalConfig(host="portal.y.example", layout="year_first"))
        navigator = Navigator(portal, Guardrails({"portal.y.example"}),
                              StatementRetrievalPolicy(), evidence_dir=directory)
        result = navigator.pursue(RetrievalGoal("1234-5678", "2025-12", "Helen Barrow"),
                                  destination=directory / "s.pdf")
        self.assertTrue(result.reached)

    def test_the_forbidden_control_is_still_refused_in_every_shape(self):
        from ria_agent.guardrails import is_forbidden_element
        for layout in ("flat", "tabbed", "year_first"):
            with self.subTest(layout=layout):
                portal = FakePortal(statements(), FakePortalConfig(layout=layout))
                page = portal.act.__self__._page(f"/accounts/1234-5678")
                banking = [e for e in page.elements if "bank" in e.label.lower()]
                self.assertTrue(banking)
                self.assertIsNotNone(is_forbidden_element(banking[0]))


class ScalingCost(unittest.TestCase):
    """Step 40: track the number, and be honest about what it means."""

    def test_every_configured_custodian_retrieves_and_verifies(self):
        for name, profile in CUSTODIANS.items():
            with self.subTest(custodian=name):
                result = measure(profile)
                self.assertTrue(result.verified, result.detail)

    def test_no_custodian_currently_needs_tuning(self):
        self.assertEqual(sum(p.tuning_cost for p in CUSTODIANS.values()), 0)

    def test_an_adjustment_is_counted_as_scaling_cost(self):
        profile = CustodianProfile("awkward", frozenset({"portal.awkward.example"}),
                                   adjustments={"statement_label": "labelled 'Download' only"})
        self.assertEqual(profile.tuning_cost, 1)

    def test_the_report_states_what_the_number_does_not_prove(self):
        report = scaling_report()
        self.assertIn("weak evidence", report)
        self.assertIn("nobody here designed", report)


class TheHome(unittest.TestCase):
    def test_chained_retrievals_each_start_from_a_known_page(self):
        directory = Path(tempfile.mkdtemp())
        log = LogStore(directory / "log")
        self.addCleanup(log.close)
        retrieval = a_retrieval(log, directory=directory)
        first = retrieval.run("RT-1", RetrievalGoal("1234-5678", "2026-08", "Helen Barrow"))
        second = retrieval.run("RT-2", RetrievalGoal("1234-5679", "2026-08", "Helen Barrow"))
        self.assertTrue(first.succeeded)
        self.assertTrue(second.succeeded)

    def test_home_does_not_resurrect_a_dead_session(self):
        directory = Path(tempfile.mkdtemp())
        log = LogStore(directory / "log")
        self.addCleanup(log.close)
        retrieval = a_retrieval(log, FakePortalConfig(authenticated=False), directory)
        outcome = retrieval.run("RT-1", RetrievalGoal("1234-5678", "2026-08"))
        self.assertFalse(outcome.succeeded)
        self.assertEqual(outcome.receipt.stop_reason, "not_logged_in")


class ESign(unittest.TestCase):
    def setUp(self):
        directory = Path(tempfile.mkdtemp())
        self.log = LogStore(directory / "log")
        self.addCleanup(self.log.close)
        self.envelopes = [
            Envelope("E-1", "Whitcombe", "Rosalind Whitcombe", "Application", SENT, "2026-08-28"),
            Envelope("E-2", "Barrow", "Helen Barrow", "Beneficiary form", SIGNED, "2026-08-20"),
            Envelope("E-3", "Okonkwo", "Ada Okonkwo", "Fee schedule", VIEWED, "2026-09-03"),
            Envelope("E-4", "Ferreira", "Luis Ferreira", "ACH form", DECLINED, "2026-08-01"),
        ]
        self.chase = ESignChase(FixtureESign(self.envelopes), self.log,
                                operator="Bea", role="client_service",
                                model_version="claude-x-1")

    def test_only_stale_outstanding_envelopes_are_chased(self):
        receipts = self.chase.run("RT-4541", today=date(2026, 9, 4))
        self.assertEqual([r.target_identifier for r in receipts],
                         ["Whitcombe / E-1"])

    def test_a_signed_envelope_is_left_alone(self):
        receipts = self.chase.run("RT-1", household="Barrow", today=date(2026, 9, 4))
        self.assertEqual(receipts, [])

    def test_a_declined_envelope_is_not_chased(self):
        receipts = self.chase.run("RT-1", household="Ferreira", today=date(2026, 9, 4))
        self.assertEqual(receipts, [])

    def test_the_draft_waits_for_a_person_and_is_not_sent(self):
        receipt = self.chase.run("RT-1", today=date(2026, 9, 4))[0]
        self.assertEqual(receipt.outcome, PENDING_APPROVAL)
        self.assertIn("message", receipt.after_state)
        self.assertEqual(receipt.errors(), [])

    def test_the_draft_names_the_recipient_and_the_delay(self):
        receipt = self.chase.run("RT-1", today=date(2026, 9, 4))[0]
        self.assertIn("Rosalind Whitcombe", receipt.after_state["message"])
        self.assertEqual(receipt.before_state["days outstanding"], "7")

    def test_the_reader_has_no_send_method(self):
        surface = {name for name in dir(FixtureESign) if not name.startswith("_")}
        self.assertEqual(surface & {"send", "remind", "resend", "void"}, set())


class Requests(unittest.TestCase):
    def setUp(self):
        directory = Path(tempfile.mkdtemp())
        self.log = LogStore(directory / "log")
        self.addCleanup(self.log.close)
        self.request = DocumentRequest(
            a_retrieval(self.log, directory=directory), self.log,
            operator="Bea", role="client_service", model_version="claude-x-1")

    def test_a_full_run_of_statements_is_retrieved(self):
        result = self.request.run("RT-4542", "1234-5678",
                                  [f"2026-{m:02d}" for m in range(1, 9)], "Helen Barrow")
        self.assertTrue(result.complete)
        self.assertEqual(len(result.retrieved), 8)

    def test_a_gap_is_reported_rather_than_glossed_over(self):
        result = self.request.run("RT-1", "1234-5678", ["2026-08", "2026-11"], "Helen Barrow")
        self.assertFalse(result.complete)
        self.assertEqual([period for period, _ in result.stopped], ["2026-11"])
        summary = result.receipts[-1]
        self.assertIn("worse than none", summary.stop_next_step)


class Packets(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.log = LogStore(self.directory / "log")
        self.addCleanup(self.log.close)
        self.packet = MeetingPrepPacket(
            a_retrieval(self.log, directory=self.directory), self.log,
            operator="Ant", role="para_planner", model_version="claude-x-1",
            output_dir=self.directory / "packets")

    def balance(self, system, account, value, **components):
        return Balance(system, account, money(value), WHEN, f"{system}:/pos", components)

    def clean_request(self):
        return PacketRequest(
            "RT-4501", "Barrow", "2026-08", ["1234-5678", "1234-5679"],
            holder="Helen Barrow",
            balances={"1234-5678": [self.balance("schwab", "1234-5678", "414118.42"),
                                    self.balance("redtail", "1234-5678", "414118.42")]},
            linkage_records=[AccountRecord("schwab", "1234-5678", "Barrow"),
                             AccountRecord("redtail", "1234-5678", "Barrow")])

    def test_a_clean_packet_is_complete(self):
        packet = self.packet.build(self.clean_request())
        self.assertEqual(packet.retrieved, ["1234-5678", "1234-5679"])
        self.assertEqual(packet.missing, [])
        self.assertEqual(packet.exceptions, [])
        self.assertTrue(packet.complete)

    def test_the_packet_is_a_readable_pdf(self):
        packet = self.packet.build(self.clean_request())
        self.assertTrue(packet.path.read_bytes().startswith(b"%PDF"))
        text = extract_text(packet.path.read_bytes())
        self.assertIn("Barrow", text)
        self.assertIn("Statements", text)

    def test_the_packet_says_it_contains_no_advice(self):
        packet = self.packet.build(self.clean_request())
        text = extract_text(packet.path.read_bytes())
        self.assertIn("no advice", text)
        self.assertIn("no view on", text)

    def test_a_missing_statement_is_carried_through_to_the_packet(self):
        request = self.clean_request()
        request.accounts.append("9999-0000")
        packet = self.packet.build(request)
        self.assertEqual([a for a, _ in packet.missing], ["9999-0000"])
        self.assertFalse(packet.complete)
        self.assertIn("9999-0000", extract_text(packet.path.read_bytes()))

    def test_a_balance_break_is_carried_through_to_the_packet(self):
        request = self.clean_request()
        request.balances["1234-5679"] = [
            self.balance("schwab", "1234-5679", "88000.00"),
            self.balance("orion", "1234-5679", "86181.58", pending_trades="1818.42")]
        packet = self.packet.build(request)
        self.assertEqual(len(packet.exceptions), 1)
        self.assertFalse(packet.complete)

    def test_a_linkage_problem_is_carried_through_to_the_packet(self):
        request = self.clean_request()
        request.linkage_records = [AccountRecord("schwab", "1234-5678", "Barrow")]
        packet = self.packet.build(request)
        self.assertFalse(packet.linkage.clean)
        self.assertFalse(packet.complete)

    def test_the_packet_waits_for_a_person(self):
        packet = self.packet.build(self.clean_request())
        self.assertEqual(packet.receipt.outcome, PENDING_APPROVAL)
        self.assertEqual(packet.receipt.errors(), [])


class Health(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.log = LogStore(self.directory / "log")
        self.addCleanup(self.log.close)
        retrieval = a_retrieval(self.log, directory=self.directory)
        for index in range(3):
            retrieval.run(f"RT-{index}",
                          RetrievalGoal("1234-5678", f"2026-0{index + 1}", "Helen Barrow"))
        retrieval.run("RT-X", RetrievalGoal("1234-5678", "2026-11", "Helen Barrow"))

    def test_it_counts_what_happened(self):
        report = health.build(self.log)
        self.assertEqual(report.handled, 4)
        line = report.lines["statement_retrieval"]
        self.assertEqual(line.awaiting, 3)
        self.assertEqual(line.stopped, 1)

    def test_it_groups_stops_by_reason(self):
        report = health.build(self.log)
        self.assertIn("element_not_found", report.stops)

    def test_without_a_baseline_it_refuses_to_claim_time_saved(self):
        report = health.build(self.log)
        self.assertIsNone(report.hours_returned)
        self.assertIn("statement_retrieval", report.missing_baselines)
        self.assertIn("NOT measurable", report.summary())

    def test_with_a_baseline_it_reports_time_returned(self):
        baselines = health.Baselines({"statement_retrieval": 6.0})
        report = health.build(self.log, baselines)
        self.assertIsNotNone(report.hours_returned)
        self.assertEqual(report.missing_baselines, [])

    def test_baselines_round_trip_through_a_file(self):
        path = self.directory / "baselines.json"
        health.Baselines({"statement_retrieval": 6.0}).save(path)
        self.assertEqual(health.Baselines.load(path).get("statement_retrieval"), 6.0)

    def test_a_missing_baselines_file_is_not_an_error(self):
        self.assertEqual(health.Baselines.load(self.directory / "nope.json").minutes, {})

    def test_it_reports_zero_unapproved_writes(self):
        self.assertIn("Unapproved writes: 0", health.build(self.log).summary())

    def test_only_the_window_asked_for_is_counted(self):
        report = health.build(self.log, days=7,
                              now=datetime.now().astimezone() + timedelta(days=30))
        self.assertEqual(report.handled, 0)


class Install(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())

    def test_python_is_new_enough(self):
        self.assertTrue(check_python().ok)

    def test_no_pinned_version_is_fine(self):
        self.assertTrue(check_version(None).ok)

    def test_an_install_that_is_behind_refuses(self):
        check = check_version("9.0.0")
        self.assertFalse(check.ok)
        self.assertIn("will not run", check.detail)

    def test_an_install_that_is_ahead_is_fine(self):
        self.assertTrue(check_version("0.0.1").ok)

    def test_a_clean_install_passes_the_doctor(self):
        self.assertTrue(all(check.ok for check in doctor(self.directory)))

    def test_the_doctor_catches_a_stored_credential(self):
        (self.directory / "cookies.json").write_text('{"sessionid": "abc"}')
        self.assertFalse(all(check.ok for check in doctor(self.directory)))

    def test_the_doctor_catches_an_install_that_is_behind(self):
        self.assertFalse(all(check.ok for check in doctor(self.directory, "9.0.0")))

    def test_the_bundle_carries_versions_and_counts(self):
        log = LogStore(self.directory / "log")
        retrieval = a_retrieval(log, directory=self.directory)
        retrieval.run("RT-1", RetrievalGoal("1234-5678", "2026-08", "Helen Barrow"))
        log.close()
        path = diagnostic_bundle(self.directory, self.directory / "bundle.json")
        data = json.loads(path.read_text())
        self.assertIn("agent_version", data)
        self.assertEqual(data["log"]["receipts"], 1)
        self.assertIn("statement_retrieval", data["log"]["workflows"])

    def test_the_bundle_carries_no_client_data(self):
        log = LogStore(self.directory / "log")
        retrieval = a_retrieval(log, directory=self.directory)
        retrieval.run("RT-1", RetrievalGoal("1234-5678", "2026-08", "Helen Barrow"))
        log.close()
        blob = diagnostic_bundle(self.directory, self.directory / "b.json").read_text()
        for secret in ("Helen", "Barrow", "1234-5678", "RT-1", "Ant"):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, blob)


if __name__ == "__main__":
    unittest.main()
