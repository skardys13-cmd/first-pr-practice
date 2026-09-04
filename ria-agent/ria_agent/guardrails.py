"""Guardrails (Step 20, Constitution VIII, F-18 to F-21).

These are refusals by the executor, not preferences expressed to a model. The
navigator asks before every action and the answer is binding, so a model that
decides it would like to click "Authorize transfer" simply does not get to.

Defence is layered on purpose, because the top layer is the fragile one:

1. **Label patterns** catch transaction-capable controls by what they are
   called. This misses a redesign that renames "Transfer funds" to "Move
   money", which is exactly F-16.
2. **Destination checks** catch a control by where it leads, whatever it is
   called.
3. **Page checks** catch a transaction confirmation page by what it says, even
   if the agent reached it by a control that slipped both earlier layers.

By layer 3 something has already been clicked, which is why nothing is ever
submitted: reaching a confirmation page is a hard stop, and the agent has no
action available that would confirm anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from . import stops
from .browser import Action, Element, PageObservation

#: Controls the agent may never interact with, in any mode, read-only included.
FORBIDDEN_LABEL_PATTERNS = [
    re.compile(r"(?i)\btransfer\b"),
    re.compile(r"(?i)\bwire\b"),
    re.compile(r"(?i)\btrade\b|\btrading\b"),
    re.compile(r"(?i)\b(?:buy|sell)\b"),
    re.compile(r"(?i)\bjournal\b"),
    re.compile(r"(?i)\bmove money\b|\bsend money\b|\bmove funds\b"),
    re.compile(r"(?i)\bauthori[sz]e\b"),
    re.compile(r"(?i)\bsubmit\b"),
    re.compile(r"(?i)\bdelete\b|\bremove\b"),
    re.compile(r"(?i)\bclose account\b"),
    re.compile(r"(?i)\b(?:change|update|edit)\b.{0,20}\baddress\b"),
    re.compile(r"(?i)\bbank(?:ing)?\b.{0,20}\b(?:details?|info(?:rmation)?|account)\b"),
    re.compile(r"(?i)\b(?:edit|update|change)\b.{0,12}\bbank\b"),
    re.compile(r"(?i)\bdirect deposit\b"),
    re.compile(r"(?i)\bwithdraw\w*\b"),
    re.compile(r"(?i)\bdistribution request\b"),
    re.compile(r"(?i)\bpay(?:ment)?\b.{0,12}\b(?:send|make|new)\b"),
]

#: Paths that lead somewhere the agent must not be, whatever the link said.
FORBIDDEN_PATH_PATTERNS = [
    re.compile(r"(?i)/(?:transfer|wire|trade|trading|journal|withdraw|payment|move-money)\b"),
    re.compile(r"(?i)/(?:banking|bank-details|direct-deposit)\b"),
]

#: Text that means this page can move money if something is clicked.
TRANSACTION_PAGE_PATTERNS = [
    re.compile(r"(?i)\bauthori[sz]e this transaction\b"),
    re.compile(r"(?i)\bcannot be reversed\b"),
    re.compile(r"(?i)\bconfirm (?:this )?(?:transfer|trade|withdrawal|wire|payment)\b"),
    re.compile(r"(?i)\bfunds will be (?:sent|transferred|debited)\b"),
    re.compile(r"(?i)\btrade confirmation\b"),
    re.compile(r"(?i)\byou are about to (?:transfer|send|trade|withdraw)\b"),
]

#: Consent, terms, and survey walls. The agent never accepts anything for the
#: firm (F-18), so these are a stop and not a click.
CONSENT_PATTERNS = [
    re.compile(r"(?i)\baccept\b.{0,24}\b(?:terms|conditions|policy|agreement)\b"),
    re.compile(r"(?i)\bterms of (?:service|use)\b"),
    re.compile(r"(?i)\bplease review and accept\b"),
    re.compile(r"(?i)\bi agree\b"),
    re.compile(r"(?i)\b(?:take|complete)\b.{0,20}\bsurvey\b"),
    re.compile(r"(?i)\bconsent\b"),
]

DEFAULT_CLICK_BUDGET = 40


@dataclass(frozen=True)
class Violation:
    stop_reason: str
    detail: str

    def __str__(self) -> str:
        return self.detail


def _matches(patterns, text: str) -> str | None:
    for pattern in patterns:
        found = pattern.search(text or "")
        if found:
            return found.group(0)
    return None


def is_forbidden_element(element: Element) -> str | None:
    """Why this control may never be touched, or None."""
    hit = _matches(FORBIDDEN_LABEL_PATTERNS, element.label)
    if hit:
        return f"its label contains {hit!r}"
    hit = _matches(FORBIDDEN_PATH_PATTERNS, element.href)
    if hit:
        return f"it leads to {hit!r}"
    return None


class Guardrails:
    """Asked before every action. The answer is binding."""

    def __init__(
        self,
        allowed_domains: set[str] | list[str],
        *,
        click_budget: int = DEFAULT_CLICK_BUDGET,
    ):
        self.allowed_domains = {d.lower().lstrip(".") for d in allowed_domains}
        self.click_budget = click_budget
        self.actions_taken = 0
        self._seen: list[tuple[str, str]] = []

    # -- page-level --------------------------------------------------------

    def check_page(self, observation: PageObservation) -> Violation | None:
        """Is it safe to still be here?"""
        host = (urlparse(observation.url).hostname or "").lower()
        if not self._domain_allowed(host):
            return Violation(
                stops.OFF_ALLOWLIST,
                f"navigation reached {host or observation.url!r}, which is not on "
                "the approved domain list",
            )

        hit = _matches(TRANSACTION_PAGE_PATTERNS, observation.text) or _matches(
            TRANSACTION_PAGE_PATTERNS, observation.title)
        if hit:
            return Violation(
                stops.TRANSACTION_PAGE,
                f"this page confirms a financial transaction (it says {hit!r}). "
                "Nothing was submitted.",
            )

        if observation.is_modal or _matches(CONSENT_PATTERNS, observation.text):
            hit = _matches(CONSENT_PATTERNS, observation.text) or "a modal dialog"
            return Violation(
                stops.CONSENT_INTERSTITIAL,
                f"a consent or notice screen is blocking the flow ({hit!r}). The "
                "agent never accepts anything on the firm's behalf.",
            )
        return None

    def _domain_allowed(self, host: str) -> bool:
        if not host:
            return False
        return any(
            host == domain or host.endswith("." + domain)
            for domain in self.allowed_domains
        )

    # -- action-level ------------------------------------------------------

    def check_action(self, action: Action, observation: PageObservation) -> Violation | None:
        """May this action happen? Checked before the driver ever sees it."""
        if self.actions_taken >= self.click_budget:
            return Violation(
                stops.CLICK_BUDGET_EXCEEDED,
                f"the task used its whole budget of {self.click_budget} actions "
                "without finishing",
            )

        element = observation.element(action.element_id)
        if element is None:
            return Violation(
                stops.ELEMENT_NOT_FOUND,
                f"there is no control called {action.element_id!r} on this page",
            )

        reason = is_forbidden_element(element)
        if reason:
            return Violation(
                stops.FORBIDDEN_ELEMENT,
                f"{element.label!r} is a control the agent may never use, because "
                f"{reason}",
            )

        fingerprint = (str(action), observation.signature)
        if fingerprint in self._seen:
            return Violation(
                stops.REPEAT_ACTION,
                f"{action} was already tried on this same page and changed nothing",
            )
        return None

    def note_action(self, action: Action, observation: PageObservation) -> None:
        """Record an action that was permitted and performed."""
        self.actions_taken += 1
        self._seen.append((str(action), observation.signature))

    @property
    def budget_left(self) -> int:
        return max(0, self.click_budget - self.actions_taken)
