"""Goal-directed navigation (Step 19).

Given a goal, the agent observes the page, decides one action, takes it, and
observes again. It does not follow a recorded click path, so a portal that moves
a link does not break it -- and a portal that moves the agent somewhere
unexpected produces an artifact that fails verification rather than a quiet
wrong answer.

Every observation and action pair is captured with a screenshot.

The policy is the decision-maker and is swappable: a rule-based one here, a
model-backed one later behind the same interface. Neither can widen what is
permitted, because the guardrails sit between the policy and the driver and are
consulted on every single action.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from . import stops
from .browser import (
    Action, BrowserDriver, CLICK, DOWNLOAD, DOWNLOAD_ACTION, ElementNotFound,
    MfaChallenge, PageObservation, SessionLost,
)
from .guardrails import Guardrails, Violation
from .matching import contains_account


@dataclass
class Step:
    """One observation, and what was decided from it."""

    index: int
    url: str
    title: str
    signature: str
    action: str | None = None
    screenshot: Path | None = None
    note: str = ""


@dataclass
class NavigationResult:
    reached: bool
    steps: list[Step] = field(default_factory=list)
    artifact: Path | None = None
    stop_reason: str | None = None
    detail: str = ""
    pages_visited: list[str] = field(default_factory=list)

    @property
    def next_step(self) -> str | None:
        return stops.next_step_for(self.stop_reason) if self.stop_reason else None


@dataclass(frozen=True)
class RetrievalGoal:
    """Retrieve the statement for one account, for one period."""

    account: str
    period: str
    holder: str = ""

    def __str__(self) -> str:
        return f"the {self.period} statement for account {self.account}"


class Policy(ABC):
    """Decides the next action from what is on screen."""

    @abstractmethod
    def next_action(
        self, goal, observation: PageObservation, steps: list[Step]
    ) -> Action | Violation | None:
        """One action, a Violation to stop on, or None when there is nothing left to try."""


#: Words that suggest a control leads toward filed documents. General to
#: custodian portals, not tuned to any one of them -- Step 39 says a new
#: custodian must not need its own script, so a portal that hides statements
#: behind a tab is the navigator's problem to solve, not the custodian's to be
#: special-cased for.
DOCUMENT_HINTS = (
    "statement", "document", "paperless", "activity", "history",
    "correspondence", "e-delivery", "edelivery", "archive",
)


class StatementRetrievalPolicy(Policy):
    """Find an account, then work toward its statement for a period.

    Four tiers, tried in order, each one more speculative than the last:

    1. a statement download that matches the account and period exactly;
    2. a control naming the account;
    3. a control naming the period or its year;
    4. a control that sounds like it leads to filed documents.

    Accounts are matched exactly (Constitution V). A portal listing both
    `1234-5678` and `1234-56789` offers the agent no way to pick the wrong one,
    and two controls matching the same account is an ambiguity it stops on.
    """

    def next_action(self, goal: RetrievalGoal, observation, steps):
        downloads = [
            element for element in observation.elements
            if element.kind == DOWNLOAD and self._is_wanted_statement(element, goal)
        ]
        if len(downloads) > 1:
            return Violation(
                stops.AMBIGUOUS_MATCH,
                f"{len(downloads)} documents on this page match {goal}",
            )
        if downloads:
            return Action(DOWNLOAD_ACTION, downloads[0].element_id)

        followed = self._followed(steps)

        named = [
            element for element in observation.elements
            if element.kind != DOWNLOAD and contains_account(element.label, goal.account)
        ]
        if len(named) > 1:
            return Violation(
                stops.AMBIGUOUS_MATCH,
                f"{len(named)} controls on this page name account {goal.account}",
            )
        action = self._first_unfollowed(named, followed)
        if action:
            return action

        year = goal.period[:4]
        by_period = [
            element for element in observation.elements
            if element.kind != DOWNLOAD
            and (goal.period in element.label or year in element.label)
        ]
        action = self._first_unfollowed(by_period, followed)
        if action:
            return action

        toward_documents = [
            element for element in observation.elements
            if element.kind != DOWNLOAD
            and any(hint in element.label.lower() for hint in DOCUMENT_HINTS)
        ]
        action = self._first_unfollowed(toward_documents, followed)
        if action:
            return action

        if any(element.kind == DOWNLOAD for element in observation.elements):
            return Violation(
                stops.ELEMENT_NOT_FOUND,
                f"this page lists statements but none of them is {goal.period}",
            )
        return None

    @staticmethod
    def _followed(steps: list[Step]) -> set[str]:
        return {
            step.action.split(" ", 1)[1]
            for step in steps
            if step.action and " " in step.action
        }

    @staticmethod
    def _first_unfollowed(elements, followed: set[str]) -> Action | None:
        for element in elements:
            if element.element_id not in followed:
                return Action(CLICK, element.element_id)
        return None

    @staticmethod
    def _is_wanted_statement(element, goal: RetrievalGoal) -> bool:
        if goal.period not in element.label and goal.period not in element.href:
            return False
        # Where the href carries "account|period", the account must agree
        # exactly as well -- a period alone is not identity.
        if "|" in element.href:
            return contains_account(element.href.split("|")[0], goal.account)
        return True


class Navigator:
    """Observe, decide, act, observe again -- with the guardrails in between."""

    def __init__(
        self,
        driver: BrowserDriver,
        guardrails: Guardrails,
        policy: Policy,
        *,
        evidence_dir: Path | None = None,
        max_steps: int = 40,
    ):
        self.driver = driver
        self.guardrails = guardrails
        self.policy = policy
        self.evidence_dir = Path(evidence_dir) if evidence_dir else None
        self.max_steps = max_steps

    def pursue(self, goal, destination: Path | None = None) -> NavigationResult:
        result = NavigationResult(reached=False)

        for index in range(self.max_steps):
            try:
                observation = self.driver.observe()
            except SessionLost as lost:
                return self._stop(result, stops.SESSION_EXPIRED, str(lost))
            except MfaChallenge as challenge:
                return self._stop(result, stops.MFA_CHALLENGE, str(challenge))

            step = self._record(result, index, observation)

            violation = self.guardrails.check_page(observation)
            if violation:
                step.note = violation.detail
                return self._stop(result, violation.stop_reason, violation.detail)

            decision = self.policy.next_action(goal, observation, result.steps)
            if decision is None:
                return self._stop(
                    result, stops.ELEMENT_NOT_FOUND,
                    f"nothing on this page leads to {goal}",
                )
            if isinstance(decision, Violation):
                step.note = decision.detail
                return self._stop(result, decision.stop_reason, decision.detail)

            violation = self.guardrails.check_action(decision, observation)
            if violation:
                step.note = violation.detail
                return self._stop(result, violation.stop_reason, violation.detail)

            step.action = str(decision)

            if decision.kind == DOWNLOAD_ACTION:
                if destination is None:
                    return self._stop(result, stops.VERIFICATION_FAILED,
                                      "there is nowhere to save the artifact")
                try:
                    result.artifact = self.driver.download(decision.element_id, destination)
                except SessionLost as lost:
                    # Nothing was written, so nothing needs cleaning up -- but
                    # the reason has to be the real one. "Element not found"
                    # would send the operator to look for a moved link when
                    # what they actually need to do is log back in.
                    return self._stop(result, stops.SESSION_EXPIRED, str(lost))
                except MfaChallenge as challenge:
                    return self._stop(result, stops.MFA_CHALLENGE, str(challenge))
                except ElementNotFound as missing:
                    return self._stop(result, stops.ELEMENT_NOT_FOUND, str(missing))
                self.guardrails.note_action(decision, observation)
                result.reached = True
                return result

            try:
                self.driver.act(decision)
            except SessionLost as lost:
                return self._stop(result, stops.SESSION_EXPIRED, str(lost))
            except MfaChallenge as challenge:
                return self._stop(result, stops.MFA_CHALLENGE, str(challenge))
            except ElementNotFound as missing:
                return self._stop(result, stops.ELEMENT_NOT_FOUND, str(missing))
            self.guardrails.note_action(decision, observation)

        return self._stop(
            result, stops.CLICK_BUDGET_EXCEEDED,
            f"the task ran to its limit of {self.max_steps} steps without finishing",
        )

    def _record(self, result: NavigationResult, index: int, observation) -> Step:
        step = Step(index=index, url=observation.url, title=observation.title,
                    signature=observation.signature)
        if self.evidence_dir is not None:
            step.screenshot = self.driver.screenshot(
                self.evidence_dir / f"step-{index:02d}.svg")
        result.steps.append(step)
        result.pages_visited.append(observation.url)
        return step

    @staticmethod
    def _stop(result: NavigationResult, reason: str, detail: str) -> NavigationResult:
        result.reached = False
        result.stop_reason = reason
        result.detail = detail
        return result
