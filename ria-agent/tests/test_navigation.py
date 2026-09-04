"""Session, guardrails, and navigation (Steps 18-20)."""

import tempfile
import unittest
from pathlib import Path

from ria_agent import session, stops
from ria_agent.browser import (
    Action, CLICK, DOWNLOAD, Element, FakePortal, FakePortalConfig, LINK,
    PageObservation, Statement,
)
from ria_agent.guardrails import Guardrails, Violation, is_forbidden_element
from ria_agent.navigator import (
    Navigator, Policy, RetrievalGoal, StatementRetrievalPolicy,
)

STATEMENTS = [
    Statement("1234-5678", "2026-08", "Helen Barrow"),
    Statement("1234-5678", "2026-07", "Helen Barrow"),
    Statement("9983-3570", "2026-08", "Rosalind Whitcombe"),
]
DOMAIN = "portal.schwab.example"
GOAL = RetrievalGoal("1234-5678", "2026-08", "Helen Barrow")


def a_portal(**config) -> FakePortal:
    return FakePortal(STATEMENTS, FakePortalConfig(**config))


class SessionDetection(unittest.TestCase):
    def test_a_live_session_is_live(self):
        self.assertTrue(session.detect(a_portal()).live)

    def test_a_signed_out_portal_stops(self):
        state = session.detect(a_portal(authenticated=False))
        self.assertFalse(state.live)
        self.assertEqual(state.stop_reason, stops.NOT_LOGGED_IN)
        self.assertIn("Log into the custodian site", state.next_step)

    def test_an_mfa_challenge_stops_with_zero_retries(self):
        state = session.detect(a_portal(mfa_on_entry=True))
        self.assertEqual(state.stop_reason, stops.MFA_CHALLENGE)
        self.assertIn("never attempt MFA", state.next_step)

    def test_the_agent_yields_to_its_own_human(self):
        class Present(session.HumanPresence):
            def is_active(self):
                return True

        state = session.detect(a_portal(), Present())
        self.assertEqual(state.stop_reason, stops.HUMAN_ACTIVE)

    def test_every_session_stop_carries_a_next_step(self):
        for config in ({"authenticated": False}, {"mfa_on_entry": True}):
            with self.subTest(config=config):
                self.assertTrue(session.detect(a_portal(**config)).next_step)


class ForbiddenControls(unittest.TestCase):
    def test_transaction_controls_are_refused_by_label(self):
        for label in ("Transfer funds", "Place a trade", "Wire request",
                      "Submit application", "Authorize transfer",
                      "Update banking details", "Change address",
                      "Withdraw funds", "Delete document", "Close account"):
            with self.subTest(label=label):
                self.assertIsNotNone(is_forbidden_element(Element("x", "button", label)))

    def test_a_redesign_that_renames_them_is_still_refused(self):
        for label in ("Move money", "Trade now", "Edit bank info", "Send money"):
            with self.subTest(label=label):
                self.assertIsNotNone(is_forbidden_element(Element("x", "button", label)))

    def test_a_control_is_refused_by_where_it_leads(self):
        innocent = Element("x", LINK, "Learn more", href="/transfer/new")
        self.assertIsNotNone(is_forbidden_element(innocent))

    def test_ordinary_controls_are_not_refused(self):
        for label in ("Statement 2026-08", "Account 1234-5678", "Documents",
                      "Back to accounts", "Download PDF"):
            with self.subTest(label=label):
                self.assertIsNone(is_forbidden_element(Element("x", LINK, label)))


class PageGuardrails(unittest.TestCase):
    def setUp(self):
        self.guardrails = Guardrails({DOMAIN})

    def test_an_ordinary_page_is_fine(self):
        self.assertIsNone(self.guardrails.check_page(a_portal().observe()))

    def test_navigating_off_the_allowlist_is_a_hard_stop(self):
        violation = self.guardrails.check_page(
            PageObservation("https://evil.example/x", "Anything"))
        self.assertEqual(violation.stop_reason, stops.OFF_ALLOWLIST)

    def test_a_subdomain_of_an_allowed_domain_is_allowed(self):
        self.assertIsNone(self.guardrails.check_page(
            PageObservation(f"https://client.{DOMAIN}/accounts", "Accounts")))

    def test_a_domain_that_merely_ends_similarly_is_refused(self):
        violation = self.guardrails.check_page(
            PageObservation(f"https://not{DOMAIN}/x", "x"))
        self.assertEqual(violation.stop_reason, stops.OFF_ALLOWLIST)

    def test_a_transaction_confirmation_page_is_a_hard_stop(self):
        portal = a_portal()
        portal._path = "/transfer"
        violation = self.guardrails.check_page(portal.observe())
        self.assertEqual(violation.stop_reason, stops.TRANSACTION_PAGE)
        self.assertIn("Nothing was submitted", violation.detail)

    def test_a_consent_wall_is_a_stop_not_a_click(self):
        violation = self.guardrails.check_page(a_portal(interstitial=True).observe())
        self.assertEqual(violation.stop_reason, stops.CONSENT_INTERSTITIAL)
        self.assertIn("never accepts anything", violation.detail)


class ActionGuardrails(unittest.TestCase):
    def setUp(self):
        self.guardrails = Guardrails({DOMAIN})
        self.observation = a_portal().observe()

    def test_a_permitted_action_passes(self):
        self.assertIsNone(self.guardrails.check_action(
            Action(CLICK, "acct-1234-5678"), self.observation))

    def test_a_forbidden_control_is_refused(self):
        violation = self.guardrails.check_action(Action(CLICK, "transfer"), self.observation)
        self.assertEqual(violation.stop_reason, stops.FORBIDDEN_ELEMENT)

    def test_an_action_on_a_control_that_is_not_there_is_refused(self):
        violation = self.guardrails.check_action(Action(CLICK, "ghost"), self.observation)
        self.assertEqual(violation.stop_reason, stops.ELEMENT_NOT_FOUND)

    def test_the_same_action_twice_on_the_same_page_stops(self):
        action = Action(CLICK, "acct-1234-5678")
        self.guardrails.note_action(action, self.observation)
        violation = self.guardrails.check_action(action, self.observation)
        self.assertEqual(violation.stop_reason, stops.REPEAT_ACTION)

    def test_the_click_budget_is_enforced(self):
        guardrails = Guardrails({DOMAIN}, click_budget=2)
        for _ in range(2):
            guardrails.note_action(Action(CLICK, "acct-1234-5678"), self.observation)
        violation = guardrails.check_action(Action(CLICK, "acct-9983-3570"), self.observation)
        self.assertEqual(violation.stop_reason, stops.CLICK_BUDGET_EXCEEDED)
        self.assertEqual(guardrails.budget_left, 0)


class GreedyPolicy(Policy):
    """A policy that wants to click the thing it must never click.

    This is the test that matters for F-19: the refusal has to live in the
    executor, above whatever the decision-maker wants. A model that is talked
    into pressing "Transfer funds" -- by a prompt injection, a bug, or a bad
    day -- must simply not be able to.
    """

    def __init__(self, element_id: str):
        self.element_id = element_id
        self.asked = 0

    def next_action(self, goal, observation, steps):
        self.asked += 1
        return Action(CLICK, self.element_id)


class NavigatorBehaviour(unittest.TestCase):
    def navigate(self, portal=None, policy=None, goal=GOAL, budget=40):
        directory = Path(tempfile.mkdtemp())
        portal = portal or a_portal()
        navigator = Navigator(
            portal, Guardrails({DOMAIN}, click_budget=budget),
            policy or StatementRetrievalPolicy(), evidence_dir=directory)
        return navigator.pursue(goal, destination=directory / "statement.pdf")

    def test_the_happy_path_reaches_the_artifact(self):
        result = self.navigate()
        self.assertTrue(result.reached)
        self.assertTrue(result.artifact.exists())
        self.assertTrue(result.artifact.read_bytes().startswith(b"%PDF"))

    def test_every_step_is_captured_with_a_screenshot(self):
        result = self.navigate()
        self.assertTrue(result.steps)
        for step in result.steps:
            self.assertTrue(step.screenshot.exists())
            self.assertTrue(step.signature)

    def test_the_executor_refuses_a_forbidden_click_the_policy_asked_for(self):
        policy = GreedyPolicy("transfer")
        result = self.navigate(policy=policy)
        self.assertFalse(result.reached)
        self.assertEqual(result.stop_reason, stops.FORBIDDEN_ELEMENT)
        self.assertEqual(policy.asked, 1)

    def test_the_executor_refuses_it_even_after_a_redesign_renames_it(self):
        result = self.navigate(portal=a_portal(redesigned=True),
                               policy=GreedyPolicy("transfer"))
        self.assertEqual(result.stop_reason, stops.FORBIDDEN_ELEMENT)

    def test_reaching_a_transaction_page_stops_before_anything_is_submitted(self):
        portal = a_portal()
        portal._path = "/transfer"
        result = self.navigate(portal=portal, policy=GreedyPolicy("authorize"))
        self.assertEqual(result.stop_reason, stops.TRANSACTION_PAGE)

    def test_a_consent_wall_stops_the_run(self):
        result = self.navigate(portal=a_portal(interstitial=True))
        self.assertEqual(result.stop_reason, stops.CONSENT_INTERSTITIAL)

    def test_a_session_that_dies_stops_with_the_right_reason(self):
        result = self.navigate(portal=a_portal(expire_after=0))
        self.assertEqual(result.stop_reason, stops.SESSION_EXPIRED)

    def test_a_session_dying_during_the_download_is_not_reported_as_a_missing_link(self):
        result = self.navigate(portal=a_portal(expire_after=1))
        self.assertEqual(result.stop_reason, stops.SESSION_EXPIRED)

    def test_an_mfa_challenge_mid_run_stops(self):
        portal = a_portal()
        portal._page("/dashboard")
        portal.config.mfa_on_entry = True
        portal._path = "/mfa"
        result = self.navigate(portal=portal)
        self.assertIn(result.stop_reason, (stops.MFA_CHALLENGE, stops.ELEMENT_NOT_FOUND))

    def test_the_click_budget_stops_a_wandering_run(self):
        result = self.navigate(policy=GreedyPolicy("acct-9983-3570"), budget=1)
        self.assertIn(result.stop_reason,
                      (stops.CLICK_BUDGET_EXCEEDED, stops.REPEAT_ACTION))

    def test_a_missing_period_stops_rather_than_taking_the_nearest(self):
        result = self.navigate(goal=RetrievalGoal("1234-5678", "2026-05"))
        self.assertFalse(result.reached)
        self.assertEqual(result.stop_reason, stops.ELEMENT_NOT_FOUND)

    def test_an_account_the_portal_does_not_have_stops(self):
        result = self.navigate(goal=RetrievalGoal("0000-0000", "2026-08"))
        self.assertFalse(result.reached)

    def test_a_lookalike_account_is_not_taken(self):
        result = self.navigate(portal=a_portal(lookalike_account="1234-56789"))
        self.assertTrue(result.reached)
        text = result.artifact.read_bytes()
        from ria_agent.pdf import extract_text
        from ria_agent.matching import contains_account
        self.assertTrue(contains_account(extract_text(text), "1234-5678"))
        self.assertFalse(contains_account(extract_text(text), "1234-56789"))

    def test_navigation_survives_a_redesign_because_it_is_not_scripted(self):
        result = self.navigate(portal=a_portal(redesigned=True))
        self.assertTrue(result.reached)

    def test_the_pages_visited_are_recorded(self):
        result = self.navigate()
        self.assertTrue(any("/dashboard" in url for url in result.pages_visited))
        self.assertTrue(any("/accounts/" in url for url in result.pages_visited))

    def test_every_stop_names_a_human_next_step(self):
        for portal in (a_portal(interstitial=True), a_portal(expire_after=0)):
            with self.subTest(portal=portal.config):
                result = self.navigate(portal=portal)
                self.assertTrue(result.next_step)


if __name__ == "__main__":
    unittest.main()
